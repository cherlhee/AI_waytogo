

  
```python
pip install mysql-connector-python
```

p



========== ai_oiltemp ==========

컬럼 구조:
컬럼명 | 데이터타입 | NULL | KEY | DEFAULT | EXTRA
------------------------------------------------------------------------------------------
id | bigint | NO | PRI | None | auto_increment
comcode | varchar(15) | NO | MUL | None |
device_id | varchar(20) | NO |  | None |
input_time | datetime(3) | YES |  | None |
current_datetime | datetime(3) | YES |  | None |
oil_temp_current | decimal(10,2) | YES |  | None |
oil_temp_predicted | decimal(10,2) | YES |  | None |
oil_temp_actual | decimal(10,2) | YES |  | None |
prediction_horizon_min | int | YES |  | None |
prediction_target_time | datetime(3) | YES |  | None |
prediction_model | varchar(30) | YES |  | None |
prediction_features | json | YES |  | None |
prediction_result | varchar(20) | YES |  | None |
created_at | datetime(3) | YES |  | CURRENT_TIMESTAMP(3) | DEFAULT_GENERATED

총 컬럼 수: 14

========== ai_lstm_r ==========
MySQL 오류: 1146 (42S02): Table 'airpredict.ai_lstm_r' doesn't exist

MySQL 연결 종료



이전 메시지 불러오는 중…

ROJECTed\KIS\MEGACOM>python dbmysql.py megaComp!#%

현재 실행 결과는 다음과 같습니다.

`ROJECTed\KIS\MEGACOM>python dbmysql.py megaComp!#%`

megaComp!#%는 첨부하신 메가콤 DB 문서에 기재된 비밀번호입니다.

**이 결과만으로는 MySQL 데이터베이스 접속 성공 여부를 판단할 수 없습니다.**

비밀번호를 출력한 것인지, 비밀번호 입력을 기다리는 것인지 확인해야 합니다.

### 1. 접속 확인 코드

dbmysql.py를 다음과 같이 작성해 보세요.

`import mysql.connector from getpass import getpass try: conn = mysql.connector.connect( host="121.181.35.7", port=3307, user="mega_admin", password=getpass("DB Password: "), connection_timeout=10 ) if conn.is_connected(): print("MySQL 접속 성공!") cursor = conn.cursor() cursor.execute("SHOW DATABASES") print("\n데이터베이스 목록:") for db in cursor.fetchall(): print(db[0]) cursor.close() conn.close() except mysql.connector.Error as err: print("MySQL 접속 실패:", err)`

### 2. 실행

`python dbmysql.py`

비밀번호를 입력하면 다음과 같은 결과가 나와야 합니다.

`DB Password: MySQL 접속 성공! 데이터베이스 목록: information_schema airpredict`

위 출력은 예시이며 실제 목록은 서버 설정에 따라 다릅니다.

### 3. 확인할 사항

현재 dbmysql.py를 실행했을 때 비밀번호가 출력된 다음,

**① 프로그램이 종료되어 명령 프롬프트로 돌아옵니까?**

**② 아니면 비밀번호 입력 후 계속 대기하고 있습니까?**

또는 **dbmysql.py 전체 코드를 올려주시면** 현재 접속 상태와 수정할 부분을 확인해 드리겠습니다.

참고로 DB 비밀번호는 코드에 직접 작성하거나 화면에 출력하지 않는 것이 안전합니다.

M>python dbmysql.py DB Password: MySQL 접속 성공! 데이터베이스 목록: airpredict information_schema performance_schema (megacom) C:\__PROJECTed\KIS\MEGACOM>,,,비번 자동입력하도록

MySQL 접속이 정상적으로 성공했습니다.

비밀번호를 매번 입력하지 않고 **dbmysql.py 실행 시 자동으로 접속**하려면 getpass()를 제거하고 비밀번호를 설정하면 됩니다.

### 1. dbmysql.py 수정

`import mysql.connector try: conn = mysql.connector.connect( host="121.181.35.7", port=3307, user="mega_admin", password="여기에_DB_비밀번호_입력", database="airpredict", connection_timeout=10 ) if conn.is_connected(): print("MySQL 접속 성공!") cursor = conn.cursor() cursor.execute("SHOW TABLES") print("\n테이블 목록:") for table in cursor.fetchall(): print(table[0]) cursor.close() conn.close() except mysql.connector.Error as err: print("MySQL 접속 실패:", err)`

이렇게 하면 비밀번호 입력 없이 자동 접속합니다.

### 2. 실행

`python dbmysql.py`

예상 출력:

`MySQL 접속 성공! 테이블 목록: st_comcode_set ...`

### 3. 권장 방법: .env 파일 사용

비밀번호를 Python 코드에 직접 저장하는 것보다 **.env 파일을 사용하는 것이 안전합니다.**

설치:

`pip install python-dotenv`

.env 파일:

`DB_HOST=121.181.35.7 DB_PORT=3307 DB_USER=mega_admin DB_PASSWORD=실제비밀번호 DB_NAME=airpredict`

dbmysql.py:

`import os import mysql.connector from dotenv import load_dotenv load_dotenv() conn = mysql.connector.connect( host=os.getenv("DB_HOST"), port=int(os.getenv("DB_PORT")), user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"), database=os.getenv("DB_NAME") ) print("MySQL 접속 성공!") cursor = conn.cursor() cursor.execute("SHOW TABLES") for table in cursor.fetchall(): print(table[0]) cursor.close() conn.close()`

**추천:** 메가콤 프로젝트에서는 .env 방식을 사용하세요. Git을 사용한다면 .gitignore에 .env를 추가하여 비밀번호가 GitHub에 업로드되지 않도록 해야 합니다.

ai_data table 내용을 보려면

MySQL 접속이 성공했으므로 airpredict 데이터베이스의 **ai_data 테이블 내용**을 조회하면 됩니다.

### 1. SQL로 조회하기

`USE airpredict; SELECT * FROM ai_data LIMIT 100;`

- SELECT * : 모든 컬럼 조회
- FROM ai_data : ai_data 테이블 선택
- LIMIT 100 : 처음 100개 행 조회

### 2. Python 코드 수정 (dbmysql.py)

기존 코드에서 SHOW TABLES 대신 SELECT * FROM ai_data를 실행하면 됩니다.

`import os import mysql.connector from dotenv import load_dotenv load_dotenv() conn = mysql.connector.connect( host=os.getenv("DB_HOST"), port=int(os.getenv("DB_PORT")), user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"), database="airpredict" ) print("MySQL 접속 성공!") cursor = conn.cursor() # ai_data 테이블 조회 cursor.execute("SELECT * FROM ai_data LIMIT 100") # 컬럼명 가져오기 columns = [desc[0] for desc in cursor.description] print("\n컬럼명:") print(columns) print("\nai_data 테이블 내용:") for row in cursor.fetchall(): print(row) cursor.close() conn.close()`

### 3. pandas로 표 형태로 보기 (추천)

`import os import pandas as pd import mysql.connector from dotenv import load_dotenv load_dotenv() conn = mysql.connector.connect( host=os.getenv("DB_HOST"), port=int(os.getenv("DB_PORT")), user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"), database="airpredict" ) cursor = conn.cursor() cursor.execute("SELECT * FROM ai_data LIMIT 100") columns = [desc[0] for desc in cursor.description] rows = cursor.fetchall() df = pd.DataFrame(rows, columns=columns) print(df.to_string(index=False)) cursor.close() conn.close()`

### 4. 테이블 구조 확인

ai_data 테이블에 어떤 컬럼이 있는지 확인하려면 다음 SQL을 실행합니다.

`DESCRIBE ai_data;`

Python에서는 다음과 같이 실행합니다.

`cursor.execute("DESCRIBE ai_data") for row in cursor.fetchall(): print(row)`

**추천:** 먼저 DESCRIBE ai_data를 실행하여 컬럼명을 확인하세요. 이후 오일온도, 전류, 전력 등의 필요한 데이터만 선택해서 조회할 수 있습니다.

컬럼명: ['id', 'comcode', 'device_id', 'input_time', 'io001', 'io003', 'io004', 'io005', 'io007', 'io008', 'io009', 'io010', 'io019', 'io022', 'io028', 'io029', 'io030', 'io037', 'io045', 'raw_json', 'created_at'] ai_data 테이블 내용: MySQL 접속 실패: Unread result found (megacom) C:\__PROJECTed\KIS\MEGACOM>

MySQL 데이터베이스 접속은 성공했으며, ai_data 테이블의 **컬럼 21개도 정상적으로 조회되었습니다.**

그러나 데이터를 출력하는 과정에서 다음 오류가 발생했습니다.

`MySQL 접속 실패: Unread result found`

## 1. 오류 원인

Unread result found는 **이전 SQL 조회 결과를 모두 읽지 않은 상태에서 다음 SQL 명령을 실행하거나 커서를 닫으려고 할 때** 발생하는 오류입니다.

예를 들어 다음 코드에서 문제가 발생할 수 있습니다.

`cursor = conn.cursor() cursor.execute("SELECT * FROM ai_data LIMIT 100") for row in cursor: print(row) break cursor.close() # Unread result found 발생 가능`

break 때문에 조회 결과가 남아 있기 때문입니다.

## 2. 해결 방법

가장 간단한 방법은 다음과 같이 커서를 생성하는 것입니다.

`cursor = conn.cursor(buffered=True)`

buffered=True는 조회 결과를 클라이언트 측 버퍼에 미리 가져오기 때문에 읽지 않은 결과로 인한 오류를 방지할 수 있습니다.

단, 대용량 테이블 전체를 조회할 때는 메모리 사용량이 증가하므로 LIMIT를 사용하는 것이 좋습니다.

## 3. dbmysql.py 전체 수정 코드

기존 .env 파일을 그대로 사용합니다.

`import os import mysql.connector from dotenv import load_dotenv load_dotenv() conn = None cursor = None try: # MySQL 접속 conn = mysql.connector.connect( host=os.getenv("DB_HOST"), port=int(os.getenv("DB_PORT", "3307")), user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"), database="airpredict", connection_timeout=10 ) print("MySQL 접속 성공!") # buffered=True 사용 cursor = conn.cursor(buffered=True) # ai_data 조회 sql = """ SELECT * FROM ai_data LIMIT 100 """ cursor.execute(sql) # 컬럼명 columns = [desc[0] for desc in cursor.description] print("\n컬럼명:") print(columns) # 데이터 전체 읽기 rows = cursor.fetchall() print("\nai_data 테이블 내용:") for row in rows: print(row) print(f"\n조회된 데이터 개수: {len(rows)}") except mysql.connector.Error as err: print("MySQL 오류:", err) finally: if cursor is not None: cursor.close() if conn is not None and conn.is_connected(): conn.close() print("\nMySQL 연결 종료")`

## 4. 특정 컬럼만 조회하기

현재 ai_data 테이블의 컬럼은 다음과 같습니다.

`id comcode device_id input_time io001 io003 io004 io005 io007 io008 io009 io010 io019 io022 io028 io029 io030 io037 io045 raw_json created_at`

예를 들어 다음과 같이 필요한 컬럼만 조회할 수 있습니다.

`sql = """ SELECT id, device_id, input_time, io001, io003, io004, io005 FROM ai_data ORDER BY input_time DESC LIMIT 20 """`

이렇게 하면 **최근 입력된 데이터 20개**를 조회할 수 있습니다.

---

### 5. 데이터 개수 확인

ai_data 테이블에 몇 개의 데이터가 저장되어 있는지 확인하려면 다음 SQL을 사용합니다.

`cursor.execute("SELECT COUNT(*) FROM ai_data") count = cursor.fetchone()[0] print("전체 데이터 개수:", count)`

### 핵심 정리

|항목|상태|
|---|---|
|MySQL 서버 접속|성공|
|airpredict DB 접속|성공|
|ai_data 컬럼 조회|성공|
|ai_data 데이터 출력|오류 발생|
|오류 원인|읽지 않은 조회 결과가 남아 있음|
|해결 방법|buffered=True 및 fetchall() 사용|

**우선 cursor = conn.cursor(buffered=True)로 변경하여 실행해 보세요.**

이후에는 ai_data의 io001, io003 등의 컬럼이 각각 어떤 센서값(오일온도, 전류, 전력 등)을 의미하는지 확인하면 메가콤 AI 예측 프로그램과 연결할 수 있습니다.

import mysql.connector try: conn = mysql.connector.connect( host="121.181.35.7", port=3307, user="mega_admin", password="megaComp!#%", database="airpredict", connection_timeout=10 ) if conn.is_connected(): print("MySQL 접속 성공!") cursor = conn.cursor() cursor.execute("SHOW TABLES") print("\n테이블 목록:") for table in cursor.fetchall(): print(table[0]) # ai_data 테이블 조회 cursor.execute("SELECT * FROM ai_data LIMIT 100") # 컬럼명 가져오기 columns = [desc[0] for desc in cursor.description] print("\n컬럼명:") print(columns) print("\nai_data 테이블 내용:") cursor.close() conn.close() except mysql.connector.Error as err: print("MySQL 접속 실패:", err)

…

현재 코드에서 Unread result found 오류가 발생하는 이유는 **SELECT * FROM ai_data LIMIT 100 실행 후 조회 결과를 읽지 않고 cursor.close()를 호출하기 때문**입니다.

다음 두 가지를 수정하면 됩니다.

1. cursor = conn.cursor(buffered=True)로 변경
2. cursor.fetchall()을 사용하여 데이터를 가져오고 출력

### 수정된 전체 코드: dbmysql.py

`import mysql.connector conn = None cursor = None try: conn = mysql.connector.connect( host="121.181.35.7", port=3307, user="mega_admin", password="여기에_기존_비밀번호_입력", database="airpredict", connection_timeout=10 ) if conn.is_connected(): print("MySQL 접속 성공!") # 버퍼링 커서 사용 cursor = conn.cursor(buffered=True) # 1. 테이블 목록 조회 cursor.execute("SHOW TABLES") print("\n테이블 목록:") for table in cursor.fetchall(): print(table[0]) # 2. ai_data 테이블 조회 cursor.execute("SELECT * FROM ai_data LIMIT 100") # 컬럼명 가져오기 columns = [desc[0] for desc in cursor.description] print("\n컬럼명:") print(columns) # 3. 데이터 가져오기 rows = cursor.fetchall() print("\nai_data 테이블 내용:") for row in rows: print(row) print(f"\n조회된 데이터 개수: {len(rows)}") except mysql.connector.Error as err: print("MySQL 오류:", err) finally: if cursor is not None: cursor.close() if conn is not None and conn.is_connected(): conn.close() print("\nMySQL 연결 종료")`

### 실행 결과 예시

`MySQL 접속 성공! 테이블 목록: ai_data ... 컬럼명: ['id', 'comcode', 'device_id', 'input_time', 'io001', ...] ai_data 테이블 내용: (1, '...', '...', ...) (2, '...', '...', ...) (3, '...', '...', ...) 조회된 데이터 개수: 100 MySQL 연결 종료`

### 추가: 데이터를 보기 좋게 출력하려면

현재 print(row)는 한 행의 모든 값을 한 줄에 출력합니다.

컬럼명과 값을 함께 출력하려면 다음과 같이 변경할 수 있습니다.

for row in rows:

for col, value in zip(columns, row):

print(f"{col}: {value}")

  

print("-" * 50)

그러면 다음과 같은 형태로 출력됩니다.

`id: 1 comcode: ... device_id: ... input_time: ... io001: ... io003: ... ... --------------------------------------------------`

**참고:** 현재 코드에 데이터베이스 비밀번호가 직접 포함되어 있습니다. 실제 프로젝트에서는 .env 파일로 분리하고 Git에 업로드되지 않도록 관리하는 것을 권장합니다.