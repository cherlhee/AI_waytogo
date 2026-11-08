"""CSV 1분 데이터로 4개 직접예측 LSTM 학습 및 permutation importance 저장."""
import argparse, json
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from config import MODEL_DIR, RESULT_DIR, FEATURES, HORIZONS, INPUT_MINUTES, MODEL_VERSION
from lstm_features import read_training_csv, minute_features

def sequences(arr, target, horizon, start, stop):
    X=[]; Y=[]; times=[]
    # 시퀀스 끝 t, 예측 대상 t+horizon; 분리 경계는 대상 시각 기준
    for t in range(max(INPUT_MINUTES-1,start-horizon), stop-horizon):
        a=arr[t-INPUT_MINUTES+1:t+1]
        y=target[t+horizon]
        if len(a)!=INPUT_MINUTES or not np.isfinite(a).all() or not np.isfinite(y): continue
        X.append(a);Y.append(y);times.append(t+horizon)
    return np.asarray(X,dtype='float32').reshape(-1,INPUT_MINUTES,len(FEATURES)), np.asarray(Y,dtype='float32'),times

def model_build():
    from tensorflow import keras
    return keras.Sequential([keras.Input(shape=(INPUT_MINUTES,len(FEATURES))),keras.layers.LSTM(64,return_sequences=True),keras.layers.Dropout(.2),keras.layers.LSTM(32),keras.layers.Dense(16,activation='relu'),keras.layers.Dense(1)])

def main():
    p=argparse.ArgumentParser();p.add_argument('--csv',required=True);p.add_argument('--epochs',type=int,default=30);p.add_argument('--importance-samples',type=int,default=300);args=p.parse_args()
    import tensorflow as tf
    MODEL_DIR.mkdir(exist_ok=True);RESULT_DIR.mkdir(exist_ok=True)
    df=read_training_csv(args.csv)
    m=minute_features(df,utc_input=True)
    n=len(m); train_end=int(n*.70); val_end=int(n*.85)
    if train_end<INPUT_MINUTES+max(HORIZONS)+50: raise ValueError('학습 데이터 부족')
    # scaler는 훈련 구간만으로 적합, NaN 포함 행 제외
    fit_x=m.iloc[:train_end].dropna()
    if fit_x.empty: raise ValueError('학습 가능한 유효 데이터가 없습니다. CSV 컬럼/값 확인')
    sx=StandardScaler().fit(fit_x)
    sy=StandardScaler().fit(m.iloc[:train_end][['io003']].dropna())
    x=sx.transform(m); y=sy.transform(m[['io003']]).ravel()
    joblib.dump(sx,MODEL_DIR/'scaler_X.pkl');joblib.dump(sy,MODEL_DIR/'scaler_y.pkl')
    (MODEL_DIR/'metadata.json').write_text(json.dumps({'features':list(FEATURES),'horizons':list(HORIZONS),'input_minutes':INPUT_MINUTES,'version':MODEL_VERSION,'training_interval_sec':60,'timezone':'Asia/Seoul'},ensure_ascii=False,indent=2),encoding='utf-8')
    summary=[];rng=np.random.default_rng(42)
    for h in HORIZONS:
        print(f'\n--- {h}분 모델 ---',flush=True)
        # 시계열의 입력 및 타깃 모두 동일한 분할 구간에 포함
        Xtr,Ytr,_=sequences(x,y,h,0,train_end)
        Xv,Yv,_=sequences(x,y,h,train_end,val_end)
        Xt,Yt,indices=sequences(x,y,h,val_end,n)
        if min(len(Xtr),len(Xv),len(Xt))==0: raise ValueError(f'{h}분 유효 시퀀스 부족')
        model=model_build();model.compile(optimizer='adam',loss='mse')
        cb=tf.keras.callbacks.EarlyStopping(monitor='val_loss',patience=6,restore_best_weights=True)
        model.fit(Xtr,Ytr,validation_data=(Xv,Yv),epochs=args.epochs,batch_size=64,shuffle=False,callbacks=[cb],verbose=2)
        model.save(MODEL_DIR/f'lstm_{h}min.keras')
        inv=lambda a: sy.inverse_transform(np.asarray(a).reshape(-1,1)).ravel()
        actual=inv(Yt); pred=inv(model.predict(Xt,verbose=0).ravel())
        mae=mean_absolute_error(actual,pred)
        summary.append({'horizon_min':h,'MAE_C':mae,'RMSE_C':np.sqrt(mean_squared_error(actual,pred)),'R2':r2_score(actual,pred),'test_samples':len(Xt)})
        pd.DataFrame({'target_time':m.index[indices],'actual_C':actual,'predicted_C':pred}).to_csv(RESULT_DIR/f'predictions_{h}min.csv',index=False,encoding='utf-8-sig')
        # 개별 feature의 시계열 전체를 다른 샘플과 교환: 전역 중요도 (MAE 증가, ℃)
        k=min(len(Xt),args.importance_samples)
        sel=rng.choice(len(Xt),size=k,replace=False); xb=Xt[sel].copy(); truth=actual[sel]
        base=mean_absolute_error(truth,inv(model.predict(xb,verbose=0)))
        imp={}
        for j,f in enumerate(FEATURES):
            deltas=[]
            for _ in range(3):
                xp=xb.copy(); xp[:,:,j]=xb[rng.permutation(k),:,j]
                deltas.append(mean_absolute_error(truth,inv(model.predict(xp,verbose=0)))-base)
            imp[f]=round(float(np.mean(deltas)),5)
        (MODEL_DIR/f'importance_{h}min.json').write_text(json.dumps(imp,ensure_ascii=False,indent=2),encoding='utf-8')
        print(summary[-1],flush=True)
    pd.DataFrame(summary).to_csv(RESULT_DIR/'metrics.csv',index=False,encoding='utf-8-sig')
    print('학습 완료:',MODEL_DIR)
if __name__=='__main__':main()
