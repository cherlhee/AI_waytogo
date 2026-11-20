

  
C:\CHERLHEE\AI_waytogo\RESEARCH\MEGACOM\UI\MEGACOM_PyQt_Designer_GUI\megacom_gui

확인했습니다. 현재 실제 GUI 프로젝트 폴더는 다음과 같습니다.

`C:\CHERLHEE\AI_waytogo\RESEARCH\MEGACOM\UI\MEGACOM_PyQt_Designer_GUI\megacom_gui`

그런데 CF 실행 로그에는 다음 경로가 표시됩니다.

`C:\CHERLHEE\AI_waytogo\RESEARCH\MEGACOM\UI\megacom_gui`

**두 경로가 다릅니다.** 따라서 CF가 다른 폴더에서 mysql_config.env를 찾고 있습니다.

### 1. main.py의 경로 수정

기존 코드:

ROOT = Path(__file__).resolve().parent

다음과 같이 변경하세요.

ROOT = Path(

r"C:\CHERLHEE\AI_waytogo\RESEARCH\MEGACOM"

r"\UI\MEGACOM_PyQt_Designer_GUI\megacom_gui"

)

이렇게 하면 RULE, CF, LSTM 스크립트의 기본 경로가 해당 폴더로 지정됩니다.

### 2. MySQL 설정 파일 확인

다음 위치에 mysql_config.env가 있어야 합니다.

`MEGACOM_PyQt_Designer_GUI/ └── megacom_gui/ ├── main.py ├── dashboard.ui ├── rule.py ├── cf.py ├── lstm_predict.py ├── mysql_config.env └── cf_11_output/ ├── cf_11_model.json └── cf_11_temperature_model.json`

단, **CF는 실행 중인 cf.py 파일의 위치를 기준으로 설정 파일을 찾도록 작성되어 있을 수 있습니다.** 따라서 GUI의 ROOT만 변경하는 것으로 충분하지 않을 수 있습니다.

### 3. 실행 경로 확인 로그 추가

start() 함수의 다음 코드 바로 아래에:

`script = self.folder / FILES[key]`

다음을 추가하세요.

`self.log(f'{key.upper()} 실행 파일: {script.resolve()}') self.log(f'{key.upper()} 작업 폴더: {self.folder.resolve()}')`

정상적으로 설정되었다면 다음과 같이 표시되어야 합니다.

`[CF] 실행 파일: C:\CHERLHEE\AI_waytogo\RESEARCH\MEGACOM\UI\MEGACOM_PyQt_Designer_GUI\megacom_gui\cf.py`

**중요:** ROOT를 변경한 뒤 GUI를 완전히 종료하고 다시 실행하세요. 또한 GUI의 폴더 선택 버튼으로 다른 경로를 선택했다면 그 경로가 우선 적용됩니다.

마지막으로 확인할 사항은 하나입니다.

**말씀하신 MEGACOM_PyQt_Designer_GUI\megacom_gui 폴더 안에 mysql_config.env 파일이 실제로 존재합니까?**

=C:\CHERLHEE\AI_waytogo\RESEARCH\MEGACOM\UI\MEGACOM_PyQt_Designer_GUI\megacom_gui\cf_11_output\cf_11_model.json [18:12:08] [CF] 2026-11-20 18:12:08,228 INFO C00088 2026-11-20 18:11:57 예측 4행 저장: 10분 정상 [18:12:08] [CF] 2026-11-20 18:12:08,242 INFO C00088 2026-11-20 18:12:02 예측 4행 저장: 10분 정상 [18:12:08] [CF] 2026-11-20 18:12:08,275 INFO C00088 2026-11-20 18:12:07 예측 4행 저장: 10분 정상 [18:12:22] [CF] 2026-11-20 18:12:22,804 INFO 실제온도 보정: 0건 입력 (대상 2003건 검사)

네. **현재 로그를 보면 CF 예측 프로그램이 정상적으로 동작하고 있으며, MySQL 저장도 성공했습니다.**

이전에 발생했던 모델 파일 경로 오류와 MySQL 환경변수 오류도 해결된 것으로 판단됩니다.

### 1. CF 실행 결과

|로그|의미|상태|
|---|---|---|
|cf_11_model.json|학습 모델 경로|정상으로 추정|
|18:11:57 예측 4행 저장|4개 예측 시간에 대한 결과 저장|✅ 성공|
|18:12:02 예측 4행 저장|다음 데이터에 대한 예측 결과 저장|✅ 성공|
|18:12:07 예측 4행 저장|다음 데이터에 대한 예측 결과 저장|✅ 성공|
|실제온도 보정: 0건 입력|실제온도 업데이트|확인 필요|

### 2. 예측 4행 저장의 의미

MEGACOM CF 프로그램은 하나의 측정 시각에 대해 네 가지 미래 시점의 오일온도를 예측합니다.

|예측 시간|저장 테이블|
|---|---|
|10분 후|ai_oiltemp|
|30분 후|ai_oiltemp|
|60분 후|ai_oiltemp|
|120분 후|ai_oiltemp|

따라서 다음 로그는

`18:12:07 예측 4행 저장: 10분 정상`

**18:12:07 측정 데이터를 기준으로 10·30·60·120분 예측 결과 4건을 저장했다**는 의미입니다.

10분 정상은 10분 예측 구간에 대한 판정으로 보입니다. 다른 예측 구간까지 모두 정상이라는 의미는 아닐 수 있습니다.

### 3. 실제온도 보정 0건은 오류인가?

`실제온도 보정: 0건 입력 (대상 2003건 검사)`

이 메시지만으로 오류라고 판단할 수는 없습니다.

프로그램이 2,003건을 검사했지만, 실제온도를 새로 입력한 행이 없다는 의미입니다.

가능한 원인은 다음과 같습니다.

- 아직 예측 목표 시각에 도달하지 않았음
- 목표 시각에 대응하는 ai_data가 없음
- 실제온도가 이미 입력되어 있음
- 실제온도 매칭 조건이 맞지 않음

다음 SQL로 실제온도 저장 상태를 확인할 수 있습니다.

`SELECT input_time, prediction_horizon_min, prediction_target_time, oil_temp_current, oil_temp_predicted, oil_temp_actual FROM ai_oiltemp WHERE comcode = 'C00088' AND device_id = 'R00012' ORDER BY input_time DESC LIMIT 20;`

### 4. 현재 MEGACOM 통합 GUI 상태

|엔진|상태|
|---|---|
|RULE|✅ 정상 분석 및 저장 확인|
|CF|✅ 정상 예측 및 저장 확인|
|LSTM|⏳ 실행 확인 필요|
|MySQL|✅ RULE·CF 저장 성공|
|PyQt5 GUI|✅ 실행 로그 출력 정상|

**이제 RULE과 CF는 정상 동작이 확인되었습니다.**

다음 단계는 **LSTM 실행을 확인하고, GUI에 CF·LSTM의 10분·30분·60분·120분 예측온도를 실시간으로 표시하는 기능**을 추가하는 것입니다.
