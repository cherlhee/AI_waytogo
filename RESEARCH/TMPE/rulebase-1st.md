



  

붙여넣은 텍스트(1)(4).txt문서

BTN_run_rulebaseRealtime 버튼이 눌러지면, 실행하는 파일은?

첨부된 Python 코드를 확인하면, **BTN_run_rulebaseRealtime 버튼을 누를 때 실행되는 함수는 startTimer_rulebaseRealtime()이며, 이후 10초마다 run_weldissue_2lotr_rulebaseRealtime() 함수가 실행됩니다.**

### 1. 버튼 클릭 시 실행되는 함수 (97행)

self.BTN_run_rulebaseRealtime.clicked.connect(

self.startTimer_rulebaseRealtime

)

### 2. 타이머 시작 (65~69행)

def startTimer_rulebaseRealtime(self):

print('--- rule-base; realtime; timer start;;; ---')

self.rule_timer.start(10000)

10000ms = 10초이므로 10초 간격으로 실행됩니다.

### 3. 실제 룰베이스 실행 함수 (60행)

# self.rule_timer.timeout.connect(self.run_rulebaseRealtime)

# self.rule_timer.timeout.connect(self.run_weldissue_rulebaseRealtime)

self.rule_timer.timeout.connect(

self.run_weldissue_2lotr_rulebaseRealtime

)

현재 활성화된 함수는 **run_weldissue_2lotr_rulebaseRealtime() (685행)** 입니다.

### 4. 실행 순서

**BTN_run_rulebaseRealtime 클릭**

startTimer_rulebaseRealtime()

QTimer — 10초 간격

**run_weldissue_2lotr_rulebaseRealtime()**

실제 DB 조회 및 룰베이스 판정

이 함수는 mt_pop_weldissue_lot에서 최근 LOT 번호를 찾고, mt_pop_weldtmp2에서 용접 데이터를 조회한 다음, 저항값 voltage / e_current를 기준으로 OK/NG를 판정하여 **mt_pop_weldtmp2_lot_r 테이블**에 결과를 저장합니다.

**결론:** 별도의 Python 파일을 실행하는 것이 아니라, 현재 Python 프로그램 내부에 정의된 685행의 함수를 타이머로 반복 실행하는 구조입니다.

AND mt_pop_weldtmp2.jig_no <> '0' AND mt_pop_weldtmp2.terms <> '0',,,이 조건을 만족할 경우 select * ,,,sql 재작성하라

기존 SQL에 jig_no <> '0' 및 terms <> '0' 조건을 추가하면 됩니다.

### 수정된 SQL (Python)

sql = """

SELECT *

FROM mt_pop_weldtmp2

WHERE mt_pop_weldtmp2.lot_no = (

SELECT TOP 1 lot_no

FROM mt_pop_weldissue_lot WITH(NOLOCK)

WHERE machine = 'TM-PE NO.1'

ORDER BY insert_dt DESC

)

AND mt_pop_weldtmp2.jig_no <> '0'

AND mt_pop_weldtmp2.terms <> '0'

"""

  

df_check = pd.read_sql(sql, self.conn)

### SQL 실행 조건

|조건|설명|
|---|---|
|lot_no|mt_pop_weldissue_lot의 가장 최근 LOT 번호|
|jig_no <> '0'|JIG 번호가 0이 아닌 데이터|
|terms <> '0'|terms 값이 0이 아닌 데이터|
|SELECT *|조건을 만족하는 모든 행과 컬럼 조회|

**참고:** jig_no와 terms가 숫자형 컬럼이라면 '0' 대신 0을 사용하는 것이 적절합니다.

또한 NULL 값은 <> '0' 조건을 만족하지 않으므로 조회 결과에서 제외됩니다.

이 SQL을 기존 **run_weldissue_2lotr_rulebaseRealtime() 함수의 706~714행**에 적용하면 됩니다.

**참고:** jig_no와 terms가 숫자형 컬럼이라면 '0' 대신 0을 사용하는 것이 적절합니다.

또한 NULL 값은 <> '0' 조건을 만족하지 않으므로 조회 결과에서 제외됩니다.,,,숫자형칼럼 혹은 문자형이든 상관없이 둘다 포함해서 ,,sql 작성하라

jig_no와 terms가 **숫자형(INT, FLOAT 등) 또는 문자형(VARCHAR, NVARCHAR 등)** 어느 쪽이든 처리할 수 있도록 SQL을 작성하면 다음과 같습니다.

### 1. 숫자형·문자형 모두 처리 (NULL 제외)

sql = """

SELECT *

FROM mt_pop_weldtmp2

WHERE mt_pop_weldtmp2.lot_no = (

SELECT TOP 1 lot_no

FROM mt_pop_weldissue_lot WITH(NOLOCK)

WHERE machine = 'TM-PE NO.1'

ORDER BY insert_dt DESC

)

AND TRY_CONVERT(FLOAT, mt_pop_weldtmp2.jig_no) <> 0

AND TRY_CONVERT(FLOAT, mt_pop_weldtmp2.terms) <> 0

"""

  

df_check = pd.read_sql(sql, self.conn)

**처리 결과**

|컬럼 값|조회 여부|
|---|---|
|숫자 0|제외|
|문자 '0'|제외|
|문자 '0.0'|제외|
|숫자 1|포함|
|문자 '1'|포함|
|숫자 2.5|포함|
|문자 'ABC'|제외|
|NULL|제외|

### 2. NULL도 포함하려면

```
AND (
    TRY_CONVERT(FLOAT, mt_pop_weldtmp2.jig_no) <> 0
    OR mt_pop_weldtmp2.jig_no IS NULL
)
AND (
    TRY_CONVERT(FLOAT, mt_pop_weldtmp2.terms) <> 0
    OR mt_pop_weldtmp2.terms IS NULL
)
```

이 경우 NULL도 조회 대상에 포함됩니다. 단, 숫자로 변환할 수 없는 문자열은 제외됩니다.

**권장:** 현재 용접 데이터의 jig_no, terms가 숫자 또는 숫자 형태의 문자열이라면 **1번 SQL**을 사용하면 됩니다.



| 확률                 | 가설 \(i=1\) | 가설 \(i=2\) | 가설 \(i=3\) |
| ------------------ | ---------- | ---------- | ---------- |
| \(P(H_i)\)         | 0.50       | 0.30       | 0.20       |
| \(P(E_1\mid H_i)\) | 0.40       | 0.70       | 0.60       |
| \(P(E_2\mid H_i)\) | 0.80       | 0.20       | 0.50       |
| \(P(E_3\mid H_i)\) | 0.30       | 0.60       | 0.90       |
| 확률                 | 가설 \(i=1\) | 가설 \(i=2\) | 가설 \(i=3\) |
| \(P(H_i)\)         | 0.50       | 0.30       | 0.20       |
| \(P(E_1\mid H_i)\) | 0.40       | 0.70       | 0.60       |
| \(P(E_2\mid H_i)\) | 0.80       | 0.20       | 0.50       |
| \(P(E_3\mid H_i)\) | 0.30       | 0.60       | 0.90       |
