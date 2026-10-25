

### ??? possible to make three interface connector of 19v, 12v, 5v

| three interface connector | 19v, 12v, 5v |     |     |     |
| ------------------------- | ------------ | --- | --- | --- |
| DC-DC converter           | 19v,12v,5v   |     |     |     |
|                           |              |     |     |     |
|                           |              |     |     |     |
|                           |              |     |     |     |

| 부품            | 권장 사양               |  수량 |
| ------------- | ------------------- | --: |
| LiFePO4 배터리   | 12.8V 10Ah, BMS 내장  |   1 |
| 충전기           | LiFePO4 4S 전용 14.6V |   1 |
| DC-DC 승압 컨버터  | 12V → 19V, 5A급      |   1 |
| DC-DC 강압 컨버터  | 12V → 5V, 5A급       |   1 |
| DC-DC 승강압 컨버터 | 12V 정전압, 모터 전류 대응   |   1 |
| 메인 스위치        | DC 정격, 20A 이상 권장    |   1 |
| 퓨즈 및 퓨즈홀더     | 회로별 전류에 맞게 선정       |   4 |
| 전원 분배 단자대     | DC 배전용              |   1 |


|출력|기능|
|---|---|
|DC 19V|Jetson Orin Nano|
|DC 12V|모터드라이버|
|DC 5V|Arduino, PCA9685, 센서|
|배터리 전압 측정|잔량 추정|
|메인 스위치|전체 전원 제어|
|퓨즈|과전류 보호|


## 제작 시 주의사항

**모터 전원과 Jetson 전원은 반드시 별도 DC-DC 회로로 분리하는 것을 권장합니다.**

모터가 출발하거나 정지할 때 순간적으로 큰 전류가 흐르면 배터리 전압이 떨어질 수 있습니다. 이때 Jetson이 재부팅되는 문제가 발생할 수 있습니다.

또한 다음 사항이 중요합니다.

- 4S LiFePO4 배터리의 완충전압은 약 14.6V입니다.
- 12V 모터에 배터리 전압을 직접 공급하면 완충 시 정격전압을 초과합니다.
- BMS는 모터 기동전류와 스톨전류를 감당할 수 있어야 합니다.
- 각 출력에는 별도 퓨즈를 설치합니다.
- 배터리 충전에는 4S LiFePO4 전용 충전기를 사용합니다.

---

## 6. 다음 단계: 실제 PCB 제작

현재 SLAM 로봇을 제작 중이므로, 배터리와 DC-DC 모듈을 연결하는 **전원 분배 PCB**를 제작하는 것도 좋은 방법입니다.

PCB에는 다음 기능을 넣을 수 있습니다.



## - 구매 가능한 DC-DC 컨버터

### 1. 5V 전원용


사이즈 17.5×12.3×4.3mm. 입력전압 5‑30V(권장 28V), 안정적인 5V 출력

![[Pasted image 20261025100156.png]]


### 2. 19 VOLT

### ① Jetson용 19V 컨버터

**[ATO ATOWG-12S1905](https://www.ato.com/dc-dc-boost-converter-12v-to-19v?utm_source=chatgpt.com)**

- 입력: DC 9~16V
- 출력: DC 19V / 5A
- 출력전력: 95W
- 효율: 약 92%
- 크기: 74 × 74 × 32mm
- 표시 가격: 약 $79.69

LiFePO4 4S 배터리의 전압 범위에 적합하며, Jetson에 필요한 19V를 안정적으로 공급하는 용도입니다. [ato.com](https://www.ato.com/dc-dc-boost-converter-12v-to-19v?utm_source=chatgpt.com)

### ② 모터용 12V 컨버터

**SC200-0920V1210**

- 입력: DC 9~20V
- 출력: DC 12V / 10A
- 출력전력: 120W
- 방식: Buck-Boost

배터리 전압이 12V보다 높거나 낮아져도 12V 출력을 유지할 수 있습니다.

제품 사양: [12V 10A 승강압 컨버터 사양서](https://www.buckboostconverter.com/image/non-isolated-dc-dc-buck-boost-converter-specs.pdf?utm_source=chatgpt.com)

다만 이 모델은 제조사 사양표에서 확인한 제품으로, 실제 판매처와 재고는 추가 확인이 필요합니다.