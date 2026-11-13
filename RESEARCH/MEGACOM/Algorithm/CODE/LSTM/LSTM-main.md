


제공하신 `lstm_predict.py` 코드는 **`ai_oiltemp`의 최신 ID를 확인하고, 새로운 ID가 발견되면 LSTM 예측을 수행하여 `ai_lstm_r`에 저장하는 구조**입니다.

현재 코드의 동작은 다음과 같습니다.

1. **5초마다** `ai_oiltemp` 테이블의 최신 ID 조회
2. 이전에 처리한 ID와 다르면 새로운 데이터로 판단
3. 해당 시각을 기준으로 `ai_data`에서 과거 38분 데이터 조회
4. 1분 단위 특징값 생성 후 최근 30분 데이터 추출
5. LSTM 모델로 **10분, 30분, 60분, 120분 후 온도 예측**
6. 예측 결과 4개를 `ai_lstm_r`에 저장
7. 설정된 주기에 따라 Integrated Gradients로 영향인자 기여도 계산


`lstm_predict_sorted_importance(1).py` 파일을 확인했습니다.

현재 코드에는 다음 기능이 구현되어 있습니다.

- **5초마다** `ai_oiltemp` 최신 ID 확인
- 신규 ID 발견 시 `ai_data`의 과거 38분 데이터 조회
- LSTM으로 10·30·60·120분 후 오일온도 예측
- `feature_importance`를 **중요도 내림차순 JSON 배열**로 저장
- `ai_lstm_r`의 `device_id` 또는 `deviceId` 컬럼 자동 확인
- Integrated Gradients를 이용한 영향인자 기여도 계산 lstm_predict_sorted_importance(…

다만 현재는 최신 ID 하나만 처리하므로 여러 ID가 연속으로 생성되면 일부 데이터가 누락될 수 있습니다.


```
python lstm_predict.py --once
```

정상적으로 동작하면 5초마다 최신 ID를 확인하도록 실행할 수 있습니다.

```
python lstm_predict.py
```


python megacom_lstm.py predict --csv realtime_5sec.csv


pip install numpy pandas scikit-learn tensorflow joblib



|                        |                                          |                                      |
| ---------------------- | ---------------------------------------- | ------------------------------------ |
| 컬럼명                    | 데이터 타입                                   | 설명                                   |
| id                     | BIGINT AUTO_INCREMENT<br><br>PRIMARY KEY | 고유번호                                 |
| oiltemp_id             | BIGINT UNSIGNED                          | FK<br><br>ai_oiltemp.id 참조           |
| comcode                | VARCHAR(15)                              | 업체 코드                                |
| device_id              | VARCHAR(20)                              | 설비 번호                                |
| input_time             | DATETIME(3)                              | 분석 기준 데이터 시각                         |
| current_datetime       | DATETIME(3)                              | 분석 실행 시각                             |
| prediction_horizon_min | INT                                      | 예측 기간(분)<br><br>(10, 30, 60, 120분 등) |
| prediction_target_time | DATETIME(3)                              | 예측 대상 시각                             |
| lstm_prediction        | DECIMAL(10,2)                            | LSTM 예측 온도값                          |
| lstm_anomaly_score     | DECIMAL(10,2)                            | LSTM 기반 이상 점수                        |
| feature_importance     | JSON                                     | 영향인자 중요도                             |
| feature_contributions  | JSON                                     | 개별 영향인자의 예측 기여도                      |
| model_version          | VARCHAR(80)                              | LSTM 모델 버전                           |
| created_at             | DATETIME(3)                              | 결과 저장 시각                             |


| 컬럼명                      | 저장 내용     | 처리 방법           |
| ------------------------ | --------- | --------------- |
| `id`                     | 고유번호      | AUTO_INCREMENT  |
| `oiltemp_id`             | 원본 데이터 ID | `ai_oiltemp.id` |
| `comcode`                | 업체 코드     | 원본 데이터          |
| `device_id`              | 설비 번호     | 원본 데이터          |
| `input_time`             | 분석 기준 시각  | 원본 데이터 시각       |
| `current_datetime`       | 분석 실행 시각  | Python 실행 시각    |
| `prediction_horizon_min` | 예측 기간     | 10, 30, 60, 120 |
| `prediction_target_time` | 예측 대상 시각  | 기준 시각 + 예측 기간   |
| `lstm_prediction`        | 미래 오일온도   | LSTM 예측값(℃)     |
| `lstm_anomaly_score`     | 이상 점수     | 별도 계산           |
| `feature_importance`     | 전체 변수 중요도 | JSON            |
| `feature_contributions`  | 개별 예측 기여도 | JSON            |
| `model_version`          | 모델 버전     | 모델 관리           |
| `created_at`             | 결과 저장 시각  | MySQL 자동 입력 가능  |
pip install numpy pandas scikit-learn tensorflow joblib


**최종 구성은 다음과 같습니다.**

- 학습변수: 16개
- 학습 데이터: 1분 간격
- LSTM 입력: 최근 30분
- 예측 시간: **10분, 30분, 60분, 120분**
- 실시간 데이터 수신: 5초 간격
- 실시간 예측 실행: 5초 간격
- 결과 저장: MySQL `ai_lstm_r`

특히 **120분 후 예측은 10분 후 예측보다 불확실성이 커질 수 있으므로**, 각 모델의 MAE와 RMSE를 별도로 평가해야 합니다.

|구분|학습변수|데이터|
|---|---|---|
|온도|현재 오일온도|`io003`|
|온도|최근 5분 오일온도 상승률|계산|
|운전|부하율|`io028`|
|운전|유효전력|`io010`|
|유량계|압력|`io044`|
|유량계|온도|`io045`|
|유량계|순간유량|`io046`|
|유량계|습도|`io048`|
|전류|U상 전류|`io007`|
|전류|V상 전류|`io008`|
|전류|W상 전류|`io009`|
|전압|U-V 선간전압|CSV 매핑 필요|
|전압|V-W 선간전압|CSV 매핑 필요|
|파생변수|평균전류|계산|
|파생변수|평균 선간전압|계산|
|파생변수|전류 불평형률|계산|


MEGACOM 11호기 LSTM 모델은 **① 미래 오일온도 예측과 ② 오일온도 변동에 영향을 미치는 주요 인자 분석**을 동시에 수행하도록 구성하는 것이 좋습니다.

두 기능을 구분해야 합니다.

- **온도 예측:** 10분, 30분, 60분, 120분 후 오일온도가 몇 ℃인지 계산
- **영향인자 분석:** 어떤 변수가 미래 오일온도 예측에 큰 영향을 미쳤는지 계산

## 1. 최종 AI 모델 구성

|구분|분석 기능|알고리즘|결과|
|---|---|---|---|
|1|10분 후 오일온도|LSTM|예측온도 ℃|
|2|30분 후 오일온도|LSTM|예측온도 ℃|
|3|60분 후 오일온도|LSTM|예측온도 ℃|
|4|120분 후 오일온도|LSTM|예측온도 ℃|
|5|주요 영향인자 분석|Permutation Importance|변수별 중요도|
|6|변수별 예측 기여도 분석|SHAP|변수별 기여도|
|7|예측 정확도 분석|MAE, RMSE|예측오차|

**LSTM은 온도를 예측하고, SHAP은 해당 예측에 각 변수가 얼마나 기여했는지 설명하는 역할**을 합니다.

## 2. 오일온도 변동 주요 인자 분석

앞서 정한 16개 학습변수를 그대로 사용합니다.


|변수|데이터|분석 목적|
|---|---|---|
|현재 오일온도|io003|현재 온도의 영향|
|5분 온도 상승률|계산|온도 상승 추세|
|부하율|io028|부하 변화의 영향|
|유효전력|io010|소비전력의 영향|
|유량계 압력|io044|압력 변화의 영향|
|유량계 온도|io045|유량계 온도의 영향|
|순간유량|io046|유량 변화의 영향|
|습도|io048|습도 변화의 영향|
|U상 전류|io007|전류 변화의 영향|
|V상 전류|io008|전류 변화의 영향|
|W상 전류|io009|전류 변화의 영향|
|U-V 선간전압|io004|전압 변화의 영향|
|V-W 선간전압|io005|전압 변화의 영향|
|평균전류|계산|전류 평균값의 영향|
|평균 선간전압|계산|전압 평균값의 영향|
|전류 불평형률|계산|전류 불평형의 영향|

여기서 중요한 것은 **현재 오일온도가 가장 중요한 변수로 나타날 가능성이 높다는 점**입니다.

그러나 현재 온도가 중요한 것은 당연한 결과일 수 있습니다.

따라서 영향인자를 두 그룹으로 분석하는 것을 권장합니다.

**그룹 A: 전체 변수 중요도**

16개 변수를 모두 분석합니다.

**그룹 B: 운전조건 영향인자**

현재 오일온도와 5분 온도 상승률을 제외한 14개 변수의 중요도를 분석합니다.

이렇게 하면 오일온도 자체의 영향과 설비 운전조건의 영향을 구분해서 확인할 수 있습니다.

단, 그룹 B의 중요도는 전체 모델에서 온도 관련 두 변수를 제외하고 나머지 변수의 중요도를 비교한 결과입니다. 온도 관련 변수의 효과를 완전히 제거한 인과분석은 아닙니다.


## 3. SHAP을 이용한 주요 영향인자 분석

예를 들어 LSTM이 다음과 같이 예측했다고 가정하겠습니다.

현재 오일온도: 78℃

|예측 시간|예측온도|
|---|---|
|10분 후|79.2℃|
|30분 후|82.5℃|
|60분 후|87.3℃|
|120분 후|94.1℃|

120분 후 예측에 대한 SHAP 분석 결과가 다음과 같을 수 있습니다.

|순위|영향인자|SHAP 기여도(예시)|
|---|---|---|
|1|현재 오일온도|+6.2℃|
|2|부하율|+3.1℃|
|3|유효전력|+2.4℃|
|4|5분 온도 상승률|+1.8℃|
|5|순간유량|-1.2℃|
|6|평균전류|+0.9℃|

이 표는 실제 분석 결과가 아닌 예시입니다.

SHAP 기여도가 양수이면 해당 변수가 모델의 예측온도를 기준 예측값보다 높이는 방향으로 작용했다는 의미입니다.

음수이면 예측온도를 낮추는 방향으로 작용했다는 의미입니다.

**주의:** SHAP은 모델의 예측에 대한 기여도를 설명합니다. 실제 설비에서 해당 변수가 온도 상승의 물리적 원인임을 증명하지는 않습니다.



---

## 4. LSTM 예측과 영향인자 분석 코드

기존 LSTM 학습 코드에 다음 기능을 추가할 수 있습니다.

먼저 Permutation Importance로 전체 변수의 중요도를 계산합니다.

```
import numpy as np        X_test,        verbose=0    )    baseline_temp = scaler_y.inverse_transform(        baseline_pred    ).flatten()    real_temp = scaler_y.inverse_transform(        y_test.reshape(-1, 1)    ).flatten()    baseline_mae = mean_absolute_error(        real_temp,        baseline_temp    )    results = []    rng = np.random.default_rng(42)    for i, feature in enumerate(feature_names):        errors = []        for _ in range(repeats):            X_perm = X_test.copy()            # 변수 i의 전체 시계열을 샘플 간 섞음            idx = rng.permutation(len(X_perm))            X_perm[:, :, i] = X_perm[idx, :, i]            pred = model.predict(                X_perm,                verbose=0            )            pred_temp = scaler_y.inverse_transform(                pred            ).flatten()            mae = mean_absolute_error(                real_temp,                pred_temp            )            errors.append(mae - baseline_mae)        results.append({            "feature": feature,            "importance": np.mean(errors),            "importance_std": np.std(errors)        })    result_df = pd.DataFrame(results)    result_df = result_df.sort_values(        "importance",        ascending=False    )    return result_df
```

사용 방법:

```
importance_df = calculate_feature_importance(    model=model,    X_test=X_test,    y_test=y_test,    scaler_y=scaler_y,    feature_names=FEATURES)print(importance_df)importance_df.to_csv(    f"LSTM_results/importance_{predict_min}min.csv",    index=False,    encoding="utf-8-sig")
```

이 코드는 각 변수의 시계열을 다른 샘플의 시계열과 교환하여 예측오차가 얼마나 증가하는지 측정합니다.

중요도가 클수록 해당 변수에 대한 모델의 의존도가 크다고 해석할 수 있습니다.

다만 평균전류와 개별 상전류처럼 서로 연관된 변수들이 있으므로, 개별 변수 중요도가 실제보다 낮거나 불안정하게 나타날 수 있습니다. 이를 보완하려면 전류 관련 변수들을 묶어 평가하는 그룹 중요도 분석도 수행하는 것이 좋습니다.


## 5. 실시간 예측 결과에 영향인자 포함

실시간 예측 결과는 다음과 같이 구성하는 것을 권장합니다.

|예측시간|예측온도|주요 영향인자 1|주요 영향인자 2|주요 영향인자 3|
|---|---|---|---|---|
|10분|79.2℃|현재온도|부하율|유효전력|
|30분|82.5℃|부하율|현재온도|평균전류|
|60분|87.3℃|유효전력|부하율|순간유량|
|120분|94.1℃|부하율|유효전력|5분 상승률|

위 결과 역시 설명용 예시입니다.

실시간으로 주요 영향인자를 구하려면 각 예측에 대해 SHAP과 같은 개별 예측 설명 기법을 적용해야 합니다.

Permutation Importance는 모델 전체의 중요도를 평가하는 데 적합하지만, 개별 예측의 주요 영향인자를 직접 제공하지는 않습니다.

또한 SHAP 계산은 LSTM 예측보다 시간이 많이 소요될 수 있으므로 다음과 같이 구분하는 것이 효율적입니다.

|기능|실행 간격|
|---|---|
|LSTM 오일온도 예측|5초|
|주요 영향인자 SHAP 분석|1분 또는 경고 발생 시|
|전체 변수 중요도 분석|모델 재학습 후|
|실제온도와 예측오차 평가|해당 예측 시각 도달 후|

## 6. 최종 권장 구조

```
            MEGACOM 11호기
                  │
           MySQL 실시간 데이터
               (5초 간격)
                  │
                  ▼
             데이터 전처리
                  │
          16개 학습변수 계산
                  │
                  ▼
             LSTM 예측
                  │
       ┌──────────┼──────────┐
       │          │          │
    10분 예측   30분 예측   60분 예측
                             │
                         120분 예측
                  │
                  ▼
            예측온도 저장
                  │
                  ▼
          주요 영향인자 분석
                  │
            ┌─────┴─────┐
            │           │
      전체 중요도     개별 예측 SHAP
            │           │
            └─────┬─────┘
                  │
                  ▼
             MySQL 저장
                  │
                  ▼
           GUI 실시간 표시
```

### 최종 개발 목표

**필수 기능**

1. 10분, 30분, 60분, 120분 후 오일온도 예측
2. 각 예측시간별 MAE, RMSE 계산
3. 각 예측시간별 주요 영향인자 3~5개 추출
4. 영향인자별 중요도 및 SHAP 기여도 계산
5. MySQL에 예측온도와 영향인자 저장

**추가로 권장하는 분석은 '미래 온도 상승량 예측'입니다.**

예를 들어 현재 온도가 78℃이고 60분 후 예측온도가 87℃라면 온도 상승량은 +9℃입니다.

이 상승량을 함께 분석하면 현재 온도가 높은 이유와 앞으로 온도가 더 상승할 것으로 예측되는 이유를 구분하는 데 도움이 됩니다.

**따라서 LSTM의 핵심 출력은 미래 오일온도(℃)로 유지하고, 추가 출력으로 예상 온도 변화량(℃)과 주요 영향인자 및 기여도를 제공하는 구조를 권장합니다.**


