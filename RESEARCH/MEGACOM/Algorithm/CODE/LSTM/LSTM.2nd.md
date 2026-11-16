
누락되는 데이터 값은 무엇인가

현재 로그에서 **누락된 것은 특정 센서값 하나가 아니라, 16:22:48을 기준으로 계산한 1분 구간의 특징값 전체**입니다.

### 1. 누락된 데이터

`2026-11-13 16:22:48 io003 NaN temp_rise_5min NaN io028 NaN io010 NaN io044 NaN io045 NaN io046 NaN io048 NaN io007 NaN io008 NaN io009 NaN io004 NaN io005 NaN current_avg NaN voltage_avg NaN current_unbalance NaN`

총 **16개 특징값이 모두 NaN**입니다.

### 2. 왜 전체가 누락되었는가?

lstm_features.py에는 다음 조건이 있습니다.

`if len(window) < 8: rows.append([np.nan] * len(RAW)) else: rows.append(window.mean().to_numpy())`

따라서 다음 시간 구간에서

**16:21:48 초과 ~ 16:22:48 이하**

센서 데이터가 8건 미만이면 모든 원본 특징값을 NaN으로 처리합니다.

이는 실제 센서값이 모두 누락되었다는 의미는 아닙니다. **데이터가 1~7건 존재하더라도 코드가 전체를 NaN으로 처리할 수 있습니다.**

### 3. 정확하게 어떤 데이터가 누락되었는지 확인하는 방법

lstm_features.py에서 다음 코드를 찾으세요.

`window = d.loc[ (d.index > t - pd.Timedelta(minutes=1)) & (d.index <= t) ]`

바로 아래에 다음 코드를 추가하세요.

`if len(window) < 8: print(f"\n[데이터 부족] 기준시각: {t}") print(f"조회 구간: {t - pd.Timedelta(minutes=1)} ~ {t}") print(f"실제 데이터 개수: {len(window)} / 예상 약 12개") print("실제 수집 시각:") print(window.index.tolist())`

실행하면 다음과 같이 확인할 수 있습니다.

`[데이터 부족] 기준시각: 2026-11-13 16:22:48 조회 구간: 16:21:48 ~ 16:22:48 실제 데이터 개수: 6 / 예상 약 12개 실제 수집 시각: 16:21:53 16:21:58 16:22:03 16:22:08 16:22:13 16:22:18`

위 시각들은 설명을 위한 예시입니다.

이 경우 16:22:18 이후 센서 데이터가 없어서 해당 1분 구간의 관측 개수가 부족한 것입니다.

**결론:** 현재 확인된 것은 16개 특징값 전체가 NaN이라는 사실입니다. 실제로 어떤 센서 데이터가 누락되었는지, 또는 수집 간격이 불규칙한 것인지는 해당 1분 구간의 원본 데이터 시각을 출력해야 정확하게 알 수 있습니다.

"""학습/추론 공통: 1분 기준, 과거 정보만 이용한 파생변수.""" import numpy as np import pandas as pd from config import RAW, FEATURES def read_training_csv(path): # 제공된 CSV는 cp949, 두 번째 행이 io 코드, 첫 번째 열은 UTC 시각 for enc in ('utf-8-sig','cp949'): try: raw = pd.read_csv(path, encoding=enc, low_memory=False) break except UnicodeDecodeError: continue io_row = raw.iloc[0] rename = {col: str(io_row[col]).strip() for col in raw.columns if str(io_row[col]).startswith('io')} rename.update({raw.columns[0]:'input_time'}) df = raw.iloc[1:].rename(columns=rename).copy() return df def normalize_time(s, utc_input=False): # CSV Z/UTC -> 한국 로컬 시간; DB DATETIME은 이미 로컬이라고 가정 if utc_input: return pd.to_datetime(s, errors='coerce', utc=True).dt.tz_convert('Asia/Seoul').dt.tz_localize(None) return pd.to_datetime(s, errors='coerce') def minute_features(df, *, utc_input=False, anchor=None, realtime=False): """realtime=True: anchor 시각에 정렬된 1분 구간의 과거 평균 36개 생성. train: 고정된 1분 구간의 평균. 동일한 센서 의미/단위를 가정한다. """ d = df.copy() missing = [c for c in RAW if c not in d] if missing: raise ValueError(f'누락된 원본 변수: {missing}') d['input_time'] = normalize_time(d['input_time'], utc_input) d = d.dropna(subset=['input_time']).sort_values('input_time') for c in RAW: d[c] = pd.to_numeric(d[c], errors='coerce') d = d.set_index('input_time')[list(RAW)] d = d[~d.index.duplicated(keep='last')] if realtime: if anchor is None: raise ValueError('실시간 anchor 필수') anchor = pd.Timestamp(anchor) # 학습 데이터의 1분 관측값과 일관되게, 각 구간의 과거 60초 평균 # [anchor-60초, anchor]의 오른쪽 끝을 시각 라벨로 사용 points = [anchor-pd.Timedelta(minutes=i) for i in range(35,-1,-1)] rows=[] for t in points: window = d.loc[(d.index > t-pd.Timedelta(minutes=1)) & (d.index <= t)] # 5초 수집시 적어도 8개 관측값 필요 if len(window) < 8: rows.append([np.nan]*len(RAW)) else: rows.append(window.mean().to_numpy()) m = pd.DataFrame(rows,index=pd.DatetimeIndex(points),columns=RAW) else: # CSV는 1분 간격. 원시값을 시간 버킷별 평균으로 집계. m = d.resample('1min').mean() m['temp_rise_5min'] = (m['io003'] - m['io003'].shift(5))/5.0 m['current_avg'] = m[['io007','io008','io009']].mean(axis=1) m['voltage_avg'] = m[['io004','io005']].mean(axis=1) diff = m[['io007','io008','io009']].sub(m['current_avg'],axis=0).abs().max(axis=1) m['current_unbalance'] = 100*diff/m['current_avg'].replace(0,np.nan) # 부분 결측 시 평균값이 유효해 보이지 않도록 원본 변수 전체 확인 m.loc[m[list(RAW)].isna().any(axis=1), ['current_avg','voltage_avg','current_unbalance']] = np.nan return m[list(FEATURES)].replace([np.inf,-np.inf],np.nan)

…

올려주신 lstm_features.py 코드를 확인했습니다.

현재 발생하는 **1분 구간 전체의 NaN 문제는 다음 부분과 관련이 있습니다.**

# 5초 수집 시 적어도 8개 관측값 필요

if len(window) < 8:

rows.append([np.nan] * len(RAW))

else:

rows.append(window.mean().to_numpy())

이 코드는 1분 구간에 센서 데이터가 7건 이하이면, 실제 측정값이 존재하더라도 해당 구간의 모든 특징값을 NaN으로 만듭니다.

### 수정 방법

센서 데이터가 1건 이상 존재하면 평균을 계산하도록 변경할 수 있습니다. 다만 원래의 8건 이상 조건을 완화하는 것이므로, 학습 데이터와의 일관성 및 예측 정확도를 검증해야 합니다.

for t in points:

start = t - pd.Timedelta(minutes=1)

  

window = d.loc[

(d.index > start) &

(d.index <= t)

]

  

if len(window) == 0:

print(f"[센서 데이터 없음] {start} ~ {t}")

rows.append([np.nan] * len(RAW))

else:

if len(window) < 8:

print(

f"[센서 데이터 부족] {t}, "

f"수집 건수: {len(window)}/12"

)

  

rows.append(window.mean().to_numpy())

이렇게 하면 센서 데이터가 1~7건인 구간도 계산할 수 있습니다. 하지만 **센서값이 전혀 없는 구간이나 특정 센서 컬럼 자체가 비어 있는 경우에는 여전히 NaN이 발생**합니다.

또한 다음 코드도 수정하는 것이 좋습니다.

기존:

m['current_avg'] = m[['io007','io008','io009']].mean(axis=1)

m['voltage_avg'] = m[['io004','io005']].mean(axis=1)

수정:

m['current_avg'] = m[

['io007', 'io008', 'io009']

].mean(axis=1, skipna=False)

  

m['voltage_avg'] = m[

['io004', 'io005']

].mean(axis=1, skipna=False)

이후 다음 코드는 삭제할 수 있습니다.

m.loc[

m[list(RAW)].isna().any(axis=1),

['current_avg', 'voltage_avg', 'current_unbalance']

] = np.nan

이 변경으로 전류와 전압이 정상이라면 io044가 결측이더라도 전류·전압 파생값은 계산됩니다. 단, io044 자체의 결측은 해결되지 않습니다.

**중요한 점:** 앞서 나타난 2026-11-13 16:22:48의 전체 NaN이 실제로 수집 건수 부족 때문인지는 아직 확인되지 않았습니다. 위 코드의 수집 건수 로그를 통해 확인할 수 있습니다.

현재 MEGACOM LSTM에서는 **1분 평균을 만들 때 정확한 초 단위 시각 일치는 필요하지 않지만, 해당 60초 구간에 실제로 몇 건이 수집되었는지 확인하는 것이 중요합니다.**

/////////


최신데이터중에서 놓치는 부분은 없는가

네. **현재 lstm_predict.py 코드에서는 최신 데이터 중 일부를 놓칠 가능성이 있습니다.**

현재 로그에서는 5초마다 정상적으로 예측하고 있지만, 모든 신규 데이터가 빠짐없이 처리된다는 보장은 없습니다.

### 1. 현재 코드의 문제점

latest = get_latest(conn, args.comcode, args.device_id)

  

if latest["input_time"] != last_success:

# LSTM 예측 수행

get_latest()는 다음 SQL을 사용합니다.

```
SELECT comcode, deviceId, input_time
FROM ai_data
WHERE comcode = %s
  AND deviceId = %s
ORDER BY input_time DESC
LIMIT 1
```

**문제는 항상 가장 최신 데이터 1건만 조회한다는 것입니다.**

예를 들어 다음과 같은 상황을 생각해 보겠습니다.

|ai_data 입력 시각|처리 상태|
|---|---|
|12:00:00|예측 완료|
|12:00:05|예측하지 못함|
|12:00:10|예측하지 못함|
|12:00:15|예측 완료|

12:00:05~12:00:15 사이에 프로그램이 지연되었다면, 12:00:15 데이터만 가져오기 때문에 중간 데이터는 놓치게 됩니다.

### 2. 현재 구조에서 누락이 발생하는 경우

|상황|데이터 누락 가능성|
|---|---|
|정상적으로 5초마다 실행|낮음|
|LSTM 계산이 5초 이상 소요|있음|
|IG 계산으로 처리 지연|있음|
|MySQL 연결 지연|있음|
|프로그램 일시 중지|있음|
|프로그램 재시작|있음|
|센서 데이터가 늦게 DB에 입력|있음|

특히 현재 코드는 last_success를 메모리에만 저장합니다. 프로그램을 재시작하면 이전에 어디까지 처리했는지 알 수 없습니다.

### 3. 누락 방지 방법

현재 방식:

```
SELECT *
FROM ai_data
ORDER BY input_time DESC
LIMIT 1;
```

권장 방식:

```
SELECT *
FROM ai_data
WHERE comcode = %s
  AND deviceId = %s
  AND input_time > %s
ORDER BY input_time ASC;
```

여기서 마지막 %s에는 **마지막으로 성공적으로 예측한 input_time**을 넣습니다.

예를 들어 마지막 처리 시각이 12:00:00이고 현재 12:00:20이라면:

`12:00:05 → LSTM 예측 → 저장 12:00:10 → LSTM 예측 → 저장 12:00:15 → LSTM 예측 → 저장 12:00:20 → LSTM 예측 → 저장`

이렇게 순서대로 처리하면 일시적인 지연으로 인한 누락을 방지할 수 있습니다.

단, 각 시각을 기준으로 과거 30분 특징값을 생성해야 하므로 현재의 get_history() 함수를 그대로 활용할 수 있습니다.

### 4. 추가로 필요한 기능

**마지막 처리 시각을 MySQL에 저장하는 것이 좋습니다.**

예를 들어 ai_lstm_r에 다음 데이터가 있다고 가정합니다.

|input_time|prediction_horizon_min|
|---|---|
|12:00:00|10|
|12:00:00|30|
|12:00:00|60|
|12:00:00|120|

프로그램 재시작 시 마지막으로 4개 예측이 모두 저장된 시각을 확인하고, 그 이후의 신규 데이터를 순서대로 처리하면 됩니다.

다만 저장 결과만으로 처리 완료를 판단하려면 4개 예측의 원자적 저장과 중복 방지용 UNIQUE KEY가 필요합니다. 더 확실한 방법은 별도 처리 상태 테이블에 마지막 성공 시각을 저장하는 것입니다.

또한 늦게 도착하는 센서 데이터까지 처리하려면 최근 일정 구간을 재조회하고, 미처리 시각을 확인하는 기능도 필요합니다.

---

### 결론

현재 코드는 **5초마다 최신 데이터 1건을 처리하는 방식**입니다.

사용자가 요구하는 것이 **5초마다 입력되는 모든 ai_data를 빠짐없이 LSTM으로 예측하여 저장하는 것**이라면 다음 구조로 변경하는 것이 적절합니다.

`ai_data ↓ 마지막 처리 시각 조회 ↓ 미처리 데이터 전체 조회 ↓ input_time 오름차순 정렬 ↓ 각 시각별 과거 30분 특징값 생성 ↓ LSTM 10/30/60/120분 예측 ↓ ai_lstm_r 저장 ↓ 마지막 처리 시각 갱신 ↓ 5초 후 반복`

**현재 코드를 이 구조로 변경하면 일시적인 처리 지연이나 프로그램 재시작으로 발생하는 데이터 누락을 크게 줄일 수 있습니다.** 완전한 누락 방지를 위해서는 지연 입력과 예측 실패 데이터의 재처리까지 구현해야 합니다.

/////////////////////////////

선택지는 두 가지입니다.

|구분|방법|
|---|---|
|A|`ai_oiltemp`와의 관계를 유지하고 저장 시에만 `oiltemp_id` 조회|
|B|`ai_lstm_r`를 독립적인 LSTM 예측 테이블로 변경하고 `oiltemp_id` 제거|

### 제안

MEGACOM에서 CF와 LSTM을 각각 독립적으로 실행하려면 **B 방식이 더 단순합니다.**

이 경우:

- CF는 `ai_data`를 읽어 `ai_oiltemp`에 저장
- LSTM도 `ai_data`를 직접 읽어 `ai_lstm_r`에 저장
- 두 결과는 `comcode`, `device_id`, `input_time`, `prediction_horizon_min`으로 연결

단, B 방식은 기존 외래키 제약과 테이블 구조를 변경해야 합니다.

**결론적으로 `ai_oiltemp`의 최신 ID를 조회해야 LSTM 예측을 할 수 있는 것은 아닙니다. `ai_data`의 최신 시각을 기준으로 예측하도록 변경하는 것이 적절합니다.**


/////////////
기존테이블에 칼럼을 추가할수 잇는가, 파이선명령으로

네. **Python 명령으로 MySQL의 기존 테이블에 새로운 컬럼을 추가할 수 있습니다.**

기존 데이터는 유지하면서 컬럼만 추가할 수 있습니다.

## 1. Python으로 컬럼 추가

예를 들어 기존 ai_lstm_r 테이블에 oil_temp_actual 컬럼을 추가하려면 다음과 같이 작성합니다.

import mysql.connector

from config import DB_CONFIG

  

conn = mysql.connector.connect(**DB_CONFIG)

cursor = conn.cursor()

  

sql = """

ALTER TABLE ai_lstm_r

ADD COLUMN oil_temp_actual DECIMAL(10,2) NULL

"""

  

try:

cursor.execute(sql)

print("컬럼 추가 완료")

  

except mysql.connector.Error as err:

print("MySQL 오류:", err)

  

finally:

cursor.close()

conn.close()

실행 후 테이블 구조:

|컬럼명|데이터 타입|설명|
|---|---|---|
|id|BIGINT|기본키|
|oiltemp_id|BIGINT|기존 참조 ID|
|lstm_prediction|DECIMAL(10,2)|LSTM 예측 온도|
|oil_temp_actual|DECIMAL(10,2)|새로 추가한 실제 온도|
|feature_importance|JSON|영향인자 중요도|

## 2. 여러 컬럼을 동시에 추가

sql = """

ALTER TABLE ai_lstm_r

ADD COLUMN oil_temp_actual DECIMAL(10,2) NULL,

ADD COLUMN prediction_error DECIMAL(10,2) NULL,

ADD COLUMN prediction_accuracy DECIMAL(10,2) NULL

"""

  

cursor.execute(sql)


**과거 38분 데이터를 조회하는 이유는 있습니다. 하지만 반드시 38분일 필요는 없습니다.**

현재 LSTM 모델은 **최근 30분 데이터를 입력받아 10분, 30분, 60분, 120분 후의 오일온도를 예측**하도록 구성되어 있습니다.

### 1. 왜 38분을 조회하는가?

현재 특징값에는 다음 변수가 포함되어 있습니다.

```
FEATURES = (    "io003",    "temp_rise_5min",    "io028",    "io010",    ...)
```

여기서 `temp_rise_5min`은 과거 5분 동안의 오일온도 상승률입니다.

따라서 최근 30분의 특징값을 만들려면 그보다 앞선 5분의 온도 데이터도 필요합니다.

|구분|필요한 데이터|
|---|---|
|LSTM 입력|최근 30분|
|5분 온도 상승률 계산|추가 5분|
|여유 데이터|추가 3분|
|합계|38분|

즉, 38분은 특징값 계산을 위한 여유를 포함한 조회 범위입니다.


pip install numpy pandas scikit-learn tensorflow joblib


MEGACOM 11호기 데이터를 기준으로 **LSTM 오일온도 예측 및 주요 영향인자 분석 Python 코드**를 작성했습니다.

### 1. Python 코드 다운로드

업로드한 `남양금속 11호기(4).csv`의 구조를 반영했습니다. CSV 첫 번째 데이터 행에 있는 `io003`, `io004` 등의 코드도 자동으로 처리합니다.

### 2. 구현 기능

|번호|기능|구현 내용|
|---|---|---|
|1|오일온도 예측|10분 후|
|2|오일온도 예측|30분 후|
|3|오일온도 예측|60분 후|
|4|오일온도 예측|120분 후|
|5|학습변수|16개|
|6|파생변수|5분 온도 상승률, 평균전류, 평균전압, 전류 불평형률|
|7|주요 영향인자|Permutation Importance|
|8|모델 평가|MAE, RMSE, R²|
|9|실시간 예측|5초 간격 데이터 입력 지원|
|10|결과 저장|CSV 및 LSTM 모델 파일|

**중요:** 현재 코드는 전체 변수 중요도를 계산합니다. 개별 예측값에 대한 SHAP 기여도 분석과 MySQL 자동 저장은 아직 포함하지 않았습니다.

### 3. 프로그램 설치

Windows 또는 Anaconda 환경에서 실행합니다.

```
pip install numpy pandas scikit-learn tensorflow joblib
```

### 4. LSTM 학습 실행

Python 코드와 CSV 파일을 같은 폴더에 저장한 후 실행합니다.

```
python megacom_lstm.py train --csv "남양금속 11호기(4).csv"
```

프로그램은 다음 작업을 수행합니다.

1. CSV 데이터 읽기
2. 16개 학습변수 구성
3. 최근 30분의 시계열 입력 생성
4. 10·30·60·120분 예측 모델 학습
5. 예측 정확도 평가
6. 주요 영향인자 분석
7. 학습 모델 및 결과 저장

### 5. 주요 영향인자 분석 결과

학습이 완료되면 예측시간별로 중요도 파일이 생성됩니다.


영향인자 분석 결과에는 다음 항목이 포함됩니다.

|항목|의미|
|---|---|
|feature|영향인자 이름|
|mae_increase_c|해당 변수를 섞었을 때 증가한 예측오차(℃)|
|std_c|반복 분석에 따른 중요도 변동|

`mae_increase_c`가 클수록 해당 변수에 대한 LSTM 모델의 의존도가 높습니다.

### 6. 실시간 예측 실행

5초 간격으로 수집한 데이터를 CSV로 저장한 경우 다음과 같이 실행합니다.

```
python megacom_lstm.py predict --csv realtime_5sec.csv
```

실시간 예측 프로그램은 최근 약 35분 이상의 데이터를 이용해 1분 간격 입력 시퀀스를 구성합니다.

예측 결과는 다음 정보를 포함합니다.

|항목|설명|
|---|---|
|input_time|예측 기준 시각|
|target_time|미래 예측 대상 시각|
|predict_min|예측 시간|
|current_temp_c|현재 오일온도|
|predicted_temp_c|미래 예측온도|
|predicted_delta_c|예상 온도 변화량|

현재 코드는 실행할 때마다 한 번 예측합니다. **5초마다 자동 실행하는 반복 처리와 MySQL 연동은 다음 단계에서 추가해야 합니다.**

---

### 7. 다음 개발 단계

최종적으로는 다음 구조를 권장합니다.

**MySQL 실시간 데이터 → LSTM 온도 예측 → SHAP 영향인자 분석 → MySQL 결과 저장**

특히 다음 두 가지를 구분해서 저장하는 것이 중요합니다.

- **예측온도:** 10·30·60·120분 후 오일온도
- **주요 영향인자:** 각 예측온도에 영향을 준 변수와 기여도

이렇게 구성하면 단순히 오일온도가 상승한다고 예측하는 것을 넘어, **어떤 운전조건이 온도 상승 예측에 크게 기여했는지** 확인할 수 있습니다.

현재 제공한 코드는 문법 검사를 완료했으며, 실제 CSV 전체를 이용한 모델 학습과 정확도 검증은 아직 수행하지 않았습니다.

megacom_lstm.py코드

