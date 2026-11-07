




다음과 같이 수정해야 합니다.

```
digitalWrite(D2, LOW);
```

- `low` → `LOW` (대문자 사용)
- `D2`는 보드에 따라 사용 가능 여부가 다릅니다.
- Arduino UNO에서는 일반적으로 `2`를 사용합니다.
- ESP8266에서는 `D2`를 사용할 수 있습니다.
- ESP32에서는 보통 GPIO 번호인 `2`를 사용합니다.

```
void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(2, OUTPUT);
}

void loop() {
  // 내장 LED ON
  digitalWrite(LED_BUILTIN, HIGH);
  delay(1000);

  // 내장 LED OFF
  digitalWrite(LED_BUILTIN, LOW);
  delay(100);

  // D2 핀 LOW
  digitalWrite(2, LOW);
  delay(1000);

  // D2 핀 HIGH
  digitalWrite(2, HIGH);
  delay(1000);
}
```

