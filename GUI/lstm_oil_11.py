# 남양금속 11호기: 1분 간격 LSTM 10분 후 오일온도 예측
# 실행: pip install pandas numpy scikit-learn tensorflow matplotlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, precision_recall_fscore_support
from tensorflow import keras




CSV = Path('남양금속 11호기.csv')  # 파일 위치에 맞게 변경
LOOKBACK, HORIZON = 30, 10
COLS = ['오일온도','부하율\n[%]','U전류 [A]','V전류 [A]','W 전류 [A]', '유효전력 [Kw]', '토출압력 [Bar]', '시스템압력 [bar]']



raw = pd.read_csv(CSV, encoding='cp949', low_memory=False, on_bad_lines='skip')
raw['time'] = pd.to_datetime(raw.iloc[:,0], errors='coerce', utc=True)
raw = raw.dropna(subset=['time']).sort_values('time').drop_duplicates('time').reset_index(drop=True)
for c in COLS: raw[c] = pd.to_numeric(raw[c], errors='coerce')
raw = raw.dropna(subset=COLS).reset_index(drop=True)
# 전원 OFF 및 센서 오류에 해당하는 0도 행은 제외하되, 시계열 단절은 유지
raw = raw[raw['오일온도'].between(20, 120)].reset_index(drop=True)
print('행 수:', len(raw), '고온 90℃ 이상:', int((raw['오일온도']>=90).sum()))

# 시점 순서대로 분리. 학습 데이터로만 정규화 학습.
n = len(raw); a = int(n*.70); b = int(n*.85)
scaler_x = StandardScaler().fit(raw.loc[:a-1, COLS].to_numpy(dtype='float32'))
scaler_y = StandardScaler().fit(raw.loc[:a-1, ['오일온도']].to_numpy(dtype='float32'))
X = scaler_x.transform(raw[COLS].to_numpy(dtype='float32')).astype('float32')
y = scaler_y.transform(raw[['오일온도']].to_numpy(dtype='float32')).astype('float32').ravel()
times = raw['time'].to_numpy()
# 결측 시간에 걸친 윈도우는 배제
valid_step = (raw['time'].diff().dt.total_seconds().fillna(60).to_numpy() == 60)
bad = (~valid_step).astype('int64')
prefix = np.r_[0, np.cumsum(bad)]
ends = np.arange(LOOKBACK-1, n-HORIZON)
targets = ends + HORIZON
valid = (prefix[targets+1] - prefix[ends-LOOKBACK+2] == 0)
ends, targets = ends[valid], targets[valid]

class WindowSequence(keras.utils.Sequence):
    def __init__(self, ends, targets, batch=256, shuffle=False):
        super().__init__(); self.ends=ends.copy(); self.targets=targets.copy(); self.batch=batch; self.shuffle=shuffle; self.on_epoch_end()
    def __len__(self): return int(np.ceil(len(self.ends)/self.batch))
    def __getitem__(self, idx):
        e=self.ends[idx*self.batch:(idx+1)*self.batch]
        t=self.targets[idx*self.batch:(idx+1)*self.batch]
        ix=e[:,None]-np.arange(LOOKBACK-1,-1,-1)[None,:]
        return X[ix], y[t]
    def on_epoch_end(self):
        if self.shuffle:
            perm=np.random.permutation(len(self.ends));self.ends=self.ends[perm];self.targets=self.targets[perm]

# 입력도 각 분할 구간 내부에 있도록 설정하여 평가 시 누출 방지
train=(targets<a)
val=(targets>=a+LOOKBACK+HORIZON)&(targets<b)
test=(targets>=b+LOOKBACK+HORIZON)
train_ds=WindowSequence(ends[train],targets[train],shuffle=True)
val_ds=WindowSequence(ends[val],targets[val])
test_ds=WindowSequence(ends[test],targets[test])
print('윈도우:',len(train_ds.ends),len(val_ds.ends),len(test_ds.ends))

model=keras.Sequential([
    keras.layers.Input(shape=(LOOKBACK,len(COLS))),
    keras.layers.LSTM(64,return_sequences=True),
    keras.layers.Dropout(.2),
    keras.layers.LSTM(32),
    keras.layers.Dense(16,activation='relu'),
    keras.layers.Dense(1)
])
model.compile(optimizer='adam',loss='mse',metrics=['mae'])
model.fit(train_ds,validation_data=val_ds,epochs=30,
          callbacks=[keras.callbacks.EarlyStopping(monitor='val_loss',patience=5,restore_best_weights=True)],verbose=1)

pred_scaled=model.predict(test_ds,verbose=1).ravel()
actual=scaler_y.inverse_transform(y[test_ds.targets,None]).ravel()
pred=scaler_y.inverse_transform(pred_scaled[:,None]).ravel()
print('MAE:',mean_absolute_error(actual,pred),'RMSE:',np.sqrt(mean_squared_error(actual,pred)),'R2:',r2_score(actual,pred))
for threshold in [80,85,90]:
    p,r,f,_=precision_recall_fscore_support(actual>=threshold,pred>=threshold,average='binary',zero_division=0)
    print(f'{threshold}℃ Precision={p:.3f} Recall={r:.3f} F1={f:.3f} (실제 양성 {(actual>=threshold).sum()}개)')
result=pd.DataFrame({'time_utc':times[test_ds.targets], 'actual_temp':actual,'predicted_temp':pred,'error':pred-actual})
for threshold in [80,85,90]: result[f'pred_ge_{threshold}']=pred>=threshold
result.to_csv('LSTM_11호기_10분예측.csv',index=False,encoding='utf-8-sig')
model.save('LSTM_11호기_10분.keras')
import joblib
joblib.dump({'x':scaler_x,'y':scaler_y,'features':COLS,'lookback':LOOKBACK,'horizon':HORIZON},'LSTM_11호기_scalers.joblib')
plt.figure(figsize=(13,5));plt.plot(actual[:1000],label='Actual');plt.plot(pred[:1000],label='LSTM 10-min ahead')
for threshold in [80,85,90]: plt.axhline(threshold,ls='--',alpha=.4)
plt.legend();plt.ylabel('Oil temperature (°C)');plt.xlabel('Test sample');plt.tight_layout();plt.savefig('LSTM_11호기_10분예측.png',dpi=160)
print('결과 저장 완료')
