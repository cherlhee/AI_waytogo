
**MAE:** Average absolute prediction error.
**RMSE:** Gives greater weight to large prediction errors.






==🔴how much values of mar, rmse is meaningful==

MAE와 RMSE는 **값이 작을수록 예측 성능이 좋습니다.** 그러나 좋은 값인지 판단하는 절대적인 기준은 없습니다. 예측 대상의 온도 범위와 시스템의 목적에 따라 달라집니다.

현재 개발 중인 **컴프레서 오일온도 LSTM 예측 시스템**을 기준으로 설명하겠습니다.

## 1. MAE와 RMSE 평가 기준

오일온도가 대략 40~100°C 범위이고, 80°C(주의), 85°C(경고), 90°C(알람)를 판단하는 시스템이라면 다음과 같은 기준을 잠정적으로 사용할 수 있습니다.

|MAE (°C)|평가|의미|
|---|---|---|
|0~1|매우 우수|평균 절대오차 1°C 이하|
|1~2|우수|비교적 정확한 온도 예측|
|2~3|양호|일반적인 온도 추세 예측에 활용 가능|
|3~5|보통|경고 판단 시 주의 필요|
|5~10|미흡|경고 판단의 신뢰성이 낮을 수 있음|
|10 이상|매우 미흡|모델 개선 필요|

이 표는 산업 표준이 아니라 **현재 프로젝트에 적용할 수 있는 임시 평가 기준**입니다.

RMSE도 함께 평가해야 합니다.

|RMSE (°C)|평가|
|---|---|
|0~2|매우 우수|
|2~3|우수|
|3~5|양호|
|5~7|보통|
|7 이상|개선 검토|

## 2. 현재 LSTM 모델 성능 평가

이전에 측정한 오일온도 예측 결과는 다음과 같습니다.

|예측시간|MAE (°C)|RMSE (°C)|
|---|--:|--:|
|10분|3.127|4.286|
|30분|3.361|4.489|
|60분|3.524|4.641|
|120분|3.631|4.741|

이 결과를 해석하면 다음과 같습니다.

**① MAE가 약 3~3.6°C**

평균적으로 예측온도와 실제온도 사이에 약 3~3.6°C의 절대오차가 발생한다는 의미입니다.

**② RMSE가 약 4.3~4.7°C**

일부 예측에서 평균보다 큰 오차가 발생하고 있음을 보여줍니다.

**③ 예측시간이 증가해도 오차 증가가 크지 않음**

10분 MAE = 3.127°C

120분 MAE = 3.631°C

차이는 약 0.5°C입니다.

다만 이것만으로 장기 예측 성능이 우수하다고 판단할 수는 없습니다. 온도가 거의 변하지 않는 구간이 많다면 단순한 현재온도 유지 모델도 비슷한 결과를 낼 수 있기 때문입니다.

## 3. 고온 경고 시스템에서는 MAE만으로 부족합니다

예를 들어 실제온도가 90°C인 경우를 생각해 보겠습니다.

|실제온도|예측온도|절대오차|경고 결과|
|---|---|---|---|
|90°C|89°C|1°C|알람 미발생|
|90°C|87°C|3°C|알람 미발생|
|90°C|91°C|1°C|알람 발생|

첫 번째 경우는 MAE 관점에서 오차가 작지만, 90°C 알람을 놓칩니다.

따라서 현재 시스템에서는 다음 두 가지를 구분해야 합니다.

- **온도 예측 성능:** MAE, RMSE
- **고온 이벤트 예측 성능:** Precision, Recall, F1-score

특히 90°C 이상을 놓치지 않는 것이 중요하다면 Recall을 중점적으로 평가해야 합니다.

또한 30분 이내 90°C 도달 여부를 평가하려면 단순히 30분 후의 예측온도만 사용하는 것은 부족합니다. 예측기간 중 한 번이라도 90°C에 도달했는지를 평가해야 합니다.

## 4. 추천 목표

현재 프로젝트에서 초기 개선 목표를 다음과 같이 설정할 수 있습니다.

|예측시간|목표 MAE|목표 RMSE|
|---|--:|--:|
|10분|≤ 2.0°C|≤ 3.0°C|
|30분|≤ 2.5°C|≤ 3.5°C|
|60분|≤ 3.0°C|≤ 4.0°C|
|120분|≤ 3.5°C|≤ 4.5°C|

이 값은 검증된 산업 기준이 아니라 모델 개선을 위한 제안 목표입니다.

실제로는 현재온도를 그대로 미래온도로 예측하는 단순 기준 모델과 비교하여 MAE와 RMSE가 얼마나 개선되는지 확인하는 것이 중요합니다.

---

### 5. 결론

현재 LSTM의 MAE 약 3.1~3.6°C는 온도 추세를 예측하는 데 활용할 가능성이 있지만, **80°C, 85°C, 90°C의 고온 경고를 정확하게 판단하기에는 오차가 클 수 있습니다.**

특히 중요한 것은 다음 질문입니다.

**전체 데이터의 MAE가 3°C이더라도, 실제온도가 85~90°C에 도달하는 고온 구간에서 MAE가 1°C라면 어떨까요?**

이 경우 전체 MAE가 3°C여도 고온 경고에 유용한 모델일 수 있습니다.

따라서 ai_lstm_r에서 전체 MAE뿐 아니라 **실제온도가 80°C 이상, 85°C 이상, 90°C 이상인 구간의 MAE와 RMSE를 별도로 계산**하는 것을 권장합니다.



==🔴can i calculate mae==

Yes. You can calculate **MAE (Mean Absolute Error)** directly from your MySQL ai_lstm_r table.

MAE measures the average absolute difference between the LSTM-predicted oil temperature and the actual oil temperature.

## 1. MAE formula

MAE=1N∑i=1N∣Actuali−Predictedi∣MAE=N1​i=1∑N​∣Actuali​−Predictedi​∣​

For example:

|Actual (°C)|LSTM Prediction (°C)|Error (°C)|Absolute Error|
|---|---|---|---|
|80|82|-2|2|
|85|81|+4|4|
|90|93|-3|3|
|75|76|-1|1|

MAE=2+4+3+14=2.5∘CMAE=42+4+3+1​=2.5∘C​

## 2. Calculate MAE using MySQL

Your ai_lstm_r table contains:

- lstm_prediction: Predicted oil temperature
- oil_temp_actual: Actual oil temperature
- oil_temp_error: Actual − Predicted
- prediction_horizon_min: 10, 30, 60, 120 minutes

**SQL: Calculate overall MAE**

```
SELECT
    COUNT(*) AS sample_count,
    ROUND(
        AVG(ABS(oil_temp_actual - lstm_prediction)),
        3
    ) AS MAE
FROM ai_lstm_r
WHERE oil_temp_actual IS NOT NULL
  AND lstm_prediction IS NOT NULL;
```

## 3. Calculate MAE for each prediction horizon

For your compressor oil-temperature prediction system, this is particularly useful.

```
SELECT
    prediction_horizon_min,
    COUNT(*) AS sample_count,

    ROUND(
        AVG(ABS(oil_temp_actual - lstm_prediction)),
        3
    ) AS MAE

FROM ai_lstm_r

WHERE oil_temp_actual IS NOT NULL
  AND lstm_prediction IS NOT NULL

GROUP BY prediction_horizon_min
ORDER BY prediction_horizon_min;
```

Example output (illustrative):

|Prediction Horizon|Samples|MAE (°C)|
|---|--:|--:|
|10 min|1500|1.25|
|30 min|1500|2.18|
|60 min|1500|3.42|
|120 min|1500|4.85|

## 4. Calculate MAE and RMSE together

I recommend calculating both MAE and RMSE to evaluate your LSTM model.

```
SELECT
    device_id,
    prediction_horizon_min,

    COUNT(*) AS sample_count,

    ROUND(
        AVG(ABS(oil_temp_actual - lstm_prediction)),
        3
    ) AS MAE,

    ROUND(
        SQRT(
            AVG(
                POW(oil_temp_actual - lstm_prediction, 2)
            )
        ),
        3
    ) AS RMSE

FROM ai_lstm_r

WHERE oil_temp_actual IS NOT NULL
  AND lstm_prediction IS NOT NULL

GROUP BY
    device_id,
    prediction_horizon_min

ORDER BY
    device_id,
    prediction_horizon_min;
```

### Difference between MAE and RMSE

**MAE:** Average absolute prediction error.

**RMSE:** Gives greater weight to large prediction errors.

For example:

- MAE = 2.5°C means the average absolute error is 2.5°C.
- RMSE = 4.0°C suggests that some larger errors contribute more strongly to the result.

## 5. Important: Actual temperature must be updated

Your system predicts oil temperature at four horizons:

- 10 minutes
- 30 minutes
- 60 minutes
- 120 minutes

Each prediction must be compared against the actual oil temperature at its corresponding prediction_target_time.

For example, a prediction made at 10:00 for 30 minutes ahead must be compared with the actual temperature at approximately 10:30, not the temperature at 10:00.

**Recommendation:** Calculate MAE separately for each prediction horizon and device. Exclude rows where actual temperature is still NULL.

You can also calculate **MAE automatically every 5 seconds** as new actual temperatures become available, although recalculating the entire table that frequently may be inefficient for a large dataset.