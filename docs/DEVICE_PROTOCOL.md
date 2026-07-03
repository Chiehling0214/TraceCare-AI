# TraceCare AI Device Protocol

TraceCare AI Sprint 4 uses an optional ESP32 demo alert device. It is not a medical device and must not be connected to infusion pumps, ventilators, monitors, or any treatment equipment.

## Modes

- `simulated`: default mode. No hardware required.
- `usb_serial`: optional local ESP32 over USB Serial.

## Environment

```text
DEVICE_ADAPTER_MODE=simulated
DEVICE_SERIAL_PORT=
DEVICE_SERIAL_BAUD_RATE=115200
DEVICE_SERIAL_TIMEOUT_SECONDS=1.0
DEVICE_HEARTBEAT_TIMEOUT_SECONDS=3.0
```

Do not hard-code a COM port. On Windows the port may look like `COM3`; on Linux it may look like `/dev/ttyUSB0` or `/dev/ttyACM0`.

## Command Protocol

Protocol version: `tracecare-device-v1`

Commands are UTF-8 line-based strings ending in `\n`.

Heartbeat:

```text
PING seq=1 protocol=tracecare-device-v1
```

Heartbeat response:

```text
PONG seq=1 status=OK protocol=tracecare-device-v1
```

State command:

```text
SET seq=2 state=WARNING led=YELLOW_BLINKING buzzer=SHORT_BEEP protocol=tracecare-device-v1
```

State response:

```text
ACK seq=2 status=OK protocol=tracecare-device-v1
```

Error response:

```text
ERR seq=2 code=BAD_COMMAND protocol=tracecare-device-v1
```

`SET` is idempotent and safe to repeat. The firmware should set LEDs and buzzer to the requested state, not toggle based on previous command history.

## State Mapping

| Backend state | LED | Buzzer |
| --- | --- | --- |
| `NORMAL` | `GREEN_SOLID` | `OFF` |
| `WARNING` | `YELLOW_BLINKING` | `SHORT_BEEP` |
| `ACKNOWLEDGED` | `YELLOW_SOLID` | `OFF` |
| `CRITICAL` | `RED_BLINKING` | `INTERMITTENT` |

## ESP32 Wiring

Default firmware pins:

| Function | ESP32 pin |
| --- | --- |
| Green LED | GPIO 18 |
| Yellow LED | GPIO 19 |
| Red LED | GPIO 21 |
| Active buzzer | GPIO 22 |

Use appropriate resistors for LEDs. Use an active buzzer module suitable for ESP32 GPIO levels.

## Firmware Sketch

Paste this sketch into Arduino IDE or `arduino-cli` as `esp32_tracecare_alert.ino`.

```cpp
const int GREEN_LED_PIN = 18;
const int YELLOW_LED_PIN = 19;
const int RED_LED_PIN = 21;
const int BUZZER_PIN = 22;

const unsigned long BLINK_INTERVAL_MS = 500;
const unsigned long SHORT_BEEP_INTERVAL_MS = 2000;
const unsigned long SHORT_BEEP_DURATION_MS = 150;
const unsigned long INTERMITTENT_BEEP_INTERVAL_MS = 900;
const unsigned long INTERMITTENT_BEEP_DURATION_MS = 250;

String currentLed = "GREEN_SOLID";
String currentBuzzer = "OFF";
unsigned long lastBlinkToggle = 0;
unsigned long lastBeepCycle = 0;
bool blinkOn = false;

void setup() {
  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(YELLOW_LED_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  Serial.begin(115200);
  applyOutputs();
}

void loop() {
  if (Serial.available() > 0) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.length() > 0) handleCommand(line);
  }
  applyOutputs();
}

void handleCommand(String line) {
  String seq = valueFor(line, "seq");
  if (valueFor(line, "protocol") != "tracecare-device-v1") {
    sendError(seq, "BAD_PROTOCOL");
    return;
  }
  if (line.startsWith("PING ")) {
    Serial.println("PONG seq=" + seq + " status=OK protocol=tracecare-device-v1");
    return;
  }
  if (!line.startsWith("SET ")) {
    sendError(seq, "BAD_COMMAND");
    return;
  }
  String led = valueFor(line, "led");
  String buzzer = valueFor(line, "buzzer");
  if (!validLed(led) || !validBuzzer(buzzer)) {
    sendError(seq, "BAD_VALUE");
    return;
  }
  currentLed = led;
  currentBuzzer = buzzer;
  applyOutputs();
  Serial.println("ACK seq=" + seq + " status=OK protocol=tracecare-device-v1");
}

String valueFor(String line, String key) {
  String prefix = key + "=";
  int start = line.indexOf(prefix);
  if (start < 0) return "";
  start += prefix.length();
  int end = line.indexOf(' ', start);
  if (end < 0) end = line.length();
  return line.substring(start, end);
}

bool validLed(String led) {
  return led == "GREEN_SOLID" || led == "YELLOW_BLINKING" ||
         led == "YELLOW_SOLID" || led == "RED_BLINKING";
}

bool validBuzzer(String buzzer) {
  return buzzer == "OFF" || buzzer == "SHORT_BEEP" || buzzer == "INTERMITTENT";
}

void sendError(String seq, String code) {
  Serial.println("ERR seq=" + seq + " code=" + code + " protocol=tracecare-device-v1");
}

void applyOutputs() {
  bool green = false;
  bool yellow = false;
  bool red = false;
  unsigned long now = millis();
  if (now - lastBlinkToggle >= BLINK_INTERVAL_MS) {
    blinkOn = !blinkOn;
    lastBlinkToggle = now;
  }
  if (currentLed == "GREEN_SOLID") green = true;
  else if (currentLed == "YELLOW_SOLID") yellow = true;
  else if (currentLed == "YELLOW_BLINKING") yellow = blinkOn;
  else if (currentLed == "RED_BLINKING") red = blinkOn;
  digitalWrite(GREEN_LED_PIN, green ? HIGH : LOW);
  digitalWrite(YELLOW_LED_PIN, yellow ? HIGH : LOW);
  digitalWrite(RED_LED_PIN, red ? HIGH : LOW);
  applyBuzzer(now);
}

void applyBuzzer(unsigned long now) {
  if (currentBuzzer == "OFF") {
    digitalWrite(BUZZER_PIN, LOW);
    return;
  }
  unsigned long interval = currentBuzzer == "INTERMITTENT" ? INTERMITTENT_BEEP_INTERVAL_MS : SHORT_BEEP_INTERVAL_MS;
  unsigned long duration = currentBuzzer == "INTERMITTENT" ? INTERMITTENT_BEEP_DURATION_MS : SHORT_BEEP_DURATION_MS;
  if (now - lastBeepCycle >= interval) lastBeepCycle = now;
  digitalWrite(BUZZER_PIN, (now - lastBeepCycle) <= duration ? HIGH : LOW);
}
```

## Verification Status

This repository includes fake serial transport tests for heartbeat, command emission, offline fallback, and reconnect behavior. Real ESP32 LED, buzzer, heartbeat, disconnect, and reconnect behavior must be marked `NOT VERIFIED` until tested with hardware.
