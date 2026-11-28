"""MEGACOM future threshold classifier, compatible with Training GUI CLI."""
import argparse, json, os, re
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.metrics import precision_recall_fscore_support

ROOT = Path(__file__).resolve().parent
RAW = ['io003','io028','io010','io044','io045','io046','io048','io007','io008','io009','io004','io005']
DERIVED = ['temp_rise_5min','current_avg','voltage_avg','current_unbalance']

def log(s): print(s, flush=True)

def read_csv_auto(csv_path):
    for encoding in ('utf-8-sig', 'cp949', 'euc-kr'):
        try:
            df = pd.read_csv(csv_path, encoding=encoding, low_memory=False)
        except UnicodeDecodeError:
            log(f'Encoding failed: {encoding}')
            continue
        # Export has a descriptive header followed by machine field names.
        if len(df) and str(df.iloc[0, 0]).strip().lower() == '_time' and str(df.iloc[0, 1]).strip().lower() == 'deviceid':
            df = pd.read_csv(csv_path, encoding=encoding, header=1, low_memory=False)
            log('Detected two-row CSV header; using machine field names')
        log(f'CSV encoding: {encoding}')
        log(f'CSV rows: {len(df):,}')
        log(f'CSV columns: {len(df.columns)}')
        return df
    raise ValueError('Unsupported CSV encoding (UTF-8, CP949, EUC-KR)')


def normalize_csv(df, a):
    mapping = {
        '장비번호':'deviceid', '토출압력[bar]':'io001', '시스템압력[bar]':'io002',
        '오일온도':'io003', 'u-v전압[v]':'io004', 'v-w전압[v]':'io005',
        'u전류[a]':'io007', 'v전류[a]':'io008', 'w전류[a]':'io009',
        '유효전력[kw]':'io010', '부하율[%]':'io028', '주파수[hz]':'io029',
        '유량계압력':'io044', '유량계온도':'io045', '유량계유량':'io046',
        '유량계총유량':'io047', '유량계습도':'io048',
        '측정시간':'input_time', '측정일시':'input_time', '수집일시':'input_time',
        'datetime':'input_time', 'timestamp':'input_time', '_time':'input_time'
    }
    df = df.rename(columns={c: mapping.get(re.sub(r'\s+', '', c).lower(), c) for c in df})
    if df.columns.duplicated().any():
        raise ValueError('Duplicate columns after CSV mapping')
    unnamed = [c for c in df if c.startswith('unnamed:')]
    log('CSV first rows: '+df.iloc[:5,:4].to_string(index=False))
    def strings(c): return df[c].astype('string').str.strip()
    date_pattern = r'\d{4}[-/.]\d{1,2}[-/.]\d{1,2}'
    time_pattern = r'\d{1,2}:\d{2}(?::\d{2}(?:\.\d+)?)?'
    def matches(c, pattern):
        v = strings(c).dropna().head(200)
        return len(v)>0 and v.str.fullmatch(pattern).mean() >= .95
    if 'input_time' not in df:
        if a.csv_time_column:
            df['input_time'] = strings(a.csv_time_column)
            if a.csv_clock_column:
                df['input_time'] += ' '+strings(a.csv_clock_column)
        else:
            full = [c for c in unnamed if matches(c, date_pattern+r'[ T]'+time_pattern)]
            dates = [c for c in unnamed if matches(c,date_pattern)]
            clocks = [c for c in unnamed if matches(c,time_pattern)]
            if len(full)==1:
                df['input_time']=strings(full[0]); log('Timestamp column: '+full[0])
            elif not full and len(dates)==1 and len(clocks)==1:
                df['input_time']=strings(dates[0])+' '+strings(clocks[0]); log('Timestamp columns: '+dates[0]+' + '+clocks[0])
            else:
                raise ValueError('Cannot identify timestamp safely. Check CSV first rows; use --csv-time-column and optionally --csv-clock-column.')
    # Convert explicit UTC/offset timestamps to Korean local time; preserve naive local timestamps.
    values = df['input_time'].astype('string').str.strip()
    zoned = values.str.contains(r'(?:Z|[+-]\d{2}:?\d{2})$', case=False, regex=True, na=False)
    parsed = pd.to_datetime(values.where(~zoned), errors='coerce')
    if zoned.any():
        parsed.loc[zoned] = pd.to_datetime(values.loc[zoned], errors='coerce', utc=True).dt.tz_convert('Asia/Seoul').dt.tz_localize(None)
        log('Timezone: UTC/offset timestamps converted to Asia/Seoul')
    df['input_time'] = parsed
    if 'deviceid' in df:
        ids = strings('deviceid').str.upper()
        df['deviceid'] = ids
        log('CSV device IDs: '+str(ids.dropna().unique()[:20].tolist()))
        if a.csv_device_value is not None:
            df=df.loc[ids==a.csv_device_value].copy()
            df['deviceid']=a.device_id
        elif not (ids==a.device_id).any():
            raise ValueError('CSV device ID differs from selected ID. Confirm mapping and use --csv-device-value; no automatic numeric mapping.')
    elif 'device_id' not in df:
        raise ValueError('CSV has no device ID column')
    log('Converted columns: '+str(df.columns.tolist()))
    return df


def connect_mysql():
    from dotenv import dotenv_values
    import mysql.connector
    path = ROOT / 'mysql_config.env'
    if not path.is_file():
        raise FileNotFoundError(f'Missing DB config: {path}. Copy mysql_config.env from the working Dashboard folder.')
    values = dotenv_values(path, encoding='utf-8-sig')
    def get(*keys, default=None):
        for key in keys:
            value = values.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()
        return default
    cfg = dict(host=get('MYSQL_HOST','DB_HOST'),
               port=int(get('MYSQL_PORT','DB_PORT',default='3307')),
               user=get('MYSQL_USER','DB_USER'),
               password=get('MYSQL_PASSWORD','DB_PASSWORD'),
               database=get('MYSQL_DATABASE','DB_DATABASE','DB_NAME','MYSQL_NAME',default='airpredict'),
               connection_timeout=10)
    if not cfg['host'] or cfg['host'] == '.':
        raise ValueError('Invalid or missing MYSQL_HOST / DB_HOST in mysql_config.env')
    if not cfg['user']:
        raise ValueError('Missing MYSQL_USER / DB_USER in mysql_config.env')
    if cfg['password'] is None:
        raise ValueError('Missing MYSQL_PASSWORD / DB_PASSWORD in mysql_config.env')
    if not 1 <= cfg['port'] <= 65535:
        raise ValueError('Invalid MySQL port')
    log(f'DB config: {path}')
    log(f"MySQL host={cfg['host']} port={cfg['port']} database={cfg['database']}")
    conn = mysql.connector.connect(**cfg)
    log('MySQL connected successfully')
    return conn


def load(a):
    start = pd.Timestamp(a.start_date); end = pd.Timestamp(a.end_date)+pd.Timedelta(days=1)
    if a.source == 'csv':
        df = read_csv_auto(a.csv_path)
        df.columns = df.columns.str.strip().str.lower()
        log(f"CSV column names: {df.columns.tolist()}")
        df = normalize_csv(df, a)
    else:
        conn = connect_mysql()
        try:
            cur=conn.cursor(dictionary=True)
            cur.execute('SELECT input_time, '+','.join(RAW)+' FROM ai_data WHERE comcode=%s AND deviceId=%s AND input_time >= %s AND input_time < %s ORDER BY input_time',(a.comcode,a.device_id,start.to_pydatetime(),end.to_pydatetime()))
            df=pd.DataFrame(cur.fetchall(), columns=cur.column_names); cur.close()
        finally: conn.close()
        df.columns=df.columns.str.lower()
    for col,val in [('comcode',a.comcode),('deviceid',a.device_id),('device_id',a.device_id)]:
        if col in df: df=df[df[col].astype(str).str.strip()==val]
    if 'input_time' not in df: raise ValueError('CSV requires input_time column')
    df['input_time']=pd.to_datetime(df['input_time'],errors='coerce')
    log(f"Invalid timestamps: {df.input_time.isna().sum():,}")
    if df.input_time.notna().any(): log(f"CSV/data time range: {df.input_time.min()} ~ {df.input_time.max()}")
    df=df[(df.input_time>=start)&(df.input_time<end)].copy()
    log(f'Raw rows: {len(df):,}')
    if df.empty: raise ValueError('No data for selected company, device and date range')
    return df

def prepare(df, features, mode):
    required=set(features)&set(RAW); required.update(['io003','io007','io008','io009'])
    if 'voltage_avg' in features: required.update(['io004','io005'])
    if mode=='exclude': required.discard('io048')
    missing=required-set(df.columns)
    if missing: raise ValueError(f'Missing columns: {sorted(missing)}')
    cols=sorted(required)
    for c in cols: df[c]=pd.to_numeric(df[c],errors='coerce')
    df=df.sort_values('input_time').drop_duplicates('input_time',keep='last')
    # Remove stopped/invalid current readings; preserve time gaps in resampling.
    df=df[(df[['io007','io008','io009']]>0).all(axis=1)]
    if df.empty: raise ValueError('No running data after current filter')
    m=df.set_index('input_time')[cols].resample('1min').mean()
    m['temp_rise_5min']=m.io003-m.io003.shift(5)
    currents=m[['io007','io008','io009']]
    m['current_avg']=currents.mean(axis=1,skipna=False)
    m['current_unbalance']=100*(currents.max(axis=1)-currents.min(axis=1))/currents.max(axis=1)
    if 'io004' in m and 'io005' in m: m['voltage_avg']=m[['io004','io005']].mean(axis=1,skipna=False)
    return m.replace([np.inf,-np.inf],np.nan)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--comcode',default='C00088'); p.add_argument('--device-id',default='R00012')
    p.add_argument('--source',choices=['csv','mysql'],default='csv'); p.add_argument('--csv-path')
    p.add_argument('--csv-time-column'); p.add_argument('--csv-clock-column'); p.add_argument('--csv-device-value')
    p.add_argument('--start-date',required=True); p.add_argument('--end-date',required=True)
    p.add_argument('--features',default=','.join(RAW+DERIVED)); p.add_argument('--horizons',default='10,30,60,120')
    p.add_argument('--thresholds',default='80,85,90'); p.add_argument('--humidity-mode',choices=['actual','mean','exclude'],default='mean')
    p.add_argument('--learning-rate',type=float,default=.001); p.add_argument('--probability-threshold',type=float,default=.30)
    a=p.parse_args(); features=list(dict.fromkeys(a.features.split(',')))
    if a.humidity_mode=='exclude': features=[f for f in features if f!='io048']
    if not features or set(features)-set(RAW+DERIVED): raise ValueError('Invalid features')
    hs=list(map(int,a.horizons.split(','))); ts=list(map(int,a.thresholds.split(',')))
    if min(hs)<=0 or not 0<a.probability_threshold<1: raise ValueError('Invalid horizon or probability threshold')
    log('PROGRESS 1'); m=prepare(load(a),features,a.humidity_mode)
    log(f'Oil temperature MIN={m.io003.min():.2f}, MAX={m.io003.max():.2f}, MEAN={m.io003.mean():.2f}')
    for t in ts:
        log(f'Oil temperature >= {t}C: {int((m.io003>=t).sum()):,}/{int(m.io003.notna().sum()):,}')
    cut=int(len(m)*.8)
    if cut<max(hs)+10 or len(m)-cut<max(hs)+10: raise ValueError('Not enough time coverage for chronological split')
    humidity=None
    if 'io048' in features and a.humidity_mode=='mean':
        humidity=float(m.io048.iloc[:cut].mean())
        if not np.isfinite(humidity): raise ValueError('No valid training humidity')
        m['io048']=humidity; log(f'Fixed humidity: {humidity:.4f}')
    out=ROOT/'models'/a.device_id/'CF'/datetime.now().strftime('%Y%m%d_%H%M%S_%f'); out.mkdir(parents=True)
    meta={'features':features,'device_id':a.device_id,'comcode':a.comcode,'humidity_mode':a.humidity_mode,'humidity_mean':humidity,'sampling':'1min','probability_threshold':a.probability_threshold,'split_time':str(m.index[cut]),'models':[],'complete':False}
    X=m[features]; valid=X.notna().all(axis=1).to_numpy(); pos=np.arange(len(m)); done=0; total=len(hs)*len(ts)
    log(f'One-minute rows: {len(m):,}; test starts {m.index[cut]}')
    for h in hs:
        # Maximum over t+1 through t+h; require all future minutes to exist.
        future=m.io003.shift(-1).iloc[::-1].rolling(h,min_periods=h).max().iloc[::-1]
        for t in ts:
            good=valid & future.notna().to_numpy()
            train=good & (pos+h<cut); test=good & (pos>=cut)
            y=(future>=t).astype(int)
            yt=y[train]; yv=y[test]
            n0,n1=int((yt==0).sum()),int((yt==1).sum())
            v0,v1=int((yv==0).sum()),int((yv==1).sum())
            record={'horizon':h,'threshold':t,'train_rows':n0+n1,'test_rows':v0+v1,'train_negative':n0,'train_positive':n1,'test_negative':v0,'test_positive':v1}
            log(f'===== {h}min / {t}C =====')
            log(f'Train samples: {n0+n1:,}; Class 0: {n0:,}; Class 1: {n1:,}')
            log(f'Test samples: {v0+v1:,}; Class 0: {v0:,}; Class 1: {v1:,}')
            if not n0 or not n1 or not test.any():
                reason='no training samples' if not train.any() else 'single training class' if not n0 or not n1 else 'no test samples'
                log(f'SKIP {h}min {t}C: {reason}')
                record.update(status='SKIPPED',reason=reason)
                log(f'CF_RESULT {h} {t} N/A N/A N/A')
            else:
                ratio=float(n0/n1)
                model=XGBClassifier(n_estimators=300,max_depth=5,learning_rate=a.learning_rate,subsample=.8,colsample_bytree=.8,scale_pos_weight=ratio,random_state=42,n_jobs=4,eval_metric='logloss',tree_method='hist')
                model.fit(X.loc[train],yt)
                prob=model.predict_proba(X.loc[test])[:,1]; pred=(prob>=a.probability_threshold).astype(int)
                tp=int(((yv==1)&(pred==1)).sum()); fp=int(((yv==0)&(pred==1)).sum())
                tn=int(((yv==0)&(pred==0)).sum()); fn=int(((yv==1)&(pred==0)).sum())
                precision,recall,f1,_=precision_recall_fscore_support(yv,pred,average='binary',zero_division=0)
                name=f'cf_{h}min_{t}c.json'; model.save_model(out/name)
                evaluated=bool(v0 and v1)
                record.update(file=name,status='EVALUATED' if evaluated else 'UNVALIDATED',precision=float(precision) if evaluated else None,recall=float(recall) if evaluated else None,f1=float(f1) if evaluated else None,tp=tp,fp=fp,tn=tn,fn=fn)
                log(f'Confusion matrix: TN={tn}, FP={fp}, FN={fn}, TP={tp}')
                log(f'Always-positive baseline F1: {2*v1/(v0+2*v1):.4f}')
                if evaluated:
                    log(f'CF_RESULT {h} {t} {precision:.4f} {recall:.4f} {f1:.4f}')
                else:
                    log(f'[WARNING] {h}min {t}C: test contains only one class; performance not validated')
                    log(f'CF_RESULT {h} {t} N/A N/A N/A')
            meta['models'].append(record)
            done+=1; log(f'PROGRESS {min(99,int(5+94*done/total))}')
    meta['complete']=all('file' in r for r in meta['models'])
    meta['evaluation_complete']=all(r['status']=='EVALUATED' for r in meta['models'])
    meta['deployment_ready']=False
    log(f"Summary: trained={sum('file' in r for r in meta['models'])}/{total}; evaluated={sum(r['status']=='EVALUATED' for r in meta['models'])}/{total}")
    (out/'metadata.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False),encoding='utf-8')
    log(f'Model directory: {out}')
    if not meta['complete']: log('[WARNING] Partial training completed; some models skipped.')
    if not meta['evaluation_complete']: log('[WARNING] Evaluation incomplete; do not automatically deploy.')
    if not any('file' in r for r in meta['models']): raise RuntimeError('No models trained; see metadata')
    log('PROGRESS 100')

if __name__=='__main__':
    try: main()
    except Exception as exc:
        log(f'[ERROR] {type(exc).__name__}: {exc}'); raise
