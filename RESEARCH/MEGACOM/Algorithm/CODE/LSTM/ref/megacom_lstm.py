"""MEGACOM 11호기: 16변수 LSTM 학습 / 5초 실시간 예측 / 영향인자 분석.

설치: pip install numpy pandas scikit-learn tensorflow joblib
학습: python megacom_lstm.py train --csv "남양금속 11호기(4).csv"
예측: python megacom_lstm.py predict --csv realtime_5sec.csv
CSV 실시간 입력: input_time 또는 _time, io003 등 12개 원본 IO 컬럼.
주의: 실시간 입력은 최소 36분 이상의 이력이 필요하며, DB 연결/저장은 별도 연동.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

RAW = ['io003','io028','io010','io044','io045','io046','io048',
       'io007','io008','io009','io004','io005']
FEATURES = ['io003','temp_rise_5min','io028','io010','io044','io045',
            'io046','io048','io007','io008','io009','io004','io005',
            'current_avg','voltage_avg','current_unbalance']
HORIZONS = [10,30,60,120]
WINDOW = 30
OUT = Path('megacom_models')


def read_csv(path):
    try:
        df = pd.read_csv(path, encoding='utf-8-sig', low_memory=False)
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding='cp949', low_memory=False)
    # Exported machine CSV: Korean labels in header, IO identifiers in first data row.
    if len(df) and str(df.iloc[0].get('오일온도', '')).strip() == 'io003':
        mapping = {col: str(df.iloc[0][col]).strip() for col in df.columns
                   if isinstance(df.iloc[0][col], str) and
                   (str(df.iloc[0][col]).strip().startswith('io') or
                    str(df.iloc[0][col]).strip() in ('_time','deviceId','DeviceName'))}
        df = df.iloc[1:].rename(columns=mapping).copy()
    timecol = next((c for c in ['input_time','_time','time'] if c in df.columns), None)
    if not timecol:
        raise ValueError('시간 컬럼(input_time 또는 _time)이 없습니다.')
    # Preserve local wall-clock for timestamps without timezone; convert UTC Z to KST.
    t = df[timecol].astype(str)
    if t.str.contains(r'(Z|[+-]\d\d:\d\d)$', regex=True).any():
        df['timestamp'] = pd.to_datetime(t, errors='coerce', utc=True).dt.tz_convert('Asia/Seoul').dt.tz_localize(None)
    else:
        df['timestamp'] = pd.to_datetime(t, errors='coerce')
    if 'deviceId' in df.columns:
        devs = df['deviceId'].dropna().astype(str).unique()
        if len(devs) > 1:
            raise ValueError(f'여러 deviceId가 포함됨: {devs}; 설비별로 분리하세요.')
    missing = [c for c in RAW if c not in df.columns]
    if missing:
        raise ValueError(f'필수 컬럼 누락: {missing}')
    for c in RAW:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.dropna(subset=['timestamp']).sort_values('timestamp')
    return df.drop_duplicates('timestamp', keep='last').set_index('timestamp')[RAW]


def engineer(frame):
    d = frame.copy()
    # Exactly five minutes earlier: time-based lookup on a 1-minute grid.
    d['temp_rise_5min'] = (d['io003'] - d['io003'].shift(5)) / 5.0
    currents = d[['io007','io008','io009']]
    d['current_avg'] = currents.mean(axis=1, skipna=False)
    d['voltage_avg'] = d[['io004','io005']].mean(axis=1, skipna=False)
    d['current_unbalance'] = currents.sub(d['current_avg'], axis=0).abs().max(axis=1) / d['current_avg'].replace(0, np.nan) * 100
    return d[FEATURES]


def minute_grid(raw, end=None, max_age_seconds=15):
    """One point per minute, most recent raw sample within max_age_seconds.
    For 5-second streams, anchor the minute grid to the newest observation,
    enabling a fresh 30-step sequence every 5 seconds without future data.
    """
    if end is None:
        end = raw.index.max()
    end = pd.Timestamp(end)
    grid = pd.date_range(end=end, periods=WINDOW + 5, freq='1min')
    left = pd.DataFrame({'timestamp': grid})
    right = raw.reset_index().rename(columns={raw.index.name or 'index':'timestamp'})
    merged = pd.merge_asof(left, right, on='timestamp', direction='backward',
                           tolerance=pd.Timedelta(seconds=max_age_seconds))
    return merged.set_index('timestamp')[RAW]


def training_frame(raw):
    # 1-minute training snapshots. Do not synthesize values over long gaps.
    d = raw.resample('1min').last()
    return engineer(d)


def sequences(frame, horizon):
    arr = frame.to_numpy(dtype='float64')
    oil = frame['io003'].to_numpy(dtype='float64')
    X, y, times = [], [], []
    for target in range(WINDOW - 1 + horizon, len(frame)):
        end = target - horizon + 1
        block = arr[end-WINDOW:end]
        if np.isfinite(block).all() and np.isfinite(oil[target]):
            X.append(block)
            y.append(oil[target])
            times.append(frame.index[target])
    return np.asarray(X, dtype='float32').reshape(-1, WINDOW, len(FEATURES)), np.asarray(y, dtype='float32'), pd.DatetimeIndex(times)


def model_factory():
    from tensorflow import keras
    model = keras.Sequential([
        keras.Input((WINDOW, len(FEATURES))),
        keras.layers.LSTM(64, return_sequences=True),
        keras.layers.Dropout(.2),
        keras.layers.LSTM(32),
        keras.layers.Dense(16, activation='relu'),
        keras.layers.Dense(1)
    ])
    model.compile(optimizer=keras.optimizers.Adam(1e-3), loss='mse')
    return model


def feature_importance(model, X, y, scaler_x, scaler_y, repeats=3, seed=42):
    """Global permutation importance: increase in MAE (degrees C).
    Correlated features can share importance; this is not causal attribution.
    """
    rng = np.random.default_rng(seed)
    pred = scaler_y.inverse_transform(model.predict(X, verbose=0)).ravel()
    actual = scaler_y.inverse_transform(y.reshape(-1,1)).ravel()
    base = mean_absolute_error(actual, pred)
    out = []
    for j, name in enumerate(FEATURES):
        diffs = []
        for _ in range(repeats):
            xp = X.copy()
            xp[:,:,j] = xp[rng.permutation(len(xp)),:,j]
            pp = scaler_y.inverse_transform(model.predict(xp, verbose=0)).ravel()
            diffs.append(mean_absolute_error(actual, pp) - base)
        out.append({'feature':name,'mae_increase_c':float(np.mean(diffs)),
                    'std_c':float(np.std(diffs))})
    return pd.DataFrame(out).sort_values('mae_increase_c', ascending=False)


def train(csv, epochs=30, batch_size=128, max_importance_samples=300):
    import tensorflow as tf
    tf.random.set_seed(42)
    np.random.seed(42)
    OUT.mkdir(exist_ok=True)
    raw = read_csv(csv)
    data = training_frame(raw)
    print('데이터:',len(data),'기간:',data.index.min(), '~', data.index.max())
    if len(data) < 300:
        raise ValueError('학습 데이터 부족: 최소 300분 이상 필요합니다.')
    n = len(data)
    # All models use same chronological train/val/test boundaries.
    train_boundary = data.index[int(n*.70)]
    val_boundary = data.index[int(n*.85)]
    summary = []
    for h in HORIZONS:
        X, y, times = sequences(data, h)
        train_idx = times < train_boundary
        val_idx = (times >= train_boundary) & (times < val_boundary)
        test_idx = times >= val_boundary
        if min(train_idx.sum(), val_idx.sum(), test_idx.sum()) < 20:
            print(f'{h}분: 분할 후 표본 부족, 건너뜀')
            continue
        # Fit scalers only on training samples.
        sx = StandardScaler().fit(X[train_idx].reshape(-1,len(FEATURES)))
        sy = StandardScaler().fit(y[train_idx].reshape(-1,1))
        def transform(xx):
            return sx.transform(xx.reshape(-1,len(FEATURES))).reshape(xx.shape).astype('float32')
        xt, xv, xte = [transform(X[idx]) for idx in [train_idx,val_idx,test_idx]]
        yt, yv, yte = [sy.transform(y[idx].reshape(-1,1)).ravel().astype('float32') for idx in [train_idx,val_idx,test_idx]]
        model = model_factory()
        cb = [tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=7, restore_best_weights=True)]
        model.fit(xt,yt,validation_data=(xv,yv),epochs=epochs,batch_size=batch_size,
                  shuffle=False,callbacks=cb,verbose=2)
        pred = sy.inverse_transform(model.predict(xte,verbose=0)).ravel()
        actual = y[test_idx]
        metrics = {'horizon_min':h,'mae_c':float(mean_absolute_error(actual,pred)),
                   'rmse_c':float(np.sqrt(mean_squared_error(actual,pred))),
                   'r2':float(r2_score(actual,pred)),'train_samples':int(train_idx.sum()),
                   'val_samples':int(val_idx.sum()),'test_samples':int(test_idx.sum())}
        summary.append(metrics)
        pd.DataFrame({'target_time':times[test_idx], 'actual_c':actual,
                      'predicted_c':pred,'error_c':pred-actual}).to_csv(OUT/f'predictions_{h}min.csv',index=False,encoding='utf-8-sig')
        model.save(OUT/f'lstm_{h}min.keras')
        joblib.dump({'x':sx,'y':sy,'features':FEATURES}, OUT/f'scalers_{h}min.joblib')
        # Importance is costly: subsample chronological test data, reproducibly.
        if max_importance_samples > 0:
            ids = np.linspace(0,len(xte)-1,min(len(xte),max_importance_samples),dtype=int)
            imp = feature_importance(model,xte[ids],yte[ids],sx,sy)
            imp.to_csv(OUT/f'importance_{h}min.csv',index=False,encoding='utf-8-sig')
        print(metrics)
    pd.DataFrame(summary).to_csv(OUT/'metrics.csv',index=False,encoding='utf-8-sig')
    (OUT/'config.json').write_text(json.dumps({'features':FEATURES,'horizons':HORIZONS,
         'window_minutes':WINDOW,'training_interval_seconds':60,
         'realtime_aggregation':'last observation at each 1min anchor'},ensure_ascii=False,indent=2),encoding='utf-8')
    print('저장 완료:',OUT.resolve())


def predict(raw):
    from tensorflow import keras
    # Input may be 5-second raw samples. Use the last 36+ minutes of readings.
    if raw.empty:
        raise ValueError('실시간 데이터 없음')
    now = raw.index.max()
    grid = minute_grid(raw, end=now)
    feat = engineer(grid).iloc[-WINDOW:]
    if len(feat) != WINDOW or not np.isfinite(feat.to_numpy(dtype=float)).all():
        raise ValueError('최근 35분+ 시계열에 결측치가 있습니다. 최소 36분의 5초 데이터를 확인하세요.')
    output = []
    for h in HORIZONS:
        path = OUT/f'lstm_{h}min.keras'
        if not path.exists():
            raise FileNotFoundError(path)
        model = keras.models.load_model(path,compile=False)
        obj = joblib.load(OUT/f'scalers_{h}min.joblib')
        sx,sy = obj['x'],obj['y']
        x = sx.transform(feat[FEATURES].to_numpy()).reshape(1,WINDOW,len(FEATURES))
        pred = float(sy.inverse_transform(model.predict(x,verbose=0))[0,0])
        current = float(feat['io003'].iloc[-1])
        output.append({'input_time':now,'target_time':now+pd.Timedelta(minutes=h),
                       'predict_min':h,'current_temp_c':current,
                       'predicted_temp_c':pred,'predicted_delta_c':pred-current})
    return pd.DataFrame(output)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command',required=True)
    p = sub.add_parser('train'); p.add_argument('--csv',required=True)
    p.add_argument('--epochs',type=int,default=30)
    p.add_argument('--importance-samples',type=int,default=300)
    p = sub.add_parser('predict'); p.add_argument('--csv',required=True)
    args = parser.parse_args()
    if args.command == 'train':
        train(args.csv,epochs=args.epochs,max_importance_samples=args.importance_samples)
    else:
        result = predict(read_csv(args.csv))
        print(result.to_string(index=False))
        OUT.mkdir(exist_ok=True)
        result.to_csv(OUT/'latest_prediction.csv',index=False,encoding='utf-8-sig')

if __name__ == '__main__':
    main()
