"""CF-style probability-rule engine for compressor oil-temperature warnings.
Assumes ordered observations sampled every minute; do not mix machines or runs.
A: temperature at exactly h minutes; B: maximum during next h minutes.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, brier_score_loss, confusion_matrix

HORIZONS = (10, 20, 30, 60, 90, 120)
TARGETS = (80, 85, 90)
LOOKBACKS = (5, 10, 20, 30, 60, 120)


def find_col(columns, names):
    def norm(x):
        return ''.join(c for c in str(x).lower() if c not in ' _-\r\n')
    cols = {c: norm(c) for c in columns}
    for name in names:
        for c, n in cols.items():
            if norm(name) in n:
                return c
    return None


def make_features(frame):
    df = frame.copy().reset_index(drop=True)
    tc = find_col(df.columns, ('오일온도', 'oiltemperature', 'oiltemp'))
    if tc is None:
        raise ValueError('오일온도 컬럼을 찾지 못했습니다.')
    lc = find_col(df.columns, ('부하율', 'load'))
    pc = find_col(df.columns, ('유효전력', 'power'))
    currents = [c for c in df.columns if '전류' in str(c) and '누적' not in str(c)]
    df['current_temp'] = pd.to_numeric(df[tc], errors='coerce')
    if lc is not None:
        df['load_value'] = pd.to_numeric(df[lc], errors='coerce')
    if pc is not None:
        df['power_value'] = pd.to_numeric(df[pc], errors='coerce')
    if currents:
        df['current_mean'] = df[currents].apply(pd.to_numeric, errors='coerce').mean(axis=1)
    for n in LOOKBACKS:
        df[f'rate_{n}'] = (df['current_temp'] - df['current_temp'].shift(n)) / n
    # A second-order trend feature.
    df['rate_accel'] = df['rate_5'] - df['rate_30']
    names = ['current_temp'] + [f'rate_{n}' for n in LOOKBACKS] + ['rate_accel']
    names += [c for c in ('load_value', 'power_value', 'current_mean') if c in df]
    return df, names


def labels(series, horizon, mode):
    if mode == 'A':
        return series.shift(-horizon)
    if mode == 'B':
        # shift(-1) ensures current temperature is excluded; full horizon required.
        reverse = series.shift(-1).iloc[::-1]
        return reverse.rolling(horizon, min_periods=horizon).max().iloc[::-1]
    raise ValueError('mode must be A or B')


def build_rules(train, valid, test, feature_names, target, min_count=20, smoothing=30):
    # All bin edges and event rates are learned from TRAIN only.
    train = train.copy(); valid = valid.copy(); test = test.copy()
    event_col = f'y_{target}'
    prior = float(train[event_col].mean())
    evidences = {}
    # Joint rules capture interactions between temperature and trend.
    for name in feature_names:
        x = train[name].dropna().to_numpy(dtype=float)
        if len(x) < 20:
            continue
        edges = np.unique(np.quantile(x, np.linspace(0, 1, 9)))
        if len(edges) < 3:
            continue
        edges[0] = -np.inf; edges[-1] = np.inf
        key = f'bin_{name}'
        for part in (train, valid, test):
            part[key] = pd.cut(part[name], edges, labels=False, include_lowest=True)
        stats = train.groupby(key)[event_col].agg(['sum', 'count'])
        stats = stats.loc[stats['count'] >= min_count]
        lookup = (stats['sum'] + smoothing * prior) / (stats['count'] + smoothing)
        evidences[name] = tuple(part[key].map(lookup).to_numpy(dtype=float) for part in (train, valid, test))
    # Interaction rule: temperature bin x recent temperature rate bin.
    if 'bin_current_temp' in train and 'bin_rate_30' in train:
        joint = ['bin_current_temp', 'bin_rate_30']
        stats = train.groupby(joint)[event_col].agg(['sum', 'count'])
        stats = stats.loc[stats['count'] >= min_count]
        lookup = ((stats['sum'] + smoothing * prior) / (stats['count'] + smoothing)).to_dict()
        vals = []
        for part in (train, valid, test):
            vals.append(np.array([lookup.get((a, b), np.nan) for a, b in zip(part[joint[0]], part[joint[1]])], dtype=float))
        evidences['temp_x_rate30'] = tuple(vals)
    if not evidences:
        raise ValueError('규칙을 만들 수 없습니다. 데이터 확인 필요.')
    matrices = []
    for j in range(3):
        mat = np.column_stack([v[j] for v in evidences.values()])
        matrices.append(np.where(np.isfinite(mat), mat, prior))
    return matrices, list(evidences), prior


def run(df, mode='A', horizons=HORIZONS, targets=TARGETS, output_dir=None):
    if mode not in ('A', 'B'):
        raise ValueError('mode must be A or B')
    out = Path(output_dir or f'cf_results_{mode}')
    out.mkdir(parents=True, exist_ok=True)
    base, features = make_features(df)
    reports, weight_reports = [], []
    for h in horizons:
        h = int(h)
        if h < 1:
            raise ValueError('예측시간은 양의 정수여야 합니다.')
        work = base.copy()
        work['future_temp'] = labels(work['current_temp'], h, mode)
        work = work.dropna(subset=features + ['future_temp']).reset_index(drop=True)
        if len(work) < 500 + 2*h:
            raise ValueError(f'{h}분 예측용 데이터가 부족합니다.')
        # Temporal separation, with a gap >= horizon to avoid label overlap.
        n = len(work); cut1 = int(n*.60); cut2 = int(n*.80)
        train = work.iloc[:cut1-h].copy()
        valid = work.iloc[cut1:cut2-h].copy()
        test = work.iloc[cut2:].copy()
        if min(len(train), len(valid), len(test)) < 50:
            raise ValueError('시간 분리 후 데이터가 부족합니다.')
        pred = pd.DataFrame({'row_index': test.index, 'current_temp': test['current_temp'].to_numpy(),
                             'future_temp_or_max': test['future_temp'].to_numpy()})
        for target in targets:
            for part in (train, valid, test):
                part[f'y_{target}'] = (part['future_temp'] >= target).astype(int)
            mats, names, prior = build_rules(train, valid, test, features, target)
            yv = valid[f'y_{target}'].to_numpy(dtype=int)
            yt = test[f'y_{target}'].to_numpy(dtype=int)
            k = mats[0].shape[1]
            def loss(w):
                p = np.clip(mats[1] @ w, 0, 1)
                return float(np.mean((p-yv)**2))
            result = minimize(loss, np.ones(k)/k, method='SLSQP',
                              bounds=[(0, 1)]*k, constraints=[{'type':'eq','fun':lambda w: w.sum()-1}],
                              options={'maxiter':300})
            w = result.x if result.success else np.ones(k)/k
            pval = np.clip(mats[1] @ w, 0, 1)
            # Select threshold on validation, NEVER on test.
            thresholds = np.unique(np.r_[np.linspace(.01, .99, 99), .5])
            scores = [f1_score(yv, pval >= th, zero_division=0) for th in thresholds]
            th = float(thresholds[int(np.argmax(scores))])
            ptest = np.clip(mats[2] @ w, 0, 1)
            yp = (ptest >= th).astype(int)
            tn, fp, fn, tp = confusion_matrix(yt, yp, labels=[0, 1]).ravel()
            reports.append({'mode':mode, '예측시간(분)':h, '목표온도':target,
                            'train_positives':int(train[f'y_{target}'].sum()),
                            'valid_positives':int(yv.sum()), 'test_positives':int(yt.sum()),
                            'threshold':th, 'Accuracy':accuracy_score(yt, yp),
                            'Precision':precision_score(yt, yp, zero_division=0),
                            'Recall':recall_score(yt, yp, zero_division=0),
                            'F1_Score':f1_score(yt, yp, zero_division=0),
                            'BrierScore':brier_score_loss(yt, ptest),
                            'TN':int(tn), 'FP':int(fp), 'FN':int(fn), 'TP':int(tp)})
            for name, value in zip(names, w):
                weight_reports.append({'mode':mode, '예측시간(분)':h, '목표온도':target,
                                       'evidence':name, 'weight':float(value)})
            pred[f'actual_{target}'] = yt
            pred[f'confidence_{target}'] = ptest
            pred[f'prediction_{target}'] = yp
        pred.to_csv(out / f'{mode}_{h}min_predictions.csv', index=False, encoding='utf-8-sig')
        print(f'{mode}: {h}분 완료')
    report = pd.DataFrame(reports)
    report.to_csv(out / f'{mode}_performance.csv', index=False, encoding='utf-8-sig')
    pd.DataFrame(weight_reports).to_csv(out / f'{mode}_weights.csv', index=False, encoding='utf-8-sig')
    return report
