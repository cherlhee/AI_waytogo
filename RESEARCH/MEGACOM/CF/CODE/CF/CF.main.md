


**한 번 실행**
```python
python cf_realtime_11_cf_temperature_with_actual.py --once
```

**5초 간격으로 계속 실행**
```python
python cf_realtime_11_cf_temperature_with_actual.py --interval 5
```
1. 오일온도 예측 결과 저장 테이블

테이블명: ai_oiltemp

|   |   |   |
|---|---|---|
|컬럼명|데이터 타입|설명|
|id|BIGINT AUTO_INCREMENT<br><br>PRIMARY KEY|고유번호|
|comcode|VARCHAR(15)|업체 코드|
|device_id|VARCHAR(20)|설비 번호|
|input_time|DATETIME(3)|예측 기준 데이터 시각|
|current_datetime|DATETIME(3)|분석 실행 시각|
|oil_temp_current|DECIMAL(10,2)|현재 오일온도(℃)|
|oil_temp_predicted|DECIMAL(10,2)|미래 예측 오일온도(℃)|
|oil_temp_actual|DECIMAL(10,2)|미래 시점의 실제 오일온도(℃)|
|prediction_horizon_min|INT|예측 기간(분)<br><br>(10, 30, 60, 120분 등)|
|prediction_target_time|DATETIME(3)|미래 예측 대상 시각|
|prediction_model|VARCHAR(30)|예측 알고리즘<br><br>(LSTM, RF, CF 등)|
|prediction_features|JSON|예측에 사용한 영향인자|
|prediction_result|VARCHAR(20)|예측 판정 결과(주의,경고,알람 등)|
|created_at|DATETIME(3)|분석결과 저장 시각|


프로그램은 매번 다음 순서로 실행됩니다.

1. 최신 측정 데이터를 읽어 CF 예측 수행
2. 예측 결과를 `ai_oiltemp`에 저장
3. 예측 대상 시각이 지난 행을 조회
4. `ai_data`에서 해당 시각의 실제 오일온도 검색
5. `oil_temp_actual` 업데이트
    conn = mysql.connector.connect(
        host="121.181.35.7",
        port=3307,
        user="mega_admin",
        password="megaComp!#%",
        database="airpredict",
        connection_timeout=10
    )



pip install mysql-connector-python python-dotenv
