# MEGACOM LSTM (11호기)

- 학습: `lstm_train.py` (CSV, 1분 간격, 16개 특징, 10/30/60/120분 모델)
- 추론: `lstm_predict.py` (MySQL 최신 ID 확인, 5초 주기, 4행 저장)
- 공통 특징: `lstm_features.py`
- 설정: `config.py` (DB 비밀번호 환경변수)

## 설치 및 학습

```powershell
pip install -r requirements.txt
python lstm_train.py --csv "남양금속 11호기(4).csv" --epochs 30
```

## 추론 (PowerShell 예)

```powershell
$env:DB_HOST="DB서버주소"
$env:DB_PORT="3306"
$env:DB_USER="DB사용자"
$env:DB_PASSWORD="비밀번호"
$env:DB_NAME="airpredict"
python lstm_predict.py --comcode "실제업체코드" --device-id "실제설비번호" --once
python lstm_predict.py --comcode "실제업체코드" --device-id "실제설비번호" --interval 5 --explain-every 12
```

`ai_oiltemp`에 `id`, `comcode`, `device_id`, `input_time`(DATETIME), 12개 io 원본 컬럼이 있어야 합니다. `ai_lstm_r`에는 사용자 지정 컬럼이 존재해야 하며 `lstm_anomaly_score`는 NULL을 허용해야 합니다. `input_time`은 DB의 한국 현지 시각이라고 가정합니다. CSV의 `Z` 시간은 한국시간으로 변환합니다. 원본 CSV는 두 번째 행이 io 코드인 구조입니다.

중복 예측 방지 (기존 중복 확인 후 실행):

```sql
ALTER TABLE ai_lstm_r ADD UNIQUE KEY uq_lstm_prediction (oiltemp_id, prediction_horizon_min, model_version);
```

중요도 `feature_importance`는 학습 시 계산한 permutation MAE 증가량(℃)입니다. `feature_contributions`는 **SHAP이 아닌 Integrated Gradients 근사치**(℃)입니다. 처음 및 12개 신규 ID마다 계산하며, 그 외 예측에서는 NULL로 저장합니다. IG는 계산 비용이 크므로 5초 주기 충족 여부를 측정하세요.

**데이터 주의:** 학습 CSV는 1분 스냅샷이고 실시간 데이터는 5초 값을 60초 평균합니다. 학습/추론의 집계 방식 차이로 분포가 달라질 수 있습니다. 실시간 운영 전에 동일한 1분 평균 방식으로 학습 데이터를 다시 만드는 것이 이상적입니다. 결측이나 5초 기록 부족 구간은 예측하지 않습니다. 120분 예측은 독립적으로 성능을 확인해야 합니다. 전류 불평형률은 평균전류가 0인 구간에 정의되지 않으므로 해당 시퀀스는 제외합니다.

**운영 주의:** 프로그램 시작 시 과거에 처리한 최신 ID도 다시 예측할 수 있으나 UNIQUE KEY가 있다면 동일 키를 갱신합니다. 프로세스가 중단된 사이의 모든 ID를 재처리하지는 않습니다. 동일한 테이블에 대해 여러 추론 프로세스를 동시에 돌리지 마세요. 예측오차 기반 이상점수는 실제 미래온도가 관측된 후 별도 계산해야 하므로 초기값은 NULL입니다.
