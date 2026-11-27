from datetime import datetime, timedelta
from bisect import bisect_left
import math
DEVICES=('R00012','R00047','R00048')

def options(p):
    p.add_argument('--date')
    p.add_argument('--start-date')
    p.add_argument('--end-date')
    p.add_argument('--device-id', choices=DEVICES)
    p.add_argument('--comcode', default='C00088')
    p.add_argument('--batch-size', type=int, default=100)

def bounds(p,a):
    if (a.date and (a.start_date or a.end_date)) or bool(a.start_date)!=bool(a.end_date):
        p.error('Use --date or both --start-date and --end-date')
    try:
        lo=datetime.strptime(a.date or a.start_date or '2026-11-01','%Y-%m-%d')
        hi=datetime.strptime(a.date or a.end_date or '2026-11-01','%Y-%m-%d')+timedelta(days=1)
    except (ValueError,OverflowError): p.error('Invalid date')
    if hi<=lo or a.batch_size<1: p.error('Invalid period or batch size')
    return lo,hi

def read_rows(conn, company, device, lo, hi, cols):
    cur=conn.cursor(dictionary=True)
    try:
        cur.execute('SELECT comcode, deviceId, input_time, '+','.join('`'+c+'`' for c in cols)+' FROM ai_data WHERE comcode=%s AND deviceId=%s AND input_time >= %s AND input_time < %s ORDER BY input_time', (company,device,str(lo),str(hi)))
        return cur.fetchall()
    finally: cur.close()

def actual_index(rows):
    pairs=[]
    for r in rows:
        try:
            v=float(r['io003'])
            if math.isfinite(v): pairs.append((r['_time'],v))
        except (TypeError,ValueError): pass
    return [x[0] for x in pairs],[x[1] for x in pairs]

def actual_at(index,t,tolerance):
    times,values=index
    i=bisect_left(times,t)
    candidates=[j for j in (i-1,i) if 0<=j<len(times)]
    if not candidates:return None
    j=min(candidates,key=lambda j:abs(times[j]-t))
    return round(values[j],2) if abs((times[j]-t).total_seconds())<=tolerance else None

def existing(conn,table,col,company,device,lo,hi,cf=False):
    cur=conn.cursor()
    try:
        cur.execute(f'SELECT input_time,prediction_horizon_min FROM {table} WHERE comcode=%s AND `{col}`=%s AND input_time >= %s AND input_time < %s'+(" AND prediction_model='CF'" if cf else ''),(company,device,lo,hi))
        return {(datetime.fromisoformat(str(t)),int(h)) for t,h in cur.fetchall()}
    finally:cur.close()
