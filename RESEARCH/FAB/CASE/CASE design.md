
![Inventor 전면 커버](Pasted%20image%2020261031040029.png)

![[Pasted image 20261031040029.png]]


![tt](Pasted image 20261031040029.png)



![[Pasted image 20261031033637.png]]

D:\__PROJECTed\__KIS\__AI\megacom\AI_waytogo  

ESP32에 BNO085 IMU 센서를 연결하는 회로와 ROS2 Humble 예제 코드를 알려주세요.
  

인벤터 커버 제작

# Autodesk Inventor를 이용한 SLAM 자율주행카트 전면 커버 제작

SLAM 자율주행카트의 **전면 커버를 Autodesk Inventor에서 3D 모델링하는 방법**을 설명하겠습니다.

기존에 설계한 150 × 200mm 크기의 메카넘 휠 자율주행카트를 기준으로 합니다.

## 1. 전면 커버 설계 치수

전면 커버는 알루미늄 판금을 절곡하여 제작하는 방식으로 설계합니다.

|항목|치수|
|---|---|
|커버 전체 폭|150mm|
|커버 높이|80mm|
|커버 깊이|30mm|
|판재 두께|2mm|
|재질|알루미늄 5052|
|절곡 각도|90°|
|모서리 라운드|R5|
|체결 구멍|Ø4.5mm|
|체결 방식|M4 볼트|

※ 위 치수는 초기 설계 예시이며, 실제 차체 및 센서 배치에 따라 조정해야 합니다.

## 2. Inventor에서 커버 제작 과정

### STEP 1. 새 판금 파일 생성

Inventor를 실행합니다.

1. 파일(File) → 새로 만들기(New)
2. Sheet Metal.ipt 선택
3. 새 부품 파일 생성
4. 파일명: SLAM_Front_Cover.ipt

판금 환경을 사용하면 절곡과 전개도 제작이 가능합니다.

### STEP 2. 판금 두께 설정

상단 메뉴에서 다음을 선택합니다.

**Sheet Metal → Sheet Metal Defaults**

설정값:

- Thickness: 2 mm
- Bend Radius: 2 mm
- Material: Aluminum 5052

### STEP 3. 전면 커버 스케치

1. Start 2D Sketch 클릭
2. XY 평면 선택
3. Rectangle 도구 선택
4. 직사각형 작성

치수:

- 가로: 150mm
- 세로: 80mm

Dimension(D) 명령으로 치수를 입력합니다.

### STEP 4. 판금 면 생성

스케치를 완료합니다.

1. Finish Sketch
2. Face 명령 선택
3. 작성한 직사각형 선택
4. 두께 2mm 적용

전면 커버의 기본 판금 면이 생성됩니다.

### STEP 5. 좌우 측면 절곡

전면 커버 양쪽에 30mm 깊이의 측면을 만듭니다.

1. Flange 명령 선택
2. 왼쪽 수직 모서리 선택
3. Distance: 30mm
4. Angle: 90°
5. 방향 확인 후 적용
6. 오른쪽 모서리에도 반복

이렇게 하면 전면과 좌우 측면으로 구성된 U자형 커버가 만들어집니다.

### STEP 6. 체결 구멍 제작

커버를 차체에 고정하기 위한 구멍을 만듭니다.

1. 측면을 선택하고 Start 2D Sketch
2. Point 명령으로 구멍 중심 지정
3. Finish Sketch
4. Hole 명령 선택
5. 구멍 지름 4.5mm
6. 관통 구멍으로 설정

반대쪽에도 같은 방법으로 구멍을 만듭니다.

### STEP 7. 모서리 라운드 처리

커버의 날카로운 모서리를 둥글게 처리합니다.

1. Corner Round 또는 적절한 Fillet 명령 선택
2. 외곽 모서리 선택
3. Radius: 5mm
4. 적용

판금의 전개 가능성을 유지하도록 모서리 형상을 확인합니다.

---

## 3. 판금 전개도 제작

커버를 실제 가공하려면 평면 전개도가 필요합니다.

Inventor에서 다음 명령을 사용합니다.

**Sheet Metal → Create Flat Pattern**

그러면 절곡된 커버가 평면으로 펼쳐집니다.

전개도를 확인한 다음 다음 형식으로 저장할 수 있습니다.

- IPT: Inventor 3D 모델
- IDW 또는 DWG: 제작 도면
- DXF: 레이저 절단용 전개도
- STEP: 다른 CAD 프로그램과 공유

전개도 크기는 절곡 반경, 판 두께, K-factor에 따라 달라지므로 단순히 측면 길이를 더해서 결정하지 않습니다.

---

## 4. SLAM 카트 전면 커버 설계 시 고려사항

전면 커버에는 다음 부품이 설치될 수 있습니다.

|부품|설치 위치|
|---|---|
|초음파센서|전면 중앙|
|USB 카메라|전면 상단|
|전원 스위치|측면|
|상태 표시 LED|전면|
|M4 고정 볼트|좌우 측면|

카메라와 초음파센서의 구멍은 실제 사용하는 제품의 외형 치수와 고정 위치를 확인한 후 추가하는 것이 좋습니다.

---

## 5. 다음 제작 단계

현재 설계는 **150mm × 80mm 전면판에 좌우 30mm 절곡부가 있는 커버**입니다.

실제 SLAM 카트 외형 제작을 위해서는 다음 중 어떤 형태인지 결정해야 합니다.

**① 전면 커버만 제작**  
전면판과 좌우 절곡부로 구성된 U자형 판금 커버

**② 상부까지 덮는 커버 제작**  
전면·좌우 측면·상부를 포함하는 보호 커버

**③ SLAM 카트 전체 외형 커버 제작**  
Jetson Orin Nano, 배터리, 카메라, LiDAR를 보호하는 전체 케이스

**어느 형태를 Inventor로 제작하시겠습니까?** 선택하시면 해당 형태의 스케치 치수와 Inventor 명령 순서를 구체적으로 설명하겠습니다.

인벤터 재질에 알루미늄5052가 없다?

Autodesk Inventor에서 **Aluminum 5052(알루미늄 5052)** 재질이 목록에 없는 경우가 있습니다. Inventor 버전이나 재질 라이브러리에 따라 제공되는 재질이 다르기 때문입니다.

SLAM 카트의 판금 커버를 제작하려면 다음 두 가지 방법이 있습니다.

## 1. 가장 간단한 방법: 일반 알루미늄 선택

Inventor에서 다음 순서로 진행합니다.

1. Sheet Metal.ipt 파일을 엽니다.
2. 상단의 **Material(재질)** 선택 메뉴를 클릭합니다.
3. 검색창에 Aluminum을 입력합니다.
4. Aluminum 또는 Aluminum 6061을 선택합니다.
5. 판금 두께를 2mm로 설정합니다.

**단, Aluminum 6061과 Aluminum 5052는 서로 다른 재질입니다.** 외형 모델링 단계에서는 임시로 사용할 수 있지만, 실제 판금 제작용 도면에는 5052를 명시해야 합니다.

## 2. Aluminum 5052 재질 직접 등록하기

실제 제작용으로는 사용자 정의 재질을 만드는 것이 좋습니다.

### STEP 1. 재질 편집기 실행

Inventor 상단 메뉴에서 다음을 선택합니다.

Tools(도구) → Material(재질)

또는 상단 재질 선택 메뉴에서 재질 브라우저를 엽니다.

### STEP 2. 기존 알루미늄 재질 복사

1. Aluminum 재질을 찾습니다.
2. 해당 재질을 복제합니다.
3. 이름을 Aluminum 5052-H32로 변경합니다.
4. 사용자 정의 재질 라이브러리 또는 문서에 저장합니다.

### STEP 3. 재질 특성 입력

5052-H32 알루미늄의 대표적인 물성값은 다음과 같습니다.

|항목|값|
|---|---|
|재질명|Aluminum 5052-H32|
|밀도|2.68 g/cm³|
|탄성계수|약 70.3 GPa|
|포아송비|0.33|
|항복강도|약 193 MPa|
|인장강도|약 228 MPa|
|판금 두께|2mm|

위 값은 대표적인 참고값이며, 실제 설계에서는 공급 판재의 규격과 인증 물성값을 확인해야 합니다.

재질 편집기의 물리적 특성 항목에 값을 입력한 후 저장합니다.

## 3. 판금 절곡 설정

SLAM 카트 전면 커버를 제작한다면 다음과 같이 설정할 수 있습니다.

**Sheet Metal → Sheet Metal Defaults**

|설정|값|
|---|---|
|Material|Aluminum 5052-H32|
|Thickness|2mm|
|Bend Radius|2mm|
|Bend Angle|90°|
|Unfold Rule|기본값으로 시작 후 가공업체 기준으로 조정|

특히 **5052-H32는 일반적으로 6061-T6보다 절곡 가공에 적합**하므로 판금 커버 제작에 많이 사용됩니다.

---

### 확인할 사항

현재 Inventor에서 알루미늄 재질이 다음 중 어떤 상태인가요?

**①** Aluminum은 있는데 Aluminum 5052가 없다.

**②** Aluminum 6061만 있다.

**③** 재질 목록에 알루미늄 자체가 없다.

**④** 재질을 새로 추가하는 메뉴를 찾을 수 없다.

번호를 알려주시면 **Inventor에서 Aluminum 5052-H32를 직접 등록하는 과정을 메뉴별로 설명**하겠습니다.

판금두께가 2mm 적당한가

네. **SLAM 자율주행카트의 전면 커버를 알루미늄 5052-H32로 제작한다면 판금 두께 2mm는 적당합니다.** 다만 커버의 용도에 따라 1.5mm도 충분할 수 있습니다.

### 1. 판금 두께 비교

|항목|1.0mm|1.5mm|2.0mm|3.0mm|
|---|---|---|---|---|
|무게|매우 가벼움|가벼움|보통|무거움|
|강성|낮음|보통|높음|매우 높음|
|절곡 가공|쉬움|쉬움|쉬움|보통|
|진동 저항|낮음|양호|우수|우수|
|가공 비용|낮음|보통|보통|높음|
|전면 커버 적합성|△|◎|◎|△|

### 2. SLAM 카트 전면 커버 무게 계산

기존 설계 치수는 다음과 같습니다.

- 전면 폭: 150mm
- 높이: 80mm
- 좌우 절곡 깊이: 30mm
- 재질: Aluminum 5052-H32
- 밀도: 2.68g/cm³

절곡부를 포함한 판재의 면적은 다음과 같습니다.

A=(150×80)+(30×80×2)A=(150×80)+(30×80×2)A=16,800 mm2A=16,800 mm2

**두께 2mm인 경우**

V=16,800×2=33,600 mm3V=16,800×2=33,600 mm3m=33.6×2.68=90.05gm=33.6×2.68=90.05g

따라서 전면 커버의 무게는 약 **90g**입니다.

|판금 두께|예상 무게|
|---|--:|
|1.0mm|45g|
|1.5mm|68g|
|2.0mm|90g|
|3.0mm|135g|

※ 절곡에 따른 전개 길이 변화, 구멍 및 모서리 가공은 제외한 근사값입니다.

### 3. SLAM 카트에 권장하는 두께

현재 제작하는 카트는 다음 부품을 탑재하는 구조입니다.

- Jetson Orin Nano
- LiDAR
- USB 카메라
- 배터리
- 메카넘 휠 4개
- JGB37-520 DC 모터 4개

이러한 구조에서는 부품별로 판금 두께를 다르게 적용하는 것이 좋습니다.

|부품|권장 두께|
|---|---|
|하부 섀시|2.0~3.0mm|
|전면 커버|**2.0mm**|
|좌우 측면 커버|1.5~2.0mm|
|상부 커버|1.5~2.0mm|
|Jetson 고정 브래킷|2.0mm|
|모터 고정 브래킷|3.0mm 또는 별도 보강|

모터 고정부와 하부 섀시는 실제 하중과 체결 구조에 따라 강도 검토가 필요합니다.

### 4. Inventor 설정 권장값

현재 전면 커버를 모델링한다면 다음과 같이 설정하십시오.

|항목|설정값|
|---|---|
|Material|Aluminum 5052-H32|
|Thickness|**2mm**|
|Bend Radius|2mm|
|Bend Angle|90°|
|Corner Relief|Round|
|K-Factor|0.4 (초기값)|

K-Factor는 실제 절곡 금형과 가공 조건에 따라 조정해야 합니다.

---

### 결론

**전면 커버는 2mm 알루미늄 5052-H32를 권장합니다.**

다만 한 가지 중요한 점이 있습니다.

현재 설계하는 커버가 **① 외형 보호만 하는 커버**인지, 아니면 **② Jetson Orin Nano와 LiDAR 등을 직접 고정하는 구조물**인지에 따라 적절한 두께가 달라집니다.

①이라면 1.5mm도 충분할 가능성이 높고, ②라면 2mm 이상에 보강 구조를 검토하는 것이 좋습니다.
# ESP32 + BNO085 IMU + ROS2 Humble 연결 및 예제

현재 제작 중인 SLAM 자율주행 카트에서는 **ESP32가 BNO085 IMU 센서의 데이터를 읽고, Wi-Fi를 통해 Jetson Orin Nano의 ROS2 Humble로 전송**하는 구성을 추천합니다.

이번 예제는 micro-ROS 대신 **UDP 통신**을 사용합니다. 별도의 micro-ROS Agent 없이 ESP32와 Jetson을 연결할 수 있어 초기 시험에 간단합니다.

## 1. 전체 시스템 구성

**BNO085 IMU 센서**

가속도 · 각속도 · 회전 Quaternion

I2C (SDA, SCL)

**ESP32**

IMU 측정 및 UDP 데이터 송신

Wi-Fi UDP (100 Hz 목표)

**Jetson Orin Nano · ROS2 Humble**

Python UDP 수신 노드

/imu/data

**robot_localization (EKF)**

IMU + 모터 엔코더 Odometry 융합

## 2. ESP32와 BNO085 연결 회로

일반적인 ESP32 DevKit V1 기준입니다.

|BNO085 핀|ESP32 핀|설명|
|---|---|---|
|VIN|3V3|전원|
|GND|GND|공통 접지|
|SDA|GPIO21|I2C 데이터|
|SCL|GPIO22|I2C 클록|
|INT|연결 안 함|기본 예제에서 미사용|
|RST|연결 안 함|기본 예제에서 미사용|

주의: 위 연결은 3.3V 전원과 I2C를 지원하는 BNO085 브레이크아웃 모듈 기준입니다. 보드에 따라 VIN, PS0, PS1, 풀업 저항 조건이 다르므로 실제 모듈의 핀 사양을 확인해야 합니다.

BNO085는 카트의 중앙 부근에 수평으로 고정하고, 센서 X축이 카트 전방, Y축이 좌측, Z축이 위쪽을 향하도록 설치하는 것이 편리합니다. 실제 장착 방향이 다르면 ROS 좌표계에 맞게 변환해야 합니다.

## 3. 중요한 사항: ESP32와 BNO085의 I2C 호환성

Adafruit 공식 문서에 따르면 BNO085의 I2C 구현은 일부 상황에서 표준 I2C 동작과 달라 **ESP32 계열에서 통신 오류가 발생할 수 있습니다.** 

따라서 위의 I2C 배선은 시험용으로 사용하고, 초기화 실패나 데이터 끊김이 발생하면 BNO085의 SPI 인터페이스로 변경하는 것이 좋습니다.

아래 코드는 우선 I2C로 센서 통신을 확인하는 예제입니다.

## 4. ESP32 Arduino 코드

Arduino IDE의 라이브러리 관리자에서 Adafruit BNO08x를 설치합니다. 의존 라이브러리도 함께 설치합니다.

ESP32는 센서에서 회전 Quaternion, 각속도, 가속도를 수신하고 UDP로 전송합니다.

파일: esp32_bno085_udp.ino

```

#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <Adafruit_BNO08x.h>

#define SDA_PIN 21
#define SCL_PIN 22

const char* SSID = "YOUR_WIFI";
const char* PASSWORD = "YOUR_PASSWORD";

// Jetson의 Wi-Fi IP로 변경
IPAddress jetsonIP(192, 168, 0, 100);
const uint16_t UDP_PORT = 8888;

WiFiUDP udp;
Adafruit_BNO08x bno(-1);
sh2_SensorValue_t event;

float qx=0, qy=0, qz=0, qw=1;
float gx=0, gy=0, gz=0;
float ax=0, ay=0, az=0;

bool hasQ=false, hasG=false, hasA=false;
uint32_t lastSend=0;

void enableReports() {
  bno.enableReport(SH2_GAME_ROTATION_VECTOR, 10000);
  bno.enableReport(SH2_GYROSCOPE_CALIBRATED, 10000);
  bno.enableReport(SH2_ACCELEROMETER, 10000);
}

void setup() {
  Serial.begin(115200);
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(100000);

  if (!bno.begin_I2C()) {
    Serial.println("BNO085 initialization failed");
    while (true) delay(1000);
  }

  enableReports();

  WiFi.mode(WIFI_STA);
  WiFi.begin(SSID, PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println(WiFi.localIP());
  udp.begin(UDP_PORT);
}

void loop() {
  if (bno.wasReset()) {
    enableReports();
  }

  // 모든 대기 이벤트 읽기
  while (bno.getSensorEvent(&event)) {
    switch (event.sensorId) {
      case SH2_GAME_ROTATION_VECTOR:
        qx = event.un.gameRotationVector.i;
        qy = event.un.gameRotationVector.j;
        qz = event.un.gameRotationVector.k;
        qw = event.un.gameRotationVector.real;
        hasQ = true;
        break;

      case SH2_GYROSCOPE_CALIBRATED:
        gx = event.un.gyroscope.x;
        gy = event.un.gyroscope.y;
        gz = event.un.gyroscope.z;
        hasG = true;
        break;

      case SH2_ACCELEROMETER:
        ax = event.un.accelerometer.x;
        ay = event.un.accelerometer.y;
        az = event.un.accelerometer.z;
        hasA = true;
        break;
    }
  }

  // 50 Hz 송신 (20 ms)
  if (millis() - lastSend >= 20) {
    lastSend = millis();

    if (hasQ && hasG && hasA &&
        WiFi.status() == WL_CONNECTED) {
      char packet[180];

      snprintf(packet, sizeof(packet),
        "%.6f,%.6f,%.6f,%.6f,"
        "%.6f,%.6f,%.6f,"
        "%.6f,%.6f,%.6f",
        qx,qy,qz,qw,gx,gy,gz,ax,ay,az);

      udp.beginPacket(jetsonIP, UDP_PORT);
      udp.print(packet);
      udp.endPacket();
    }
  }

  delay(1);
}
```

이 코드는 SH2_GAME_ROTATION_VECTOR를 사용하므로 자기장 기반 절대 방위각 대신 상대 회전 자세를 제공합니다. 실내 SLAM에서는 자기장 간섭을 피하는 데 유리하지만 yaw 드리프트는 발생할 수 있습니다.

또한 50Hz는 UDP 송신 목표 주기이며, 실제 센서 데이터 갱신 주기 및 통신 지연은 별도로 확인해야 합니다.

## 5. Jetson Orin Nano ROS2 Humble 수신 코드

Jetson에서 IP 주소를 확인합니다.

```
hostname -I
```

표시된 Jetson의 IP를 ESP32 코드의 jetsonIP에 입력합니다.

이후 Python 수신 노드를 만듭니다.

파일: imu_udp_node.py

`#!/usr/bin/env python3 import socket import math import rclpy from rclpy.node import Node from sensor_msgs.msg import Imu class IMUNode(Node): def __init__(self): super().__init__('imu_udp_node') self.pub = self.create_publisher( Imu, '/imu/data', 10 ) self.sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM ) self.sock.bind(('0.0.0.0', 8888)) self.sock.setblocking(False) self.timer = self.create_timer( 0.01, self.receive_data ) self.get_logger().info( 'IMU UDP receiver started' ) def receive_data(self): # 대기 중인 최신 패킷 사용 latest = None for _ in range(20): try: latest, addr = self.sock.recvfrom(1024) except BlockingIOError: break if latest is None: return try: values = [ float(x) for x in latest.decode().strip().split(',') ] if len(values) != 10: return if not all(math.isfinite(v) for v in values): return qx,qy,qz,qw,gx,gy,gz,ax,ay,az = values norm = math.sqrt( qx*qx + qy*qy + qz*qz + qw*qw ) if norm < 0.5 or norm > 1.5: return msg = Imu() msg.header.stamp = ( self.get_clock().now().to_msg() ) msg.header.frame_id = 'imu_link' msg.orientation.x = qx / norm msg.orientation.y = qy / norm msg.orientation.z = qz / norm msg.orientation.w = qw / norm msg.angular_velocity.x = gx msg.angular_velocity.y = gy msg.angular_velocity.z = gz msg.linear_acceleration.x = ax msg.linear_acceleration.y = ay msg.linear_acceleration.z = az # 초기 시험용 공분산 추정값 msg.orientation_covariance = [ 0.01,0,0, 0,0.01,0, 0,0,0.04 ] msg.angular_velocity_covariance = [ 0.0025,0,0, 0,0.0025,0, 0,0,0.0025 ] msg.linear_acceleration_covariance = [ 0.04,0,0, 0,0.04,0, 0,0,0.04 ] self.pub.publish(msg) except (ValueError, UnicodeDecodeError) as e: self.get_logger().warning(str(e)) def destroy_node(self): self.sock.close() super().destroy_node() def main(): rclpy.init() node = IMUNode() try: rclpy.spin(node) except KeyboardInterrupt: pass finally: node.destroy_node() rclpy.shutdown() if __name__ == '__main__': main()`

ROS2의 sensor_msgs/msg/Imu 메시지는 Quaternion, rad/s 단위 각속도, m/s² 단위 가속도를 사용합니다. 

위 공분산 값은 예시이므로 실제 측정 노이즈를 바탕으로 조정해야 합니다. 또한 센서 데이터가 ENU 좌표계와 일치하도록 장착 방향 및 초기 기준을 확인해야 합니다.

## 6. ROS2 실행 방법

Jetson에서 다음 명령을 실행합니다.

```
source /opt/ros/humble/setup.bash

python3 imu_udp_node.py
```

다른 터미널에서 확인합니다.

```
source /opt/ros/humble/setup.bash

ros2 topic list
ros2 topic echo /imu/data
ros2 topic hz /imu/data
```

정상 동작하면 다음과 같은 토픽이 생성됩니다.

`/imu/data`

센서를 Z축 기준으로 회전시키면 angular_velocity.z 값이 변하고, Quaternion 값도 함께 변화해야 합니다.

## 7. SLAM Toolbox에 IMU 적용

SLAM Toolbox에 IMU를 직접 연결하는 것이 아니라, 일반적으로 robot_localization의 EKF로 엔코더 오도메트리와 IMU를 융합합니다.

```
sudo apt install ros-humble-robot-localization
```

최소 구성 예시는 다음과 같습니다.

파일: ekf.yaml

```

ekf_filter_node:
  ros__parameters:
    frequency: 30.0
    two_d_mode: true

    map_frame: map
    odom_frame: odom
    base_link_frame: base_link
    world_frame: odom

    publish_tf: true

    odom0: /wheel/odom
    odom0_config: [
      false, false, false,
      false, false, false,
      true,  true,  false,
      false, false, true,
      false, false, false
    ]

    imu0: /imu/data
    imu0_config: [
      false, false, false,
      false, false, false,
      false, false, false,
      false, false, true,
      false, false, false
    ]

    imu0_remove_gravitational_acceleration: false
```

이 설정은 IMU의 Z축 각속도와 엔코더의 평면 속도만 융합합니다. 초기에는 절대 yaw와 가속도 융합을 제외하여 설정을 단순화했습니다.

```
ros2 run robot_localization ekf_node \
  --ros-args --params-file ekf.yaml
```

출력 토픽은 다음과 같습니다.

`/odometry/filtered`

이 토픽을 SLAM Toolbox의 오도메트리 입력으로 사용하도록 TF 구성을 설정하면 됩니다. odom → base_link 변환을 여러 노드가 동시에 발행하지 않도록 주의해야 합니다.

## 8. 실제 카트 적용 시 확인할 사항

1. ESP32와 Jetson이 동일한 Wi-Fi 네트워크에 연결되어 있어야 합니다.
2. BNO085의 센서 좌표축을 ROS imu_link 좌표계와 맞춰야 합니다.
3. UDP는 패킷 손실 가능성이 있으므로 실제 자율주행에서는 데이터 시각, 유효기간 및 통신 끊김 감지를 추가해야 합니다.
4. 위 예제의 시간은 Jetson 수신 시각입니다. 정확한 센서 융합에는 ESP32 측 측정 타임스탬프와 시간 동기화가 필요합니다.
5. wheel/odom은 실제 엔코더 기반 오도메트리 노드가 별도로 발행해야 합니다.

**현재 SLAM 카트에 대한 추천:** 먼저 BNO085 → ESP32 → /imu/data까지 정상 동작을 확인하고, 이후 JGB37-520 모터 4개의 엔코더 데이터를 이용해 메카넘 휠 오도메트리를 구현하는 순서가 좋습니다.

특히 BNO085와 ESP32 조합에서는 I2C 통신 안정성이 문제가 될 수 있으므로, 실제 제작용 PCB에서는 **SPI 연결을 고려하는 것이 더 안전합니다.**

**1. 용역명**:

**2. 과업의 목적 및 필요성**

-,,,슬램카트ㅡㅡ외형제작에 필요한 과업지시서 작성하라

-

**3. 과업기간**:

**4. 규격 및 수량**

-

-

-

**5. 제작 방법 및 상세 내용**

-

-

-

-

-

**5. 활용방안**

-

-

**6. 기타**

-

-

…

# SLAM 자율주행 카트 외형 제작 과업지시서

**1. 용역명**

- SLAM 기반 자율주행 카트의 외형 및 기구 구조물 설계·제작 용역
    

**2. 과업의 목적 및 필요성**

- 본 과업은 SLAM(Simultaneous Localization and Mapping) 기반 실내 자율주행 카트의 개발을 위하여 차체 프레임 및 외형 구조물을 설계·제작하는 것을 목적으로 한다.
    
- Jetson Orin Nano, LiDAR, 카메라, IMU 센서, 모터 구동장치 및 배터리 등을 안정적으로 장착할 수 있는 기구 구조물 제작이 필요하다.
    
- 메카넘 휠(Mecanum Wheel) 4개를 적용하여 전후진, 좌우 이동 및 제자리 회전이 가능한 이동형 플랫폼을 구현하고자 한다.
    
- 향후 SLAM 지도 작성, 장애물 회피 및 자율주행 알고리즘의 성능 검증에 활용할 수 있는 시제품을 확보하고자 한다.
    

**3. 과업기간**

- 계약일로부터 30일 이내(협의 가능)
    

**4. 규격 및 수량**

- 제작 수량: SLAM 자율주행 카트 외형 및 차체 구조물 1식
    
- 차체 기본 크기: 약 150 × 200 mm(가로 × 세로), 세부 치수는 부품 배치에 따라 조정 가능
    
- 차체 재질: 알루미늄 판재(AL5052 등), 두께 약 2.0~3.0 mm
    
- 제작 방식: 알루미늄 판금 절단 및 절곡 가공
    
- 구동 방식: 직경 80 mm 메카넘 휠 4개 및 DC 기어드 모터 4개 장착 구조
    
- 설계 하중: 탑재 장비를 포함한 총중량 약 5 kg 기준
    
- 장착 대상: Jetson Orin Nano, LiDAR, 카메라, ESP32 제어보드, 모터 드라이버, 배터리 및 기타 센서류
    

**5. 제작 방법 및 상세 내용**

- **차체 구조 설계**
    
    - 3D CAD를 활용하여 SLAM 카트의 차체 프레임 및 외형 구조를 설계한다.
        
    - 알루미늄 판재를 절곡한 일체형 또는 조립형 프레임 구조를 적용한다.
        
    - 전자장치의 장착, 배선 및 유지보수가 용이하도록 구조를 설계한다.
        
- **모터 및 메카넘 휠 장착 구조 제작**
    
    - JGB37-520 DC 기어드 모터 4개를 장착할 수 있는 고정 브래킷 및 체결 구조를 제작한다.
        
    - 메카넘 휠의 전후좌우 배치와 회전 시 간섭이 발생하지 않도록 설계한다.
        
    - 모터의 진동 및 구동 하중을 고려하여 충분한 구조적 강성을 확보한다.
        
- **전자장치 및 센서 장착부 제작**
    
    - Jetson Orin Nano 및 ESP32 제어보드의 고정용 브래킷과 체결 홀을 구성한다.
        
    - LiDAR 센서의 수평 설치 및 주변 장애물 감지가 가능하도록 상단 장착부를 설계한다.
        
    - 카메라와 IMU 센서의 설치 위치를 고려하여 센서 장착 공간을 확보한다.
        
    - 배터리 고정 구조와 전원 및 통신 배선용 공간을 확보한다.
        
- **판금 가공 및 조립**
    
    - 설계도면에 따라 알루미늄 판재를 레이저 절단 또는 CNC 가공한다.
        
    - 절곡 및 체결 홀 가공을 수행하고 날카로운 모서리는 디버링 처리한다.
        
    - 볼트 및 너트를 이용하여 조립과 분해가 가능한 구조로 제작한다.
        
    - 필요시 표면 아노다이징 또는 도장 처리를 적용한다.
        
- **제작품 검증 및 납품**
    
    - 외형 치수, 체결 위치 및 조립 상태를 확인한다.
        
    - 모터, 휠 및 주요 전자장치의 장착 적합성을 검토한다.
        
    - 바퀴 회전 간섭, 차체 강성 및 장비 배치 안정성을 확인한다.
        
    - 최종 제작품과 2D 제작도면, 3D CAD 파일을 납품한다.
        

**6. 활용방안**

- ROS2 기반 SLAM 지도 작성 및 자율주행 알고리즘의 실험용 이동 플랫폼으로 활용한다.
    
- LiDAR, 카메라, IMU 및 모터 엔코더를 이용한 위치 추정, 장애물 회피 및 메카넘 휠 이동제어 기술 개발에 활용한다.
    
- 향후 실내 자율주행 로봇 및 소형 물류 이송 로봇의 시제품 개발을 위한 기초 플랫폼으로 활용한다.
    

**7. 기타**

- 최종 외형 치수와 장착 홀 위치는 실제 적용 부품의 규격을 확인한 후 발주처와 협의하여 확정한다.
    
- 제작 과정에서 구조 변경이 필요한 경우 발주처와 사전 협의하여 반영한다.
    
- 납품 시 최종 조립품, 제작도면 및 부품 장착 관련 자료를 함께 제출한다.
    
- 제작 완료 후 확인된 가공 불량 및 조립 불량에 대해서는 협의를 통해 보완한다.
    

본 과업지시서는 **외형 및 기구 구조물 제작 용역**을 기준으로 작성하였습니다. 따라서 Jetson, 모터, LiDAR 등의 전자부품 구매와 자율주행 소프트웨어 개발은 과업 범위에서 제외하고, 해당 부품의 장착 구조 설계 및 가공에 중점을 두었습니다.

실제 발주 시에는 차체 크기 150 × 200 mm에 모든 부품이 들어가는지 확인한 후 최종 치수를 확정하는 것이 좋습니다.

대략적인 제조 도면 작성하라

# SLAM 자율주행 카트 개략 제조도면

기존 과업지시서를 기준으로 **알루미늄 절곡형 차체와 4륜 메카넘 휠 구조**의 개략 제조도면을 작성하겠습니다.

|항목|설계 기준|
|---|---|
|차체 크기|200(L) × 150(W) mm|
|차체 재질|AL5052, 두께 2 mm|
|차체 구조|바닥판 + 양측 절곡부|
|메카넘 휠|Ø80 mm × 4개|
|모터|JGB37-520 × 4개|
|탑재 장비|Jetson Orin Nano, LiDAR, 카메라, 배터리, ESP32|
|설계 총중량|약 5 kg|

도면은 상면도, 측면도, 정면도 및 판금 전개도를 포함하며, 치수 단위는 mm입니다. 모터 고정홀과 전자장치 장착홀은 실제 부품 실측 후 최종 확정하는 조건입니다.

## 제조도면 초안

도면 확인 및 인쇄용

수정 가능한 도면

이 도면은 **제작업체와 협의하기 위한 개략 설계도**입니다. 상면도에는 주요 부품의 배치, 측면도에는 바퀴와 차체 구조, 정면도에는 절곡 형태를 표시했습니다.

실제 판금 제작을 의뢰하려면 다음 사항을 확정해야 합니다.

- JGB37-520 모터 브래킷 체결홀 위치와 축 높이
- Jetson Orin Nano 및 배터리의 실제 장착 치수
- 절곡 반경, 절곡 여유 및 전개 치수
- 메카넘 휠과 차체 사이의 간섭 여부

특히 **150 × 200 mm 차체에 모든 부품이 들어가는지** 실물 치수로 확인해야 합니다. 현재 도면의 부품 배치는 개념적 위치이며, 확정된 가공 치수는 아닙니다.

SLAM_cart_concept_drawing.png이미지SLAM_cart_concept_drawing.svg이미지

![사용자 첨부 파일](blob:https://chatgpt.com/a62f54ab-eda8-4baf-8487-83511b105cd8)

사진을 참고로 하는 대략적인 도면 작성하라

원가계산서 작성하라,,,1800만원 상당의 용역 계약임

# SLAM 자율주행 카트 외형 설계·제작 용역 원가계산서

**계약금액 18,000,000원(부가가치세 포함)**을 기준으로, 앞서 작성한 SLAM 카트 제조도면과 과업지시서를 반영하여 원가계산서를 작성하겠습니다.

본 용역은 단순 판금 제작이 아니라 **기구설계, 3D CAD 설계, 제작도면 작성, 알루미늄 판금 가공, 모터 브래킷 제작, 시제품 조립 및 검증**을 포함하는 기술용역으로 구성합니다.

## 1. 용역비 총괄

|구분|금액|
|---|---|
|재료비|3,200,000원|
|노무비|8,000,000원|
|경비|2,000,000원|
|일반관리비|1,000,000원|
|이윤|2,163,636원|
|**공급가액**|**16,363,636원**|
|부가가치세(10%)|1,636,364원|
|**계약금액 합계**|**18,000,000원**|

위 금액은 계약 예산에 맞춘 **예시 원가 배분안**으로, 실제 견적·노임단가·계약 방식에 따라 조정해야 합니다. 특히 공공기관 제출용이라면 적용되는 원가계산 기준과 일반관리비·이윤 요율을 별도로 검토해야 합니다.

## 2. 세부 원가계산 내역서

단위: 원 / 부가가치세 별도

|구분|세부 산출내역|금액|
|---|---|---|
|재료비|AL5052 판재 및 구조재|650,000|
||모터 브래킷 및 고정 부품|800,000|
||LiDAR·카메라 장착 구조물|450,000|
||상판·측판 및 보강 부품|700,000|
||볼트, 너트, 체결 부품 등|250,000|
||가공 소모품 및 부자재|350,000|
|**재료비 소계**||**3,200,000**|
|노무비|기구 구조 설계(8인일 × 300,000)|2,400,000|
||3D CAD 및 제작도면(6인일 × 300,000)|1,800,000|
||판금·절곡 가공 작업(6인일 × 250,000)|1,500,000|
||기구 조립 및 부품 장착(5인일 × 250,000)|1,250,000|
||시제품 검사 및 수정(3인일 × 350,000)|1,050,000|
|**노무비 소계**||**8,000,000**|
|경비|레이저 절단 및 CNC 장비 사용료|750,000|
||절곡·표면처리 외주가공비|550,000|
||시제품 조립·검사용 장비 사용료|350,000|
||운송 및 납품비|200,000|
||설계 출력 및 기타 경비|150,000|
|**경비 소계**||**2,000,000**|
|일반관리비|사업관리 및 행정관리 비용|1,000,000|
|이윤|계약금액 조정분 포함|2,163,636|
|**공급가액 합계**||**16,363,636**|
|부가가치세|10%, 원 단위 반올림|1,636,364|
|**총 계약금액**||**18,000,000**|

## 3. 계약 범위 및 납품 조건

본 원가계산서는 다음의 제작 범위를 전제로 합니다.

- SLAM 카트 외형 및 기구설계 1식
- 3D CAD 모델 및 2D 판금 제작도면 1식
- 알루미늄 차체, 상판, 측판 및 모터 브래킷 제작 1식
- LiDAR·카메라·제어보드 장착 구조물 제작 1식
- 시제품 조립, 치수 검사 및 수정 보완 1식
- 최종 조립품과 제작도면 납품

**계약 범위 제외:** Jetson Orin Nano, LiDAR, 카메라, 메카넘 휠, 모터, 배터리 등 주요 전자·구동 부품의 구매비와 SLAM 소프트웨어 개발비는 포함하지 않았습니다.

## 4. 원가계산 시 유의사항

18,000,000원 규모의 외형 제작 용역은 일반적인 소형 판금 제작비와 비교하면 상당한 금액이므로, 설계 개발과 시제품 제작·검증에 필요한 기술인력 투입 및 작업 범위를 명확히 하는 것이 중요합니다.

특히 실제 계약서에는 설계도면의 종류, 제작 수량, 수정 횟수, 검사 항목 및 납품물을 구체적으로 명시하는 것이 좋습니다.

현재 원가계산서의 금액은 예산 배분을 위한 추정치입니다. **실제 발주용 원가계산서에는 견적서, 노무 투입 근거 및 외주가공비 증빙을 반영**해야 합니다.

이윤을 제외한 비용 계산

# SLAM 자율주행 카트 외형 제작 용역 원가계산서 (이윤 제외)

기존 계약금액 **18,000,000원(VAT 포함)**을 기준으로 이윤 2,163,636원을 제외하면 다음과 같습니다.

## 1. 이윤 제외 원가계산

|구분|금액(원)|
|---|---|
|재료비|3,200,000|
|노무비|8,000,000|
|경비|2,000,000|
|일반관리비|1,000,000|
|**공급가액 합계**|**14,200,000**|
|부가가치세(10%)|1,420,000|
|**총금액(VAT 포함)**|**15,620,000**|

따라서 기존 원가 항목을 유지하고 이윤만 제외한 총금액은 **15,620,000원**입니다.

## 2. 계약금액 1,800만원을 유지하면서 이윤을 제외하는 경우

이윤 항목을 없애고 재료비·노무비·경비·일반관리비로 전체 계약금액을 구성하려면 다음과 같은 예산 배분이 가능합니다.

|구분|금액(원)|
|---|---|
|재료비|3,700,000|
|노무비|9,500,000|
|경비|2,000,000|
|일반관리비|1,163,636|
|이윤|0|
|**공급가액 합계**|**16,363,636**|
|부가가치세(10%)|1,636,364|
|**총 계약금액**|**18,000,000**|

**추천:** 1,800만원 계약금액을 유지해야 한다면 두 번째 표를 예산 편성 초안으로 활용할 수 있습니다. 다만 증액된 재료비와 노무비는 실제 설계·제작 작업량 및 견적 근거로 뒷받침되어야 합니다. 이윤을 다른 비용 항목으로 단순 전가해서는 안 되며, 적용 계약 규정에 따라 이윤 별도 계상이 필요한지도 확인해야 합니다.

계약금액 1,800만원을 유지하면서 이윤을 제외하는 경우에 대해서 엑셀표를 작성하라

**SLAM 자율주행 카트 외형 제작 용역 원가계산서**를 엑셀 파일로 작성했습니다.

**SLAM 카트 원가계산서.xlsx**

이윤 제외 · 부가세 포함 1,800만원

## 원가계산 요약

|구분|금액|
|---|---|
|재료비|3,700,000원|
|노무비|9,500,000원|
|경비|2,000,000원|
|일반관리비|1,163,636원|
|이윤|0원|
|**공급가액**|**16,363,636원**|
|부가가치세|1,636,364원|
|**총 계약금액**|**18,000,000원**|

엑셀에는 공급가액, 부가가치세, 계약금액을 **자동 계산하는 수식**을 넣었습니다. 재료비나 노무비를 변경하면 합계가 자동으로 변경됩니다.

실제 계약 제출 시에는 각 비용의 산출 근거와 적용 계약 기준을 확인해야 합니다.

SLAM_카트_원가계산서_1800만원_이윤제외.xlsxExcel

  

⋮⋮⋮⋮
