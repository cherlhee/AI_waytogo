

==🔴comcode 칼럼도 있ㄷ==
==🔴그렇다면 comcode와 std_item을 조건으로 사용하여 st_comcode_set 테이블의 set_high 값을 가져오면 됩니다.==



### 1. SENSORS 설정

"전압평균": {

"columns": ["io004", "io005"],

"code": "004",

"standard_table": "st_comcode_set",

"standard_item": "io004",

"standard_column": "set_high"

},

### 2. 기준값 조회 함수

def get_standard(cursor, sensor):

  

table = sensor.get("standard_table")

item = sensor.get("standard_item")

column = sensor.get("standard_column")

  

# 고정 기준값을 사용하는 센서

if not table:

return to_float(sensor.get("standard"))

  

sql = f"""

SELECT `{column}`

FROM `{table}`

WHERE comcode = %s

AND std_item = %s

LIMIT 1

"""

  

cursor.execute(sql, (COM_CODE, item))

  

row = cursor.fetchone()

  

if row is None:

return None

  

return to_float(row[0])

테이블명과 컬럼명은 SENSORS에 미리 정의한 값만 사용해야 합니다.

### 3. analyze() 수정

기존:

def analyze(current, previous):

변경:

def analyze(cursor, current, previous):

기존:

standard = sensor["standard"]

변경:

standard = get_standard(cursor, sensor)

run() 함수에서도 다음과 같이 변경합니다.

results = analyze(cursor, current, previous)

### 4. 실제 실행되는 SQL

```
SELECT set_high
FROM st_comcode_set
WHERE comcode = 'C00088'
  AND std_item = 'io004'
LIMIT 1;
```

이제 전압평균 분석은 다음과 같이 동작합니다.

|구분|내용|
|---|---|
|현재값|ai_data의 (io004 + io005) / 2|
|기준값|st_comcode_set의 set_high|
|업체 조건|comcode = 'C00088'|
|센서 조건|std_item = 'io004'|
|점수 계산|score_voltage(value, standard)|

**이 구조를 적용하면 st_comcode_set의 set_high 값이 변경될 때마다 다음 분석 실행에서 새로운 기준값이 자동으로 반영됩니다.**

다른 센서도 동일한 방식으로 설정할 수 있습니다. 기존 standard 고정값을 사용하는 센서들은 그대로 유지할 수 있습니다.

참고로 현재 score_voltage()는 기준값과의 편차를 계산합니다. set_high가 상한값이라면, 상한 초과 여부를 판정하도록 점수 계산식을 변경할지도 검토해야 합니다.

==🔴rule(2).py코드==
==🔴sensors,,센서항목에 standard 항목에 일정한 값들이 기록되어있다...이것을 ai-data에 있는 특정칼럼값들을 지정해서 불러오려면,,==
==🔴첨부하신 rule(2).py를 확인했습니다.==

현재 SENSORS의 standard에는 고정된 기준값이 들어 있습니다. 이를 **ai_data 테이블의 특정 컬럼에서 자동으로 조회하도록 변경**할 수 있습니다.

예를 들어 현재 코드는 다음과 같습니다.

### 1. 현재 코드

SENSORS = {

"유량계온도": {

"columns": ["io045"],

"code": "045",

"standard": 30

},

  

"전압평균": {

"columns": ["io004", "io005"],

"code": "004",

"standard": 380

},

  

"전류평균": {

"columns": ["io007", "io008", "io009"],

"code": "007",

"standard": 15

}

}

여기서 standard는 고정값입니다.

### 2. 변경 방법: standard에 컬럼명 지정

다음과 같이 standard_column 항목을 추가하는 방법을 권장합니다.

SENSORS = {

"유량계온도": {

"columns": ["io045"],

"code": "045",

"standard_column": "io045"

},

  

"전압평균": {

"columns": ["io004", "io005"],

"code": "004",

"standard_column": "io050"

},

  

"전류평균": {

"columns": ["io007", "io008", "io009"],

"code": "007",

"standard_column": "io051"

}

}

위의 io050, io051은 설명을 위한 예시입니다. 실제 ai_data에 존재하는 컬럼으로 지정해야 합니다.

이렇게 하면 다음과 같이 동작합니다.

|센서|현재값|기준값|
|---|---|---|
|유량계온도|io045|io045|
|전압평균|io004, io005 평균|io050|
|전류평균|io007, io008, io009 평균|io051|

단, 유량계온도처럼 현재값과 기준값에 동일한 컬럼을 지정하면 두 값이 같아지므로, 기준값의 의미에 맞는 컬럼을 선택해야 합니다.

### 3. get_sensor_data() 수정

현재 프로그램의 get_sensor_data()는 columns에 지정된 컬럼만 조회합니다. 

따라서 standard_column에 지정된 컬럼도 함께 조회하도록 수정해야 합니다.

def get_sensor_data(cursor):

  

columns = list(dict.fromkeys(

col

for sensor in SENSORS.values()

for col in (

sensor["columns"]

+ ([sensor["standard_column"]]

if sensor.get("standard_column") else [])

)

))

  

column_sql = ", ".join(

f"`{column}`" for column in columns

)

  

sql = f"""

SELECT input_time, {column_sql}

FROM `{SOURCE_TABLE}`

WHERE comcode = %s

AND deviceId = %s

ORDER BY input_time DESC

LIMIT 2

"""

  

cursor.execute(sql, (COM_CODE, DEVICE_ID))

  

rows = cursor.fetchall()

  

if not rows:

return None, None

  

keys = ["input_time"] + columns

  

current = dict(zip(keys, rows[0]))

  

### 4. analyze() 수정

현재 코드에는 다음 부분이 있습니다.

standard = sensor["standard"]

이 부분을 다음과 같이 변경합니다.

standard_column = sensor.get("standard_column")

  

if standard_column:

standard = to_float(current.get(standard_column))

else:

standard = sensor.get("standard")

이렇게 하면 기준값을 지정하는 방법이 두 가지가 됩니다.

**① 고정값 사용**

"standard": 380

**② ai_data 컬럼값 사용**

"standard_column": "io050"

기준값이 NULL이거나 숫자로 변환할 수 없으면 standard는 None이 됩니다. 현재 일부 점수 함수는 None을 처리하지만, 모든 함수가 동일하게 처리하는 것은 아니므로 결측 처리도 함께 검토해야 합니다.

---

### 5. 중요한 사항: 기준값을 어느 시점에서 가져올 것인가?

현재 프로그램은 ai_data의 최신 데이터를 조회합니다.

기준값을 DB에서 가져오는 방법에는 다음과 같은 차이가 있습니다.

|방법|설명|
|---|---|
|① 최신값|현재 분석하는 행의 특정 컬럼값|
|② 과거값|이전 시점의 특정 컬럼값|
|③ 평균값|최근 10분 또는 30분의 평균|
|④ 별도 기준값|별도 테이블에 저장된 설비별 기준값|

**질문:** 원하시는 것은 standard에 ai_data의 **최신 행에 있는 특정 컬럼값**을 지정하는 것인가요?

그렇다면 위 방법으로 구현할 수 있으며, 기존 8개 센서 항목과 5초 주기 분석 구조를 유지하면서 변경할 수 있습니다.