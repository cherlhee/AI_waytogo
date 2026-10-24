


  

SLAM-KIT,,,PCB

## SLAM-KIT 전용 PCB 설계

교육·실습용 **SLAM-KIT(자율주행 로봇)**의 PCB를 설계하려는 것으로 이해했습니다.

기존에 검토한 **ESP32 + JGB37-520 DC 모터 + 모터드라이버 + LiDAR** 구성을 기준으로 전용 PCB를 제작할 수 있습니다.

### 1. SLAM-KIT PCB 기본 구성

|구성 요소|추천 부품|기능|
|---|---|---|
|메인 MCU|ESP32-WROOM-32|모터 제어 및 통신|
|모터|JGB37-520 (12V)|로봇 구동|
|모터드라이버|HR8833 또는 고전류 드라이버|DC 모터 정·역회전|
|거리 센서|2D LiDAR|거리 측정 및 SLAM|
|엔코더|모터 내장 엔코더|속도 및 이동거리 측정|
|IMU|MPU6050|자세 및 회전 측정|
|전원|11.1V 3S LiPo|시스템 전원|
|전압 변환|DC-DC 5V / 3.3V|MCU 및 센서 전원|
|통신|Wi-Fi / UART|ROS2 컴퓨터와 통신|

모터드라이버는 JGB37-520의 **정격전류 및 기동·구속전류**를 확인한 후 선정해야 합니다.

### 2. PCB 시스템 구조

`┌─────────────────────┐ │ Jetson Orin Nano │ │ ROS2 Humble │ │ SLAM / Nav2 │ └──────────┬──────────┘ │ Wi-Fi │ ┌──────────▼──────────┐ │ ESP32 PCB │ │ │ │ ┌───────────────┐ │ │ │ ESP32 │ │ │ └───────┬───────┘ │ │ │ │ │ ┌───────▼───────┐ │ │ │ Motor Driver │ │ │ └───────┬───────┘ │ │ │ │ └──────────┼──────────┘ │ DC Motor × 2`

LiDAR는 Jetson에 USB/UART로 직접 연결하고, ESP32는 모터와 엔코더를 담당하도록 분리하면 개발이 간단합니다.

### 3. PCB 설계 방향

**추천: 2층 PCB, ESP32 기반 모터제어 통합보드**

PCB에 다음 기능을 포함합니다.

1. ESP32 모듈 장착
2. DC 모터 2개 또는 4개 제어
3. 엔코더 입력 2~4채널
4. IMU 센서 연결
5. 12V 배터리 입력
6. 5V 및 3.3V 전원회로
7. LiDAR 및 확장 센서용 커넥터
8. UART/I²C 통신 커넥터
9. 전원 스위치 및 보호회로

### 4. 설계 전에 결정할 사항

**어떤 PCB를 제작하려고 합니까?**

**① ESP32 기반 SLAM-KIT 메인 PCB**

- 모터제어, 엔코더, IMU, 전원회로 통합
- Jetson과 Wi-Fi 통신

**② ESP32 + 모터드라이버 통합 PCB**

- ESP32와 모터드라이버만 통합
- 가장 간단하고 저렴한 구조

**③ SLAM-KIT 전체 통합 PCB**

- ESP32, 모터드라이버, LiDAR 인터페이스, IMU, 전원회로 통합
- 교육용 SLAM-KIT 전용 보드

**추가 질문:** SLAM-KIT는 **2륜구동인가요, 4륜구동인가요?**

이 두 가지를 결정하면 **KiCad용 회로도, 부품 목록(BOM), PCB 배치 및 배선 설계**를 구체적으로 진행할 수 있습니다.

ESP32 + JGB37-520 DC 모터 + 모터드라이버,,PCA9685,,를 사용하라,,HR8833,,사용하여,,,회로도를 그려라

4륜구동회로 그려라

does esp32devkit use 3.3volt or 5volt

The **ESP32 DevKit uses 3.3V logic**, but most ESP32 DevKit boards can be powered using **5V**.

### 1. ESP32 DevKit Voltage

|Pin|Voltage|Description|
|---|---|---|
|**VIN / 5V**|5V|Power input through onboard regulator|
|**3V3**|3.3V|Regulated 3.3V power|
|**GPIO**|3.3V|Digital input/output logic|
|**GND**|0V|Ground|
|**USB**|5V|Powers the board through USB|

**Important:** ESP32 GPIO pins are **not 5V tolerant**. Applying 5V directly to a GPIO can damage the ESP32.

### 2. For Your SLAM-KIT

With your ESP32 + PCA9685 + HR8833 + JGB37-520 motors, I recommend:

`11.1V LiPo Battery | DC-DC Converter 5V | +-------+---------+ | | ESP32 DevKit PCA9685 VIN / 5V V+ (5V) | 3.3V Regulator | ESP32 GPIO (3.3V) | +------ PCA9685 VCC (3.3V)`

For the PCA9685:

- **VCC = 3.3V** (logic power)
- **V+ = 5V** (servo power rail, if needed)
- **SDA/SCL = 3.3V logic**
- **GND = common ground**

For the HR8833 motor driver, use a motor supply within the **specific driver's rated voltage range**. Do not assume that an 11.1V LiPo battery is compatible with every HR8833 board.

### 3. ESP32 to PCA9685 Connections

|ESP32 DevKit|PCA9685|
|---|---|
|3V3|VCC|
|GND|GND|
|GPIO21|SDA|
|GPIO22|SCL|

**Conclusion:** Supply **5V to the ESP32 DevKit VIN/5V pin** or power it through USB. The ESP32 itself operates at **3.3V**, and its GPIO signals must remain at 3.3V.

esp32devkit,,does it change 5volt to 3.3volt internally?

**Yes. The ESP32 DevKit has an onboard voltage regulator that converts 5V to 3.3V.**

### 1. Internal Power Circuit

`USB 5V or VIN 5V │ ▼ ┌─────────────────┐ │ Voltage │ │ Regulator (LDO) │ │ 5V → 3.3V │ └────────┬────────┘ │ 3.3V │ ┌───────┴────────┐ │ │ ▼ ▼ ESP32 Chip 3V3 Pin (3.3V) (3.3V)`

### 2. ESP32 DevKit Power Pins

|Pin|Voltage|Function|
|---|---|---|
|USB|5V|Power input|
|VIN / 5V|5V|Power input on most DevKit boards|
|3V3|3.3V|Regulated voltage|
|GND|0V|Ground|

The onboard regulator is commonly an **AMS1117-3.3** or a similar 3.3V regulator, depending on the board model.

### 3. For Your SLAM-KIT PCB

You can use the following configuration:

`11.1V LiPo Battery │ ▼ DC-DC Buck 5V │ ├──────── ESP32 VIN (5V) │ │ │ Internal LDO │ │ │ 3.3V │ │ │ ESP32 Chip │ └──────── Other 5V Devices`

**Important:**

- Do not apply 11.1V directly to the ESP32 DevKit VIN pin.
- ESP32 GPIO pins operate at **3.3V**, not 5V.
- The 3V3 pin can supply limited current to external devices, depending on the DevKit's regulator and power budget.
- Avoid powering the board simultaneously through USB and an external 5V supply unless the specific DevKit supports it.

**Conclusion:** For your SLAM-KIT, a **5V DC-DC converter connected to the ESP32 DevKit 5V/VIN pin** is a suitable power solution. You do not need a separate 3.3V regulator for the ESP32 itself.

주파수를 계속 증가시키면 파동의 주기가 충전/방전 시간보다 매우 짧아짐 또한 전류가 금속판으로 흘러들어가거나 나가는 빠르기가 도선으로 대치될 때 흐르는 전류의 빠르기와 같아짐 ,capacitor,,,

## 커패시터(Capacitor)에서 주파수가 증가하면 어떻게 되는가?

질문하신 내용은 **교류 주파수가 높아질수록 커패시터가 마치 도선처럼 동작하는 이유**를 설명한 것입니다.

다만, 충전·방전 시간과 전류의 관계를 조금 더 정확하게 이해할 필요가 있습니다.

### 1. 커패시터의 기본 원리

커패시터는 두 금속판 사이에 절연체가 있는 구조입니다.

`Capacitor ┌─────┐ │ │ ──────┤ + │ │ │ └─────┘ ║ ┌─────┐ │ - ├────── │ │ └─────┘ 두 금속판 사이에는 전자가 직접 이동하지 않음`

커패시터에 전압을 가하면 금속판에 전하가 축적됩니다.

커패시터의 전하와 전압 관계는

Q=CVQ=CV

입니다.

양변을 시간에 대해 미분하면

i(t)=Cdv(t)dti(t)=Cdtdv(t)​​

즉, **커패시터 전류는 전압의 변화율에 비례합니다.**

---

### 2. 교류 주파수를 증가시키면?

커패시터에 정현파 전압을 인가한다고 가정하겠습니다.

v(t)=Vmsin⁡(ωt)v(t)=Vm​sin(ωt)

여기서

ω=2πfω=2πf

입니다.

커패시터 전류는

i(t)=Cdv(t)dti(t)=Cdtdv(t)​

이므로

i(t)=ωCVmcos⁡(ωt)i(t)=ωCVm​cos(ωt)

따라서

Im=2πfCVmIm​=2πfCVm​​

입니다.

이 식에서 중요한 사실을 알 수 있습니다.

**전압의 진폭이 일정하다면 주파수가 증가할수록 커패시터에 흐르는 전류의 진폭이 증가합니다.**

예를 들어 커패시터가 100 μF100μF라면 다음과 같습니다.

|주파수|용량성 리액턴스|
|---|---|
|10 Hz|159.15 Ω|
|100 Hz|15.92 Ω|
|1 kHz|1.59 Ω|
|10 kHz|0.159 Ω|
|100 kHz|0.0159 Ω|

용량성 리액턴스는

XC=12πfCXC​=2πfC1​​

이므로 주파수가 증가할수록 감소합니다.

---

### 3. 충전·방전 시간이 교류 주기보다 길어지면?

질문하신 핵심입니다.

커패시터가 저항을 통해 충전되는 회로에서는 시정수가

τ=RCτ=RC

입니다.

교류의 주기는

T=1fT=f1​

입니다.

주파수를 계속 증가시키면

T≪RCT≪RC

가 됩니다.

이때 커패시터는 한 주기 동안 완전히 충전되거나 방전되지 못할 수 있습니다.

그렇다고 전류가 흐르지 않는 것은 아닙니다.

오히려 RC 직렬회로에서 주파수가 증가하면 커패시터의 리액턴스가 감소하므로 회로 전류는 증가하여 저항에 의해 제한되는 값에 가까워집니다.

여기서 구분해야 할 사항이 있습니다.

- **충전·방전이 완료되는가?** → 주기가 짧으면 완료되지 않을 수 있습니다.
- **교류 전류가 흐르는가?** → 전압이 변하는 동안 전류가 흐릅니다.
- **주파수가 증가하면?** → 이상적인 커패시터의 리액턴스가 감소합니다.

---

### 4. 커패시터가 도선처럼 동작한다는 의미

커패시터의 임피던스는

ZC=1jωCZC​=jωC1​

또는

ZC=−j1ωCZC​=−jωC1​

입니다.

주파수를 무한히 증가시키면 이상적인 커패시터에서는

lim⁡ω→∞ZC=0ω→∞lim​ZC​=0

입니다.

따라서

f→∞⇒ZC→0f→∞⇒ZC​→0​

가 됩니다.

이는 **이상적인 커패시터가 고주파 교류에 대해 단락회로에 가까워진다**는 의미입니다.

하지만 실제 커패시터에는 기생 인덕턴스와 저항이 존재하므로, 충분히 높은 주파수에서는 다시 임피던스가 증가할 수 있습니다.

---

### 5. 금속판 사이에 전자가 이동하지 않는데 왜 전류가 흐르는가?

이 부분이 특히 중요합니다.

커패시터의 두 금속판 사이에는 절연체가 존재합니다.

따라서 이상적인 커패시터에서는 전자가 절연체를 통과하지 않습니다.

그런데도 외부 회로에는 전류가 흐릅니다.

그 이유는 **변위전류(Displacement Current)** 때문입니다.

맥스웰은 시간에 따라 변하는 전기장이 전류와 같은 방식으로 자기장을 형성한다는 사실을 설명했습니다.

변위전류는

Id=ϵdΦEdtId​=ϵdtdΦE​​​

로 표현할 수 있습니다. 여기서는 유전율이 일정한 매질을 가정합니다.

이상적인 평행판 커패시터에서는

Id=IcId​=Ic​​

가 성립합니다.

여기서

- IdId​: 금속판 사이의 변위전류
- IcIc​: 도선에 흐르는 전도전류

입니다.

즉, 금속판 사이로 전자가 직접 이동하지 않아도 **시간에 따라 변하는 전기장이 전류의 연속성을 유지합니다.**

---

### 6. 결론

질문하신 문장을 물리적으로 정리하면 다음과 같습니다.

> 교류 주파수가 증가하면 커패시터의 충전·방전 주기가 짧아지고, 이상적인 커패시터의 용량성 리액턴스는 감소한다. 따라서 커패시터는 고주파 교류에 대해 도선과 유사한 낮은 임피던스를 나타낸다. 그러나 두 금속판 사이로 전자가 직접 이동하는 것은 아니며, 변위전류가 전도전류와 연속성을 이룬다.

### 한 가지 중요한 질문

**커패시터가 완전히 충전되지도 못하는데, 왜 주파수가 높아질수록 더 큰 전류가 흐를 수 있을까요?**

핵심은 커패시터에 저장된 전하량 QQ 자체가 아니라, **전하량의 시간에 대한 변화율 dQ/dtdQ/dt** 이 전류를 결정한다는 점입니다.

i=dQdt=Cdvdti=dtdQ​=Cdtdv​​

주파수가 높으면 전하량의 변화 폭이 작더라도 그 변화가 매우 짧은 시간에 일어날 수 있습니다.

다만 전류가 실제로 증가하는 정도는 전원과 직렬저항 등 전체 회로의 조건에 따라 달라집니다.