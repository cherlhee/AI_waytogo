"""Train empirical CF-style temperature-bin models for R00015.
Usage: python train_cf_11_temperature.py --csv "남양금속 11호기(3).csv"
Requires: pandas numpy scikit-learn
"""
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from train_cf_11 import read_csv, features_and_labels, FEATURES, HORIZONS, fit_bin_edges, bins_for

# Finite temperature bands, so a real temperature estimate is possible.
TEMP_EDGES = np.arange(-5.0, 116.0, 2.0)
TEMP_CENTERS = (TEMP_EDGES[:-1] + TEMP_EDGES[1:]) / 2

def future_at_time(times, values, minutes, tolerance_seconds=90):
    target = times + np.int64(minutes) * 60 * 10**9
    ix = np.searchsorted(times, target, side='left')
    left = np.clip(ix - 1, 0, len(times)-1)
    right = np.clip(ix, 0, len(times)-1)
    chosen = np.where(abs(times[left]-target) <= abs(times[right]-target), left, right)
    ok = (abs(times[chosen]-target) <= tolerance_seconds*10**9) & (target <= times[-1])
    out = values[chosen].astype(float).copy()
    out[~ok] = np.nan
    return out

def fit_one(df, target_values, horizon):
    ok = np.isfinite(target_values) & (target_values >= TEMP_EDGES[0]) & (target_values < TEMP_EDGES[-1])
    d = df.loc[ok].copy().reset_index(drop=True)
    y = target_values[ok]
    n = len(d)
    if n < 1000: raise ValueError(f'{horizon}min: usable rows insufficient: {n}')
    a,b = int(n*.6),int(n*.8)
    ns = d.time.astype('int64').to_numpy()
    # Purge training/validation samples whose target lies beyond split boundary.
    tr = np.arange(a)[ns[:a] + horizon*60*10**9 < ns[a]]
    va = np.arange(a,b)[ns[a:b] + horizon*60*10**9 < ns[b]]
    te = np.arange(b,n)
    if min(len(tr),len(va),len(te)) < 100: raise ValueError('Not enough data after purge')
    yi = np.searchsorted(TEMP_EDGES[1:-1],y,side='right')
    K=len(TEMP_CENTERS)
    prior = np.bincount(yi[tr],minlength=K).astype(float)
    prior = (prior + 0.2) / (len(tr) + 0.2*K)
    edges={name:fit_bin_edges(d.loc[tr,name].to_numpy()) for name in FEATURES}
    rates={}
    # Each feature bin maps to a smoothed distribution of future temperature bands.
    for name in FEATURES:
        binids=bins_for(d.loc[tr,name].to_numpy(),edges[name]); B=len(edges[name])-1
        counts=np.bincount(binids,minlength=B)
        matrix=np.zeros((B,K),float)
        np.add.at(matrix,(binids,yi[tr]),1)
        alpha=30.0
        rates[name]=(matrix + alpha*prior[None,:])/(counts[:,None]+alpha)
    # Validation: derive nonnegative evidence weights using per-feature log loss.
    eps=1e-12
    losses=[]
    for name in FEATURES:
        bval=bins_for(d.loc[va,name].to_numpy(),edges[name])
        p=rates[name][bval,yi[va]]
        losses.append(float(-np.log(np.maximum(p,eps)).mean()))
    weights=np.exp(-(np.array(losses)-min(losses))*3)
    weights/=weights.sum()
    def predict(indices):
        p=np.zeros((len(indices),K),float)
        for i,name in enumerate(FEATURES):
            p+=weights[i]*rates[name][bins_for(d.loc[indices,name].to_numpy(),edges[name])]
        return p@TEMP_CENTERS
    pred=predict(te)
    metrics={'horizon_min':horizon,'train_n':len(tr),'val_n':len(va),'test_n':len(te),
             'mae_c':float(mean_absolute_error(y[te],pred)),
             'rmse_c':float(np.sqrt(mean_squared_error(y[te],pred))),
             'bias_c':float(np.mean(pred-y[te]))}
    model={'horizon_min':horizon,'features':FEATURES,'temperature_edges_c':TEMP_EDGES.tolist(),
           'temperature_centers_c':TEMP_CENTERS.tolist(),
           'edges':{k:[None if not np.isfinite(z) else float(z) for z in v] for k,v in edges.items()},
           'rates':{k:v.tolist() for k,v in rates.items()},
           'weights':{k:float(weights[i]) for i,k in enumerate(FEATURES)}}
    return model,metrics

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--csv',default='남양금속 11호기(3).csv')
    ap.add_argument('--out',default='cf_11_output')
    args=ap.parse_args()
    raw=read_csv(args.csv)
    df=features_and_labels(raw)
    ns=raw.time.astype('int64').to_numpy()
    temp=raw.oil_temp.to_numpy(float)
    models={}; reports=[]
    # Join on original time: labels are from raw unfiltered readings.
    for h in HORIZONS:
        future=future_at_time(ns,temp,h)
        target=pd.Series(future,index=raw.time).reindex(df.time).to_numpy(float)
        model,report=fit_one(df,target,h)
        models[f'{h}min']=model;reports.append(report)
        print(f'{h:3}min: MAE={report["mae_c"]:.3f}°C, RMSE={report["rmse_c"]:.3f}°C, test={report["test_n"]:,}')
    output=Path(args.out);output.mkdir(parents=True,exist_ok=True)
    artifact={'device_id':'R00015','model_type':'empirical_CF_temperature_bins',
              'notes':'Temperature prediction is empirical temperature-bin weighted evidence; not a physical temperature model.',
              'models':models}
    (output/'cf_11_temperature_model.json').write_text(json.dumps(artifact,ensure_ascii=False),encoding='utf-8')
    pd.DataFrame(reports).to_csv(output/'cf_11_temperature_metrics.csv',index=False,encoding='utf-8-sig')
    print('Saved:',output/'cf_11_temperature_model.json')
if __name__=='__main__':main()
