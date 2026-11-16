"""ai_data -> ai_analysis 룰베이스 판정. 실행 전 DB 환경변수 설정 필요."""
import argparse
import logging
import os
import time
from datetime import datetime
from decimal import Decimal, InvalidOperation

import mysql.connector

LOG = logging.getLogger('rulebase')
RAW = ('io001','io003','io004','io005','io007','io008','io009','io029','io030','io045')
ALLOWED = {'ai_data','ai_analysis','st_comcode_set','ai_current_std','ai_oiltemp_std'}


def num(x):
    if x is None or str(x).strip() == '': return None
    try:
        v = float(Decimal(str(x).strip().replace(',','')))
        return v if v == v and abs(v) != float('inf') else None
    except (InvalidOperation, ValueError, TypeError): return None


def pct(a, b):
    return abs(a-b)/abs(b)*100 if a is not None and b not in (None,0) else None


def grade(v, bounds):
    if v is None: return None
    result = 0
    for threshold, score in bounds:
        if v >= threshold: result = score
    return result


def alarm(score):
    # 설계서: 0 정상, 5 경고, 9 알람. 주의=5, 경고=9 매핑(운영 확정 필요).
    return None if score is None else ('0' if score == 0 else '5' if score < 70 else '9')


def ts(x):
    if isinstance(x, datetime): return x
    if x is None: return None
    try: return datetime.fromisoformat(str(x).strip())
    except ValueError: return None


def fetch_one(cur, sql, params):
    cur.execute(sql, params)
    return cur.fetchone()


def std(cur, comcode, device, item):
    row = fetch_one(cur, "SELECT std_high FROM st_comcode_set WHERE comcode=%s AND deviceId=%s AND std_item=%s LIMIT 1", (comcode,device,item))
    return num(row['std_high']) if row else None


def ref(cur, table, column, comcode, device, frequency, outside=None):
    assert table in ALLOWED
    if frequency is None: return None
    where = 'comcode=%s AND deviceId=%s AND CAST(frequency AS DECIMAL(12,3))=%s'
    args = [comcode,device,frequency]
    if outside is not None:
        where += ' AND CAST(outside_temp AS DECIMAL(12,3))=%s'
        args.append(outside)
    row = fetch_one(cur, f'SELECT `{column}` AS val FROM `{table}` WHERE {where} LIMIT 1', args)
    return num(row['val']) if row else None


def score_row(cur, row, previous):
    c,d = row['comcode'],row['deviceId']
    vals = {k:num(row.get(k)) for k in RAW}
    out = {'comcode':c,'deviceId':d}
    stamp = row['input_time']
    uv,vw = vals['io004'], vals['io005']
    currents = [vals[k] for k in ('io007','io008','io009')]
    current_avg = sum(currents)/3 if all(v is not None and v>0 for v in currents) else None
    voltage_avg = (uv+vw)/2 if uv is not None and vw is not None else None
    freq, outside = vals['io029'], vals['io045']

    def put(code, value, score, base=None):
        out['io'+code] = round(value,2) if value is not None else None
        out['grade_'+code] = score
        out['alarm_'+code] = alarm(score)
        # gradestd_*는 기준점수로 정의됨. 참조기준 물리값이 아님.
        if base is not None: out['gradestd_'+code] = base

    put('045', outside, grade(outside,[(30,40),(35,50),(40,60),(45,70)]))
    base_v = std(cur,c,d,'io004')
    put('004',voltage_avg,grade(pct(voltage_avg,base_v),[(5,40),(7,70)]))
    base_i = ref(cur,'ai_current_std','current_std',c,d,freq)
    put('007',current_avg,grade(pct(current_avg,base_i),[(5,40),(10,60),(15,70)]))
    if uv is not None and vw is not None and max(abs(uv),abs(vw))>0:
        imbalance_v = abs(uv-vw)/max(abs(uv),abs(vw))*100
    else: imbalance_v=None
    # 문서 7~10% 주의와 <=10% 정상 문구 충돌: 7% 이상 주의로 적용.
    put('900',imbalance_v,grade(imbalance_v,[(7,40),(10.000000001,70)]))
    if current_avg is not None:
        imbalance_i = (max(currents)-min(currents))/max(currents)*100
    else: imbalance_i=None
    put('901',imbalance_i,grade(imbalance_i,[(10,40),(15,70)]))
    pressure=vals['io001']
    oldp=num(previous.get('io001')) if previous else None
    t1,t0=ts(stamp),ts(previous['input_time']) if previous else (None)
    dt=(t1-t0).total_seconds() if t1 and t0 else None
    pressure_score = (70 if abs(pressure-oldp)>=3 else 0) if pressure is not None and oldp is not None and dt is not None and 0<dt<=5 else None
    put('001',pressure,pressure_score)
    base_o = ref(cur,'ai_oiltemp_std','oiltemp_std',c,d,freq,outside) if outside is not None else None
    put('003',vals['io003'],grade(pct(vals['io003'],base_o),[(5,40),(10,70)]))
    base_cycle=std(cur,c,d,'io030')
    cycle_ratio=vals['io030']/base_cycle*100 if vals['io030'] is not None and base_cycle not in (None,0) else None
    put('030',vals['io030'],grade(cycle_ratio,[(90,40),(100,70)]))
    # 902는 AI 예측 결과 연계 전까지 미판정
    put('902',None,None)
    put('029',freq,None)
    return out


def run(conn, device=None, limit=2000, dry_run=False):
    cur=conn.cursor(dictionary=True)
    try:
        cur.execute('SHOW COLUMNS FROM `ai_analysis`')
        columns={r['Field'] for r in cur.fetchall()}
        time_col='judge_time' if 'judge_time' in columns else 'input_time' if 'input_time' in columns else None
        if not time_col: raise RuntimeError('ai_analysis에 judge_time/input_time 컬럼이 없습니다.')
        cur.execute('SHOW COLUMNS FROM `ai_data`')
        raw_columns={r['Field'] for r in cur.fetchall()}
        missing={'comcode','deviceId','input_time',*RAW}-raw_columns
        if missing: raise RuntimeError(f'ai_data 필수 컬럼 누락: {sorted(missing)}')
        where='WHERE deviceId=%s' if device else ''
        args=[device] if device else []
        # 처리 순서 보장을 위해 최신 N건을 가져온 후 시간순으로 처리
        cur.execute(f'SELECT * FROM (SELECT * FROM ai_data {where} ORDER BY input_time DESC LIMIT %s) t ORDER BY comcode, deviceId, input_time',args+[limit])
        rows=cur.fetchall()
        prev_cache={}
        count=0
        for row in rows:
            key=(row['comcode'],row['deviceId'])
            prev=prev_cache.get(key)
            if prev is None:
                prev=fetch_one(cur,'SELECT input_time,io001 FROM ai_data WHERE comcode=%s AND deviceId=%s AND input_time<%s ORDER BY input_time DESC LIMIT 1',(*key,row['input_time']))
            result=score_row(cur,row,prev)
            result[time_col]=str(row['input_time'])
            # 설계서에 gradestd_044 오타 존재. 실제 컬럼과 일치할 때만 삽입.
            available={k:v for k,v in result.items() if k in columns}
            if not {'comcode','deviceId',time_col} <= available.keys():
                raise RuntimeError('ai_analysis 기본 키 컬럼 불일치')
            if dry_run:
                LOG.info('DRY RUN %s %s %s: %s',*key,row['input_time'],available)
            else:
                names=list(available)
                marks=','.join(['%s']*len(names))
                updates=','.join(f'`{k}`=VALUES(`{k}`)' for k in names if k not in ('comcode','deviceId',time_col))
                sql=f"INSERT INTO ai_analysis ({','.join('`'+k+'`' for k in names)}) VALUES ({marks}) ON DUPLICATE KEY UPDATE {updates}"
                cur.execute(sql,[available[k] for k in names])
            prev_cache[key]=row
            count+=1
        if dry_run: conn.rollback()
        else: conn.commit()
        return count
    except Exception:
        conn.rollback()
        raise
    finally: cur.close()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--device-id',default=None)
    p.add_argument('--limit',type=int,default=2000)
    p.add_argument('--once',action='store_true')
    p.add_argument('--dry-run',action='store_true')
    a=p.parse_args()
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
    while True:
        conn=mysql.connector.connect(host=os.environ.get('DB_HOST','127.0.0.1'),port=int(os.environ.get('DB_PORT','3306')),user=os.environ['DB_USER'],password=os.environ['DB_PASSWORD'],database=os.environ.get('DB_NAME','airpredict'),connection_timeout=10)
        try: LOG.info('처리 %d건',run(conn,a.device_id,a.limit,a.dry_run))
        finally: conn.close()
        if a.once: break
        time.sleep(5)

if __name__=='__main__': main()
