"""MEGACOM: ai_data 최신 시각 기준 LSTM 예측, 목표시각 실제온도 보정 및 MAE/RMSE 조회.

사용: python lstm_predict.py --once
      python lstm_predict.py --interval 5
"""
import argparse
import json
import logging
import time
from datetime import timedelta

import joblib
import mysql.connector
import numpy as np
import pandas as pd

from config import (
    DB_CONFIG, COMCODE, DEVICE_ID, MODEL_DIR, HORIZONS,
    FEATURES, INPUT_MINUTES,
)
from lstm_features import minute_features

LOG = logging.getLogger("lstm_predict")

# ai_data의 실제 컬럼명은 deviceId (ai_oiltemp은 device_id)
SENSOR_COLS = (
    "io003", "io028", "io010", "io044", "io045", "io046", "io048",
    "io007", "io008", "io009", "io004", "io005",
)


def get_latest(conn, comcode, device_id):
    sql = """
        SELECT
            comcode,
            deviceId,
            input_time,
            io003
        FROM ai_data
        WHERE comcode = %s
          AND deviceId = %s
        ORDER BY input_time DESC
        LIMIT 1
    """

    cur = conn.cursor(dictionary=True)

    try:
        cur.execute(sql, (comcode, device_id))
        latest = cur.fetchone()

        if latest:
            latest["device_id"] = latest["deviceId"]
            latest["oil_temp_current"] = float(latest["io003"]) if latest["io003"] not in (None, "") else None
            latest["input_time"] = pd.Timestamp(
                latest["input_time"]
            ).to_pydatetime()

        return latest

    finally:
        cur.close()


def get_history(conn, latest):
    """ai_oiltemp.id의 업체/설비/시각에 대응하는 ai_data 과거 38분 센서값.

    ai_data.input_time은 VARCHAR(20) 'YYYY-MM-DD HH:MM:SS' 형식을 가정.
    ISO 형식(T 구분자), 밀리초/UTC 등 다른 형식이면 수정 필요.
    """
    end = pd.Timestamp(latest["input_time"]).to_pydatetime()
    start = end - timedelta(minutes=38)
    columns = ", ".join(("input_time", *SENSOR_COLS))
    sql = f"""SELECT {columns}
              FROM ai_data
              WHERE comcode=%s AND deviceId=%s
                AND input_time > %s AND input_time <= %s
              ORDER BY input_time ASC"""
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(sql, (
            latest["comcode"], latest["device_id"],
            start.strftime("%Y-%m-%d %H:%M:%S"),
            end.strftime("%Y-%m-%d %H:%M:%S"),
        ))
        rows = cur.fetchall()
    finally:
        cur.close()
    if not rows:
        return pd.DataFrame(columns=("input_time", *SENSOR_COLS))
    df = pd.DataFrame(rows)
    df["input_time"] = pd.to_datetime(df["input_time"], errors="coerce")
    df = df.dropna(subset=["input_time"])
    for col in SENSOR_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    LOG.info("기준 input_time=%s / ai_data 센서 %d건", latest["input_time"], len(df))
    return df


def integrated_gradients(model, x, sy, steps=16):
    import tensorflow as tf
    z = tf.convert_to_tensor(x, dtype=tf.float32)
    baseline = tf.zeros_like(z)
    total = tf.zeros_like(z)
    for alpha in np.linspace(0, 1, steps + 1)[1:]:
        v = baseline + float(alpha) * (z - baseline)
        with tf.GradientTape() as tape:
            tape.watch(v)
            y = model(v, training=False)
        grad = tape.gradient(y, v)
        if grad is None:
            raise ValueError("Integrated Gradients 계산 실패: 기울기 없음")
        total += grad
    attrs = (z - baseline) * total / steps
    by_feature = tf.reduce_sum(attrs, axis=1).numpy()[0] * float(sy.scale_[0])
    return {name: round(float(val), 4) for name, val in zip(FEATURES, by_feature)}


def importance_as_sorted_json(importance):
    """중요도 내림차순 JSON 배열 생성 (MySQL JSON 배열은 순서 유지)."""
    if isinstance(importance, dict):
        items = importance.items()
    elif isinstance(importance, list):
        items = [(row["feature"], row["importance"]) for row in importance]
    else:
        raise TypeError("중요도는 dict 또는 feature/importance 객체 배열이어야 합니다")

    ranked = [
        {"feature": str(feature), "importance": float(value)}
        for feature, value in items
    ]
    if not all(np.isfinite(row["importance"]) for row in ranked):
        raise ValueError("중요도에 NaN 또는 무한대가 있습니다")
    ranked.sort(key=lambda row: row["importance"], reverse=True)
    return json.dumps(ranked, ensure_ascii=False, allow_nan=False)


def check_schema(conn):
    cur = conn.cursor()
    try:
        cur.execute("SHOW COLUMNS FROM ai_lstm_r")
        cols = {row[0] for row in cur.fetchall()}
    finally:
        cur.close()
    device_col = next((c for c in ("device_id", "deviceId") if c in cols), None)
    required = {"idx", "comcode", "input_time", "current_datetime",
                "prediction_horizon_min", "prediction_target_time",
                "oil_temp_current", "oil_temp_actual", "prediction_error",
                "lstm_prediction", "lstm_anomaly_score", "feature_importance",
                "feature_contributions", "model_version", "created_at"}
    missing = required - cols
    if not device_col or missing:
        raise ValueError(f"ai_lstm_r 스키마 확인 필요: device={device_col}, 누락={sorted(missing)}")
    return device_col


def write_results(conn, latest, outputs, importances, contributions, version, device_col):
    """4개 예측 저장. 실제온도/오차는 미래 시각에 별도 보정."""
    if latest["oil_temp_current"] is None or not np.isfinite(latest["oil_temp_current"]):
        raise ValueError("현재 io003 온도가 유효하지 않습니다")
    sql = f"""
        INSERT INTO ai_lstm_r
        (comcode, `{device_col}`, input_time, current_datetime,
         prediction_horizon_min, prediction_target_time,
         oil_temp_current, lstm_prediction, lstm_anomaly_score,
         feature_importance, feature_contributions, model_version, created_at)
        VALUES (%s,%s,%s,NOW(3),%s,%s,%s,%s,NULL,%s,%s,%s,NOW(3))
        ON DUPLICATE KEY UPDATE
            oil_temp_current=VALUES(oil_temp_current),
            lstm_prediction=VALUES(lstm_prediction),
            feature_importance=VALUES(feature_importance),
            feature_contributions=COALESCE(VALUES(feature_contributions), feature_contributions),
            current_datetime=NOW(3)
    """
    cur = conn.cursor()
    try:
        for horizon, prediction in outputs.items():
            contribution = (json.dumps({"method": "integrated_gradients", "unit": "C",
                                        "values": contributions[horizon]}, ensure_ascii=False)
                            if contributions.get(horizon) is not None else None)
            cur.execute(sql, (latest["comcode"], latest["device_id"],
                              latest["input_time"], horizon,
                              latest["input_time"] + timedelta(minutes=horizon),
                              round(latest["oil_temp_current"], 2),
                              round(float(prediction), 2),
                              importance_as_sorted_json(importances[horizon]),
                              contribution, version))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def update_actuals(conn, comcode, device_id, device_col, latest_time, tolerance_seconds=5, batch=500):
    """센서 기준시각이 목표시각+허용오차에 도달한 건만 보정.

    ai_data.input_time: YYYY-MM-DD HH:MM:SS 문자열. 같은 설비의 가장 가까운
    관측값을 ±tolerance_seconds 내에서 선택. 없으면 NULL 유지.
    """
    cur = conn.cursor(dictionary=True)
    updated = 0
    try:
        # 미래 관측값까지 고려한 뒤에 확정; 누락된 센서값은 NULL로 남김.
        cutoff = latest_time - timedelta(seconds=tolerance_seconds)
        cur.execute(f"""
            SELECT idx, prediction_target_time, lstm_prediction
            FROM ai_lstm_r
            WHERE comcode=%s AND `{device_col}`=%s
              AND oil_temp_actual IS NULL
              AND prediction_target_time <= %s
            ORDER BY prediction_target_time ASC LIMIT %s
        """, (comcode, device_id, cutoff, batch))
        pending = cur.fetchall()
        for row in pending:
            target = pd.Timestamp(row["prediction_target_time"]).to_pydatetime()
            lo = (target - timedelta(seconds=tolerance_seconds)).strftime("%Y-%m-%d %H:%M:%S")
            hi = (target + timedelta(seconds=tolerance_seconds)).strftime("%Y-%m-%d %H:%M:%S")
            cur.execute("""
                SELECT input_time, io003 FROM ai_data
                WHERE comcode=%s AND deviceId=%s
                  AND input_time >= %s AND input_time <= %s
                  AND io003 IS NOT NULL AND TRIM(io003) <> ''
                ORDER BY input_time ASC
            """, (comcode, device_id, lo, hi))
            candidates = []
            for r in cur.fetchall():
                try:
                    value = float(r["io003"])
                    ts = pd.Timestamp(r["input_time"]).to_pydatetime()
                    if np.isfinite(value):
                        candidates.append((abs((ts-target).total_seconds()), ts, value))
                except (ValueError, TypeError):
                    continue
            if not candidates:
                continue
            _, actual_time, actual = min(candidates, key=lambda x: (x[0], x[1]))
            prediction = float(row["lstm_prediction"])
            cur.execute("""
                UPDATE ai_lstm_r
                SET oil_temp_actual=%s, prediction_error=%s
                WHERE idx=%s AND oil_temp_actual IS NULL
            """, (round(actual, 2), round(prediction-actual, 2), row["idx"]))
            updated += cur.rowcount
        conn.commit()
        if updated:
            LOG.info("실제온도/오차 보정 %d건 (조회 %d건)", updated, len(pending))
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
    return updated


def log_metrics(conn, comcode, device_id, device_col):
    """예측기간별 누적 MAE/RMSE (실제온도 확보 건만)."""
    cur = conn.cursor()
    try:
        cur.execute(f"""
            SELECT prediction_horizon_min, COUNT(*),
                   ROUND(AVG(ABS(prediction_error)),3),
                   ROUND(SQRT(AVG(POW(prediction_error,2))),3)
            FROM ai_lstm_r
            WHERE comcode=%s AND `{device_col}`=%s
              AND prediction_error IS NOT NULL
            GROUP BY prediction_horizon_min ORDER BY prediction_horizon_min
        """, (comcode, device_id))
        for horizon, n, mae, rmse in cur.fetchall():
            LOG.info("%s분 성능: N=%d MAE=%s°C RMSE=%s°C", horizon, n, mae, rmse)
    finally:
        cur.close()


from batch_common import options,bounds,DEVICES,read_rows,actual_index,actual_at,existing

def main():
    p=argparse.ArgumentParser(description='Historical LSTM backfill');options(p)
    p.add_argument('--explain-every',type=int,default=12)
    a=p.parse_args();lo,hi=bounds(p,a)
    if a.explain_every<0:p.error('Invalid explain interval')
    from tensorflow.keras.models import load_model
    meta=json.loads((MODEL_DIR/'metadata.json').read_text(encoding='utf-8'))
    if tuple(meta['features'])!=tuple(FEATURES) or int(meta['input_minutes'])!=INPUT_MINUTES or tuple(meta['horizons'])!=tuple(HORIZONS):raise ValueError('Model configuration mismatch')
    sx=joblib.load(MODEL_DIR/'scaler_X.pkl');sy=joblib.load(MODEL_DIR/'scaler_y.pkl')
    models={h:load_model(MODEL_DIR/f'lstm_{h}min.keras',compile=False) for h in HORIZONS}
    importance={h:json.loads((MODEL_DIR/f'importance_{h}min.json').read_text(encoding='utf-8')) for h in HORIZONS}
    conn=mysql.connector.connect(**DB_CONFIG)
    try:
        col=check_schema(conn)
        for device in ((a.device_id,) if a.device_id else DEVICES):
            day=lo; count=0
            while day<hi:
                end=min(day+timedelta(days=1),hi)
                rows=read_rows(conn,a.comcode,device,day-timedelta(minutes=38),end+timedelta(minutes=121),SENSOR_COLS)
                for r in rows:r['_time']=pd.Timestamp(r['input_time']).to_pydatetime()
                idx=actual_index(rows); done=existing(conn,'ai_lstm_r',col,a.comcode,device,day,end)
                df=pd.DataFrame(rows,columns=['input_time',*SENSOR_COLS]);df['input_time']=pd.to_datetime(df['input_time'])
                for c in SENSOR_COLS:df[c]=pd.to_numeric(df[c],errors='coerce')
                times=df['input_time']; pending=[]; skipped=0; cur=conn.cursor()
                def flush():
                    nonlocal count
                    if not pending:return
                    X=np.stack([v[1] for v in pending]); predictions={h:sy.inverse_transform(models[h].predict(X,verbose=0))[:,0] for h in HORIZONS}
                    for j,(latest,x,missing) in enumerate(pending):
                        outputs={h:float(predictions[h][j]) for h in missing}
                        contributions={h:integrated_gradients(models[h],x[None,...],sy) if a.explain_every and count%a.explain_every==0 else None for h in missing}
                        write_results(conn,latest,outputs,importance,contributions,meta['version'],col);count+=1
                    pending.clear()
                try:
                    for i,r in enumerate(rows):
                        t=r['_time']
                        if not day<=t<end:continue
                        missing=[h for h in HORIZONS if (t,h) not in done]
                        if missing:
                            left=times.searchsorted(t-timedelta(minutes=38),side='right')
                            history=df.iloc[left:i+1].copy()
                            tail=minute_features(history,anchor=t,realtime=True).iloc[-INPUT_MINUTES:]
                            current=df.iloc[i]['io003']
                            if len(tail)!=INPUT_MINUTES or not np.isfinite(tail[list(FEATURES)].to_numpy(dtype=float)).all() or not np.isfinite(current):skipped+=1
                            else:
                                x=sx.transform(tail[list(FEATURES)]).astype('float32')
                                pending.append((dict(comcode=a.comcode,device_id=device,input_time=t,oil_temp_current=float(current)),x,missing))
                                if len(pending)>=a.batch_size:flush();print(device,t,'predicted anchors',count,flush=True)
                    flush()
                    for r in rows:
                        t=r['_time']
                        if not day<=t<end:continue
                        for h in HORIZONS:
                            v=actual_at(idx,t+timedelta(minutes=h),5)
                            if v is not None:cur.execute(f'UPDATE ai_lstm_r SET oil_temp_actual=%s,prediction_error=ROUND(lstm_prediction-%s,2) WHERE comcode=%s AND `{col}`=%s AND input_time=%s AND prediction_horizon_min=%s AND oil_temp_actual IS NULL',(v,v,a.comcode,device,t,h))
                    conn.commit();print(device,day,'predicted anchors',count,'invalid inputs',skipped,flush=True)
                except BaseException:conn.rollback();raise
                finally:cur.close()
                day=end
    finally:conn.close()
if __name__=='__main__':main()
