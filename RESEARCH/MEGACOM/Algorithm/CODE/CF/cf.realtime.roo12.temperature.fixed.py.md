

  

이전 메시지 불러오는 중…

1-06 10:22:40 예측 4행 저장: 10분 정상 2026-11-06 10:22:38,233 INFO 실제온도 보정: 4건 입력 (대상 4건 검사) 2026-11-06 10:22:43,391 INFO C00088 2026-11-06 10:22:45 예측 4행 저장: 10분 정상 2026-11-06 10:22:43,439 INFO 실제온도 보정: 4건 입력 (대상 4건 검사) 2026-11-06 10:22:48,577 INFO C00088 2026-11-06 10:22:50 예측 4행 저장: 10분 정상 2026-11-06 10:22:48,625 INFO 실제온도 보정: 4건 입력 (대상 4건 검사) 2026-11-06 10:22:53,765 INFO C00088 2026-11-06 10:22:55 예측 4행 저장: 10분 정상 2026-11-06 10:22:53,814 INFO 실제온도 보정: 4건 입력 (대상 4건 검사) 2026-11-06 10:22:58,967 INFO C00088 2026-11-06 10:23:00 예측 4행 저장: 10분 정상 2026-11-06 10:22:59,015 INFO 실제온도 보정: 4건 입력 (대상 4건 검사),,실제온도 보정이 무엇인가

…

**실제온도 보정: 4건 입력은 과거에 CF가 예측한 온도에 대해, 실제 측정된 오일온도를 찾아 oil_temp_actual 컬럼에 기록했다는 의미입니다.**

### 1. 로그의 의미

`2026-11-06 10:22:43 예측 4행 저장 2026-11-06 10:22:43 실제온도 보정: 4건 입력 (대상 4건 검사)`

두 작업은 서로 다릅니다.

|작업|의미|
|---|---|
|예측 4행 저장|10·30·60·120분 뒤 오일온도 예측|
|실제온도 보정 4건|예측 대상 시각이 지난 기존 4개 행에 실제 측정온도 입력|

### 2. 실제 동작 예시

10:00에 다음과 같이 예측했다고 가정하겠습니다.

|예측시간|예측 대상시간|예측온도|실제온도|
|---|---|--:|--:|
|10:00|10:10|76.5℃|NULL|
|10:00|10:30|78.2℃|NULL|
|10:00|11:00|81.3℃|NULL|
|10:00|12:00|84.5℃|NULL|

10:10이 지나면 ai_data에서 10:10의 실제 측정온도를 찾아 입력합니다.

`oil_temp_predicted = 76.5 oil_temp_actual = 77.1`

이것이 **실제온도 보정**입니다.

### 3. 현재 로그에서 주의할 점

로그를 보면 5초마다 다음 메시지가 반복됩니다.

`실제온도 보정: 4건 입력 (대상 4건 검사)`

이는 매번 실제온도가 비어 있는 예측 행 4개를 찾아 업데이트했다는 의미입니다.

다만 **방금 생성한 예측 4행의 실제온도가 즉시 입력된 것이라면 오류입니다.**

예를 들어 10:22:45에 예측한 10분 뒤 온도는 10:32:45가 지나야 실제온도를 입력할 수 있습니다.

따라서 다음 조건이 반드시 적용되어야 합니다.

`WHERE oil_temp_actual IS NULL AND prediction_target_time <= NOW()`

### 4. 확인할 SQL

`SELECT id, input_time, prediction_target_time, oil_temp_predicted, oil_temp_actual FROM airpredict.ai_oiltemp WHERE device_id = 'R00015' AND prediction_model = 'CF' ORDER BY id DESC LIMIT 20;`

**확인할 사항은 prediction_target_time이 아직 지나지 않은 행에 oil_temp_actual이 입력되어 있는지 여부입니다.**

미래 시각의 실제온도가 이미 입력되어 있다면 시간 비교 또는 실제온도 조회 로직을 수정해야 합니다.

반대로 과거 예측 4건을 정상적으로 채운 것이라면 문제없는 동작입니다.

import mysql.connector import pandas as pd from datetime import datetime import os try: # 1. MySQL 연결 conn = mysql.connector.connect( host="121.181.35.7", port=3307, user="mega_admin", password="megaComp!#%", database="airpredict", connection_timeout=10 ) print("MySQL 접속 성공!") # 2. 최근 20개 데이터 조회 sql = """ SELECT * FROM ai_oiltemp ORDER BY input_time DESC LIMIT 2000 """ # 3. 데이터 읽기 cursor = conn.cursor() cursor.execute(sql) rows = cursor.fetchall() columns = [desc[0] for desc in cursor.description] # 4. DataFrame 생성 df = pd.DataFrame(rows, columns=columns) print(f"조회된 데이터: {len(df)}개") print(df) # 5. CSV 저장 폴더 생성 save_dir = "./CSV_results" os.makedirs(save_dir, exist_ok=True) # 6. 파일명 생성 now = datetime.now().strftime("%Y%m%d_%H%M%S") filename = f"ai_data_recent20_{now}.csv" filepath = os.path.join(save_dir, filename) # 7. CSV 파일 저장 df.to_csv( filepath, index=False, encoding="utf-8-sig" ) print("\nCSV 저장 완료!") print("저장 위치:", os.path.abspath(filepath)) except mysql.connector.Error as err: print("MySQL 오류:", err) finally: if "cursor" in locals(): cursor.close() if "conn" in locals() and conn.is_connected(): conn.close(),,,가장최신의 데이터 저장하라

…

ai_oiltemp 테이블에서 **가장 최근에 저장된 2,000개 데이터를 조회하여 CSV 파일로 저장**하도록 수정하면 됩니다.

기존 코드의 ORDER BY input_time DESC 대신 **`ORDER BY id DESC`**를 사용하세요.

id는 자동 증가하는 값이므로 가장 최근에 추가된 데이터부터 조회할 수 있습니다.

### 1. 수정된 전체 코드

`import mysql.connector import pandas as pd from datetime import datetime import os conn = None cursor = None try: # 1. MySQL 연결 conn = mysql.connector.connect( host="121.181.35.7", port=3307, user="mega_admin", password=os.environ["MYSQL_PASSWORD"], database="airpredict", connection_timeout=10 ) print("MySQL 접속 성공!") # 2. 가장 최근에 저장된 2000개 데이터 조회 sql = """ SELECT * FROM ai_oiltemp WHERE device_id = 'R00015' AND prediction_model = 'CF' ORDER BY id DESC LIMIT 2000 """ cursor = conn.cursor() cursor.execute(sql) rows = cursor.fetchall() columns = [desc[0] for desc in cursor.description] # 3. DataFrame 생성 df = pd.DataFrame(rows, columns=columns) print(f"조회된 데이터: {len(df)}개") # 4. CSV 저장 시 시간순으로 정렬 if not df.empty: df = df.sort_values( by=["input_time", "prediction_horizon_min"], ascending=[False, True] ) print(df) # 5. CSV 저장 폴더 생성 save_dir = "./CSV_results" os.makedirs(save_dir, exist_ok=True) # 6. 파일명 생성 now = datetime.now().strftime("%Y%m%d_%H%M%S") filename = f"ai_oiltemp_recent2000_{now}.csv" filepath = os.path.join(save_dir, filename) # 7. CSV 저장 df.to_csv( filepath, index=False, encoding="utf-8-sig" ) print("\nCSV 저장 완료!") print("저장 위치:", os.path.abspath(filepath)) except mysql.connector.Error as err: print("MySQL 오류:", err) finally: if cursor is not None: cursor.close() if conn is not None and conn.is_connected(): conn.close()`

비밀번호는 코드에 직접 입력하지 않고 환경변수 MYSQL_PASSWORD에서 읽도록 변경했습니다. 기존에 노출된 비밀번호는 교체하는 것이 좋습니다.

### 2. 변경된 부분

|항목|기존|수정|
|---|---|---|
|조회 테이블|ai_oiltemp|ai_oiltemp|
|조회 건수|2,000개|2,000개|
|정렬 기준|input_time DESC|**id DESC**|
|설비|전체|R00015|
|예측 모델|전체|CF|
|CSV 파일명|ai_data_recent20|ai_oiltemp_recent2000|
|저장 위치|CSV_results|CSV_results|

### 3. 가장 중요한 SQL

`SELECT * FROM ai_oiltemp WHERE device_id = 'R00015' AND prediction_model = 'CF' ORDER BY id DESC LIMIT 2000;`

이 SQL은 **가장 최근에 INSERT된 CF 예측 데이터 2,000개**를 가져옵니다.

단, oil_temp_actual은 나중에 UPDATE되므로, id DESC는 최근에 실제온도가 보정된 순서가 아니라 **예측 결과가 처음 저장된 순서**입니다.

**참고:** 모든 설비의 최신 데이터를 저장하려면 WHERE device_id = 'R00015' AND prediction_model = 'CF' 조건을 삭제하면 됩니다.

붙여넣은 텍스트(1)(7).txt문서

설비호기 3대가 있다.. r00012호기 1대만 데이터를 기록하고자 한다

현재 CF 프로그램은 **11호기(R00015) 전용**으로 설정되어 있습니다. 이를 **R00012 설비 1대만 예측하고 MySQL에 저장**하도록 변경하면 됩니다.

첨부하신 코드에서는 다음 부분을 수정하세요.

### 1. 29번째 줄 수정 — 가장 중요

**변경 전**

`DEVICE_ID = 'R00015'`

**변경 후**

`DEVICE_ID = 'R00012'`

이렇게 변경하면 ai_data에서 R00012 데이터만 조회하고, ai_oiltemp에도 해당 설비의 예측 결과만 저장합니다.

현재 코드의 recent_rows(), last_predictions(), update_actual_temperatures() 함수가 모두 DEVICE_ID를 사용하므로 별도로 수정할 필요는 없습니다.

### 2. 373번째 줄 — 설명 변경

`ap = argparse.ArgumentParser( description='R00012 전용 CF 실시간 예측' )`

### 3. 400번째 줄 — 로그 변경

`LOG.info( 'CF 예측 deviceId=%s, comcode=%s, model=%s', DEVICE_ID, comcode or '(전체)', args.model )`

### 4. 주의: CF 학습 모델

현재 프로그램은 다음 두 모델을 사용합니다.

`cf_11_output/ cf_11_model.json cf_11_temperature_model.json`

이 모델들은 기존 11호기 데이터로 학습한 모델입니다.

**R00012 설비에 적용하려면 해당 설비의 과거 데이터로 다시 학습하는 것이 좋습니다.** 그렇지 않으면 설비 특성 차이 때문에 예측오차가 커질 수 있습니다.

### 5. 실행

```
python cf_realtime_11_cf_temperature.py --interval 5
```

이후에는 다음과 같이 저장됩니다.

|device_id|prediction_model|예측 시간|
|---|---|---|
|R00012|CF|10분|
|R00012|CF|30분|
|R00012|CF|60분|
|R00012|CF|120분|

**결론:** 현재 코드에서는 **29번째 줄의 DEVICE_ID = 'R00012'만 변경하면 설비 3대 중 R00012 한 대만 처리**합니다. 기존에 저장된 다른 설비의 데이터는 삭제되지 않습니다.

NFO 실제온도 보정: 2건 입력 (대상 2건 검사) 2026-11-06 10:42:53,437 INFO C00088 2026-11-06 10:42:55 예측 4행 저장: 10분 경고 2026-11-06 10:42:53,480 INFO 실제온도 보정: 2건 입력 (대상 2건 검사) 2026-11-06 10:42:58,624 INFO C00088 2026-11-06 10:43:00 예측 4행 저장: 10분 경고 2026-11-06 10:42:58,657 INFO 실제온도 보정: 2건 입력 (대상 2건 검사) 2026-11-06 10:43:03,796 INFO C00088 2026-11-06 10:43:05 예측 4행 저장: 10분 경고 2026-11-06 10:43:03,828 INFO 실제온도 보정: 2건 입력 (대상 2건 검사) 2026-11-06 10:43:08,967 INFO C00088 2026-11-06 10:43:10 예측 4행 저장: 10분 경고 2026-11-06 10:43:09,008 INFO 실제온도 보정: 2건 입력 (대상 2건 검사) 2026-11-06 10:43:14,150 INFO C00088 2026-11-06 10:43:15 예측 4행 저장: 10분 경고 2026-11-06 10:43:14,184 INFO 실제온도 보정: 2건 입력 (대상 2건 검사) 2026-11-06 10:43:19,312 INFO C00088 2026-11-06 10:43:20 예측 4행 저장: 10분 경고 2026-11-06 10:43:19,343 INFO 실제온도 보정: 2건 입력 (대상 2건 검사),,,예측온도가 80도 미만이면 정상, 80-85 ; 주의 ,,,85-90; 경고,,,90 이상-알람,,,,이렇게 한다.. 실제저장되는 결과는 80도인데 경고가 기록된다???

…

원인은 확인되었습니다. **현재 CF 프로그램은 oil_temp_predicted가 아니라 80·85·90℃ 도달 확신도(CF)를 기준으로 prediction_result를 결정하고 있기 때문입니다.**

따라서 예측온도가 80℃인데도 경고가 저장될 수 있습니다.

요청하신 대로 **예측온도만을 기준으로 판정하도록 변경**하면 됩니다.

## 1. 변경할 판정 기준

|oil_temp_predicted|prediction_result|
|---|---|
|80℃ 미만|정상|
|80℃ 이상 ~ 85℃ 미만|주의|
|85℃ 이상 ~ 90℃ 미만|경고|
|90℃ 이상|알람|

예를 들어 다음과 같습니다.

|예측온도|기존 CF 판정|변경 후|
|--:|---|---|
|79.5℃|경고 가능|정상|
|80.0℃|경고 가능|주의|
|82.3℃|경고 가능|주의|
|85.0℃|주의 가능|경고|
|87.5℃|알람 가능|경고|
|90.0℃|경고 가능|알람|

## 2. Python 코드 수정

첨부하신 cf_realtime_11_cf_temperature.py의 **`prediction_rows()` 함수(196번째 줄 부근)**를 수정하면 됩니다.

현재 코드는 다음과 같이 CF 도달 판정으로 경보를 결정합니다.

if alarms['alarm_90']:

severity, reached_target = '알람', 90

elif alarms['alarm_85']:

severity, reached_target = '경고', 85

elif alarms['alarm_80']:

severity, reached_target = '주의', 80

else:

severity, reached_target = '정상', None

**위 부분을 삭제하고**, 다음과 같이 predicted_temp를 계산한 직후 판정하도록 변경하세요.

# CF 미래 오일온도 예측

predicted_temp = predict_temperature(

temperature_artifact['models'][f'{horizon}min'],

features

)

  

# 예측온도 기준 판정

if predicted_temp >= 90:

severity = '알람'

elif predicted_temp >= 85:

severity = '경고'

elif predicted_temp >= 80:

severity = '주의'

else:

severity = '정상'

## 3. 수정된 prediction_rows() 전체 함수

기존 prediction_rows() 함수를 아래 코드로 교체하면 됩니다.

def prediction_rows(row, features, artifact, temperature_artifact):

  

result = []

  

for horizon in HORIZONS:

  

cf = {}

alarms = {}

thresholds = {}

  

# 기존 CF 도달 확신도 계산은 유지

for target in TARGETS:

  

model = artifact['models'][f'{horizon}min_{target}c']

  

value = cf_score(model, features)

  

cf[f'cf_{target}'] = round(value, 6)

  

thresholds[f'threshold_{target}'] = float(

model['threshold']

)

  

alarms[f'alarm_{target}'] = bool(

value >= model['threshold']

)

  

# 10, 30, 60, 120분 뒤 예측온도 계산

predicted_temp = predict_temperature(

temperature_artifact['models'][f'{horizon}min'],

features

)

  

# 예측온도를 기준으로 경보 판정

if predicted_temp >= 90:

severity = '알람'

이제 prediction_result는 **oil_temp_predicted만을 기준으로 결정**됩니다. 기존 CF 도달 확신도는 prediction_features에 참고 정보로 계속 저장됩니다.

## 4. 이미 저장된 MySQL 데이터도 수정

기존에 잘못 기록된 prediction_result는 다음 SQL로 일괄 수정할 수 있습니다.

먼저 변경될 내용을 확인하세요.

```
SELECT
    id,
    device_id,
    oil_temp_predicted,
    prediction_result AS old_result,
    CASE
        WHEN oil_temp_predicted >= 90 THEN '알람'
        WHEN oil_temp_predicted >= 85 THEN '경고'
        WHEN oil_temp_predicted >= 80 THEN '주의'
        ELSE '정상'
    END AS new_result
FROM airpredict.ai_oiltemp
WHERE device_id = 'R00012'
  AND prediction_model = 'CF'
  AND oil_temp_predicted IS NOT NULL;
```

확인 후 다음 SQL을 실행하면 됩니다.

```
UPDATE airpredict.ai_oiltemp
SET prediction_result =
    CASE
        WHEN oil_temp_predicted >= 90 THEN '알람'
        WHEN oil_temp_predicted >= 85 THEN '경고'
        WHEN oil_temp_predicted >= 80 THEN '주의'
        ELSE '정상'
    END
WHERE device_id = 'R00012'
  AND prediction_model = 'CF'
  AND oil_temp_predicted IS NOT NULL;
```

이 SQL은 prediction_result만 수정하며 예측온도와 실제온도는 변경하지 않습니다.

**결론:** 앞으로는 CF가 예측한 온도가 80.0℃이면 주의, 85.0℃이면 경고, 90.0℃이면 알람으로 저장됩니다.

붙여넣은 텍스트(1)(8).txt문서

첨부하신 CF 프로그램을 확인하고, **예측온도에 따라 prediction_result가 결정되도록 수정했습니다.**

### 1. 수정된 전체 코드

📥 **CF 실시간 예측 프로그램 수정본 다운로드**

기존 기능은 유지하면서 경보 판정 부분을 변경했습니다.

### 2. 변경된 판정 기준

|oil_temp_predicted|prediction_result|
|---|---|
|80℃ 미만|정상|
|80℃ 이상 ~ 85℃ 미만|주의|
|85℃ 이상 ~ 90℃ 미만|경고|
|90℃ 이상|알람|

기존 프로그램은 CF 도달 확신도로 경보를 결정했지만, 수정본은 **CF가 추정한 미래 오일온도**를 기준으로 판정합니다.

### 3. 유지되는 기능

- 설비: **R00012 한 대만 처리**
- 예측 알고리즘: CF
- 예측 시간: 10·30·60·120분
- 예측 주기: 5초
- prediction_model: CF
- oil_temp_predicted: CF 미래 예측온도
- oil_temp_actual: 실제 측정온도 자동 입력
- 기존 실제온도는 덮어쓰지 않음

기존 80·85·90℃ 도달 확신도도 prediction_features JSON에 계속 저장됩니다.

### 4. 실행 방법

```
python cf_realtime_R00012_temperature_fixed.py --interval 5
```

한 번만 실행하려면:

```
python cf_realtime_R00012_temperature_fixed.py --once
```

### 5. 주의사항

**이미 MySQL에 저장된 예측 결과는 자동으로 수정되지 않습니다.** 기존 데이터도 새로운 기준으로 변경하려면 다음 SQL을 실행하세요.

```
UPDATE airpredict.ai_oiltemp
SET prediction_result =
    CASE
        WHEN oil_temp_predicted >= 90 THEN '알람'
        WHEN oil_temp_predicted >= 85 THEN '경고'
        WHEN oil_temp_predicted >= 80 THEN '주의'
        ELSE '정상'
    END
WHERE device_id = 'R00012'
  AND prediction_model = 'CF'
  AND oil_temp_predicted IS NOT NULL;
```

**참고:** 현재 사용하는 CF 모델은 기존 11호기 데이터로 학습한 모델입니다. R00012 설비에 적용한 예측 정확도는 별도로 검증해야 합니다.

수정된 Python 파일은 구문 검사를 완료했으며, 실제 MySQL 실행 시험은 수행하지 않았습니다.

cf_realtime_R00012_temperature_fixed.py코드
