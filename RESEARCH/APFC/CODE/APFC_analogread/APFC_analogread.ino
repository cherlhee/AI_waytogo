


#include <math.h>

// ======================================
// LM393N Zero Crossing Detection
// Arduino UNO
// ======================================

// Pin Configuration
const byte CURR_PIN = A0;  // Current ZCD
const byte VOLT_PIN = A3;  // Voltage ZCD

const int THRESHOLD = 512;
const float FREQUENCY = 60.0;

// Timing variables
unsigned long voltageTime = 0;
unsigned long currentTime = 0;

bool prevVoltage = false;
bool prevCurrent = false;

long timeDifference = 0;

float phaseAngle = 0.0;
float powerFactor = 0.0;

unsigned long lastPrintTime = 0;
unsigned long lastCurrentEdgeTime = 0;

bool validMeasurement = false;

// ======================================
// SETUP
// ======================================
void setup() {

  Serial.begin(115200);

  // LM393N open collector outputs
  pinMode(CURR_PIN, INPUT_PULLUP);
  pinMode(VOLT_PIN, INPUT_PULLUP);

  prevCurrent = analogRead(CURR_PIN) > THRESHOLD;
  prevVoltage = analogRead(VOLT_PIN) > THRESHOLD;

  Serial.println("================================");
  Serial.println("LM393N Zero Crossing Detection");
  Serial.println("Current ZCD = A0");
  Serial.println("Voltage ZCD = A3");
  Serial.println("Frequency = 60 Hz");
  Serial.println("================================");
}

// ======================================
// LOOP
// ======================================
void loop() {

  // Read current and voltage
  int currentADC = analogRead(CURR_PIN);
  unsigned long currentSampleTime = micros();

  int voltageADC = analogRead(VOLT_PIN);
  unsigned long voltageSampleTime = micros();

  bool currentState = currentADC > THRESHOLD;
  bool voltageState = voltageADC > THRESHOLD;

  // ------------------------------------
  // Current rising edge
  // ------------------------------------
  if (currentState && !prevCurrent) {

    currentTime = currentSampleTime;
    lastCurrentEdgeTime = currentTime;
  }

  // ------------------------------------
  // Voltage rising edge
  // ------------------------------------
  if (voltageState && !prevVoltage) {

    voltageTime = voltageSampleTime;
  }

  prevCurrent = currentState;
  prevVoltage = voltageState;

  // ------------------------------------
  // Calculate phase difference
  // ------------------------------------
  if (currentTime != 0 && voltageTime != 0) {

    const long periodUs =
        (long)(1000000.0 / FREQUENCY);

    long dt = (long)(currentTime - voltageTime);

    // Normalize to -180 to +180 degrees
    while (dt > periodUs / 2) {
      dt -= periodUs;
    }

    while (dt < -periodUs / 2) {
      dt += periodUs;
    }

    timeDifference = dt;

    // Positive dt = Current lags voltage
    // Negative dt = Current leads voltage

    phaseAngle =
        timeDifference * FREQUENCY * 360.0 / 1000000.0;

    powerFactor =
        cos(phaseAngle * PI / 180.0);

    validMeasurement = true;
  }

  // ------------------------------------
  // Print every 2 seconds
  // ------------------------------------
  if (millis() - lastPrintTime >= 2000) {

    lastPrintTime = millis();

    Serial.println();
    Serial.println("===== APFC Measurement =====");

    Serial.print("Current ADC (A0): ");
    Serial.println(currentADC);

    Serial.print("Voltage ADC (A3): ");
    Serial.println(voltageADC);

    if (validMeasurement &&
        (micros() - lastCurrentEdgeTime < 100000)) {

      Serial.print("Time Difference: ");
      Serial.print(timeDifference);
      Serial.println(" us");

      Serial.print("Phase Angle: ");
      Serial.print(phaseAngle, 2);
      Serial.println(" degrees");

      Serial.print("Power Factor: ");
      Serial.println(powerFactor, 3);

      if (phaseAngle > 1.0) {
        Serial.println("Current: LAGGING");
      }
      else if (phaseAngle < -1.0) {
        Serial.println("Current: LEADING");
      }
      else {
        Serial.println("Current: IN PHASE");
      }

    } else {

      Serial.println("Waiting for valid zero crossings...");
    }

    Serial.println("============================");
  }
}
