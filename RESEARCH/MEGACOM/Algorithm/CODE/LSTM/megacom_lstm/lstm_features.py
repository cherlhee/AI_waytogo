"""학습/추론 공통: 1분 기준, 과거 정보만 이용한 파생변수."""
import logging
import numpy as np
import pandas as pd
from config import RAW, FEATURES

LOG = logging.getLogger(__name__)

def read_training_csv(path):
    # 제공된 CSV는 cp949, 두 번째 행이 io 코드, 첫 번째 열은 UTC 시각
    for enc in ('utf-8-sig','cp949'):
        try:
            raw = pd.read_csv(path, encoding=enc, low_memory=False)
            break
        except UnicodeDecodeError:
            continue
    io_row = raw.iloc[0]
    rename = {col: str(io_row[col]).strip() for col in raw.columns if str(io_row[col]).startswith('io')}
    rename.update({raw.columns[0]:'input_time'})
    df = raw.iloc[1:].rename(columns=rename).copy()
    return df

def normalize_time(s, utc_input=False):
    # CSV Z/UTC -> 한국 로컬 시간; DB DATETIME은 이미 로컬이라고 가정
    if utc_input:
        return pd.to_datetime(s, errors='coerce', utc=True).dt.tz_convert('Asia/Seoul').dt.tz_localize(None)
    return pd.to_datetime(s, errors='coerce')

def minute_features(df, *, utc_input=False, anchor=None, realtime=False):
    """realtime=True: anchor 시각에 정렬된 1분 구간의 과거 평균 36개 생성.
    train: 고정된 1분 구간의 평균. 동일한 센서 의미/단위를 가정한다.
    """
    d = df.copy()
    missing = [c for c in RAW if c not in d]
    if missing: raise ValueError(f'누락된 원본 변수: {missing}')
    d['input_time'] = normalize_time(d['input_time'], utc_input)
    d = d.dropna(subset=['input_time']).sort_values('input_time')
    for c in RAW: d[c] = pd.to_numeric(d[c], errors='coerce')
    d = d.set_index('input_time')[list(RAW)]
    d = d[~d.index.duplicated(keep='last')]
    if realtime:
        if anchor is None: raise ValueError('실시간 anchor 필수')
        anchor = pd.Timestamp(anchor)
        # 학습 데이터의 1분 관측값과 일관되게, 각 구간의 과거 60초 평균
        # [anchor-60초, anchor]의 오른쪽 끝을 시각 라벨로 사용
        points = [anchor-pd.Timedelta(minutes=i) for i in range(35,-1,-1)]
        rows=[]
        for t in points:
            window = d.loc[(d.index > t-pd.Timedelta(minutes=1)) & (d.index <= t)]
            # 1분 구간에 1건 이상 있으면 해당 구간 평균을 사용한다.
            # 8건 미만이면 품질 경고를 남긴다. 미래 데이터는 사용하지 않는다.
            if len(window) == 0:
                LOG.warning("센서 데이터 없음: (%s, %s]", t - pd.Timedelta(minutes=1), t)
                rows.append([np.nan] * len(RAW))
            else:
                if len(window) < 8:
                    LOG.warning("1분 센서 관측 부족: 기준=%s, %d건 (권장 8건 이상)", t, len(window))
                rows.append(window.mean().to_numpy())
        m = pd.DataFrame(rows,index=pd.DatetimeIndex(points),columns=RAW)
    else:
        # CSV는 1분 간격. 원시값을 시간 버킷별 평균으로 집계.
        m = d.resample('1min').mean()
    
    
    m['temp_rise_5min'] = (m['io003'] - m['io003'].shift(5))/5.0
    
    m['current_avg'] = m[['io007','io008','io009']].mean(axis=1, skipna=False)
    
    m['voltage_avg'] = m[['io004','io005']].mean(axis=1, skipna=False)
    
    diff = m[['io007','io008','io009']].sub(m['current_avg'],axis=0).abs().max(axis=1, skipna=False)
    
    m['current_unbalance'] = 100*diff/m['current_avg'].replace(0,np.nan)
    return m[list(FEATURES)].replace([np.inf,-np.inf],np.nan)
