

==🔴`lstm_predict.py`를 수정했습니다. 기존 LSTM 모델과 학습변수 16개는 유지하면서 **센서 데이터 조회 대상을 `ai_oiltemp`에서 `ai_data`로 변경**했습니다.==

### 수정된 코드 다운로드

📄 **lstm_predict.py**

### 1. 변경된 데이터 처리 방식

```
① ai_oiltemp
   └─ 최신 id 조회
      ├─ id
      ├─ comcode
      ├─ device_id
      └─ input_time
           │
           ▼
② ai_data
   └─ 동일 업체·설비의 과거 38분 센서 데이터 조회
      ├─ io003 : 오일온도
      ├─ io028 : 부하율
      ├─ io010 : 유효전력
      └─ 기타 센서값
           │
           ▼
③ LSTM
   └─ 16개 입력변수로 예측
      ├─ 10분
      ├─ 30분
      ├─ 60분
      └─ 120분
           │
           ▼
④ ai_lstm_r
   └─ oiltemp_id = ai_oiltemp.id
      └─ 예측 결과 4건 저장
```

### 2. 주요 수정 사항

|항목|기존 코드|수정 코드|
|---|---|---|
|기준 ID 조회|`ai_oiltemp.id`|유지|
|센서 데이터 조회|`ai_oiltemp`|**`ai_data`**|
|설비번호 컬럼|`device_id`|`ai_data.deviceId`|
|조회 기준|최신 ID의 측정시각|유지|
|LSTM 입력|16개 변수|유지|
|예측 기간|10·30·60·120분|유지|
|결과 저장|`ai_lstm_r`|유지|
|연결 ID|`oiltemp_id`|유지|

`ai_data.input_time`은 `YYYY-MM-DD HH:MM:SS` 형식의 문자열이라고 가정했습니다.

### 3. 실행 방법

다운로드한 파일을 기존 `lstm_predict.py`와 교체하세요.

먼저 한 번만 실행합니다.

```
python lstm_predict.py --once
```

정상적으로 동작하면 5초마다 최신 ID를 확인하도록 실행할 수 있습니다.

```
python lstm_predict.py
```

### 4. 확인해야 할 사항

현재 코드는 다음 조건을 전제로 작성했습니다.

- `ai_data`에 필요한 센서 컬럼 12개가 존재해야 합니다.
- `ai_oiltemp.input_time`과 `ai_data.input_time`이 같은 시간대를 사용해야 합니다.
- 기존 `models` 폴더에 학습된 LSTM 모델이 있어야 합니다.
- `ai_lstm_r`에 `(oiltemp_id, prediction_horizon_min, model_version)` 유니크 키가 설정되어 있어야 중복 저장을 방지할 수 있습니다.

**참고:** 이번 수정은 코드 작성과 문법 검사까지 완료한 상태입니다. 실제 MySQL 데이터와 LSTM 모델을 이용한 실행 검증은 아직 하지 않았습니다.

우선 `python lstm_predict.py --once`를 실행해 보세요. 다음 오류가 발생하면 그 결과를 기준으로 센서 데이터 처리 부분을 수정할 수 있습니다.

lstm_predict.py코드


//////////////////////

==🔴**`ai_oiltemp`에서 최신 `id`를 가져오고, 해당 행의 `comcode`, `device_id`, `input_time`을 이용하여 `ai_data`의 센서값을 조회**하는 방식으로 구현하겠습니다.==

다만 중요한 점이 있습니다. 현재 확인된 `ai_data` 구조에는 `oiltemp_id` 컬럼이 없으므로, `ai_oiltemp.id`와 `ai_data`를 직접 연결할 수는 없습니다. 대신 **업체코드 + 설비번호 + 측정시각**을 이용해 해당 센서 데이터를 찾습니다.

## 1. 데이터 처리 구조

```
ai_oiltemp
──────────────────────────
id           = 1050
comcode      = C00088
device_id    = R00015
input_time   = 2026-11-06 15:00:00
──────────────────────────
             │
             │ id = 1050
             ▼
       기준 정보 조회
             │
             ▼
ai_data
──────────────────────────
comcode      = C00088
deviceId     = R00015
input_time   = 2026-11-06 15:00:00

io003        = 오일온도
io028        = 부하율
io010        = 유효전력
...
──────────────────────────
             │
             ▼
      과거 30분 센서값
             │
             ▼
        LSTM 예측
             │
             ▼
ai_lstm_r
──────────────────────────
oiltemp_id   = 1050
10분 예측온도
30분 예측온도
60분 예측온도
120분 예측온도
──────────────────────────
```

## 2. lstm_predict.py의 get_latest() 함수

`ai_oiltemp`에서 최신 ID를 가져옵니다.

```
def get_latest(conn, comcode, device_id):    sql = """        SELECT            id,            comcode,            device_id,            input_time        FROM ai_oiltemp        WHERE comcode = %s          AND device_id = %s        ORDER BY id DESC        LIMIT 1    """    cur = conn.cursor(dictionary=True)    try:        cur.execute(sql, (comcode, device_id))        return cur.fetchone()    finally:        cur.close()
```

## 3. get_history() 함수 수정

가져온 ID에 해당하는 측정시각을 기준으로 `ai_data`에서 과거 센서값을 조회합니다.

기존 `get_history()` 함수를 아래 코드로 교체하세요.

```
def get_history(conn, latest):    # ai_oiltemp에서 가져온 기준 정보    oiltemp_id = latest["id"]    comcode = latest["comcode"]    device_id = latest["device_id"]    end = latest["input_time"]    # LSTM 입력에 필요한 과거 데이터    start = end - timedelta(minutes=38)    cols = [        "input_time",        "io003",        "io028",        "io010",        "io044",        "io045",        "io046",        "io048",        "io007",        "io008",        "io009",        "io004",        "io005"    ]    sql = f"""        SELECT            {",".join(cols)}        FROM ai_data        WHERE comcode = %s          AND deviceId = %s          AND STR_TO_DATE(              input_time,              '%%Y-%%m-%%d %%H:%%i:%%s'          ) > %s          AND STR_TO_DATE(              input_time,              '%%Y-%%m-%%d %%H:%%i:%%s'          ) <= %s        ORDER BY            STR_TO_DATE(                input_time,                '%%Y-%%m-%%d %%H:%%i:%%s'            ) ASC    """    cur = conn.cursor(dictionary=True)    try:        cur.execute(            sql,            (comcode, device_id, start, end)        )        rows = cur.fetchall()        df = pd.DataFrame(rows)        if not df.empty:            df["input_time"] = pd.to_datetime(
```

이 코드는 `ai_data.input_time`이 `YYYY-MM-DD HH:MM:SS` 형식으로 저장되어 있다는 전제입니다. 실제 형식이 다르면 변환식을 변경해야 합니다.

## 4. ai_lstm_r 저장

기존 `write_results()` 함수를 그대로 사용할 수 있습니다.

핵심은 다음 부분입니다.

```
int(latest["id"])
```

이 값이 `ai_lstm_r.oiltemp_id`에 저장됩니다.

예를 들어 `ai_oiltemp.id = 1050`이면 다음과 같이 저장됩니다.

|oiltemp_id|prediction_horizon_min|lstm_prediction|
|---|---|---|
|1050|10|82.50|
|1050|30|84.20|
|1050|60|86.70|
|1050|120|89.30|

예측온도는 설명을 위한 가상 값입니다.

## 5. 실행

```
python lstm_predict.py --once
```

정상 실행되면 다음과 같은 로그가 표시됩니다.

```
ai_oiltemp ID: 1050
조회 설비: R00015
센서 데이터: 450건

LSTM 예측 수행

10분 예측 완료
30분 예측 완료
60분 예측 완료
120분 예측 완료

ai_lstm_r 저장 완료
```

실제 데이터 건수는 수집 주기에 따라 달라집니다.

---

### 최종 확인 사항

현재 구조에서는 **`ai_oiltemp.id`로 기준 행을 식별하고, 그 행의 시각과 설비정보로 `ai_data` 센서값을 조회**합니다.

한 가지 확인할 부분은 `ai_data.input_time`과 `ai_oiltemp.input_time`의 시간 기준이 동일한지입니다. 예를 들어 한쪽은 UTC, 다른 쪽은 한국시간이라면 조회 시각을 보정해야 합니다.

또한 동일한 측정시각에 `ai_oiltemp` 행이 여러 개 생성될 수 있으므로, 최신 ID를 기준으로 실행하되 동일 ID에 대한 중복 예측을 방지하는 현재 로직을 유지하면 됩니다.

////////////////

==🔴제공하신 `ai_oiltemp` 테이블 구조를 확인했습니다. 이제 앞서 발생한 오류의 원인이 명확해졌습니다.==

```
1054 (42S22): Unknown column 'io003' in 'field list'
```

**`ai_oiltemp`에는 `io003` 컬럼이 없습니다.** 이 테이블은 센서 원본 데이터를 저장하는 테이블이 아니라 오일온도 예측 결과를 관리하는 테이블입니다.

따라서 `lstm_predict.py`의 데이터 조회 구조를 변경해야 합니다.

## 1. MySQL 테이블별 역할

|테이블|역할|주요 컬럼|
|---|---|---|
|`ai_data`|설비의 원본 센서 데이터|`io003`, `io028`, `io010` 등|
|`ai_oiltemp`|오일온도 예측 결과 및 판정|`id`, `oil_temp_current`, `oil_temp_predicted`|
|`ai_lstm_r`|LSTM 전용 예측 결과|`oiltemp_id`, `lstm_prediction`, `feature_importance`|

### 권장 데이터 처리 구조

```
             ai_data
         (원본 센서 데이터)
                │
                ▼
       최근 30분 데이터 추출
                │
                ▼
        16개 영향인자 계산
                │
                ▼
           LSTM 예측
                │
       ┌────────┼────────┐
       ▼        ▼        ▼
      10분     30분     60분     120분
       │        │        │        │
       └────────┴────────┴────────┘
                │
                ▼
           ai_lstm_r
         (예측 결과 저장)
                │
                ▼
      oiltemp_id로 ai_oiltemp 연결
```

## 2. get_history() 함수 수정

현재 코드는 `ai_oiltemp`에서 센서 데이터를 가져오도록 되어 있습니다.

```
sql = f"""    SELECT {','.join(cols)}    FROM ai_oiltemp    ..."""
```

이를 `ai_data`로 변경해야 합니다.

다만 이전에 확인한 `ai_data`의 설비번호 컬럼은 `deviceId`이고, `input_time`은 `VARCHAR(20)`이었습니다.

따라서 다음과 같이 작성할 수 있습니다.

```
def get_history(conn, latest):    end = latest["input_time"]    start = end - timedelta(minutes=38)    cols = [        "input_time",        "io003", "io028", "io010",        "io044", "io045", "io046", "io048",        "io007", "io008", "io009",        "io004", "io005"    ]    sql = f"""        SELECT {','.join(cols)}        FROM ai_data        WHERE comcode = %s          AND deviceId = %s          AND STR_TO_DATE(input_time, '%%Y-%%m-%%d %%H:%%i:%%s') > %s          AND STR_TO_DATE(input_time, '%%Y-%%m-%%d %%H:%%i:%%s') <= %s        ORDER BY STR_TO_DATE(input_time, '%%Y-%%m-%%d %%H:%%i:%%s') ASC    """    cur = conn.cursor(dictionary=True)    try:        cur.execute(            sql,            (                latest["comcode"],                latest["device_id"],                start,                end            )        )
```

이 코드는 `input_time`이 `YYYY-MM-DD HH:MM:SS` 형식의 문자열이라는 가정하에 동작합니다. 실제 저장 형식이 다르면 변환식을 조정해야 합니다.

또한 현재 `get_latest()`는 `ai_oiltemp`의 최신 ID를 조회하므로, **LSTM 실행 시점에 해당 ID가 이미 생성되어 있어야 합니다.**

## 3. ai_oiltemp와 ai_lstm_r 연결

두 테이블은 다음 관계를 갖습니다.

```
ai_oiltemp
──────────────────────
id = 1050
comcode = C00088
device_id = R00015
input_time = 2026-11-06 15:00:00
         │
         │ 1:N
         ▼
ai_lstm_r
──────────────────────
oiltemp_id = 1050
prediction_horizon_min = 10
lstm_prediction = 82.50

oiltemp_id = 1050
prediction_horizon_min = 30
lstm_prediction = 84.20

oiltemp_id = 1050
prediction_horizon_min = 60
lstm_prediction = 86.70

oiltemp_id = 1050
prediction_horizon_min = 120
lstm_prediction = 89.30
```

위 수치는 저장 구조를 설명하기 위한 예시입니다.

이렇게 하면 `ai_oiltemp.id` 하나에 대해 4개의 LSTM 예측 결과를 연결할 수 있습니다.

## 4. 중요한 설계 문제

현재 `ai_oiltemp`에는 다음 컬럼이 있습니다.

```
prediction_horizon_min
prediction_model
oil_temp_predicted
```

즉, `ai_oiltemp` 자체도 **예측 기간과 예측 알고리즘별로 여러 행이 생성될 수 있는 구조**입니다.

따라서 `ai_oiltemp.id`가 반드시 하나의 측정 시점만 나타내는 것은 아닙니다.

예를 들어 동일한 시각에 CF 예측 4건이 저장되었다면 각각 다른 ID를 갖게 됩니다.

이 경우 단순히 가장 큰 ID를 조회하는 것보다, 어떤 예측 행을 LSTM 결과의 기준으로 사용할지 결정해야 합니다.

**권장 방식은 `ai_oiltemp`에서 기준 행을 명확하게 선택하고, `ai_lstm_r.oiltemp_id`로 연결하는 것입니다.**

---

### 다음 단계

현재까지 확인된 구조를 기준으로 `lstm_predict.py`를 수정할 수 있습니다.

다만 한 가지를 결정해야 합니다.

**LSTM은 어느 시점에 실행할 예정인가요?**

**①** `ai_data`에 새로운 센서 데이터가 입력될 때마다 LSTM 실행 → `ai_oiltemp`와 `ai_lstm_r`에 결과 저장

**②** 기존 프로그램이 `ai_oiltemp`에 새로운 예측 결과를 저장하면 → 해당 `id`를 기준으로 LSTM 실행 → `ai_lstm_r`에 결과 저장

현재 작성된 프로그램은 **②번 방식**입니다. 두 방식 중 어느 것을 사용할지에 따라 `get_latest()`와 결과 저장 코드를 다르게 작성해야 합니다.


////////////

==🔴코드를 작성하라==

MEGACOM 11호기 오일온도 예측을 위한 **LSTM 학습 프로그램과 실시간 추론 프로그램을 분리하여 작성했습니다.**

## 1. 전체 코드 다운로드

📦 **MEGACOM LSTM 전체 Python 코드 다운로드**

압축파일에는 다음 6개 파일이 포함되어 있습니다.

|파일명|기능|
|---|---|
|lstm_train.py|LSTM 모델 학습|
|lstm_predict.py|MySQL 실시간 추론 및 결과 저장|
|lstm_features.py|16개 학습변수 및 파생변수 계산|
|config.py|DB 연결 및 공통 설정|
|requirements.txt|Python 패키지 목록|
|README.md|설치 및 실행 설명서|

## 2. LSTM 학습 프로그램

**학습 조건**

|항목|설정|
|---|---|
|학습 데이터|남양금속 11호기 CSV|
|데이터 간격|1분|
|학습변수|16개|
|LSTM 입력|최근 30분|
|예측 시간|10·30·60·120분|
|모델|예측시간별 독립 LSTM 4개|
|성능 평가|MAE, RMSE, R²|
|영향인자 분석|Permutation Importance|

실행 방법:

```python
pip install -r requirements.txt

python lstm_train.py --csv "남양금속 11호기(4).csv"
```

학습이 완료되면 다음 모델이 생성됩니다.

`models/ lstm_10min.keras lstm_30min.keras lstm_60min.keras lstm_120min.keras scaler_X.pkl scaler_y.pkl importance_10min.json importance_30min.json importance_60min.json importance_120min.json`

## 3. 실시간 추론 프로그램

추론 프로그램은 MySQL의 ai_oiltemp 테이블에서 **가장 최근의 ID를 조회**합니다.

처리 순서는 다음과 같습니다.

`MySQL ai_oiltemp ↓ 가장 최근 id 조회 ↓ 해당 ID와 동일 설비의 과거 데이터 조회 ↓ 5초 데이터를 1분 단위로 변환 ↓ 16개 학습변수 계산 ↓ LSTM 모델 4개 실행 ↓ 10분, 30분, 60분, 120분 후 온도 예측 ↓ 주요 영향인자 분석 ↓ MySQL ai_lstm_r 저장`

### 실행 방법

먼저 config.py와 환경변수에 DB 접속정보를 설정합니다.

1회 예측:

```
python lstm_predict.py --comcode "업체코드" --device-id "설비번호" --once
```

5초 간격 연속 예측:

```
python lstm_predict.py --comcode "업체코드" --device-id "설비번호" --interval 5
```

새로운 ID가 발견되면 4개 예측 결과를 생성합니다.

## 4. ai_lstm_r 저장

예측 결과는 지정한 ai_lstm_r 테이블에 저장됩니다.

|컬럼|저장 내용|
|---|---|
|oiltemp_id|최신 ai_oiltemp.id|
|prediction_horizon_min|10, 30, 60, 120|
|lstm_prediction|예측 오일온도|
|feature_importance|전체 변수 중요도 JSON|
|feature_contributions|개별 예측 기여도 JSON|
|model_version|모델 버전|
|prediction_target_time|미래 예측 대상 시각|

**영향인자 분석은 두 가지로 구분했습니다.**

- feature_importance: 학습 시 계산한 변수별 중요도
- feature_contributions: 실시간 예측에 대한 Integrated Gradients 기여도

현재 개별 기여도 분석은 SHAP이 아닌 Integrated Gradients 방식입니다. 기본적으로 처음과 신규 ID 12개마다 계산하도록 설정했습니다.

lstm_anomaly_score는 실제 미래온도가 확인되기 전까지 NULL로 저장합니다.

## 5. 실행 전 확인사항

**① MySQL 연결정보**

DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME 환경변수를 설정해야 합니다.

**② 학습과 추론 데이터 차이**

학습 CSV는 1분 간격 측정값이고 실시간 데이터는 5초 간격 측정값입니다. 현재 추론 프로그램은 5초 데이터를 1분 평균으로 변환합니다.

따라서 실제 운영 전 두 데이터의 전처리 방식 차이가 예측 정확도에 미치는 영향을 검증해야 합니다.

**③ MySQL 중복 저장 방지**

동일한 oiltemp_id, 예측시간, 모델 버전의 결과가 중복되지 않도록 UNIQUE KEY 설정을 권장합니다.

---

### 현재 구현 상태

|기능|상태|
|---|---|
|LSTM 학습 코드|작성 완료|
|10·30·60·120분 예측|작성 완료|
|16개 학습변수|작성 완료|
|주요 영향인자 분석|작성 완료|
|최신 ai_oiltemp.id 조회|작성 완료|
|5초 주기 실시간 추론|작성 완료|
|ai_lstm_r 저장|작성 완료|
|Python 문법 검사|완료|
|실제 CSV 전체 학습 및 정확도 검증|미실행|
|실제 MySQL 연동 시험|미실행|

**권장 실행 순서는 lstm_train.py로 모델을 학습한 다음, lstm_predict.py --once로 DB 저장을 시험하고, 정상 동작이 확인되면 5초 간격 연속 추론을 시작하는 것입니다.**


////////////////////

==🔴학습하는 코드와 추론하는 코드를 분라할수잇는가?==

네. **LSTM 학습 코드와 실시간 추론 코드를 분리하는 것이 좋습니다.** 특히 현재 MEGACOM 11호기 오일온도 예측 시스템에서는 두 프로그램을 독립적으로 운영하는 것을 권장합니다.

학습은 필요할 때만 실행하고, 추론은 MySQL에서 최신 데이터를 읽어 5초마다 실행하는 구조입니다.

## 1. 프로그램 구성

|구분|학습 프로그램|추론 프로그램|
|---|---|---|
|파일명|lstm_train.py|lstm_predict.py|
|목적|LSTM 모델 학습|미래 오일온도 예측|
|데이터|1분 간격 CSV|5초 간격 MySQL|
|학습변수|16개|16개|
|입력 시계열|최근 30분|최근 30분|
|예측 시간|10·30·60·120분|10·30·60·120분|
|영향인자 분석|전체 변수 중요도|개별 예측 기여도|
|실행 주기|필요할 때|5초마다|
|GPU|권장|필수 아님|
|출력|모델 및 정규화 파일|ai_lstm_r 저장|

## 2. 전체 파일 구성

`MEGACOM_LSTM/ │ ├── lstm_train.py │ └── LSTM 학습 프로그램 │ ├── lstm_predict.py │ └── MySQL 실시간 추론 프로그램 │ ├── lstm_features.py │ └── 16개 학습변수 및 파생변수 계산 │ ├── config.py │ └── 공통 설정 │ ├── models/ │ ├── lstm_10min.keras │ ├── lstm_30min.keras │ ├── lstm_60min.keras │ ├── lstm_120min.keras │ ├── scaler_X.pkl │ ├── scaler_y.pkl │ └── feature_importance.json │ └── results/ ├── training_metrics.csv └── feature_importance.csv`

**중요한 점은 lstm_features.py를 공통으로 사용한다는 것입니다.**

학습과 추론에서 변수 계산 방법, 순서, 정규화 방식이 달라지면 예측 정확도가 떨어질 수 있습니다.

---

## 3. 학습 프로그램 — lstm_train.py

학습 프로그램은 다음 순서로 동작합니다.

`남양금속 11호기.csv │ ▼ 1분 간격 데이터 읽기 │ ▼ 16개 학습변수 생성 │ ▼ LSTM 학습 │ ├── 10분 모델 ├── 30분 모델 ├── 60분 모델 └── 120분 모델 │ ▼ MAE / RMSE 평가 │ ▼ Permutation Importance 계산 │ ▼ 학습 모델 저장`

실행 명령은 다음과 같이 구성할 수 있습니다.

```
python lstm_train.py
```

학습이 완료되면 .keras 파일이 생성됩니다.

학습 데이터가 추가되거나 모델 성능을 개선할 때만 다시 실행하면 됩니다.

---

## 4. 추론 프로그램 — lstm_predict.py

추론 프로그램은 학습을 수행하지 않습니다.

**이미 학습한 LSTM 모델을 불러와 최신 오일온도를 예측합니다.**

`MySQL ai_oiltemp │ ▼ 가장 최근 id 조회 │ ▼ 해당 id의 학습변수 확인 │ ▼ 동일 설비의 과거 데이터 조회 │ ▼ 5초 데이터를 1분 입력으로 변환 │ ▼ 16개 변수 × 30개 시점 │ ▼ 저장된 LSTM 모델 실행 │ ├── 10분 후 예측온도 ├── 30분 후 예측온도 ├── 60분 후 예측온도 └── 120분 후 예측온도 │ ▼ SHAP 주요 영향인자 분석 │ ▼ MySQL ai_lstm_r 저장`

실행 명령:

```
python lstm_predict.py
```

추론 프로그램은 계속 실행되면서 5초마다 새로운 데이터를 확인합니다.

새로운 ai_oiltemp.id가 발견되면 예측을 수행합니다.

---

## 5. 학습 모델을 추론 프로그램에서 사용하는 방법

학습 프로그램에서는 다음과 같이 모델을 저장합니다.

model.save("models/lstm_10min.keras")

추론 프로그램에서는 다음과 같이 불러옵니다.

from tensorflow.keras.models import load_model

  

model_10 = load_model("models/lstm_10min.keras")

model_30 = load_model("models/lstm_30min.keras")

model_60 = load_model("models/lstm_60min.keras")

model_120 = load_model("models/lstm_120min.keras")

모델은 프로그램 시작 시 한 번만 불러오면 됩니다.

5초마다 다시 불러올 필요는 없습니다.

## 6. ai_lstm_r 저장

추론 프로그램은 최신 ai_oiltemp.id를 기준으로 다음 4개 결과를 저장합니다.

|oiltemp_id|prediction_horizon_min|lstm_prediction|feature_importance|feature_contributions|
|---|--:|--:|---|---|
|15230|10|79.5|JSON|JSON|
|15230|30|82.3|JSON|JSON|
|15230|60|86.2|JSON|JSON|
|15230|120|92.1|JSON|JSON|

예측온도는 예시값입니다.

feature_importance는 학습 시 계산한 전체 변수 중요도를 사용하고, feature_contributions는 실시간 개별 예측에 대한 SHAP 분석 결과를 저장하도록 구성합니다.

SHAP 계산 시간이 5초를 초과할 수 있으므로, 예측온도를 먼저 저장하고 기여도는 별도로 계산해 업데이트하는 방식이 안정적입니다.

---

## 7. 권장하는 최종 설계

현재 프로젝트에서는 **3개 Python 프로그램과 1개 설정 파일**로 구성하는 것이 적절합니다.

|파일|기능|
|---|---|
|lstm_train.py|CSV 학습, 4개 LSTM 모델 생성, 변수 중요도 계산|
|lstm_predict.py|최신 ai_oiltemp.id 조회, 실시간 예측, DB 저장|
|lstm_features.py|학습·추론 공통 16개 변수 계산|
|config.py|DB 연결정보, 예측시간, 모델 경로 설정|

학습 데이터는 1분 간격이고 추론 데이터는 5초 간격이므로, **두 프로그램에서 동일한 1분 단위 입력 시계열을 생성하도록 설계하는 것이 가장 중요합니다.**

이 구조라면 학습 프로그램을 종료해도 추론 프로그램은 독립적으로 계속 실행할 수 있으며, 새로운 모델을 학습한 후 추론 프로그램에 적용할 수도 있습니다.



/////////////////////

==🔴**`ai_oiltemp` 테이블에서 가장 최근의 `id`를 자동으로 조회한 후 LSTM 예측을 수행**하도록 구성하겠습니다.==

## 1. 최신 ID 조회 SQL

```
SELECT *
FROM ai_oiltemp
WHERE comcode = %s
  AND device_id = %s
ORDER BY id DESC
LIMIT 1;
```

이 SQL은 지정된 업체와 설비의 가장 큰 `id`를 가져옵니다.

단, `id`가 데이터 입력 순서대로 증가한다는 전제입니다.

## 2. Python 코드

```
import mysql.connectordef get_latest_oiltemp(conn, comcode, device_id):    sql = """        SELECT *        FROM ai_oiltemp        WHERE comcode = %s          AND device_id = %s        ORDER BY id DESC        LIMIT 1    """    cursor = conn.cursor(dictionary=True)    try:        cursor.execute(sql, (comcode, device_id))        return cursor.fetchone()    finally:        cursor.close()
```

### LSTM 예측 실행

```
def run_latest_prediction(conn, comcode, device_id):    # 1. 가장 최근 데이터 조회    latest = get_latest_oiltemp(        conn,        comcode,        device_id    )    if latest is None:        print("예측할 데이터가 없습니다.")        return    oiltemp_id = latest["id"]    print("최신 oiltemp_id:", oiltemp_id)    print("데이터 시각:", latest["input_time"])    # 2. 최신 ID를 기준으로 LSTM 예측    predictions = predict_oiltemp(oiltemp_id)    return predictions
```

여기서 `predict_oiltemp()`는 앞서 설명한 예측 함수이며, 실제 실행을 위해서는 과거 데이터 조회, 16개 변수 전처리, 저장된 LSTM 모델 로딩 및 예측 기능을 구현해야 합니다.

## 3. 최종 처리 구조

```
ai_oiltemp
    │
    ▼
가장 최근 id 조회
ORDER BY id DESC LIMIT 1
    │
    ▼
해당 ID의 16개 학습변수 조회
    │
    ▼
동일 설비의 과거 30분 데이터 조회
    │
    ▼
LSTM 예측
    │
    ├── 10분 후 오일온도
    ├── 30분 후 오일온도
    ├── 60분 후 오일온도
    └── 120분 후 오일온도
    │
    ▼
주요 영향인자 분석
    │
    ▼
ai_lstm_r 저장
    │
    ├── oiltemp_id = 최신 id
    ├── lstm_prediction
    ├── feature_importance
    └── feature_contributions
```

## 4. 5초 간격 자동 실행

실시간 데이터가 5초마다 들어오므로 다음과 같이 처리합니다.

```
import timelast_processed_id = Nonewhile True:    latest = get_latest_oiltemp(        conn,        comcode,        device_id    )    if latest is not None:        current_id = latest["id"]        # 새로운 데이터가 들어온 경우에만 예측        if current_id != last_processed_id:            print("새 데이터:", current_id)            try:                predict_oiltemp(current_id)                # 예측 및 DB 저장 성공 후 갱신                last_processed_id = current_id            except Exception as e:                print("LSTM 예측 오류:", e)    time.sleep(5)
```

이 코드는 **5초마다 최신 ID를 확인하고, 새로운 ID가 있을 때만 예측**합니다.

실제 운영에서는 MySQL 연결이 끊겼을 때 재연결하는 기능과 프로그램 재시작 시 이미 처리한 ID를 확인하는 기능도 추가하는 것이 좋습니다.

### 최종 확정 사항

|항목|설정|
|---|---|
|원본 테이블|`ai_oiltemp`|
|데이터 선택|가장 최근 `id`|
|조회 주기|5초|
|LSTM 입력|최근 30분 × 16개 변수|
|예측 시간|10·30·60·120분|
|영향인자 분석|변수 중요도 및 개별 예측 기여도|
|결과 테이블|`ai_lstm_r`|
|원본 연결|`ai_lstm_r.oiltemp_id = ai_oiltemp.id`|
|결과 저장|최신 ID당 4개 행|

**즉, 최신 `ai_oiltemp.id`를 자동으로 찾아서 예측하고, 그 결과를 `ai_lstm_r`에 저장하는 방식입니다.**/////////////////////
////////////////////////////////////////////////

|   |   |   |
|---|---|---|
|컬럼명|데이터 타입|설명|
|id|BIGINT AUTO_INCREMENT<br><br>PRIMARY KEY|고유번호|
|oiltemp_id|BIGINT UNSIGNED|FK<br><br>ai_oiltemp.id 참조|
|comcode|VARCHAR(15)|업체 코드|
|device_id|VARCHAR(20)|설비 번호|
|input_time|DATETIME(3)|분석 기준 데이터 시각|
|current_datetime|DATETIME(3)|분석 실행 시각|
|prediction_horizon_min|INT|예측 기간(분)<br><br>(10, 30, 60, 120분 등)|
|prediction_target_time|DATETIME(3)|예측 대상 시각|
|lstm_prediction|DECIMAL(10,2)|LSTM 예측 온도값|
|lstm_anomaly_score|DECIMAL(10,2)|LSTM 기반 이상 점수|
|feature_importance|JSON|영향인자 중요도|
|feature_contributions|JSON|개별 영향인자의 예측 기여도|
|model_version|VARCHAR(80)|LSTM 모델 버전|
|created_at|DATETIME(3)|결과 저장 시각|


|컬럼명|저장 내용|처리 방법|
|---|---|---|
|`id`|고유번호|AUTO_INCREMENT|
|`oiltemp_id`|원본 데이터 ID|`ai_oiltemp.id`|
|`comcode`|업체 코드|원본 데이터|
|`device_id`|설비 번호|원본 데이터|
|`input_time`|분석 기준 시각|원본 데이터 시각|
|`current_datetime`|분석 실행 시각|Python 실행 시각|
|`prediction_horizon_min`|예측 기간|10, 30, 60, 120|
|`prediction_target_time`|예측 대상 시각|기준 시각 + 예측 기간|
|`lstm_prediction`|미래 오일온도|LSTM 예측값(℃)|
|`lstm_anomaly_score`|이상 점수|별도 계산|
|`feature_importance`|전체 변수 중요도|JSON|
|`feature_contributions`|개별 예측 기여도|JSON|
|`model_version`|모델 버전|모델 관리|
|`created_at`|결과 저장 시각|MySQL 자동 입력 가능|