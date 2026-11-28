"""MEGACOM LSTM trainer for Training UI. Requires train_cf.py alongside it."""
import argparse, json
from datetime import datetime
from pathlib import Path
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from train_cf import RAW, DERIVED, load, prepare, log

ROOT = Path(__file__).resolve().parent

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--comcode', default='C00088')
    p.add_argument('--device-id', default='R00012')
    p.add_argument('--source', choices=['csv','mysql'], default='csv')
    for key in ('csv-path','csv-time-column','csv-clock-column','csv-device-value'):
        p.add_argument('--'+key)
    p.add_argument('--start-date', required=True)
    p.add_argument('--end-date', required=True)
    p.add_argument('--features', default=','.join(RAW+DERIVED))
    p.add_argument('--horizons', default='10,30,60,120')
    p.add_argument('--humidity-mode', choices=['actual','mean','exclude'], default='mean')
    p.add_argument('--learning-rate', type=float, default=.001)
    p.add_argument('--epochs', type=int, default=50)
    p.add_argument('--batch-size', type=int, default=64)
    p.add_argument('--sequence-length', type=int, default=30)
    a=p.parse_args()
    import tensorflow as tf
    tf.keras.utils.set_random_seed(42)
    features=list(dict.fromkeys(f.strip() for f in a.features.split(',') if f.strip()))
    if a.humidity_mode=='exclude': features=[f for f in features if f!='io048']
    hs=list(dict.fromkeys(map(int,a.horizons.split(','))))
    L=a.sequence_length
    if not features or set(features)-set(RAW+DERIVED): raise ValueError('Invalid features')
    if min(hs+[L,a.epochs,a.batch_size])<=0 or a.learning_rate<=0: raise ValueError('Invalid training parameters')
    log('PROGRESS 1')
    m=prepare(load(a),features,a.humidity_mode)
    n=len(m); cut=int(n*.8); valcut=int(cut*.85)
    if valcut<L+max(hs) or n-cut<L+max(hs): raise ValueError('Insufficient time coverage')
    humidity=None
    if 'io048' in features and a.humidity_mode=='mean':
        humidity=float(m.io048.iloc[:valcut].mean())
        if not np.isfinite(humidity): raise ValueError('No valid training humidity')
        m['io048']=humidity
        log(f'Fixed humidity: {humidity:.4f}')
    x=m[features].to_numpy(dtype=np.float32); y=m.io003.to_numpy(dtype=np.float32)
    valid=np.isfinite(x).all(axis=1)
    fitrows=valid & (np.arange(n)<valcut)
    if not fitrows.any(): raise ValueError('No valid training features')
    scaler=StandardScaler().fit(x[fitrows]); xs=scaler.transform(x).astype(np.float32)
    # Window ends at t; target is exactly t+h on the regular minute grid.
    ends=np.arange(L-1,n)
    bad=np.r_[0,np.cumsum(~valid)]
    ends=ends[(bad[ends+1]-bad[ends-L+1])==0]
    out=ROOT/'models'/a.device_id/'LSTM'/datetime.now().strftime('%Y%m%d_%H%M%S_%f'); out.mkdir(parents=True)
    meta=dict(features=features,device_id=a.device_id,comcode=a.comcode,sampling='1min',sequence_length=L,humidity_mode=a.humidity_mode,humidity_mean=humidity,feature_mean=scaler.mean_.tolist(),feature_scale=scaler.scale_.tolist(),validation_start=str(m.index[valcut]),test_start=str(m.index[cut]),models=[],deployment_ready=False)
    log(f'One-minute rows: {n:,}; validation starts {m.index[valcut]}; test starts {m.index[cut]}')
    log(f'Oil temperature MIN={np.nanmin(y):.2f}, MAX={np.nanmax(y):.2f}, MEAN={np.nanmean(y):.2f}')
    def save_meta():
        (out/'metadata.json').write_text(json.dumps(meta,indent=2,allow_nan=False),encoding='utf-8')
    def windows(e):
        return xs[e[:,None]-np.arange(L-1,-1,-1)[None,:]]
    for i,h in enumerate(hs):
        e=ends[ends+h<n]; e=e[np.isfinite(y[e+h])]
        # Keep input and target entirely within each chronological partition.
        tr=e[e+h<valcut]; va=e[(e-L+1>=valcut)&(e+h<cut)]; te=e[e-L+1>=cut]
        log(f'===== LSTM {h}min =====')
        log(f'Train sequences: {len(tr):,}; Validation: {len(va):,}; Test: {len(te):,}')
        record=dict(horizon=h,train_rows=len(tr),validation_rows=len(va),test_rows=len(te))
        if min(len(tr),len(va),len(te))<2:
            record.update(status='SKIPPED',reason='Insufficient continuous sequences')
            meta['models'].append(record); save_meta(); log(f'SKIP {h}min: insufficient continuous sequences'); log(f'PROGRESS {int(5+94*(i+1)/len(hs))}'); continue
        target=StandardScaler().fit(y[tr+h,None]); ym=float(target.mean_[0]); ys=float(target.scale_[0])
        tf.keras.backend.clear_session()
        model=tf.keras.Sequential([tf.keras.layers.Input(shape=(L,len(features))),tf.keras.layers.LSTM(64,return_sequences=True),tf.keras.layers.Dropout(.2),tf.keras.layers.LSTM(32),tf.keras.layers.Dense(16,activation='relu'),tf.keras.layers.Dense(1)])
        model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=a.learning_rate),loss='mse')
        class Reporter(tf.keras.callbacks.Callback):
            def on_epoch_end(self,epoch,logs=None):
                logs=logs or {}; log(f'LOSS {h} {epoch+1} {logs["loss"]:.8f} {logs["val_loss"]:.8f}')
                log(f'PROGRESS {min(99,int(5+94*(i+(epoch+1)/a.epochs)/len(hs)))}')
        model.fit(windows(tr),(y[tr+h]-ym)/ys,validation_data=(windows(va),(y[va+h]-ym)/ys),epochs=a.epochs,batch_size=a.batch_size,shuffle=False,verbose=0,callbacks=[Reporter(),tf.keras.callbacks.EarlyStopping(monitor='val_loss',patience=10,restore_best_weights=True),tf.keras.callbacks.TerminateOnNaN()])
        actual=y[te+h]; pred=model.predict(windows(te),batch_size=a.batch_size,verbose=0).ravel()*ys+ym
        if not np.isfinite(pred).all(): raise ValueError(f'Nonfinite predictions for {h}min')
        mae=float(mean_absolute_error(actual,pred)); rmse=float(np.sqrt(mean_squared_error(actual,pred))); r2=float(r2_score(actual,pred)) if np.ptp(actual)>0 else None
        baseline=float(mean_absolute_error(actual,y[te]))
        name=f'lstm_{h}min.keras'; model.save(out/name)
        record.update(status='EVALUATED',file=name,target_mean=ym,target_scale=ys,mae=mae,rmse=rmse,r2=r2,persistence_mae=baseline)
        meta['models'].append(record); save_meta()
        log(f'Persistence baseline MAE: {baseline:.4f} C')
        log(f'LSTM_RESULT {h} {mae:.4f} {rmse:.4f} {r2 if r2 is not None else "N/A"}')
        for j in np.linspace(0,len(te)-1,min(300,len(te)),dtype=int): log(f'PRED {h} {actual[j]:.4f} {pred[j]:.4f}')
        log(f'PROGRESS {int(5+94*(i+1)/len(hs))}')
    meta['complete']=all(r['status']=='EVALUATED' for r in meta['models']); save_meta()
    log(f'Model directory: {out}')
    if not any('file' in r for r in meta['models']): raise RuntimeError('No LSTM models trained')
    if not meta['complete']: log('[WARNING] Partial training completed; do not automatically deploy')
    log('PROGRESS 100')

if __name__=='__main__':
    try: main()
    except Exception as exc:
        log(f'[ERROR] {type(exc).__name__}: {exc}'); raise
