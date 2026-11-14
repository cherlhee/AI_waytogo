



==🔴when inserting columns,,can i insert beween selected columns==
==🔴Yes. In MySQL, you can insert a new column **between existing columns** using ALTER TABLE with the AFTER keyword.==

### 1. Insert a column after a selected column

For example, insert oil_temp_current immediately after prediction_target_time in ai_lstm_r.

```
ALTER TABLE ai_lstm_r
ADD COLUMN oil_temp_current DECIMAL(10,2) NULL
AFTER prediction_target_time;
```

### 2. Insert multiple columns in a specific order

Suppose your current table contains:

`prediction_horizon_min prediction_target_time lstm_prediction lstm_anomaly_score feature_importance`

You want:

`prediction_horizon_min prediction_target_time oil_temp_current <-- NEW lstm_prediction oil_temp_actual <-- NEW oil_temp_error <-- NEW lstm_anomaly_score feature_importance`

Use:

```
ALTER TABLE ai_lstm_r
ADD COLUMN oil_temp_current DECIMAL(10,2) NULL
    AFTER prediction_target_time,

ADD COLUMN oil_temp_actual DECIMAL(10,2) NULL
    AFTER lstm_prediction,

ADD COLUMN oil_temp_error DECIMAL(10,2) NULL
    AFTER oil_temp_actual;
```

### 3. Move an existing column

If the column already exists, use MODIFY COLUMN instead of ADD COLUMN.

```
ALTER TABLE ai_lstm_r
MODIFY COLUMN oil_temp_actual DECIMAL(10,2) NULL
AFTER lstm_prediction;
```

**Important:** When using MODIFY COLUMN, specify the column's full definition to avoid unintentionally changing its properties.

### 4. Insert a column at the beginning

Use FIRST:

```
ALTER TABLE ai_lstm_r
ADD COLUMN oil_temp_current DECIMAL(10,2) NULL
FIRST;
```

### 5. Check column order

```
DESCRIBE ai_lstm_r;
```

**Note:** AFTER and FIRST control the column order in the table definition. They do not change the data values.

For your LSTM prediction table, I recommend placing oil_temp_current, lstm_prediction, oil_temp_actual, and oil_temp_error next to each other to make prediction accuracy easier to inspect.



==🔴how can i insert new columns into ai-lstmr table,,example,,,현재오일온도,,,리매시전실제오일온도,,,에러값==

MySQL의 ai_lstm_r 테이블에 다음 3개 컬럼을 추가하려면 **ALTER TABLE** 명령을 사용하면 됩니다.

### 1. 추가할 컬럼

|컬럼명|데이터 타입|설명|
|---|---|---|
|oil_temp_current|DECIMAL(10,2)|예측 당시 현재 오일온도|
|oil_temp_actual|DECIMAL(10,2)|예측 목표 시각의 실제 오일온도|
|oil_temp_error|DECIMAL(10,2)|예측온도와 실제온도의 오차|

오차는 다음과 같이 정의하겠습니다.

Error=Actual−PredictionError=Actual−Prediction

예를 들어:

- 현재 오일온도: 75℃
- 30분 후 LSTM 예측온도: 85℃
- 30분 후 실제 오일온도: 82℃
- 예측오차: 82 - 85 = **-3℃**

### 2. MySQL 컬럼 추가

```
ALTER TABLE ai_lstm_r
ADD COLUMN oil_temp_current DECIMAL(10,2) NULL
    COMMENT '예측 당시 현재 오일온도',

ADD COLUMN oil_temp_actual DECIMAL(10,2) NULL
    COMMENT '예측 목표 시각의 실제 오일온도',

ADD COLUMN oil_temp_error DECIMAL(10,2) NULL
    COMMENT '실제온도 - LSTM 예측온도';
```

기존 데이터는 그대로 유지되고 새로운 컬럼에는 NULL이 저장됩니다.

### 3. 실제 오일온도와 오차 업데이트

ai_lstm_r에는 이미 다음 컬럼이 있습니다.

- oiltemp_id: ai_oiltemp.id 참조
- lstm_prediction: LSTM 예측온도

따라서 ai_oiltemp의 데이터를 이용하여 현재온도와 실제온도를 가져올 수 있습니다.

```
UPDATE ai_lstm_r AS l
JOIN ai_oiltemp AS o
    ON l.oiltemp_id = o.id
SET
    l.oil_temp_current = o.oil_temp_current,
    l.oil_temp_actual = o.oil_temp_actual,
    l.oil_temp_error =
        o.oil_temp_actual - l.lstm_prediction;
```

**주의:** oil_temp_actual은 예측 목표 시각이 지난 후에야 알 수 있으므로, 그전에는 NULL로 유지해야 합니다.

### 4. 결과 확인

```
SELECT
    id,
    device_id,
    prediction_horizon_min,
    oil_temp_current,
    lstm_prediction,
    oil_temp_actual,
    oil_temp_error
FROM ai_lstm_r
ORDER BY id DESC
LIMIT 20;
```

예상 결과:

|예측기간|현재온도|LSTM 예측|실제온도|오차|
|---|--:|--:|--:|--:|
|10분|75.0|78.5|79.0|+0.5|
|30분|75.0|85.0|82.0|-3.0|
|60분|75.0|87.5|NULL|NULL|
|120분|75.0|91.0|NULL|NULL|

### 5. 실시간 LSTM 프로그램 적용

현재 운영하는 lstm_predict.py에도 다음 기능을 추가하는 것이 좋습니다.

1. LSTM 예측 시 oil_temp_current 저장
2. 10/30/60/120분 예측온도를 lstm_prediction에 저장
3. 예측 목표 시각이 지나면 ai_oiltemp.oil_temp_actual을 가져와 oil_temp_actual 업데이트
4. oil_temp_error = oil_temp_actual - lstm_prediction 자동 계산

**중요:** ai_lstm_r의 예측오차는 CF 예측값이 아니라 반드시 **LSTM 예측값(lstm_prediction)**을 기준으로 계산해야 합니다.

이렇게 구성하면 10분, 30분, 60분, 120분별 LSTM 예측 정확도를 MAE, RMSE 등으로 평가할 수 있습니다.

