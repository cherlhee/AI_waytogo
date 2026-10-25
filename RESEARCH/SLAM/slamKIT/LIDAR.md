

1. LiDAR 모델별 전원 사양

|LiDAR 모델|공급전압|소비전류(대략)|
|---|---|---|
|RPLIDAR A1|5V|0.2~0.5A|
|RPLIDAR A2|5V|0.5A 내외|
|RPLIDAR A3|5V|1A 내외|
|YDLIDAR X2|5V|0.3~0.5A|
|YDLIDAR X4|5V|0.5A 내외|
|YDLIDAR G4|5V|0.5~1A|


Jetson Orin Nano + ROS2 Humble 기반 SLAM 로봇에는 **SLAMTEC RPLIDAR A1M8**을 추천합니다.

![[Pasted image 20261025101144.png]]

|항목|사양|
|---|---|
|모델명|**RPLIDAR A1M8**|
|제조사|SLAMTEC|
|전원|DC 5V|
|연결|USB 어댑터를 통해 Jetson 연결|
|측정거리|최대 약 12m|
|스캔 범위|360°|
|ROS2 Humble|지원|
|용도|실내 SLAM, 장애물 감지|


### 추천 이유

1. Jetson Orin Nano에 USB로 연결 가능
2. 별도 전원회로 없이 사용 가능
3. ROS2 드라이버 제공
4. `slam_toolbox`와 연동 가능
5. 실내 자율주행 로봇에 적합

**구매 시에는 RPLIDAR A1M8 본체와 USB 어댑터가 포함된 키트**를 선택하세요.

제조사: [SLAMTEC 공식 홈페이지](https://www.slamtec.com?utm_source=chatgpt.com)

**결론:** 현재 제작하시는 15×20cm 메카넘 휠 SLAM 로봇에는 **RPLIDAR A1M8**이 간단하고 적합한 선택입니다.