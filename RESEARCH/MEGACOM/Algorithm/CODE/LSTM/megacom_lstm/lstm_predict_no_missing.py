"""MEGACOM LSTM: ai_data 신규 시각 순차 처리 + 재시작 복구 + 지연 입력 재검사.

최초 실행 전 ai_lstm_r의 oiltemp_id는 NULL 허용이어야 하며,
(comcode, device_id, input_time, prediction_horizon_min) UNIQUE KEY가 필요합니다.

사용:
  python lstm_predict_no_missing.py --once
  python lstm_predict_no_missing.py --interval 5 --lookback-minutes 10
  python lstm_predict_no_missing.py --initial-backfill-minutes 60
"""
import argparse
import json
import logging
import time
from datetime import datetime, timedelta

import joblib
import mysql.connector
import numpy as np
import pandas as pd

from config import DB_CONFIG, COMCODE, DEVICE_ID, MODEL_DIR, HORIZONS, FEATURES, INPUT_MINUTES
from lstm_features import minute_features

LOG = logging.getLogger('lstm_predict')
SENSOR_COLS = ('io003', 'io028', 'io010', 'io044', 'io045', 'io046', 'io048',
               'io007', 'io008', 'io009', 'io004', 'io005')
STATE_TABLE = 'ai_lstm_progress'
RESULT_TABLE = 'ai_lstm_r'


def dt(value):
    return pd.Timestamp(value).to_pydatetime().replace(tzinfo=None)


def sqltime(value):
    return dt(value).strftime('%Y-%m-%d %H:%M:%S')


def setup(conn):
    cur = conn.cursor()
    try:
        cur.execute(f'''CREATE TABLE IF NOT EXISTS {STATE_TABLE} (
            comcode VARCHAR(15) NOT NULL,
            device_id VARCHAR(20) NOT NULL,
            last_success_time DATETIME(3) NULL,
            updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                ON UPDATE CURRENT_TIMESTAMP(3),
            PRIMARY KEY (comcode, device_id)
        ) ENGINE=InnoDB''')
        cur.execute(f'SHOW COLUMNS FROM {RESULT_TABLE}')
        columns = {row[0]: row for row in cur.fetchall()}
        device_col = next((x for x in ('device_id', 'deviceId') if x in columns), None)
        if device_col is None:
            raise RuntimeError('ai_lstm_r에 device_id/deviceId 컬럼이 없습니다')
        needed = {'comcode', 'input_time', 'prediction_horizon_min',
                  'prediction_target_time', 'lstm_prediction', 'feature_importance',
                  'feature_contributions', 'model_version', 'current_datetime', 'created_at'}
        missing = needed - set(columns)
        if missing:
            raise RuntimeError(f'ai_lstm_r 필수 컬럼 없음: {sorted(missing)}')
        if 'oiltemp_id' in columns and columns['oiltemp_id'][2] == 'NO' and columns['oiltemp_id'][4] is None:
            raise RuntimeError('ai_lstm_r.oiltemp_id가 NOT NULL입니다. NULL 허용으로 변경해야 합니다.')
        # ON DUPLICATE KEY UPDATE가 시각+예측기간을 기준으로 작동하도록 검사
        cur.execute(f'SHOW INDEX FROM {RESULT_TABLE}')
        indexes = {}
        for row in cur.fetchall():
            if row[1] == 0:  # Non_unique == 0
                indexes.setdefault(row[2], []).append((row[3], row[4]))
        expected = ['comcode', device_col, 'input_time', 'prediction_horizon_min']
        if not any([c for _, c in sorted(parts)] == expected for parts in indexes.values()):
            raise RuntimeError(
                'ai_lstm_r에 UNIQUE KEY(comcode, '+device_col+', input_time, '
                'prediction_horizon_min)가 필요합니다. 안내된 SQL로 먼저 추가하세요.')
        conn.commit()
        return device_col, columns
    finally:
        cur.close()


def get_progress(conn, comcode, device_id):
    cur = conn.cursor()
    try:
        cur.execute(f'SELECT last_success_time FROM {STATE_TABLE} '
                    'WHERE comcode=%s AND device_id=%s', (comcode, device_id))
        row = cur.fetchone()
        return dt(row[0]) if row and row[0] is not None else None
    finally:
        cur.close()


def get_latest_time(conn, comcode, device_id):
    cur = conn.cursor()
    try:
        cur.execute('SELECT input_time FROM ai_data WHERE comcode=%s AND deviceId=%s '
                    'ORDER BY input_time DESC LIMIT 1', (comcode, device_id))
        row = cur.fetchone()
        return dt(row[0]) if row else None
    finally:
        cur.close()


def get_times(conn, comcode, device_id, start, limit):
    cur = conn.cursor()
    try:
        cur.execute('SELECT input_time FROM ai_data WHERE comcode=%s AND deviceId=%s '
                    'AND input_time >= %s ORDER BY input_time ASC LIMIT %s',
                    (comcode, device_id, sqltime(start), limit))
        return [dt(row[0]) for row in cur.fetchall()]
    finally:
        cur.close()


def completed_times(conn, comcode, device_id, times, device_col):
    if not times:
        return set()
    placeholders = ','.join(['%s'] * len(times))
    cur = conn.cursor()
    try:
        cur.execute(f'''SELECT input_time, COUNT(DISTINCT prediction_horizon_min)
            FROM {RESULT_TABLE} WHERE comcode=%s AND `{device_col}`=%s
            AND input_time IN ({placeholders})
            AND prediction_horizon_min IN ({','.join(['%s'] * len(HORIZONS))})
            GROUP BY input_time''',
            (comcode, device_id, *times, *HORIZONS))
        return {dt(row[0]) for row in cur.fetchall() if int(row[1]) == len(HORIZONS)}
    finally:
        cur.close()


def get_history(conn, comcode, device_id, anchor):
    start = anchor - timedelta(minutes=38)
    cols = ', '.join(('input_time', *SENSOR_COLS))
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(f'''SELECT {cols} FROM ai_data WHERE comcode=%s AND deviceId=%s
            AND input_time > %s AND input_time <= %s ORDER BY input_time ASC''',
            (comcode, device_id, sqltime(start), sqltime(anchor)))
        rows = cur.fetchall()
    finally:
        cur.close()
    if not rows:
        return pd.DataFrame(columns=('input_time', *SENSOR_COLS))
    frame = pd.DataFrame(rows)
    frame['input_time'] = pd.to_datetime(frame['input_time'], errors='coerce')
    frame = frame.dropna(subset=['input_time'])
    for col in SENSOR_COLS:
        frame[col] = pd.to_numeric(frame[col], errors='coerce')
    return frame


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
            raise ValueError('Integrated Gradients 기울기 없음')
        total += grad
    attrs = (z - baseline) * total / steps
    values = tf.reduce_sum(attrs, axis=1).numpy()[0] * float(sy.scale_[0])
    return {name: round(float(val), 4) for name, val in zip(FEATURES, values)}


def importance_as_sorted_json(importance):
    if isinstance(importance, dict):
        items = importance.items()
    elif isinstance(importance, list):
        items = [(r['feature'], r['importance']) for r in importance]
    else:
        raise TypeError('중요도 JSON 형식 오류')
    ranked = [{'feature': str(k), 'importance': float(v)} for k, v in items]
    if not all(np.isfinite(row['importance']) for row in ranked):
        raise ValueError('중요도에 NaN/Inf 존재')
    ranked.sort(key=lambda row: row['importance'], reverse=True)
    return json.dumps(ranked, ensure_ascii=False, allow_nan=False)


def save_results_and_progress(conn, comcode, device_id, anchor, outputs,
                              importances, contributions, version, device_col, columns,
                              update_progress):
    # 네 개 결과와 체크포인트를 하나의 트랜잭션으로 저장
    fields = ['comcode', f'`{device_col}`', 'input_time', 'current_datetime',
              'prediction_horizon_min', 'prediction_target_time', 'lstm_prediction']
    vals = ['%s', '%s', '%s', 'NOW(3)', '%s', '%s', '%s']
    if 'lstm_anomaly_score' in columns:
        fields.append('lstm_anomaly_score')
        vals.append('NULL')
    fields += ['feature_importance', 'feature_contributions', 'model_version', 'created_at']
    vals += ['%s', '%s', '%s', 'NOW(3)']
    sql = f'''INSERT INTO {RESULT_TABLE} ({', '.join(fields)})
        VALUES ({', '.join(vals)})
        ON DUPLICATE KEY UPDATE
        lstm_prediction=VALUES(lstm_prediction),
        feature_importance=VALUES(feature_importance),
        feature_contributions=COALESCE(VALUES(feature_contributions), feature_contributions),
        model_version=VALUES(model_version), current_datetime=NOW(3)'''
    cur = conn.cursor()
    try:
        for horizon, prediction in outputs.items():
            imp = importance_as_sorted_json(importances[horizon])
            contribution = (json.dumps({'method': 'integrated_gradients', 'unit': 'C',
                                        'values': contributions[horizon]}, ensure_ascii=False)
                            if contributions.get(horizon) is not None else None)
            params = (comcode, device_id, anchor, int(horizon),
                      anchor + timedelta(minutes=int(horizon)), round(float(prediction), 2),
                      imp, contribution, version)
            cur.execute(sql, params)
        if update_progress:
            cur.execute(f'''INSERT INTO {STATE_TABLE}
                (comcode, device_id, last_success_time) VALUES (%s,%s,%s)
                ON DUPLICATE KEY UPDATE last_success_time=GREATEST(
                COALESCE(last_success_time, VALUES(last_success_time)), VALUES(last_success_time))''',
                (comcode, device_id, anchor))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def advance_progress(conn, comcode, device_id, anchor):
    cur = conn.cursor()
    try:
        cur.execute(f'''INSERT INTO {STATE_TABLE}
            (comcode, device_id, last_success_time) VALUES (%s,%s,%s)
            ON DUPLICATE KEY UPDATE last_success_time=GREATEST(
            COALESCE(last_success_time, VALUES(last_success_time)), VALUES(last_success_time))''',
            (comcode, device_id, anchor))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def predict_at(conn, comcode, device_id, anchor, models, scaler_x, scaler_y,
               importances, meta, device_col, columns, explain):
    history = get_history(conn, comcode, device_id, anchor)
    if history.empty:
        raise ValueError('과거 센서 데이터 없음')
    minute_data = minute_features(history, anchor=anchor, realtime=True)
    tail = minute_data.iloc[-INPUT_MINUTES:]
    if len(tail) != INPUT_MINUTES:
        raise ValueError(f'1분 특징값 부족: {len(tail)}/{INPUT_MINUTES}')
    nan_cols = tail[list(FEATURES)].isna().sum()
    if nan_cols.any():
        raise ValueError(f'센서 결측값: {nan_cols[nan_cols > 0].to_dict()}')
    x = scaler_x.transform(tail[list(FEATURES)]).astype('float32')
    x = x.reshape(1, INPUT_MINUTES, len(FEATURES))
    outputs = {h: float(scaler_y.inverse_transform(models[h].predict(x, verbose=0))[0, 0])
               for h in HORIZONS}
    contributions = {h: integrated_gradients(models[h], x, scaler_y) if explain else None
                     for h in HORIZONS}
    return outputs, contributions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true', help='현재 미처리 데이터를 1회 점검')
    parser.add_argument('--interval', type=float, default=5)
    parser.add_argument('--explain-every', type=int, default=12)
    parser.add_argument('--comcode', default=COMCODE)
    parser.add_argument('--device-id', default=DEVICE_ID)
    parser.add_argument('--lookback-minutes', type=int, default=10,
                        help='지연 입력 재확인 구간(분), 기본 10')
    parser.add_argument('--initial-backfill-minutes', type=int, default=10,
                        help='체크포인트 없는 최초 실행 시 과거 몇 분부터 처리할지')
    parser.add_argument('--batch-size', type=int, default=2000)
    args = parser.parse_args()
    if not args.comcode or not args.device_id:
        parser.error('comcode와 device-id를 지정하세요')
    if args.interval <= 0 or args.explain_every < 0 or args.lookback_minutes < 0 or args.initial_backfill_minutes < 0 or args.batch_size < 1:
        parser.error('인수 범위를 확인하세요')

    from tensorflow.keras.models import load_model
    meta = json.loads((MODEL_DIR / 'metadata.json').read_text(encoding='utf-8'))
    if (tuple(meta['features']) != tuple(FEATURES)
            or int(meta['input_minutes']) != INPUT_MINUTES
            or tuple(meta['horizons']) != tuple(HORIZONS)):
        raise ValueError('학습 모델과 추론 설정 불일치')
    scaler_x = joblib.load(MODEL_DIR / 'scaler_X.pkl')
    scaler_y = joblib.load(MODEL_DIR / 'scaler_y.pkl')
    models = {h: load_model(MODEL_DIR / f'lstm_{h}min.keras', compile=False)
              for h in HORIZONS}
    importances = {h: json.loads((MODEL_DIR / f'importance_{h}min.json').read_text(encoding='utf-8'))
                   for h in HORIZONS}
    LOG.info('LSTM 모델 로딩 완료: %s', list(HORIZONS))
    count = 0
    while True:
        conn = None
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            device_col, columns = setup(conn)
            progress = get_progress(conn, args.comcode, args.device_id)
            latest = get_latest_time(conn, args.comcode, args.device_id)
            if latest is None:
                LOG.warning('ai_data에 센서 데이터 없음')
            else:
                if progress is None:
                    start = latest - timedelta(minutes=args.initial_backfill_minutes)
                else:
                    start = progress - timedelta(minutes=args.lookback_minutes)
                # 최근 구간의 누락된 행과 체크포인트 이후의 신규 행을 함께 처리
                times = get_times(conn, args.comcode, args.device_id, start, args.batch_size)
                complete = completed_times(conn, args.comcode, args.device_id, times, device_col)
                done, skipped = 0, 0
                for anchor in times:
                    if anchor in complete:
                        skipped += 1
                        if progress is None or anchor > progress:
                            advance_progress(conn, args.comcode, args.device_id, anchor)
                            progress = anchor
                        continue
                    # 체크포인트 이전의 지연 입력은 결과만 보정, 체크포인트는 이동하지 않음
                    is_new = progress is None or anchor > progress
                    explain = args.explain_every > 0 and count % args.explain_every == 0
                    try:
                        outputs, contributions = predict_at(
                            conn, args.comcode, args.device_id, anchor,
                            models, scaler_x, scaler_y, importances, meta,
                            device_col, columns, explain)
                        save_results_and_progress(
                            conn, args.comcode, args.device_id, anchor,
                            outputs, importances, contributions, meta['version'],
                            device_col, columns, update_progress=is_new)
                    except Exception:
                        LOG.exception('예측 실패 input_time=%s (재시도 예정)', anchor)
                        # 순차 처리 실패 시 이후 시각으로 체크포인트를 넘기지 않음
                        break
                    if is_new:
                        progress = anchor
                    count += 1
                    done += 1
                    LOG.info('저장 완료 input_time=%s / 예측=%s / IG=%s', anchor,
                             {h: round(v, 2) for h, v in outputs.items()}, explain)
                LOG.info('점검 완료: 조회=%d 저장=%d 기존완료=%d 체크포인트=%s',
                         len(times), done, skipped, progress)
        except Exception:
            LOG.exception('DB/처리 실패')
            if args.once:
                raise
        finally:
            if conn is not None and conn.is_connected():
                conn.close()
        if args.once:
            break
        time.sleep(args.interval)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s')
    main()
