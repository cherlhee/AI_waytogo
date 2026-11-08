"""11호기 CF 학습: python train_cf_11.py --csv '남양금속 11호기(3).csv' --out cf_11_output
필수: pip install pandas numpy scipy scikit-learn
"""
import argparse, json, warnings
from collections import deque
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.metrics import precision_score, recall_score, f1_score, average_precision_score, brier_score_loss




HORIZONS = [10, 30, 60, 120]
TARGETS = [80, 85, 90]


# 원본 CSV에는 W-U 전압이 없으므로 두 선간전압만 사용함.
COLS = {
    'oil_temp':'오일온도', 'load':'부하율\n[%]', 'power':'유효전력 [Kw]',
    'flow_pressure':'유량계\n압력', 'flow_temp':'유량계\n온도',
    'flow_rate':'유량계\n유량', 'flow_humidity':'유량계\n습도',
    'current_u':'U전류 [A]', 'current_v':'V전류 [A]', 'current_w':'W 전류 [A]',
    'voltage_uv':'U-V전압 [V]', 'voltage_vw':'V-W 전압 [V]',
}
FEATURES = ['oil_temp','temp_rate_5min','load','power','flow_pressure','flow_temp',
            'flow_rate','flow_humidity','current_u','current_v','current_w',
            'voltage_uv','voltage_vw','current_mean','voltage_mean_measured','current_unbalance_pct']



def read_csv(path):
    df = pd.read_csv(path, encoding='cp949', low_memory=False)
    # 첫 행은 영문 필드 식별자이며 측정값이 아님
    if str(df.iloc[0,0]).strip() == '_time':
        df = df.iloc[1:].copy()
    missing = [v for v in COLS.values() if v not in df.columns]
    if missing: raise ValueError(f'CSV에 필요한 컬럼이 없습니다: {missing}')
    df['time'] = pd.to_datetime(df.iloc[:,0], utc=True, errors='coerce')
    for key, name in COLS.items():
        df[key] = pd.to_numeric(df[name], errors='coerce')
    df = df.dropna(subset=['time']).sort_values('time').drop_duplicates('time', keep='last')
    return df.reset_index(drop=True)




def future_max_window(times_ns, temps, horizon_min):
    """(현재, 현재+h] 범위의 관측 온도 최댓값. O(n), 불규칙 시간 지원.
    미래 관측치가 horizon 끝까지 충분히 존재하는 행에만 정답 부여.
    """
    n=len(temps)
    end=np.searchsorted(times_ns, times_ns + np.int64(horizon_min)*60*10**9, side='right')
    # NaN을 제외한 관측값의 최댓값. 전체 구간 데이터가 없으면 NaN
    arr=np.where(np.isfinite(temps),temps,-np.inf)
    result=np.full(n,np.nan)
    dq=deque(); right=1
    for i in range(n):
        r=int(end[i]); r=min(r,n)
        while right<r:
            while dq and arr[dq[-1]]<=arr[right]: dq.pop()
            dq.append(right); right+=1
        while dq and dq[0]<=i: dq.popleft()
        # 미래 관측 구간의 끝이 실제 데이터 끝보다 앞서야 완전한 horizon
        if dq and times_ns[-1]>=times_ns[i]+np.int64(horizon_min)*60*10**9:
            value=arr[dq[0]]
            if np.isfinite(value): result[i]=value
    return result

def features_and_labels(raw):
    df=raw[['time']+list(COLS)].copy()
    # 학습 시점은 전류 3상 중 하나라도 0 또는 NaN이면 제거
    valid_curr=df[['current_u','current_v','current_w']].notna().all(axis=1) & (df[['current_u','current_v','current_w']]>0).all(axis=1)
    print(f'전체 측정행: {len(df):,}, 전류 0/결측/음수 제거 대상: {(~valid_curr).sum():,}')
    # 원본 온도 전체를 미래 정답 생성에 사용 (전류 0인 시점의 고온도 보존)
    ns=df.time.astype('int64').to_numpy()
    temp=df.oil_temp.to_numpy(dtype=float)
    labels={h:future_max_window(ns,temp,h) for h in HORIZONS}
    # 5분 전 값은 삭제된 행을 건너뛰는 shift(5)가 아니라 실제 시간으로 찾음
    past_time=ns-5*60*10**9
    j=np.searchsorted(ns,past_time,side='right')-1
    prev=np.full(len(df),np.nan)
    valid=j>=0
    prev[valid]=temp[j[valid]]
    # 5분 시점의 관측치가 ±90초 이내인 경우에만 유효 (장시간 결측 방지)
    valid &= (np.abs(ns[np.maximum(j,0)]-past_time)<=90*10**9)
    prev[~valid]=np.nan
    df['temp_rate_5min']=(df.oil_temp-prev)/5
    cur=df[['current_u','current_v','current_w']]
    df['current_mean']=cur.mean(axis=1,skipna=False)
    df['voltage_mean_measured']=df[['voltage_uv','voltage_vw']].mean(axis=1,skipna=False)
    df['current_unbalance_pct']=(cur.sub(df.current_mean,axis=0).abs().max(axis=1,skipna=False)/df.current_mean.replace(0,np.nan)*100)
    for h,v in labels.items(): df[f'future_max_{h}']=v
    df=df.loc[valid_curr].copy()
    # 모든 16개 학습 특징이 존재해야 함
    df=df.replace([np.inf,-np.inf],np.nan).dropna(subset=FEATURES).reset_index(drop=True)
    print(f'학습 특징이 모두 존재하는 행: {len(df):,}')
    return df

def fit_bin_edges(values):
    x=np.asarray(values,dtype=float)
    q=np.unique(np.quantile(x,np.linspace(0,1,9)))
    interior=q[1:-1]
    return np.r_[-np.inf,interior,np.inf]

def bins_for(x, edges):
    return np.searchsorted(edges[1:-1],x,side='right')

def train_rules(X,y,edges,prior,min_count=30):
    rules=[]
    for col in FEATURES:
        ids=bins_for(X[col].to_numpy(),edges[col]); k=len(edges[col])-1
        counts=np.bincount(ids,minlength=k)
        positives=np.bincount(ids,weights=y,minlength=k)
        # 경험적 조건부 빈도 + Laplace shrinkage; 표본 부족 시 prior 사용
        rates=(positives+20*prior)/(counts+20)
        rates[counts<min_count]=prior
        rules.append(rates)
    return rules

def score_rules(X,edges,rules,weights):
    vals=np.column_stack([rules[i][bins_for(X[c].to_numpy(),edges[c])] for i,c in enumerate(FEATURES)])
    return vals @ weights

def metrics(y,s,thr):
    p=s>=thr
    return dict(n=int(len(y)), positives=int(y.sum()), precision=float(precision_score(y,p,zero_division=0)),
                recall=float(recall_score(y,p,zero_division=0)),f1=float(f1_score(y,p,zero_division=0)),
                pr_auc=float(average_precision_score(y,s)) if y.sum()>0 else None,
                brier=float(brier_score_loss(y,s)),threshold=float(thr))

def train_one(df,h,target):
    d=df.loc[df[f'future_max_{h}'].notna()].copy()
    if len(d)<1000: return None,None
    y=(d[f'future_max_{h}'].to_numpy()>=target).astype(int)
    # 시간순 분할 60/20/20. 룰, 가중치/임계값, 최종평가를 서로 분리
    n=len(d); a=int(n*.6); b=int(n*.8)
    Xtr=d.iloc[:a]; Xval=d.iloc[a:b]; Xte=d.iloc[b:]
    ytr=y[:a]; yval=y[a:b]; yte=y[b:]
    # 미래 구간이 학습/검증 경계를 넘어가는 행을 제외 (120분 purge)
    t=d.time.astype('int64').to_numpy()
    purge=h*60*10**9
    tr_mask=t[:a]+purge<t[a]
    va_mask=t[a:b]+purge<t[b]
    Xtr=Xtr.loc[tr_mask]; ytr=ytr[tr_mask]
    Xval=Xval.loc[va_mask]; yval=yval[va_mask]
    if len(Xtr)<100 or len(Xval)<100 or len(Xte)<100: return None,None
    prior=float(ytr.mean())
    edges={c:fit_bin_edges(Xtr[c]) for c in FEATURES}
    rules=train_rules(Xtr,ytr,edges,prior)
    v=np.column_stack([rules[i][bins_for(Xval[c].to_numpy(),edges[c])] for i,c in enumerate(FEATURES)])
    k=len(FEATURES)
    objective=lambda w: float(np.mean((v@w-yval)**2))
    opt=minimize(objective,np.ones(k)/k,method='SLSQP',bounds=[(0,1)]*k,
                 constraints=[{'type':'eq','fun':lambda w:w.sum()-1}],options={'maxiter':250})
    weights=opt.x if opt.success else np.ones(k)/k
    scores_val=v@weights
    thresholds=np.linspace(.01,.99,99)
    f1s=[f1_score(yval,scores_val>=th,zero_division=0) for th in thresholds]
    threshold=float(thresholds[int(np.argmax(f1s))])
    scores_test=score_rules(Xte,edges,rules,weights)
    report=dict(horizon_min=h,target_c=target,train_n=len(Xtr),val_n=len(Xval),train_positives=int(ytr.sum()),
                val_positives=int(yval.sum()),**metrics(yte,scores_test,threshold))
    model=dict(horizon_min=h,target_c=target,features=FEATURES,prior=prior,
               edges={c:[None if not np.isfinite(x) else float(x) for x in edges[c]] for c in FEATURES},
               rates={c:rules[i].tolist() for i,c in enumerate(FEATURES)},
               weights={c:float(weights[i]) for i,c in enumerate(FEATURES)},threshold=threshold)
    return model,report

def main():
    p=argparse.ArgumentParser();p.add_argument('--csv',default='남양금속 11호기.csv');p.add_argument('--out',default='cf_11_output')
    args=p.parse_args();out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    raw=read_csv(args.csv)
    df=features_and_labels(raw)
    models={}; reports=[]
    for h in HORIZONS:
        for t in TARGETS:
            model,report=train_one(df,h,t)
            if model is None:
                warnings.warn(f'{h}분 {t}℃ 모델: 학습 데이터 부족');continue
            key=f'{h}min_{t}c';models[key]=model;reports.append(report)
            print(f'{key}: test positives={report["positives"]:,}, F1={report["f1"]:.3f}, recall={report["recall"]:.3f}')
    artifact={'device':'11호기','model_type':'empirical_weighted_CF','feature_count':len(FEATURES),
              'notes':['CF 점수는 확률 보정된 예측 확률이 아님','W-U 전압은 원본 CSV에 없어 제외',
                       '유량계 총유량은 제외','미래 정답은 전류 필터링 이전 원본 온도 기반'], 'models':models}
    (out/'cf_11_model.json').write_text(json.dumps(artifact,ensure_ascii=False,indent=2),encoding='utf-8')
    pd.DataFrame(reports).to_csv(out/'cf_11_test_metrics.csv',index=False,encoding='utf-8-sig')
    print('저장:',out/'cf_11_model.json',out/'cf_11_test_metrics.csv')

if __name__=='__main__':main()
