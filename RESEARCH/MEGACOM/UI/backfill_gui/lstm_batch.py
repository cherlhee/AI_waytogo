"""MEGACOM: ai_data 최신 시각 기준 LSTM 예측, 목표시각 실제온도 보정 및 MAE/RMSE 조회.

사용: python lstm_predict.py --once
      python lstm_predict.py --interval 5
"""
from collections import Counter
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


def write_results(conn, latest, outputs, importances, contributions, version, device_col, actuals, done, overwrite, cursor):
    """Update existing rows by logical key, preserving idx and foreign keys."""
    t = latest["input_time"]
    key_prefix = (latest["comcode"], latest["device_id"], t)
    cur = cursor
    inserted = updated = 0
    for horizon, prediction in outputs.items():
        prediction = round(float(prediction), 2)
        if not np.isfinite(prediction):
            raise ValueError("Non-finite LSTM prediction")
        actual = actuals[horizon]
        error = None if actual is None else round(prediction - actual, 2)
        contribution = (json.dumps({"method": "integrated_gradients", "unit": "C",
                                    "values": contributions[horizon]}, ensure_ascii=False)
                        if contributions.get(horizon) is not None else None)
        values = (t + timedelta(seconds=5), t + timedelta(minutes=horizon),
                  round(latest["oil_temp_current"], 2), prediction, actual, error,
                  importance_as_sorted_json(importances[horizon]), contribution,
                  version, t + timedelta(seconds=5, milliseconds=500))
        key = (*key_prefix, horizon)
        if (t, horizon) in done:
            if not overwrite:
                continue
            cur.execute(f"""UPDATE ai_lstm_r SET current_datetime=%s,
                prediction_target_time=%s, oil_temp_current=%s, lstm_prediction=%s,
                oil_temp_actual=%s, prediction_error=%s, feature_importance=%s,
                feature_contributions=%s, model_version=%s, created_at=%s,
                lstm_anomaly_score=NULL
                WHERE comcode=%s AND `{device_col}`=%s AND input_time=%s
                AND prediction_horizon_min=%s""", (*values, *key))
            updated += 1
        else:
            cur.execute(f"""INSERT INTO ai_lstm_r
                (current_datetime,prediction_target_time,oil_temp_current,lstm_prediction,
                 oil_temp_actual,prediction_error,feature_importance,feature_contributions,
                 model_version,created_at,comcode,`{device_col}`,input_time,
                 prediction_horizon_min,lstm_anomaly_score)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL)""", (*values, *key))
            done.add((t, horizon))
            inserted += 1
    return inserted, updated


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


from batch_common import options,bounds,DEVICES,read_rows,existing

from bisect import bisect_left

def actual_index(rows):
    values = {}
    for r in rows:
        try:
            v = float(r['io003'])
            if np.isfinite(v):
                values[pd.Timestamp(r['input_time']).to_pydatetime()] = v
        except (TypeError, ValueError):
            continue
    return sorted(values), values

def future_actual(index, anchor, horizon, tolerance=0):
    target = anchor + timedelta(minutes=int(horizon))
    times, values = index
    i = bisect_left(times, target)
    candidates = [times[j] for j in (i-1,i) if 0 <= j < len(times)
                  and times[j] > anchor]
    if not candidates:
        return target, None, None
    matched = min(candidates, key=lambda t: (abs(t-target), t))
    if abs((matched-target).total_seconds()) > tolerance:
        return target, None, None
    return target, matched, round(values[matched], 2)

def repair_actuals(conn, col, company, device, lo, hi, index, tolerance, batch_size):
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT input_time,prediction_horizon_min FROM ai_lstm_r WHERE comcode=%s AND `{col}`=%s AND input_time >= %s AND input_time < %s", (company,device,lo,hi))
        keys = cur.fetchall()
        sql = f"UPDATE ai_lstm_r SET prediction_target_time=%s, oil_temp_actual=%s, prediction_error=ROUND(lstm_prediction-%s,2) WHERE comcode=%s AND `{col}`=%s AND input_time=%s AND prediction_horizon_min=%s"
        params=[]; matched_count=missing_count=0
        for raw_t,h in keys:
            t=pd.Timestamp(raw_t).to_pydatetime(); h=int(h)
            if h not in HORIZONS: continue
            target, matched, v=future_actual(index,t,h,tolerance)
            if matched is None: missing_count+=1
            else: matched_count+=1
            if matched_count+missing_count<=8:
                print(f'[{device}] ACTUAL anchor={t} horizon={h} target={target} source={matched} io003={v}',flush=True)
            params.append((target,v,v,company,device,raw_t,h))
            if len(params)>=batch_size*4:
                cur.executemany(sql,params); conn.commit(); params.clear()
        if params: cur.executemany(sql,params); conn.commit()
        print(f'[{device}] actual repair: matched={matched_count}, NULL={missing_count}',flush=True)
    except BaseException:
        conn.rollback(); raise
    finally: cur.close()


class BufferedWrites:
    def __init__(self, cursor):
        self.cursor = cursor
        self.groups = {}
    def execute(self, sql, params):
        self.groups.setdefault(sql, []).append(params)
    def flush(self):
        for sql, params in self.groups.items():
            self.cursor.executemany(sql, params)
        self.groups.clear()


def main():
    p=argparse.ArgumentParser(description='Historical LSTM backfill'); options(p)
    p.add_argument('--explain-every',type=int,default=12)
    p.add_argument('--fill-io045',action='store_true',help='Legacy option; io044/io045/io046 missing values are now filled by default')
    p.add_argument('--ig-batch-size',type=int,default=32)
    mode=p.add_mutually_exclusive_group()
    mode.add_argument('--overwrite',dest='overwrite',action='store_true')
    mode.add_argument('--skip-existing',dest='overwrite',action='store_false')
    p.set_defaults(overwrite=True)
    p.add_argument('--actual-only',action='store_true',help='Repair actual temperatures without running LSTM')
    p.add_argument('--actual-tolerance-seconds',type=int,default=0)
    a=p.parse_args(); lo,hi=bounds(p,a)
    if a.actual_tolerance_seconds<0 or a.explain_every<0 or a.ig_batch_size<1: p.error('Invalid tolerance or explain interval')
    print('LSTM mode:', 'overwrite' if a.overwrite else 'skip-existing',flush=True)
    if a.actual_only:
        conn=mysql.connector.connect(**DB_CONFIG)
        try:
            col=check_schema(conn)
            for device in ((a.device_id,) if a.device_id else DEVICES):
                day=lo
                while day<hi:
                    end=min(day+timedelta(days=1),hi)
                    rows=read_rows(conn,a.comcode,device,day,end+timedelta(minutes=max(HORIZONS),seconds=a.actual_tolerance_seconds+1),('io003',))
                    repair_actuals(conn,col,a.comcode,device,day,end,actual_index(rows),a.actual_tolerance_seconds,a.batch_size)
                    day=end
        finally: conn.close()
        return
    print('Loading TensorFlow and models...',flush=True)
    import tensorflow as tf
    from tensorflow.keras.models import load_model
    meta=json.loads((MODEL_DIR/'metadata.json').read_text(encoding='utf-8'))
    if tuple(meta['features'])!=tuple(FEATURES) or int(meta['input_minutes'])!=INPUT_MINUTES or tuple(meta['horizons'])!=tuple(HORIZONS): raise ValueError('Model configuration mismatch')
    sx=joblib.load(MODEL_DIR/'scaler_X.pkl'); sy=joblib.load(MODEL_DIR/'scaler_y.pkl')
    # Keep the trained 16-feature layout, but never query humidity in backfill.
    humidity_idx = FEATURES.index('io048')
    means = getattr(sx, 'mean_', None)
    if means is None or np.asarray(means).shape != (len(FEATURES),):
        raise ValueError('scaler_X.pkl has no compatible training mean_; cannot fix humidity safely')
    humidity_mean = float(means[humidity_idx])
    if not np.isfinite(humidity_mean):
        raise ValueError('Training humidity mean is not finite')
    fill_cols = ('io044', 'io045', 'io046')
    train_means = {c: float(means[FEATURES.index(c)]) for c in fill_cols}
    if not all(np.isfinite(v) for v in train_means.values()):
        raise ValueError('Non-finite training means for missing sensor imputation')
    print(f'Missing sensor values filled with training means: {train_means}', flush=True)
    batch_sensor_cols = tuple(c for c in SENSOR_COLS if c != 'io048')
    print(f'Humidity io048 fixed to training mean={humidity_mean:.6f}; DB humidity read disabled', flush=True)
    models={}; predictors={}; explainers={}
    def make_explainer(model):
        @tf.function(input_signature=[tf.TensorSpec((None, INPUT_MINUTES, len(FEATURES)), tf.float32)])
        def explain(z):
            total = tf.zeros_like(z)
            for k in tf.range(1, 17):
                v = z * (tf.cast(k, tf.float32) / 16.0)
                with tf.GradientTape() as tape:
                    tape.watch(v)
                    y = model(v, training=False)
                total += tape.gradient(y, v)
            return tf.reduce_sum(z * total / 16.0, axis=1) * float(sy.scale_[0])
        return explain
    def make_predictor(model):
        @tf.function(input_signature=[tf.TensorSpec((None, INPUT_MINUTES, len(FEATURES)), tf.float32)], reduce_retracing=True)
        def infer(x):
            return model(x, training=False)
        return infer
    for h in HORIZONS:
        models[h]=load_model(MODEL_DIR/f'lstm_{h}min.keras',compile=False)
        predictors[h]=make_predictor(models[h])
        explainers[h]=make_explainer(models[h])
        print(f'{h}min model loaded',flush=True)
    importance={h:json.loads((MODEL_DIR/f'importance_{h}min.json').read_text(encoding='utf-8')) for h in HORIZONS}
    print('Connecting to database...',flush=True)
    conn=mysql.connector.connect(**DB_CONFIG)
    try:
        col=check_schema(conn)
        for device in ((a.device_id,) if a.device_id else DEVICES):
            day=lo; count=0
            while day<hi:
                end=min(day+timedelta(days=1),hi)
                started=time.monotonic()
                print(f'[{device}] {day.date()} loading historical data...',flush=True)
                rows=read_rows(conn,a.comcode,device,day-timedelta(minutes=38),end+timedelta(minutes=120,seconds=a.actual_tolerance_seconds+1),batch_sensor_cols)
                for r in rows:r['_time']=pd.Timestamp(r['input_time']).to_pydatetime()
                idx=actual_index(rows); done=existing(conn,'ai_lstm_r',col,a.comcode,device,day,end)
                df=pd.DataFrame(rows,columns=['input_time',*batch_sensor_cols]);df['input_time']=pd.to_datetime(df['input_time'])
                for c in batch_sensor_cols:df[c]=pd.to_numeric(df[c],errors='coerce')
                df['io048'] = humidity_mean
                times=df['input_time']; reasons=Counter(); bad_columns=Counter(); pending=[]; skipped=0; seen=0; inserted=0; updated=0; already=0
                total=sum(day<=r['_time']<end for r in rows)
                print(f'[{device}] source anchors={total}, existing predictions={len(done)}, IG every={a.explain_every}',flush=True)
                print(f'[{device}] loaded rows={len(df)}, range={times.min()} ~ {times.max()}',flush=True)
                print(f'[{device}] raw missing counts={df[list(batch_sensor_cols)].isna().sum().to_dict()}',flush=True)
                print(f'[{device}] zero current counts={(df[["io007","io008","io009"]]==0).sum().to_dict()}',flush=True)
                cur=conn.cursor()
                def progress():
                    elapsed=time.monotonic()-started
                    eta=elapsed*(total-seen)/seen if seen else 0
                    print(f'[{device}] {seen}/{total} ({100*seen/max(total,1):.2f}%) inserted={inserted} updated={updated} invalid={skipped} existing anchors={already} elapsed={elapsed:.1f}s ETA={eta:.1f}s (prediction phase)',flush=True)
                    if reasons:
                        print(f'[{device}] invalid reasons={dict(reasons)}; nonfinite feature columns={dict(bad_columns)}',flush=True)
                def flush():
                    nonlocal count, inserted, updated
                    if not pending:return
                    tick=time.monotonic()
                    writer=BufferedWrites(cur)
                    X=tf.convert_to_tensor(np.stack([v[1] for v in pending]),dtype=tf.float32)
                    predictions={h:sy.inverse_transform(predictors[h](X).numpy().reshape(-1,1))[:,0] for h in HORIZONS}
                    infer_seconds=time.monotonic()-tick
                    tick=time.monotonic()
                    ig = {}
                    if a.explain_every:
                        for h in HORIZONS:
                            selected = [j for j, (_, _, missing) in enumerate(pending)
                                        if h in missing and (count+j)%a.explain_every==0]
                            for start in range(0, len(selected), a.ig_batch_size):
                                js = selected[start:start+a.ig_batch_size]
                                vals = explainers[h](tf.gather(X, js)).numpy()
                                for j, row in zip(js, vals):
                                    ig[j,h] = {name: round(float(v),4) for name,v in zip(FEATURES,row)}
                    ig_seconds=time.monotonic()-tick
                    tick=time.monotonic()
                    for j,(latest,x,missing) in enumerate(pending):
                        outputs={h:float(predictions[h][j]) for h in missing}
                        contributions={h:ig.get((j,h)) for h in missing}
                        actuals={h:future_actual(idx,latest['input_time'],h,a.actual_tolerance_seconds)[2] for h in missing}
                        ni,nu=write_results(conn,latest,outputs,importance,contributions,meta['version'],col,actuals,done,a.overwrite,writer)
                        inserted+=ni; updated+=nu; count+=1
                    writer.flush()
                    conn.commit()
                    print(f'[{device}] batch={len(pending)} inference={infer_seconds:.2f}s IG={ig_seconds:.2f}s DB/packing={time.monotonic()-tick:.2f}s',flush=True)
                    pending.clear()
                try:
                    for i,r in enumerate(rows):
                        t=r['_time']
                        if not day<=t<end:continue
                        seen+=1
                        missing=[h for h in HORIZONS if a.overwrite or (t,h) not in done]
                        if missing:
                            left=times.searchsorted(t-timedelta(minutes=38),side='right')
                            history=df.iloc[left:i+1].copy()
                            tail=minute_features(history,anchor=t,realtime=True).iloc[-INPUT_MINUTES:].copy()
                            tail['io048'] = humidity_mean
                            for c, mean in train_means.items():
                                tail[c] = tail[c].replace([np.inf, -np.inf], np.nan).fillna(mean)
                            current=df.iloc[i]['io003']
                            arr=tail[list(FEATURES)].to_numpy(dtype=float)
                            bad=~np.isfinite(arr)
                            cols=[c for j,c in enumerate(FEATURES) if bad[:,j].any()]
                            reason=None
                            if len(tail)!=INPUT_MINUTES:
                                reason='insufficient feature rows'
                            elif cols:
                                reason='nonfinite features'
                            elif not np.isfinite(current):
                                reason='invalid current oil temperature'
                            else:
                                x=sx.transform(tail[list(FEATURES)]).astype('float32')
                                if not np.isfinite(x).all():
                                    reason='nonfinite scaled input'
                            if reason:
                                skipped+=1
                                reasons[reason]+=1
                                bad_columns.update(cols)
                                if skipped<=5:
                                    print(f'[{device}] INVALID {t}: {reason}; history={len(history)}, feature rows={len(tail)}, bad columns={cols}',flush=True)
                                    if cols:
                                        print(tail.loc[bad.any(axis=1),cols].head(5).to_string(),flush=True)
                                    print(f'raw missing={history[list(batch_sensor_cols)].isna().sum().to_dict()}; zero current={(history[["io007","io008","io009"]]==0).sum().to_dict()}',flush=True)
                            else:
                                pending.append((dict(comcode=a.comcode,device_id=device,input_time=t,oil_temp_current=float(current)),x,missing))
                        else: already+=1
                        if seen%a.batch_size==0:
                            flush(); progress()
                    flush(); progress()
                    print(f'[{device}] correcting actual temperatures for existing predictions...',flush=True)
                    repair_actuals(conn,col,a.comcode,device,day,end,idx,a.actual_tolerance_seconds,a.batch_size)
                    print(f'[{device}] {day.date()} completed: inserted={inserted}, updated={updated}, invalid={skipped}, elapsed={time.monotonic()-started:.1f}s',flush=True)
                except BaseException:conn.rollback();raise
                finally:cur.close()
                day=end
    finally:conn.close()
    print('LSTM backfill completed',flush=True)
if __name__=='__main__':main()
