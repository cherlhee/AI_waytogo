"""11호기(R00015) CF 실시간 추론 및 MySQL 저장.

pip install mysql-connector-python python-dotenv
python cf_realtime_11.py --model cf_11_output/cf_11_model.json

설정 파일: mysql_config.env (이 스크립트와 같은 폴더)
환경변수: MYSQL_HOST, MYSQL_PORT(3306), MYSQL_USER, MYSQL_PASSWORD,
          MYSQL_DATABASE(airpredict), MYSQL_COMCODE(선택), SOURCE_TIME_UTC(기본 false)

주의: 학습은 1분 간격 관측값, 추론은 5초 간격 현재값+실제 5분 전 값.
실시간 분포 차이와 모델 성능을 별도로 검증해야 함.
"""
import argparse
import json
import logging
import math
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

# 실행 위치와 관계없이 스크립트 옆의 설정 파일을 자동으로 읽습니다.
ENV_PATH = Path(__file__).resolve().parent / 'mysql_config.env'
load_dotenv(dotenv_path=ENV_PATH, override=False)

DEVICE_ID = 'R00015'
HORIZONS = (10, 30, 60, 120)
TARGETS = (80, 85, 90)
SOURCE_COLS = {
    'oil_temp': 'io003', 'load': 'io028', 'power': 'io010',
    'flow_pressure': 'io044', 'flow_temp': 'io045',
    'flow_rate': 'io046', 'flow_humidity': 'io048',
    'current_u': 'io007', 'current_v': 'io008', 'current_w': 'io009',
    'voltage_uv': 'io004', 'voltage_vw': 'io005',
}
LOG = logging.getLogger('cf_realtime_11')


def num(value):
    try:
        v = float(value)
        return v if math.isfinite(v) else None
    except (ValueError, TypeError):
        return None


def parse_source_time(value, source_time_utc=False):
    """DB varchar(20) 시간은 YYYY-MM-DD HH:MM:SS[.fff] 가정.
    SOURCE_TIME_UTC=true인 경우 UTC -> 한국시간(naive KST) 변환.
    """
    if isinstance(value, datetime):
        dt = value
    else:
        s = str(value).strip().replace('T', ' ')
        if s.endswith('Z'):
            s = s[:-1] + '+00:00'
        dt = datetime.fromisoformat(s)
    if dt.tzinfo is not None:
        return dt.astimezone(timezone(timedelta(hours=9))).replace(tzinfo=None)
    if source_time_utc:
        return dt.replace(tzinfo=timezone.utc).astimezone(
            timezone(timedelta(hours=9))).replace(tzinfo=None)
    return dt


def load_model(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    models = data.get('models', {})
    expected = {f'{h}min_{t}c' for h in HORIZONS for t in TARGETS}
    missing = expected - set(models)
    if missing:
        raise ValueError(f'학습 모델 누락: {sorted(missing)}. 12개 모델 학습 완료 후 실행하세요.')
    return data


def db_connect():
    required = ('MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD')
    absent = [x for x in required if not os.environ.get(x)]
    if absent:
        raise RuntimeError(f'환경변수 설정 필요: {", ".join(absent)} (설정 파일: {ENV_PATH})')
    return mysql.connector.connect(
        host=os.environ['MYSQL_HOST'], port=int(os.getenv('MYSQL_PORT', '3307')),
        user=os.environ['MYSQL_USER'], password=os.environ['MYSQL_PASSWORD'],
        database=os.getenv('MYSQL_DATABASE', 'airpredict'),
        connection_timeout=10, autocommit=False, charset='utf8mb4')


def recent_rows(conn, comcode, limit, source_time_utc):
    """시간은 varchar이므로 표준 ISO형 문자열로 저장되어야 정렬이 유효함.
    현재 코드에서는 최신 limit개를 가져오고 Python에서 시간 정렬함.
    """
    where = 'WHERE deviceId = %s'
    params = [DEVICE_ID]
    if comcode:
        where += ' AND comcode = %s'
        params.append(comcode)
    cols = ', '.join('`'+v+'`' for v in SOURCE_COLS.values())
    sql = (f'SELECT `comcode`, `deviceId`, `input_time`, {cols} '
           f'FROM `ai_data` {where} ORDER BY `input_time` DESC LIMIT %s')
    params.append(limit)
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
    finally:
        cur.close()
    for row in rows:
        row['_time'] = parse_source_time(row['input_time'], source_time_utc)
    rows.sort(key=lambda r: (r['comcode'], r['_time']))
    return rows


def last_predictions(conn, comcode):
    where = "WHERE device_id = %s AND prediction_model = 'CF_WINDOW'"
    params = [DEVICE_ID]
    if comcode:
        where += ' AND comcode = %s'
        params.append(comcode)
    sql = f'SELECT comcode, MAX(input_time) AS latest FROM ai_oiltemp {where} GROUP BY comcode'
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(sql, tuple(params))
        return {r['comcode']: r['latest'] for r in cur.fetchall()}
    finally:
        cur.close()


def build_features(row, history):
    """history: 같은 comcode의 시간순 측정값(전류 0인 과거 행도 온도 참조 가능)."""
    f = {k: num(row[v]) for k, v in SOURCE_COLS.items()}
    currents = [f[k] for k in ('current_u', 'current_v', 'current_w')]
    if any(x is None or x <= 0 for x in currents):
        return None, '3상 전류 0/결측/음수'
    if any(v is None for v in f.values()):
        return None, '학습 입력변수 결측'
    mean_i = sum(currents)/3
    f['current_mean'] = mean_i
    f['current_unbalance_pct'] = max(abs(x-mean_i) for x in currents)/mean_i*100
    f['voltage_mean_measured'] = (f['voltage_uv']+f['voltage_vw'])/2

    # 현재 시점으로부터 5분 전과 가장 가까운 과거 샘플(오차 최대 90초).
    target = row['_time'] - timedelta(minutes=5)
    candidates = [r for r in history if r['comcode'] == row['comcode'] and r['_time'] <= row['_time']
                  and r['_time'] <= target and num(r['io003']) is not None]
    if not candidates:
        return None, '5분 전 온도 이력 부족'
    past = max(candidates, key=lambda r: r['_time'])
    if abs((past['_time']-target).total_seconds()) > 90:
        return None, '5분 전 관측 시각 오차 초과'
    f['temp_rate_5min'] = (f['oil_temp'] - num(past['io003']))/5
    return f, None


def cf_score(model, features):
    """train_cf_11.py의 searchsorted(side='right')와 동일한 bin 규칙."""
    score = 0.0
    for name in model['features']:
        x = features[name]
        if x is None or not math.isfinite(x):
            raise ValueError(f'특징값 없음: {name}')
        edges = model['edges'][name]
        # 경계값과 같으면 오른쪽 bin (train: searchsorted side='right')
        idx = sum(x >= edge for edge in edges[1:-1])
        score += model['rates'][name][idx] * model['weights'][name]
    return max(0., min(1., score))


def prediction_rows(row, features, artifact):
    result = []
    for horizon in HORIZONS:
        cf = {}
        alarms = {}
        thresholds = {}
        for target in TARGETS:
            model = artifact['models'][f'{horizon}min_{target}c']
            value = cf_score(model, features)
            cf[f'cf_{target}'] = round(value, 6)
            thresholds[f'threshold_{target}'] = float(model['threshold'])
            alarms[f'alarm_{target}'] = value >= model['threshold']
        # 90℃ > 85℃ > 80℃ 우선순위 (임계값 기준 판정)
        severity = ('DANGER' if alarms['alarm_90'] else
                    'WARNING' if alarms['alarm_85'] or alarms['alarm_80'] else 'NORMAL')
        payload = {**cf, **thresholds, **alarms, 'features': features,
                   'model_device': artifact.get('device'),
                   'cf_is_calibrated_probability': False}
        result.append((row['comcode'], DEVICE_ID, row['_time'], datetime.now(),
                       features['oil_temp'], horizon,
                       row['_time']+timedelta(minutes=horizon), 'CF_WINDOW',
                       json.dumps(payload, ensure_ascii=False, allow_nan=False), severity))
    return result


INSERT_SQL = '''
INSERT INTO ai_oiltemp
(comcode, device_id, input_time, current_datetime, oil_temp_current,
 prediction_horizon_min, prediction_target_time, prediction_model,
 prediction_features, prediction_result)
SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
FROM DUAL WHERE NOT EXISTS (
 SELECT 1 FROM ai_oiltemp WHERE comcode=%s AND device_id=%s
 AND input_time=%s AND prediction_model=%s AND prediction_horizon_min=%s
)
'''


def save_predictions(conn, records):
    cur = conn.cursor()
    inserted = 0
    try:
        for r in records:
            args = r + (r[0], r[1], r[2], r[7], r[5])
            cur.execute(INSERT_SQL, args)
            inserted += cur.rowcount
        conn.commit()
        return inserted
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def poll_once(conn, artifact, comcode, limit, source_time_utc, startup_latest_only):
    rows = recent_rows(conn, comcode, limit, source_time_utc)
    if not rows:
        LOG.info('11호기(R00015) ai_data 없음')
        return 0
    last = last_predictions(conn, comcode)
    groups = {}
    for r in rows:
        groups.setdefault(r['comcode'], []).append(r)
    total = 0
    for company, history in groups.items():
        latest_saved = last.get(company)
        if latest_saved is None and startup_latest_only:
            candidates = [history[-1]]
        else:
            candidates = [r for r in history if latest_saved is None or r['_time'] > latest_saved]
        for r in candidates:
            f, reason = build_features(r, history)
            if f is None:
                LOG.warning('%s %s 건너뜀: %s', company, r['_time'], reason)
                continue
            records = prediction_rows(r, f, artifact)
            n = save_predictions(conn, records)
            total += n
            LOG.info('%s %s 예측 %d행 저장: 10분 %s', company, r['_time'], n,
                     records[0][-1])
    return total


def main():
    ap = argparse.ArgumentParser(description='11호기 R00015 전용 CF 실시간 예측')
    ap.add_argument('--model', default='cf_11_output/cf_11_model.json')
    ap.add_argument('--interval', type=float, default=5)
    ap.add_argument('--limit', type=int, default=1500,
                    help='한 번 조회할 최신 데이터 행 수. 5분 전 이력 확보를 위해 충분히 크게 설정')
    ap.add_argument('--once', action='store_true', help='한 번 실행 후 종료')
    ap.add_argument('--backfill-on-first-run', action='store_true',
                    help='최초 실행시 조회된 모든 과거 행 처리(기본은 최신 1건만)')
    args = ap.parse_args()
    if args.interval <= 0 or args.limit < 100:
        ap.error('--interval > 0, --limit >= 100 필요')
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    artifact = load_model(args.model)
    comcode = os.getenv('MYSQL_COMCODE', '').strip() or None
    utc = os.getenv('SOURCE_TIME_UTC', 'false').lower() in ('1','true','yes')
    LOG.info('11호기 전용 deviceId=%s, comcode=%s, model=%s', DEVICE_ID, comcode or '(전체)', args.model)
    while True:
        conn = None
        try:
            conn = db_connect()
            poll_once(conn, artifact, comcode, args.limit, utc, not args.backfill_on_first_run)
        except (mysql.connector.Error, ValueError, RuntimeError) as exc:
            LOG.exception('조회/예측/저장 실패: %s', exc)
            if args.once:
                raise
        finally:
            if conn is not None and conn.is_connected():
                conn.close()
        if args.once:
            break
        time.sleep(args.interval)


if __name__ == '__main__':
    main()
