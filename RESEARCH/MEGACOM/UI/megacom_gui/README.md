# MEGACOM AI Monitoring Console

## 실행

```bash
pip install -r requirements.txt
python main.py
```

Qt Designer에서 `dashboard.ui`를 열어 배치/문구를 수정할 수 있습니다. 실행할 때 `main.py`가 `.ui`를 직접 읽으므로 `pyuic5` 변환은 필요 없습니다.

`rule.py`, `cf.py`, `lstm_predict.py`를 GUI와 같은 폴더에 배치하거나 **스크립트 폴더 선택**으로 세 파일이 있는 경로를 지정합니다. 원본 CF 모델 JSON, LSTM 모델, `config.py`, `lstm_features.py`, DB 설정 등 관련 의존 파일도 원본 프로젝트의 경로 구조에 맞춰 준비해야 합니다.

GUI의 업체/설비 ID는 LSTM 실행 인자 및 최근 데이터 조회에 적용됩니다. **rule.py의 COM_CODE/DEVICE_ID는 소스 상수이며, cf.py의 DEVICE_ID는 소스 상수, 업체 코드는 MYSQL_COMCODE 환경변수입니다. GUI 입력값을 이 두 스크립트에 자동 반영하지 않습니다.** 변경이 필요하면 원본 스크립트 설정을 먼저 수정하세요.

DB 최근 데이터 표는 `mysql_config.env`의 MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE를 사용합니다. 읽기 전용 SELECT이며, 15초마다 자동 갱신됩니다. 분석 엔진은 별도 프로세스로 실행되고 종료 시 중지됩니다.

주의: 실제 DB 및 모델 파일이 제공되지 않아 실환경 실행은 검증되지 않았습니다.
