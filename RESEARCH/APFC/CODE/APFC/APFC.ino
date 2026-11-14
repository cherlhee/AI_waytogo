

// LM393 Zero Crossing Detection
// Arduino UNO
//
// A0 = Voltage Zero Crossing
// A3 = Current Zero Crossing

const byte VOLT_PIN = A3;
const byte CURR_PIN = A0;

unsigned long voltageTime = 0;
unsigned long currentTime = 0;

bool prevVoltage = LOW;
bool prevCurrent = LOW;

const float FREQUENCY = 60.0; // Change to 50.0 if needed





void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(2, OUTPUT);


  Serial.begin(115200);

  pinMode(VOLT_PIN, INPUT_PULLUP);
  pinMode(CURR_PIN, INPUT_PULLUP);

  prevVoltage = digitalRead(VOLT_PIN);
  prevCurrent = digitalRead(CURR_PIN);

  Serial.println("LM393 Zero Crossing Detection");

  
}

void loop() {


  // relay; D2 HIGH
  digitalWrite(2, HIGH);
  delay(1000);

  // relay; D2 LOW
  digitalWrite(2, LOW);
  delay(1000);





  bool voltageState = digitalRead(VOLT_PIN);
  bool currentState = digitalRead(CURR_PIN);



  Serial.print("voltage: ");
  Serial.print(voltageState);
  Serial.println(" volt");

  Serial.print("current: ");
  Serial.print(currentState);
  Serial.println(" ampere");


        
  // Voltage rising edge
  if (voltageState == HIGH && prevVoltage == LOW) {
    voltageTime = micros();
  }

  // Current rising edge
  if (currentState == HIGH && prevCurrent == LOW) {

    currentTime = micros();

    if (voltageTime != 0) {

      long timeDifference =
          (long)(currentTime - voltageTime);

      float phaseAngle =
          timeDifference * FREQUENCY * 360.0 / 1000000.0;

      float powerFactor =
          cos(phaseAngle * PI / 180.0);

      Serial.print("Time Difference: ");
      Serial.print(timeDifference);
      Serial.println(" us");

      Serial.print("Phase Angle: ");
      Serial.print(phaseAngle);
      Serial.println(" degrees");

      Serial.print("Power Factor: ");
      Serial.println(powerFactor, 3);

      Serial.println("-------------------");
    }
  }

  prevVoltage = voltageState;
  prevCurrent = currentState;
  
}
