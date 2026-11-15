


==🔴Your Arduino UNO is reporting:==
==🔴`Voltage ADC: 46 Current ADC: 691 Time Difference: 8000 us Phase Angle: 172.80 degrees Power Factor: -0.992`==
==🔴**The result suggests a problem with the zero-crossing measurement or signal polarity.** It does not necessarily mean your actual power factor is −0.992.==

## 1. Why is the phase angle approximately 173°?

For 60 Hz:

T=160=16.667 msT=601​=16.667 ms

Your measured time difference is:

Δt=8.0 msΔt=8.0 ms

Therefore:

θ=8.016.667×360∘θ=16.6678.0​×360∘θ=172.8∘θ=172.8∘​

This is almost 180°, corresponding to half an AC cycle.

There are several possible causes:

1. **The LM393 voltage and current outputs have opposite polarities.**
2. The PT or CT signal polarity is reversed.
3. The comparator circuits detect different zero-crossing directions.
4. One comparator has an incorrect reference voltage.
5. The current and voltage signals are not being paired correctly.

The first three possibilities are especially worth checking.

## 2. Check the ADC readings

Your readings show:

|Input|ADC reading|Approximate voltage|
|---|--:|--:|
|A0 (Voltage)|46|0.225 V|
|A3 (Current)|691|3.38 V|

Assuming a 5 V ADC reference:

VADC=ADC1023×5VADC​=1023ADC​×5

An LM393 normally produces a HIGH or LOW output, but your current reading of 691 is between these levels.

This could indicate a weak pull-up, an unstable output, or a transition being sampled. A single intermediate reading does not establish a fault.

Check that each LM393 output switches reliably between approximately 0 V and 5 V.

## 3. Check whether the signals are inverted

If your LM393 outputs have opposite polarities, one signal may need to be inverted in software.

For example, change:

```
bool currentState = currentADC > THRESHOLD;
```

to:

```
bool currentState = currentADC < THRESHOLD;
```

Keep the voltage input unchanged:

```
bool voltageState = voltageADC > THRESHOLD;
```

This makes the program detect the opposite edge of the current comparator signal.

**Only make this change if you confirm that the comparator outputs represent opposite crossing directions.** Otherwise, it could introduce an additional 180° error.

## 4. Test the corrected phase difference

If the two comparator signals are inverted relative to each other, the measured 172.8° could correspond to a physical phase difference of approximately:

θcorrected=172.8∘−180∘θcorrected​=172.8∘−180∘θcorrected=−7.2∘θcorrected​=−7.2∘​

Then:

PF=cos⁡(−7.2∘)PF=cos(−7.2∘)PF≈0.992PF≈0.992​

This is a plausible result for a nearly resistive load, but it is **not yet a verified power-factor measurement**.

## 5. Recommended test

First, test your circuit using a resistive load, such as an incandescent lamp.

For a nearly resistive load, the voltage and current should have approximately the same phase.

Expected result:

`Time Difference: approximately 0 us Phase Angle: approximately 0 degrees Power Factor: approximately 1.000`

Small differences are expected because of PT/CT phase shifts, comparator delays, and ADC sampling.

Also, your readings remain almost identical over several seconds. This suggests the measurement is stable, but it does not prove that the detected edges correspond to the correct zero crossings.

**One important question:** Are your A0 and A3 signals connected to **two separate LM393 comparators**, one receiving the PT voltage signal and the other receiving the CT current signal?

If so, I recommend checking the polarity of their outputs before changing the phase-calculation code.

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

