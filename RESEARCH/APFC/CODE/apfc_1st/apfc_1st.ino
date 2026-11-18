


#include <Arduino.h>
#include <math.h>

// =====================================
// PIN CONFIGURATION
// =====================================

const byte VOLT_PIN  = A3;
const byte CURR_PIN  = A0;
const byte RELAY_PIN = 2;

// =====================================
// AC FREQUENCY
// =====================================

const float FREQUENCY = 60.0;

const unsigned long PERIOD_US = 1000000UL / 60;

// =====================================
// PRINT INTERVAL
// =====================================

// 1000 = 1초, 2000 = 2초
const unsigned long PRINT_INTERVAL = 1000;

// =====================================
// RELAY CONTROL
// =====================================

const unsigned long RELAY_INTERVAL = 1000;

unsigned long relayPreviousMillis = 0;
bool relayState = LOW;

// =====================================
// ZERO CROSSING VARIABLES
// =====================================

unsigned long voltageTime = 0;
unsigned long currentTime = 0;

bool prevVoltage = LOW;
bool prevCurrent = LOW;

bool voltageDetected = false;
bool currentDetected = false;

// =====================================
// MEASUREMENT VARIABLES
// =====================================

long timeDifference = 0;

float phaseAngle = 0.0;
float powerFactor = 0.0;

bool newMeasurement = false;

unsigned long previousPrintMillis = 0;

// =====================================
// SETUP
// =====================================

void setup() {

  Serial.begin(115200);

  pinMode(VOLT_PIN, INPUT_PULLUP);
  pinMode(CURR_PIN, INPUT_PULLUP);

  pinMode(RELAY_PIN, OUTPUT);

  digitalWrite(RELAY_PIN, LOW);

  prevVoltage = digitalRead(VOLT_PIN);
  prevCurrent = digitalRead(CURR_PIN);

  Serial.println();
  Serial.println("================================");
  Serial.println(" LM393 APFC POWER FACTOR METER");
  Serial.println("================================");

  Serial.println("Voltage ZCD : A3");
  Serial.println("Current ZCD : A0");
  Serial.println("Relay       : D2");
  Serial.println("Frequency   : 60 Hz");
  Serial.println("Print       : Every 1 second");
  Serial.println("================================");
}

// =====================================
// RELAY CONTROL
// =====================================

void controlRelay() {

  unsigned long currentMillis = millis();

  if (currentMillis - relayPreviousMillis >= RELAY_INTERVAL) {

    relayPreviousMillis = currentMillis;

    relayState = !relayState;

    digitalWrite(RELAY_PIN, relayState);
  }
}

// =====================================
// ZERO CROSSING DETECTION
// =====================================

void detectZeroCrossing() {

  bool voltageState = digitalRead(VOLT_PIN);
  bool currentState = digitalRead(CURR_PIN);

  unsigned long now = micros();

  // Voltage rising edge
  if (voltageState == HIGH && prevVoltage == LOW) {

    voltageTime = now;
    voltageDetected = true;
  }

  // Current rising edge
  if (currentState == HIGH && prevCurrent == LOW) {

    currentTime = now;
    currentDetected = true;
  }

  prevVoltage = voltageState;
  prevCurrent = currentState;

  // Calculate phase difference
  if (voltageDetected && currentDetected) {

    long dt = (long)(currentTime - voltageTime);

    long halfPeriod = PERIOD_US / 2;

    if (dt > halfPeriod) {
      dt -= PERIOD_US;
    }

    if (dt < -halfPeriod) {
      dt += PERIOD_US;
    }

    timeDifference = dt;

    phaseAngle =
        dt * FREQUENCY * 360.0 / 1000000.0;

    powerFactor =
        cos(phaseAngle * PI / 180.0);

    newMeasurement = true;

    voltageDetected = false;
    currentDetected = false;
  }
}

// =====================================
// PRINT RESULTS
// =====================================

void printResults() {

  unsigned long currentMillis = millis();

  if (currentMillis - previousPrintMillis >= PRINT_INTERVAL) {

    previousPrintMillis = currentMillis;

    if (newMeasurement) {

      Serial.println();
      Serial.println("========== APFC Measurement ==========");

      Serial.print("Time Difference : ");
      Serial.print(timeDifference);
      Serial.println(" us");

      Serial.print("Phase Angle     : ");
      Serial.print(phaseAngle, 2);
      Serial.println(" degrees");

      Serial.print("Power Factor    : ");
      Serial.println(powerFactor, 3);

      Serial.print("Current State   : ");

      if (phaseAngle > 0.5) {

        Serial.println("LAGGING (지상)");

      }
      else if (phaseAngle < -0.5) {

        Serial.println("LEADING (진상)");

      }
      else {

        Serial.println("IN PHASE (동상)");
      }

      Serial.print("Relay State     : ");

      if (relayState == HIGH) {
        Serial.println("ON");
      }
      else {
        Serial.println("OFF");
      }

      Serial.println("======================================");

      newMeasurement = false;
    }
  }
}

// =====================================
// MAIN LOOP
// =====================================

void loop() {

  detectZeroCrossing();

  controlRelay();

  printResults();
}
