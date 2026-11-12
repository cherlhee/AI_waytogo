

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(2, OUTPUT);
}

void loop() {

  // 내장 LED ON
  //digitalWrite(LED_BUILTIN, HIGH);
  //delay(1000);

  // 내장 LED OFF
  //digitalWrite(LED_BUILTIN, LOW);
  //delay(1000);

  // D2 HIGH
  digitalWrite(2, HIGH);
  delay(4000);

  // D2 LOW
  digitalWrite(2, LOW);
  delay(4000);
}
