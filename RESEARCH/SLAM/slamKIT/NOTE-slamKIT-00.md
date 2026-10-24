


  

이전 메시지 불러오는 중…

#include <Arduino.h> #include "FaBoPWM_PCA9685.h" FaBoPWM faboPWM; void setAllPWM(int pwm) { for (int ch = 0; ch < 4; ch++) { faboPWM.set_channel_value(ch, pwm); } } void setup() { Serial.begin(115200); if (!faboPWM.begin()) { Serial.println("PCA9685 not found"); while (1); } Serial.println("PCA9685 found"); faboPWM.init(307); faboPWM.set_hz(50); } void loop() { // setAllPWM(1500); // delay(2000); // setAllPWM(1340); // delay(6000); // setAllPWM(2507); // delay(2000); // setAllPWM(3300); // delay(6000); faboPWM.set_channel_value(0, 800); delay(2000); faboPWM.set_channel_value(0, 0); delay(10000); faboPWM.set_channel_value(2, 800); delay(2000); faboPWM.set_channel_value(2, 0); delay(10000); faboPWM.set_channel_value(3, 800); delay(2000); faboPWM.set_channel_value(3, 0); delay(10000); },,,,it detect channel 0, 1,,,,2axis,,but salmkit has 4 axes...how can i do it

…

Your **PCA9685 supports 16 PWM channels (CH0–CH15)**, so it can control all four motors of your 4WD SLAM-KIT.

However, there is an important distinction:

- **PCA9685:** Generates 16 PWM signals.
- **HR8833:** Drives DC motors using PWM and direction-control inputs.
- **JGB37-520:** Your four DC motors.

If your HR8833 board has two motor outputs (Motor A and Motor B), **one board controls two motors**. You need two such boards for four motors, provided their voltage and current ratings are sufficient.

## 1. Four-motor connection

For two-input H-bridge control, use eight PCA9685 channels:

|Motor|Position|PCA9685 channel|Driver inputs|
|---|---|---|---|
|Motor 1|Front left|CH0, CH1|Driver 1: AIN1, AIN2|
|Motor 2|Front right|CH2, CH3|Driver 1: BIN1, BIN2|
|Motor 3|Rear left|CH4, CH5|Driver 2: AIN1, AIN2|
|Motor 4|Rear right|CH6, CH7|Driver 2: BIN1, BIN2|

`ESP32 | I2C Bus | PCA9685 | +---------+---------+ | | HR8833 #1 HR8833 #2 | | +---+---+ +---+---+ | | | | Motor1 Motor2 Motor3 Motor4 FL FR RL RR`

## 2. Complete Arduino code for four motors

This code tests all four motors individually, then runs them together.

It assumes your set_channel_value() function accepts raw 12-bit PWM counts.

`#include <Arduino.h> #include <Wire.h> #include "FaBoPWM_PCA9685.h" FaBoPWM faboPWM; // Motor channel assignments #define M1_IN1 0 #define M1_IN2 1 #define M2_IN1 2 #define M2_IN2 3 #define M3_IN1 4 #define M3_IN2 5 #define M4_IN1 6 #define M4_IN2 7 // Motor speed: 0–4095 #define MOTOR_SPEED 1500 void motorForward(int in1, int in2, int speed) { faboPWM.set_channel_value(in1, speed); faboPWM.set_channel_value(in2, 0); } void motorStop(int in1, int in2) { faboPWM.set_channel_value(in1, 0); faboPWM.set_channel_value(in2, 0); } void stopAll() { motorStop(M1_IN1, M1_IN2); motorStop(M2_IN1, M2_IN2); motorStop(M3_IN1, M3_IN2); motorStop(M4_IN1, M4_IN2); } void forwardAll(int speed) { motorForward(M1_IN1, M1_IN2, speed); motorForward(M2_IN1, M2_IN2, speed); motorForward(M3_IN1, M3_IN2, speed); motorForward(M4_IN1, M4_IN2, speed); } void setup() { Serial.begin(115200); Wire.begin(21, 22); // ESP32 SDA, SCL if (!faboPWM.begin()) { Serial.println("PCA9685 not found"); while (1); } Serial.println("PCA9685 found"); faboPWM.init(307); faboPWM.set_hz(1000); stopAll(); } void loop() { Serial.println("Testing Motor 1"); motorForward(M1_IN1, M1_IN2, MOTOR_SPEED); delay(2000); stopAll(); delay(1000); Serial.println("Testing Motor 2"); motorForward(M2_IN1, M2_IN2, MOTOR_SPEED); delay(2000); stopAll(); delay(1000); Serial.println("Testing Motor 3"); motorForward(M3_IN1, M3_IN2, MOTOR_SPEED); delay(2000); stopAll(); delay(1000); Serial.println("Testing Motor 4"); motorForward(M4_IN1, M4_IN2, MOTOR_SPEED); delay(2000); stopAll(); delay(1000); Serial.println("All Motors Forward"); forwardAll(MOTOR_SPEED); delay(3000); stopAll(); delay(3000); }`

**Note:** Confirm that your installed FaBoPWM library supports 1,000 Hz and that its set_channel_value() method uses raw duty counts. Some library versions interpret channel values differently.

## 3. Why you currently detect only two axes

Your existing code controls only channels 0, 2, and 3:

`faboPWM.set_channel_value(0, 800); faboPWM.set_channel_value(2, 800); faboPWM.set_channel_value(3, 800);`

You never command channels 4–7.

Also, the PCA9685 does not detect motors or axes. It only produces PWM signals. If your board exposes two motor output connectors, that is a limitation of the motor-driver board, not the PCA9685.

**Important:** Before testing, verify the HR8833 motor voltage and current limits. A typical DRV8833-class device cannot directly handle a fully charged 3S LiPo battery (12.6V), and JGB37-520 motors may exceed its current rating during startup or stall.

### One question

Does your SLAM-KIT have **four independent JGB37-520 motors**, or **two motor-driver outputs connected to four motors (two motors in parallel per output)**?

The wiring and control code depend on this distinction.

it connects to arduino uno not to esp32

Understood. Your **4WD SLAM-KIT uses Arduino Uno + PCA9685 + HR8833 + four JGB37-520 DC motors**, not ESP32.

The PCA9685 connects to the Arduino Uno through I²C.

### 1. Arduino Uno → PCA9685

|Arduino Uno|PCA9685|
|---|---|
|A4 (SDA)|SDA|
|A5 (SCL)|SCL|
|5V|VCC|
|GND|GND|

The Arduino Uno uses **5V logic**, so the PCA9685 logic supply can be 5V.

### 2. Four-motor channel assignments

Assuming each HR8833 driver has two motor channels:

|Motor|Position|PCA9685|
|---|---|---|
|M1|Front left|CH0, CH1|
|M2|Front right|CH2, CH3|
|M3|Rear left|CH4, CH5|
|M4|Rear right|CH6, CH7|

### 3. Arduino Uno code — four motors

This version uses your existing FaBoPWM_PCA9685.h library.

```
#include <Arduino.h>
#include <Wire.h>
#include "FaBoPWM_PCA9685.h"

FaBoPWM faboPWM;

// PCA9685 channel assignments
const int motorPins[4][2] = {
  {0, 1},   // Motor 1: Front Left
  {2, 3},   // Motor 2: Front Right
  {4, 5},   // Motor 3: Rear Left
  {6, 7}    // Motor 4: Rear Right
};

// Speed: 0–4095
const int SPEED = 800;

// Control one motor
void motorRun(int motor, int speed) {

  if (motor < 0 || motor >= 4) return;

  speed = constrain(speed, -4095, 4095);

  int in1 = motorPins[motor][0];
  int in2 = motorPins[motor][1];

  if (speed > 0) {
    faboPWM.set_channel_value(in1, speed);
    faboPWM.set_channel_value(in2, 0);
  }
  else if (speed < 0) {
    faboPWM.set_channel_value(in1, 0);
    faboPWM.set_channel_value(in2, -speed);
  }
  else {
    faboPWM.set_channel_value(in1, 0);
    faboPWM.set_channel_value(in2, 0);
  }
}

// Stop all four motors
void stopAll() {
  for (int i = 0; i < 4; i++) {
    motorRun(i, 0);
  }
}

// Run all four motors
void runAll(int speed) {
  for (int i = 0; i < 4; i++) {
    motorRun(i, speed);
  }
}

void setup() {

  Serial.begin(115200);

  Wire.begin();

  if (!faboPWM.begin()) {
    Serial.println("PCA9685 not found");
    while (1);
  }

  Serial.println("PCA9685 found");

  faboPWM.init(307);
  faboPWM.set_hz(50);

  stopAll();
}

void loop() {

  // Test Motor 1
  Serial.println("Motor 1");
  motorRun(0, SPEED);
  delay(2000);
  stopAll();
  delay(1000);

  // Test Motor 2
  Serial.println("Motor 2");
  motorRun(1, SPEED);
  delay(2000);
  stopAll();
  delay(1000);

  // Test Motor 3
  Serial.println("Motor 3");
  motorRun(2, SPEED);
  delay(2000);
  stopAll();
  delay(1000);

  // Test Motor 4
  Serial.println("Motor 4");
  motorRun(3, SPEED);
  delay(2000);
  stopAll();
  delay(1000);

  // All motors
  Serial.println("All Motors Forward");
  runAll(SPEED);
  delay(3000);

  stopAll();
  delay(3000);
}
```

### 4. Important: Your HR8833 connections

`Arduino UNO A4 A5 | | SDA SCL | | +-----------+ | PCA9685 | +-----------+ | | | | | | | | 0 1 2 3 4 5 6 7 | | | | | | | | +-------+ +-------+ |HR8833 | |HR8833 | | #1 | | #2 | +-------+ +-------+ | | | | M1 M2 M3 M4`

This arrangement requires two dual-channel HR8833 drivers, or four single-channel drivers. All logic grounds must be connected.

**Motor power warning:** Do not connect your 11.1V 3S LiPo directly to an HR8833 unless its datasheet explicitly permits the full 12.6V charged-battery voltage. Also verify that the driver can handle each JGB37-520 motor's stall current.

### 5. Why your previous code controlled only two axes

Your previous code used channels 0–3, but four independently controlled DC motors require **eight driver-control signals** when using two-input H-bridges.

The code above uses CH0–CH7.

One more distinction: four-wheel drive does not necessarily mean four independent steering axes. With ordinary JGB37-520 motors, you can implement skid steering by controlling the left and right wheel speeds.

**Question:** Are your four JGB37-520 motors connected to **two HR8833 boards**, or are you using a single motor-driver board with four motor outputs?

That will determine the exact wiring.

#include <PS2X_lib.h> //for MOEBIUS #include "FaBoPWM_PCA9685.h" //#include "servo.hpp" FaBoPWM faboPWM; int pos = 0; int MAX_VALUE = 2000; // 电机速度限制 int MIN_VALUE = 300; #define DIRA1 0 #define DIRA2 1 #define DIRB1 2 #define DIRB2 3 #define DIRC1 4 #define DIRC2 5 #define DIRD1 6 #define DIRD2 7 //电机控制，前进、后退、停止 #define MOTORA_FORWARD(pwm) do{faboPWM.set_channel_value(DIRA1,pwm);faboPWM.set_channel_value(DIRA2, 0);}while(0) #define MOTORA_STOP(x) do{faboPWM.set_channel_value(DIRA1,0);faboPWM.set_channel_value(DIRA2, 0);}while(0) #define MOTORA_BACKOFF(pwm) do{faboPWM.set_channel_value(DIRA1,0);faboPWM.set_channel_value(DIRA2, pwm);}while(0) #define MOTORB_FORWARD(pwm) do{faboPWM.set_channel_value(DIRB1,pwm);faboPWM.set_channel_value(DIRB2, 0);}while(0) #define MOTORB_STOP(x) do{faboPWM.set_channel_value(DIRB1,0);faboPWM.set_channel_value(DIRB2, 0);}while(0) #define MOTORB_BACKOFF(pwm) do{faboPWM.set_channel_value(DIRB1,0);faboPWM.set_channel_value(DIRB2, pwm);}while(0) #define MOTORC_FORWARD(pwm) do{faboPWM.set_channel_value(DIRC1,pwm);faboPWM.set_channel_value(DIRC2, 0);}while(0) #define MOTORC_STOP(x) do{faboPWM.set_channel_value(DIRC1,0);faboPWM.set_channel_value(DIRC2, 0);}while(0) #define MOTORC_BACKOFF(pwm) do{faboPWM.set_channel_value(DIRC1,0);faboPWM.set_channel_value(DIRC2, pwm);}while(0) #define MOTORD_FORWARD(pwm) do{faboPWM.set_channel_value(DIRD1,pwm);faboPWM.set_channel_value(DIRD2, 0);}while(0) #define MOTORD_STOP(x) do{faboPWM.set_channel_value(DIRD1,0);faboPWM.set_channel_value(DIRD2, 0);}while(0) #define MOTORD_BACKOFF(pwm) do{faboPWM.set_channel_value(DIRD1,0);faboPWM.set_channel_value(DIRD2, pwm);}while(0) #define SERIAL Serial //#define SERIAL Serial3 #define LOG_DEBUG #ifdef LOG_DEBUG #define M_LOG SERIAL.print #else #define M_LOG #endif //PWM参数 #define MAX_PWM 2000 #define MIN_PWM 300 int Motor_PWM = 1900; //控制电机运动 宏定义 // ↑A-----B↑ // | ↑ | // | | | // ↑C-----D↑ void ADVANCE(uint8_t pwm_A,uint8_t pwm_B,uint8_t pwm_C,uint8_t pwm_D) { MOTORA_BACKOFF(Motor_PWM);MOTORB_FORWARD(Motor_PWM); MOTORC_BACKOFF(Motor_PWM);MOTORD_FORWARD(Motor_PWM); } // ↓A-----B↓ // | | | // | ↓ | // ↓C-----D↓ void BACK() { MOTORA_FORWARD(Motor_PWM);MOTORB_BACKOFF(Motor_PWM); MOTORC_FORWARD(Motor_PWM);MOTORD_BACKOFF(Motor_PWM); } // =A-----B↑ // | ↖ | // | ↖ | // ↑C-----D= void LEFT_1() { MOTORA_STOP(Motor_PWM);MOTORB_FORWARD(Motor_PWM); MOTORC_BACKOFF(Motor_PWM);MOTORD_STOP(Motor_PWM); } // ↓A-----B↑ // | ← | // | ← | // ↑C-----D↓ void LEFT_2() { MOTORA_FORWARD(Motor_PWM);MOTORB_FORWARD(Motor_PWM); MOTORC_BACKOFF(Motor_PWM);MOTORD_BACKOFF(Motor_PWM); } // ↓A-----B= // | ↙ | // | ↙ | // =C-----D↓ void LEFT_3() { MOTORA_FORWARD(Motor_PWM);MOTORB_STOP(Motor_PWM); MOTORC_STOP(Motor_PWM);MOTORD_BACKOFF(Motor_PWM); } // ↑A-----B= // | ↗ | // | ↗ | // =C-----D↑ void RIGHT_1() { MOTORA_BACKOFF(Motor_PWM);MOTORB_STOP(Motor_PWM); MOTORC_STOP(Motor_PWM);MOTORD_FORWARD(Motor_PWM); } // ↑A-----B↓ // | → | // | → | // ↓C-----D↑ void RIGHT_2() { MOTORA_BACKOFF(Motor_PWM);MOTORB_BACKOFF(Motor_PWM); MOTORC_FORWARD(Motor_PWM);MOTORD_FORWARD(Motor_PWM); } // =A-----B↓ // | ↘ | // | ↘ | // ↓C-----D= void RIGHT_3() { MOTORA_STOP(Motor_PWM);MOTORB_BACKOFF(Motor_PWM); MOTORC_FORWARD(Motor_PWM);MOTORD_STOP(Motor_PWM); } // ↑A-----B↓ // | ↗ ↘ | // | ↖ ↙ | // ↑C-----D↓ void rotate_1() //tate_1(uint8_t pwm_A,uint8_t pwm_B,uint8_t pwm_C,uint8_t pwm_D) { MOTORA_BACKOFF(Motor_PWM);MOTORB_BACKOFF(Motor_PWM); MOTORC_BACKOFF(Motor_PWM);MOTORD_BACKOFF(Motor_PWM); } // ↓A-----B↑ // | ↙ ↖ | // | ↘ ↗ | // ↓C-----D↑ void rotate_2() // rotate_2(uint8_t pwm_A,uint8_t pwm_B,uint8_t pwm_C,uint8_t pwm_D) { MOTORA_FORWARD(Motor_PWM);MOTORB_FORWARD(Motor_PWM); MOTORC_FORWARD(Motor_PWM);MOTORD_FORWARD(Motor_PWM); } // =A-----B= // | = | // | = | // =C-----D= void STOP() { MOTORA_STOP(Motor_PWM);MOTORB_STOP(Motor_PWM); MOTORC_STOP(Motor_PWM);MOTORD_STOP(Motor_PWM); } //串口输入控制 void UART_Control() { char Uart_Date=0; if(SERIAL.available()) { Uart_Date = SERIAL.read(); } switch(Uart_Date) { case 'A': ADVANCE(500,500,500,500); M_LOG("Run!\r\n"); break; case 'B': RIGHT_1(); M_LOG("Right up!\r\n"); break; case 'C': rotate_2(); break; case 'D': RIGHT_3(); M_LOG("Right down!\r\n"); break; case 'E': BACK(); M_LOG("Run!\r\n"); break; case 'F': LEFT_3(); M_LOG("Left down!\r\n"); break; case 'G': rotate_1(); break; case 'H': LEFT_1(); M_LOG("Left up!\r\n"); break; case 'Z': STOP(); M_LOG("Stop!\r\n"); break; case 'z': STOP(); M_LOG("Stop!\r\n"); break; case 'd': LEFT_2(); M_LOG("Left!\r\n"); break; case 'b': RIGHT_2(); M_LOG("Right!\r\n"); break; case 'L': Motor_PWM = 1500; break; case 'M': Motor_PWM = 500; break; } } void IO_init() { STOP(); } void setup() { SERIAL.begin(9600); IO_init(); if(faboPWM.begin()) { Serial.println("Find PCA9685"); faboPWM.init(300); } faboPWM.set_hz(50); SERIAL.print("Start"); } void loop() { UART_Control();//串口接收处理 //CAR_Control();//小车控制 },,,this code is for example with bluetooth control...

…

Yes. This example is designed for a **4WD robot car controlled by serial commands**, which can come from a Bluetooth module connected to an Arduino Uno.

It also confirms that your SLAM-KIT uses **eight PCA9685 channels (CH0–CH7) to control four motors independently**.

## 1. Your SLAM-KIT motor configuration

|Motor|Position|PCA9685 channels|
|---|---|---|
|A|Front left|CH0, CH1|
|B|Front right|CH2, CH3|
|C|Rear left|CH4, CH5|
|D|Rear right|CH6, CH7|

Your original code uses these channels correctly.

The control functions support forward, backward, lateral movement, diagonal movement, and rotation.

**Important:** The lateral movement functions (LEFT_2, RIGHT_2) suggest that the original SLAM-KIT may use **Mecanum wheels**, rather than ordinary wheels. Ordinary four-wheel robots cannot move directly sideways.

## 2. One problem in your original code

In setup():

```
void setup()
{
  SERIAL.begin(9600);
  IO_init();
  
  if(faboPWM.begin()) 
  {
    Serial.println("Find PCA9685");
    faboPWM.init(300);
  }

  faboPWM.set_hz(50);
  SERIAL.print("Start");
}
```

You call IO_init() before initializing the PCA9685.

However, IO_init() calls STOP(), which sends commands to the PCA9685.

**The PCA9685 should be initialized before calling STOP().**

## 3. Simplified code for testing four motors without Bluetooth

The following code uses your original motor directions and the same FaBoPWM library.

It tests motors A, B, C, and D individually, followed by forward, backward, and stop.

```
#include <Arduino.h>
#include <Wire.h>
#include "FaBoPWM_PCA9685.h"

FaBoPWM faboPWM;

#define DIRA1 0
#define DIRA2 1
#define DIRB1 2
#define DIRB2 3
#define DIRC1 4
#define DIRC2 5
#define DIRD1 6
#define DIRD2 7

int Motor_PWM = 800;

// Motor control
void motorControl(int ch1, int ch2, int pwm, bool forward)
{
  if (forward) {
    faboPWM.set_channel_value(ch1, pwm);
    faboPWM.set_channel_value(ch2, 0);
  }
  else {
    faboPWM.set_channel_value(ch1, 0);
    faboPWM.set_channel_value(ch2, pwm);
  }
}

// Stop one motor
void motorStop(int ch1, int ch2)
{
  faboPWM.set_channel_value(ch1, 0);
  faboPWM.set_channel_value(ch2, 0);
}

// Stop all motors
void STOP()
{
  motorStop(DIRA1, DIRA2);
  motorStop(DIRB1, DIRB2);
  motorStop(DIRC1, DIRC2);
  motorStop(DIRD1, DIRD2);
}

// Forward — original SLAM-KIT directions
void ADVANCE()
{
  motorControl(DIRA1, DIRA2, Motor_PWM, false);
  motorControl(DIRB1, DIRB2, Motor_PWM, true);
  motorControl(DIRC1, DIRC2, Motor_PWM, false);
  motorControl(DIRD1, DIRD2, Motor_PWM, true);
}

// Backward
void BACK()
{
  motorControl(DIRA1, DIRA2, Motor_PWM, true);
  motorControl(DIRB1, DIRB2, Motor_PWM, false);
  motorControl(DIRC1, DIRC2, Motor_PWM, true);
  motorControl(DIRD1, DIRD2, Motor_PWM, false);
}

void setup()
{
  Serial.begin(115200);
  Wire.begin();

  if (!faboPWM.begin()) {
    Serial.println("PCA9685 not found!");
    while (1);
  }

  Serial.println("PCA9685 found");

  faboPWM.init(300);
  faboPWM.set_hz(50);

  STOP();

  Serial.println("4WD SLAM-KIT Ready");
}

void loop()
{
  Serial.println("Motor A");
  motorControl(DIRA1, DIRA2, Motor_PWM, false);
  delay(2000);
  STOP();
  delay(1000);

  Serial.println("Motor B");
  motorControl(DIRB1, DIRB2, Motor_PWM, true);
  delay(2000);
  STOP();
  delay(1000);

  Serial.println("Motor C");
  motorControl(DIRC1, DIRC2, Motor_PWM, false);
  delay(2000);
  STOP();
  delay(1000);

  Serial.println("Motor D");
  motorControl(DIRD1, DIRD2, Motor_PWM, true);
  delay(2000);
  STOP();
  delay(1000);

  Serial.println("Forward");
  ADVANCE();
  delay(3000);

  Serial.println("Stop");
  STOP();
  delay(2000);

  Serial.println("Backward");
  BACK();
  delay(3000);

  STOP();
  delay(3000);
}
```

**Testing precautions:** Raise the robot so its wheels are off the ground. Start with a low PWM value and increase it gradually. Verify that the motor-driver supply voltage and current ratings are compatible with the JGB37-520 motors.

## 4. Arduino Uno and Bluetooth connection

Your original code uses:

```
#define SERIAL Serial
```

Therefore, commands are received through the Arduino Uno hardware serial port (pins 0 and 1).

If you connect a Bluetooth serial module, you can send commands such as:

|Command|Action|
|---|---|
|A|Forward|
|E|Backward|
|Z|Stop|
|G|Rotate|
|C|Rotate opposite direction|
|d|Move left|
|b|Move right|
|L|Speed 1500|
|M|Speed 500|

You can also test these commands directly through the Arduino Serial Monitor without Bluetooth.

### 5. Next step: SLAM-KIT with ESP32

Since your existing 4WD SLAM-KIT works with **Arduino Uno + PCA9685**, you can later replace the Uno with ESP32 while retaining much of the motor-control logic.

The principal changes would be:

|Feature|Arduino Uno|ESP32|
|---|---|---|
|Logic voltage|5V|3.3V|
|I²C SDA|A4|GPIO21|
|I²C SCL|A5|GPIO22|
|PCA9685|Supported|Supported|
|Wi-Fi|External module|Built in|
|Bluetooth|External module|Built in on original ESP32|

For ESP32, the PCA9685 VCC should be connected to 3.3V so its I²C pull-ups do not expose ESP32 GPIO pins to 5V.

**One important question:** Does your SLAM-KIT have **four Mecanum wheels** (rollers mounted diagonally around each wheel), or four ordinary rubber wheels?

Your original code strongly suggests Mecanum wheels. This matters because the correct four-motor movement algorithm depends on the wheel type.

mecamum wheel.. i use

Great! Your SLAM-KIT uses **four Mecanum wheels**.

That explains why your original Arduino code includes LEFT_2(), RIGHT_2(), and diagonal movement functions.

Unlike ordinary wheels, Mecanum wheels allow the robot to move sideways without rotating.

## 1. Your SLAM-KIT configuration

|Component|Hardware|
|---|---|
|Microcontroller|Arduino Uno|
|PWM controller|PCA9685|
|Motor driver|HR8833|
|Motors|4 × JGB37-520|
|Wheels|4 × Mecanum|
|Communication|Bluetooth / Serial|

### Motor positions

`FRONT ┌───────────┐ │ │ A │ │ B FL │ │ FR │ │ │ │ C │ │ D RL └───────────┘ RR REAR`

## 2. Mecanum wheel movement

Your original code supports these movements:

|Movement|Function|
|---|---|
|Forward|ADVANCE()|
|Backward|BACK()|
|Left sideways|LEFT_2()|
|Right sideways|RIGHT_2()|
|Diagonal left-front|LEFT_1()|
|Diagonal right-front|RIGHT_1()|
|Rotate clockwise/counterclockwise|rotate_1(), rotate_2()|
|Stop|STOP()|

The motor direction combinations in your original program are appropriate to test with your existing wheel arrangement. Actual movement direction depends on wheel mounting and motor polarity.

## 3. Simplified Arduino Uno test code

We can retain your original motor direction definitions and test four fundamental movements.

```
#include <Arduino.h>
#include <Wire.h>
#include "FaBoPWM_PCA9685.h"

FaBoPWM faboPWM;

#define A1 0
#define A2 1
#define B1 2
#define B2 3
#define C1 4
#define C2 5
#define D1 6
#define D2 7

int speed = 1000;

// Motor control
void motor(int ch1, int ch2, int pwm)
{
  pwm = constrain(pwm, -4095, 4095);

  if (pwm > 0) {
    faboPWM.set_channel_value(ch1, pwm);
    faboPWM.set_channel_value(ch2, 0);
  }
  else if (pwm < 0) {
    faboPWM.set_channel_value(ch1, 0);
    faboPWM.set_channel_value(ch2, -pwm);
  }
  else {
    faboPWM.set_channel_value(ch1, 0);
    faboPWM.set_channel_value(ch2, 0);
  }
}

// Forward
void forward()
{
  motor(A1, A2, -speed);
  motor(B1, B2,  speed);
  motor(C1, C2, -speed);
  motor(D1, D2,  speed);
}

// Backward
void backward()
{
  motor(A1, A2,  speed);
  motor(B1, B2, -speed);
  motor(C1, C2,  speed);
  motor(D1, D2, -speed);
}

// Move left
void left()
{
  motor(A1, A2,  speed);
  motor(B1, B2,  speed);
  motor(C1, C2, -speed);
  motor(D1, D2, -speed);
}

// Move right
void right()
{
  motor(A1, A2, -speed);
  motor(B1, B2, -speed);
  motor(C1, C2,  speed);
  motor(D1, D2,  speed);
}

// Stop
void stopAll()
{
  motor(A1, A2, 0);
  motor(B1, B2, 0);
  motor(C1, C2, 0);
  motor(D1, D2, 0);
}

void setup()
{
  Serial.begin(115200);
  Wire.begin();

  if (!faboPWM.begin()) {
    Serial.println("PCA9685 not found");
    while (1);
  }

  faboPWM.init(300);
  faboPWM.set_hz(50);

  stopAll();

  Serial.println("Mecanum SLAM-KIT Ready");
}

void loop()
{
  Serial.println("Forward");
  forward();
  delay(2000);

  stopAll();
  delay(1000);

  Serial.println("Backward");
  backward();
  delay(2000);

  stopAll();
  delay(1000);

  Serial.println("Left");
  left();
  delay(2000);

  stopAll();
  delay(1000);

  Serial.println("Right");
  right();
  delay(2000);

  stopAll();
  delay(3000);
}
```

Test with the wheels raised first. This code assumes the library interprets PWM values as 12-bit duty counts. Confirm the motor driver's electrical ratings before applying power.

## 4. Next step: Mecanum SLAM robot

For your SLAM-KIT project, we can extend this system:

`Jetson Orin Nano │ ROS2 Humble │ SLAM + Navigation │ USB Serial │ Arduino UNO │ PCA9685 │ Motor Drivers │ ┌───────┴───────┐ │ │ Front Motors Rear Motors │ │ └───────┬───────┘ │ Mecanum 4WD`

For accurate autonomous navigation, I recommend adding **wheel encoders** to measure actual wheel speeds and estimate robot odometry.

**One important question:** Do your four JGB37-520 motors have built-in encoders (typically six wires per motor), or do they have only two motor wires?

This determines how we should design the SLAM-KIT PCB and implement ROS2 odometry.

front and back acts..right and left does not work

Since **forward and backward work**, your Arduino Uno, PCA9685, and motor drivers are at least partially working.

The problem is likely related to the **Mecanum wheel direction combinations** or wheel installation.

## 1. Check the motor direction combinations

Your original program uses these motor commands:

|Movement|A (Front Left)|B (Front Right)|C (Rear Left)|D (Rear Right)|
|---|---|---|---|---|
|Forward|BACKOFF|FORWARD|BACKOFF|FORWARD|
|Backward|FORWARD|BACKOFF|FORWARD|BACKOFF|
|Left|FORWARD|FORWARD|BACKOFF|BACKOFF|
|Right|BACKOFF|BACKOFF|FORWARD|FORWARD|

These combinations can work for a particular motor polarity and Mecanum wheel arrangement.

However, they are **not guaranteed to work for every Mecanum robot**.

### 2. First, test all four motors individually

Use this code to verify that all four motors can rotate in both directions.

```
void loop()
{
  Serial.println("Motor A forward");
  motor(A1, A2, 1000);
  delay(2000);
  stopAll();
  delay(1000);

  Serial.println("Motor B forward");
  motor(B1, B2, 1000);
  delay(2000);
  stopAll();
  delay(1000);

  Serial.println("Motor C forward");
  motor(C1, C2, 1000);
  delay(2000);
  stopAll();
  delay(1000);

  Serial.println("Motor D forward");
  motor(D1, D2, 1000);
  delay(2000);
  stopAll();
  delay(1000);
}
```

This tests the electrical FORWARD direction of each motor.

## 3. Correct Mecanum movement equations

For a conventional X-configuration Mecanum robot, define positive wheel rotation as the direction that moves the robot forward.

Then the wheel speeds are:

FL=Vx−Vy−ωFR=Vx+Vy+ωRL=Vx+Vy−ωRR=Vx−Vy+ωFLFRRLRR​=Vx​−Vy​−ω=Vx​+Vy​+ω=Vx​+Vy​−ω=Vx​−Vy​+ω​

Here, VxVx​ is forward velocity, VyVy​ is leftward velocity, and ωω is counterclockwise rotation. The equations assume a particular wheel arrangement and coordinate convention.

For pure sideways motion:

**Move left:**

(FL,FR,RL,RR)=(−,+,+,−)(FL,FR,RL,RR)=(−,+,+,−)

**Move right:**

(FL,FR,RL,RR)=(+,−,−,+)(FL,FR,RL,RR)=(+,−,−,+)

These are physical wheel rotation directions, not necessarily the electrical FORWARD/BACKOFF commands.

## 4. Try these modified functions

Using your original motor polarity, try:

```
// Move LEFT
void left()
{
  motor(A1, A2,  speed);
  motor(B1, B2,  speed);
  motor(C1, C2, -speed);
  motor(D1, D2, -speed);
}

// Move RIGHT
void right()
{
  motor(A1, A2, -speed);
  motor(B1, B2, -speed);
  motor(C1, C2,  speed);
  motor(D1, D2,  speed);
}
```

These match your original LEFT_2() and RIGHT_2() functions. If those functions already fail, changing only the code to these functions will not resolve the issue.

## 5. Check your Mecanum wheel installation

This is especially important.

For the conventional **X configuration**, the rollers should form an X pattern when viewed from above.

Incorrect wheel placement can cause sideways commands to produce rotation, diagonal movement, or little movement.

Also check that the robot's wheels are not slipping excessively and that all four motors have sufficient torque.

---

### I need two observations from your robot

When you execute:

```
left();
delay(2000);
stopAll();
```

**1. What happens?**

- A. All four motors rotate, but the robot does not move.
- B. Only two motors rotate.
- C. The robot rotates instead of moving sideways.
- D. The robot moves diagonally.

**2. Are your Mecanum wheels installed in an X configuration or an O configuration?**

These two details will help identify whether the problem is in the motor wiring, PWM control, or Mecanum wheel arrangement.