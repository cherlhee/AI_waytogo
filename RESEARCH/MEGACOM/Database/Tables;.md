


========== ai_data ==========

컬럼 구조:
컬럼명 | 데이터타입 | NULL | KEY | DEFAULT | EXTRA
------------------------------------------------------------------------------------------
id | bigint | NO | PRI | None | auto_increment
comcode | varchar(15) | NO | MUL | None |
device_id | varchar(20) | NO | MUL | None |
input_time | datetime(3) | NO | MUL | None |
io001 | decimal(12,4) | YES |  | None |
io003 | decimal(12,4) | YES |  | None |
io004 | decimal(12,4) | YES |  | None |
io005 | decimal(12,4) | YES |  | None |
io007 | decimal(12,4) | YES |  | None |
io008 | decimal(12,4) | YES |  | None |
io009 | decimal(12,4) | YES |  | None |
io010 | decimal(14,4) | YES |  | None |
io019 | varchar(255) | YES |  | None |
io022 | varchar(100) | YES |  | None |
io028 | decimal(12,4) | YES |  | None |
io029 | decimal(12,4) | YES |  | None |
io030 | decimal(14,4) | YES |  | None |
io037 | decimal(12,4) | YES |  | None |
io045 | decimal(12,4) | YES |  | None |
raw_json | json | YES |  | None |
created_at | datetime(3) | NO |  | CURRENT_TIMESTAMP(3) | DEFAULT_GENERATED

총 컬럼 수: 21




========== ai_alarm ==========

컬럼 구조:
컬럼명 | 데이터타입 | NULL | KEY | DEFAULT | EXTRA
------------------------------------------------------------------------------------------
alarm_no | varchar(40) | NO | PRI | None |
alarm_dt | datetime(3) | NO |  | None |
comcode | varchar(15) | NO |  | None |
device_id | varchar(20) | NO | MUL | None |
std_item | varchar(20) | YES |  | None |
grade | decimal(10,2) | YES |  | None |
risk_score | decimal(10,2) | YES |  | None |
alarm_level | varchar(20) | YES |  | None |
alarm_cont | varchar(1000) | YES |  | None |
status | varchar(20) | NO | MUL | OPEN |
ack_by | varchar(50) | YES |  | None |
ack_at | datetime(3) | YES |  | None |
closed_at | datetime(3) | YES |  | None |
remark | varchar(255) | YES |  | None |

총 컬럼 수: 14



========== ai_analysis ==========

컬럼 구조:
컬럼명 | 데이터타입 | NULL | KEY | DEFAULT | EXTRA
------------------------------------------------------------------------------------------
comcode | varchar(15) | NO | PRI | None |
device_id | varchar(20) | NO | PRI | None |
input_time | datetime(3) | NO | PRI | None |
risk_score | decimal(10,2) | NO |  | 0.00 |
risk_level | varchar(20) | NO | MUL | NORMAL |
rule_score_max | decimal(10,2) | YES |  | None |
score_external_temp | decimal(10,2) | YES |  | None |
score_voltage | decimal(10,2) | YES |  | None |
score_current | decimal(10,2) | YES |  | None |
score_pressure | decimal(10,2) | YES |  | None |
score_oil_temp | decimal(10,2) | YES |  | None |
score_consumable | decimal(10,2) | YES |  | None |
score_line_voltage | decimal(10,2) | YES |  | None |
score_current_imbalance | decimal(10,2) | YES |  | None |
score_timeseries | decimal(10,2) | YES |  | None |
ai_anomaly_score | decimal(10,2) | YES |  | None |
ai_future_risk_score | decimal(10,2) | YES |  | None |
failure_probability | decimal(10,2) | YES |  | None |
model_version | varchar(80) | YES |  | None |
rule_json | json | YES |  | None |
explanation_json | json | YES |  | None |
created_at | datetime(3) | YES |  | CURRENT_TIMESTAMP(3) | DEFAULT_GENERATED