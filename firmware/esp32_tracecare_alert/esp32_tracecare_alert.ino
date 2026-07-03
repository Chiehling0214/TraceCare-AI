/*
  TraceCare AI ESP32 physical alert prototype.
  This firmware is for a competition demo alert device only.
  It must not be connected to or used to control medical equipment.

  Serial protocol: tracecare-device-v1
  Commands:
    PING seq=1 protocol=tracecare-device-v1
    SET seq=2 state=WARNING led=YELLOW_BLINKING buzzer=SHORT_BEEP protocol=tracecare-device-v1
  Responses:
    PONG seq=1 status=OK protocol=tracecare-device-v1
    ACK seq=2 status=OK protocol=tracecare-device-v1
    ERR seq=2 code=BAD_COMMAND protocol=tracecare-device-v1
*/

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
    if (line.length() > 0) {
      handleCommand(line);
    }
  }
  applyOutputs();
}

void handleCommand(String line) {
  String seq = valueFor(line, "seq");
  String protocol = valueFor(line, "protocol");
  if (protocol != "tracecare-device-v1") {
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

  if (currentLed == "GREEN_SOLID") {
    green = true;
  } else if (currentLed == "YELLOW_SOLID") {
    yellow = true;
  } else if (currentLed == "YELLOW_BLINKING") {
    yellow = blinkOn;
  } else if (currentLed == "RED_BLINKING") {
    red = blinkOn;
  }

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

  unsigned long interval = SHORT_BEEP_INTERVAL_MS;
  unsigned long duration = SHORT_BEEP_DURATION_MS;
  if (currentBuzzer == "INTERMITTENT") {
    interval = INTERMITTENT_BEEP_INTERVAL_MS;
    duration = INTERMITTENT_BEEP_DURATION_MS;
  }

  if (now - lastBeepCycle >= interval) {
    lastBeepCycle = now;
  }
  digitalWrite(BUZZER_PIN, (now - lastBeepCycle) <= duration ? HIGH : LOW);
}
