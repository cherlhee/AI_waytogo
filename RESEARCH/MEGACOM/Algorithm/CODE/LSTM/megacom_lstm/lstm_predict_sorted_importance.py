"""MEGACOM: ai_oiltemp 최신 ID 기준으로 ai_data 이력 조회 후 LSTM 예측 저장.

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
    sql = """SELECT id, comcode, device_id, input_time
             FROM ai_oiltemp
             WHERE comcode=%s AND device_id=%s
             ORDER BY id DESC LIMIT 1"""
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(sql, (comcode, device_id))
        return cur.fetchone()
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
    LOG.info("기준 oiltemp_id=%s / ai_data 센서 %d건", latest["id"], len(df))
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


def write_results(conn, latest, outputs, importances, contributions, version):
    """ai_lstm_r 실제 컬럼명(device_id 또는 deviceId)을 확인한 후 저장."""
    cur = conn.cursor()
    try:
        cur.execute("SHOW COLUMNS FROM ai_lstm_r")
        available = {row[0] for row in cur.fetchall()}
        device_col = next((c for c in ("device_id", "deviceId") if c in available), None)
        if device_col is None:
            raise ValueError(
                "ai_lstm_r에 device_id/deviceId 컬럼이 없습니다. "
                f"실제 컬럼: {sorted(available)}"
            )
        required = {
            "oiltemp_id", "comcode", "input_time", "current_datetime",
            "prediction_horizon_min", "prediction_target_time", "lstm_prediction",
            "lstm_anomaly_score", "feature_importance", "feature_contributions",
            "model_version", "created_at",
        }
        missing = required - available
        if missing:
            raise ValueError(f"ai_lstm_r 필수 컬럼 누락: {sorted(missing)}")
        sql = f"""INSERT INTO ai_lstm_r
           (oiltemp_id, comcode, `{device_col}`, input_time, current_datetime,
            prediction_horizon_min, prediction_target_time, lstm_prediction,
            lstm_anomaly_score, feature_importance, feature_contributions,
            model_version, created_at)
           VALUES (%s,%s,%s,%s,NOW(3),%s,%s,%s,NULL,%s,%s,%s,NOW(3))
           ON DUPLICATE KEY UPDATE
             lstm_prediction=VALUES(lstm_prediction),
             feature_importance=VALUES(feature_importance),
             feature_contributions=COALESCE(VALUES(feature_contributions),feature_contributions),
             current_datetime=NOW(3)"""
        for horizon, prediction in outputs.items():
            imp = importance_as_sorted_json(importances[horizon])
            contribution = (
                json.dumps({"method": "integrated_gradients", "unit": "C",
                            "values": contributions[horizon]}, ensure_ascii=False)
                if contributions.get(horizon) is not None else None
            )
            cur.execute(sql, (
                int(latest["id"]), latest["comcode"], latest["device_id"],
                latest["input_time"], horizon,
                latest["input_time"] + timedelta(minutes=horizon),
                round(float(prediction), 2), imp, contribution, version,
            ))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="한 번만 실행")
    parser.add_argument("--interval", type=float, default=5, help="폴링 간격(초)")
    parser.add_argument("--explain-every", type=int, default=12,
                        help="새 ID 몇 건마다 IG를 계산할지 (0=미계산)")
    parser.add_argument("--comcode", default=COMCODE)
    parser.add_argument("--device-id", default=DEVICE_ID)
    args = parser.parse_args()
    if not args.comcode or not args.device_id:
        parser.error("--comcode 및 --device-id를 지정하세요")
    if args.interval <= 0 or args.explain_every < 0:
        parser.error("--interval은 양수, --explain-every는 0 이상이어야 합니다")

    from tensorflow.keras.models import load_model
    meta = json.loads((MODEL_DIR / "metadata.json").read_text(encoding="utf-8"))
    if (tuple(meta["features"]) != tuple(FEATURES)
            or int(meta["input_minutes"]) != INPUT_MINUTES
            or tuple(meta["horizons"]) != tuple(HORIZONS)):
        raise ValueError("학습 모델과 추론 설정이 다릅니다")

    scaler_x = joblib.load(MODEL_DIR / "scaler_X.pkl")
    scaler_y = joblib.load(MODEL_DIR / "scaler_y.pkl")
    models = {h: load_model(MODEL_DIR / f"lstm_{h}min.keras", compile=False)
              for h in HORIZONS}
    importances = {
        h: json.loads((MODEL_DIR / f"importance_{h}min.json").read_text(encoding="utf-8"))
        for h in HORIZONS
    }

    last_success = None
    count = 0
    while True:
        conn = None
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            latest = get_latest(conn, args.comcode, args.device_id)
            if latest is None:
                LOG.warning("ai_oiltemp에 해당 업체/설비의 데이터가 없습니다")
            elif latest["id"] != last_success:
                history = get_history(conn, latest)
                if history.empty:
                    raise ValueError("ai_data 과거 센서 데이터가 없습니다. 시간 형식을 확인하세요")
                minute_data = minute_features(history, anchor=latest["input_time"], realtime=True)
                tail = minute_data.iloc[-INPUT_MINUTES:]
                if len(tail) != INPUT_MINUTES or tail[list(FEATURES)].isna().any().any():
                    raise ValueError("과거 30분 입력이 부족하거나 센서 결측값이 있습니다")
                x = scaler_x.transform(tail[list(FEATURES)]).astype("float32")
                x = x.reshape(1, INPUT_MINUTES, len(FEATURES))
                outputs = {
                    h: float(scaler_y.inverse_transform(models[h].predict(x, verbose=0))[0, 0])
                    for h in HORIZONS
                }
                explain = args.explain_every > 0 and count % args.explain_every == 0
                contributions = {
                    h: integrated_gradients(models[h], x, scaler_y) if explain else None
                    for h in HORIZONS
                }
                write_results(conn, latest, outputs, importances, contributions, meta["version"])
                last_success = latest["id"]
                count += 1
                LOG.info("저장 완료 oiltemp_id=%s, 예측=%s, IG=%s",
                         last_success, outputs, explain)
            if args.once:
                break
        except Exception:
            LOG.exception("예측/DB 처리 실패")
            if args.once:
                raise
        finally:
            if conn is not None and conn.is_connected():
                conn.close()
        if not args.once:
            time.sleep(args.interval)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    main()
