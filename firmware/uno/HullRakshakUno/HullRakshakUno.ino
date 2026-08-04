#include <avr/wdt.h>

// ELEGOO Conqueror TB6612 pin mapping.
constexpr uint8_t PIN_RIGHT_PWM = 5;
constexpr uint8_t PIN_LEFT_PWM = 6;
constexpr uint8_t PIN_RIGHT_DIR = 7;
constexpr uint8_t PIN_LEFT_DIR = 8;
constexpr uint8_t PIN_MOTOR_STBY = 3;
constexpr uint8_t PIN_LINE_RIGHT = A0;
constexpr uint8_t PIN_LINE_MIDDLE = A1;
constexpr uint8_t PIN_LINE_LEFT = A2;
constexpr uint8_t PIN_ULTRASONIC_ECHO = 12;
constexpr uint8_t PIN_ULTRASONIC_TRIGGER = 13;

constexpr int16_t MAX_PWM = 100;
constexpr uint16_t MAX_MOTION_MS = 3000;
constexpr uint32_t ULTRASONIC_TIMEOUT_US = 30000;
constexpr size_t FRAME_CAPACITY = 160;

char frameBuffer[FRAME_CAPACITY];
size_t frameLength = 0;
bool receivingFrame = false;
bool motionActive = false;
uint32_t motionStartedAt = 0;
uint16_t motionDurationMs = 0;
char motionRequestId[17] = "MOVE";

void stopMotors() {
  analogWrite(PIN_LEFT_PWM, 0);
  analogWrite(PIN_RIGHT_PWM, 0);
  digitalWrite(PIN_MOTOR_STBY, LOW);
  motionActive = false;
}

void setOneMotor(uint8_t pwmPin, uint8_t directionPin, int16_t pwm) {
  digitalWrite(directionPin, pwm >= 0 ? HIGH : LOW);
  analogWrite(pwmPin, abs(pwm));
}

void startMotion(int16_t leftPwm, int16_t rightPwm, uint16_t durationMs,
                 const char *requestId) {
  if (abs(leftPwm) > MAX_PWM || abs(rightPwm) > MAX_PWM || durationMs == 0 ||
      durationMs > MAX_MOTION_MS) {
    stopMotors();
    Serial.print(F("{error_motion_limits}"));
    return;
  }

  strncpy(motionRequestId, requestId, sizeof(motionRequestId) - 1);
  motionRequestId[sizeof(motionRequestId) - 1] = '\0';
  digitalWrite(PIN_MOTOR_STBY, HIGH);
  setOneMotor(PIN_LEFT_PWM, PIN_LEFT_DIR, leftPwm);
  setOneMotor(PIN_RIGHT_PWM, PIN_RIGHT_DIR, rightPwm);
  motionStartedAt = millis();
  motionDurationMs = durationMs;
  motionActive = true;
}

bool rawMotionWithinLimits(long leftPwm, long rightPwm, long durationMs) {
  return leftPwm >= -MAX_PWM && leftPwm <= MAX_PWM &&
         rightPwm >= -MAX_PWM && rightPwm <= MAX_PWM && durationMs >= 1 &&
         durationMs <= MAX_MOTION_MS;
}

void printValue(const char *label, long value) {
  Serial.print('{');
  Serial.print(label);
  Serial.print('_');
  Serial.print(value);
  Serial.print('}');
}

long readUltrasonicCm() {
  digitalWrite(PIN_ULTRASONIC_TRIGGER, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_ULTRASONIC_TRIGGER, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_ULTRASONIC_TRIGGER, LOW);
  const unsigned long pulse =
      pulseIn(PIN_ULTRASONIC_ECHO, HIGH, ULTRASONIC_TIMEOUT_US);
  return pulse == 0 ? 0 : static_cast<long>(pulse / 58UL);
}

bool readIntegerField(const char *json, const char *key, long *value) {
  char pattern[8];
  snprintf(pattern, sizeof(pattern), "\"%s\"", key);
  const char *field = strstr(json, pattern);
  if (field == nullptr) {
    return false;
  }
  const char *colon = strchr(field + strlen(pattern), ':');
  if (colon == nullptr) {
    return false;
  }
  char *end = nullptr;
  const long parsed = strtol(colon + 1, &end, 10);
  if (end == colon + 1) {
    return false;
  }
  *value = parsed;
  return true;
}

bool readStringField(const char *json, const char *key, char *value,
                     size_t capacity) {
  char pattern[8];
  snprintf(pattern, sizeof(pattern), "\"%s\"", key);
  const char *field = strstr(json, pattern);
  if (field == nullptr) {
    return false;
  }
  const char *colon = strchr(field + strlen(pattern), ':');
  const char *start = colon == nullptr ? nullptr : strchr(colon + 1, '"');
  if (start == nullptr) {
    return false;
  }
  ++start;
  const char *end = strchr(start, '"');
  if (end == nullptr || static_cast<size_t>(end - start) >= capacity) {
    return false;
  }
  const size_t length = static_cast<size_t>(end - start);
  memcpy(value, start, length);
  value[length] = '\0';
  return true;
}

void handleCommand(const char *json) {
  long commandValue = -1;
  if (!readIntegerField(json, "N", &commandValue)) {
    stopMotors();
    Serial.print(F("{error_json}"));
    return;
  }

  const int command = static_cast<int>(commandValue);
  char requestId[17] = "R";
  readStringField(json, "H", requestId, sizeof(requestId));

  if (command == 100) {
    stopMotors();
    Serial.print(F("{ok}"));
    return;
  }

  // Read-only capability probe. Python must receive CAP_1 before it is allowed
  // to send the project-specific differential motion command.
  if (command == 41) {
    Serial.print(F("{CAP_1}"));
    return;
  }

  if (command == 40) {
    long left = 0;
    long right = 0;
    long duration = 0;
    if (!readIntegerField(json, "L", &left) ||
        !readIntegerField(json, "R", &right) ||
        !readIntegerField(json, "T", &duration)) {
      stopMotors();
      Serial.print(F("{error_motion_fields}"));
      return;
    }
    if (!rawMotionWithinLimits(left, right, duration)) {
      stopMotors();
      Serial.print(F("{error_motion_limits}"));
      return;
    }
    startMotion(static_cast<int16_t>(left), static_cast<int16_t>(right),
                static_cast<uint16_t>(duration), requestId);
    return;
  }

  // Preserve the exact legacy N=2 command used by the raw serial diagnostic.
  if (command == 2) {
    long directionValue = 0;
    long speedValue = 0;
    long durationValue = 0;
    if (!readIntegerField(json, "D1", &directionValue) ||
        !readIntegerField(json, "D2", &speedValue) ||
        !readIntegerField(json, "T", &durationValue)) {
      stopMotors();
      Serial.print(F("{error_motion_fields}"));
      return;
    }
    const int direction = static_cast<int>(directionValue);
    if (speedValue < 1 || speedValue > MAX_PWM || durationValue < 1 ||
        durationValue > MAX_MOTION_MS) {
      stopMotors();
      Serial.print(F("{error_motion_limits}"));
      return;
    }
    const int speed = static_cast<int>(speedValue);
    int16_t left = 0;
    int16_t right = 0;
    if (direction == 1) {
      left = -speed;
      right = speed;
    } else if (direction == 2) {
      left = speed;
      right = -speed;
    } else if (direction == 3) {
      left = speed;
      right = speed;
    } else if (direction == 4) {
      left = -speed;
      right = -speed;
    } else {
      stopMotors();
      Serial.print(F("{error_direction}"));
      return;
    }
    startMotion(left, right, static_cast<uint16_t>(durationValue), requestId);
    return;
  }

  if (command == 22) {
    long sensorValue = -1;
    if (!readIntegerField(json, "D1", &sensorValue)) {
      Serial.print(F("{error_sensor}"));
      return;
    }
    const int sensor = static_cast<int>(sensorValue);
    if (sensor == 0) {
      printValue(requestId, analogRead(PIN_LINE_LEFT));
    } else if (sensor == 1) {
      printValue(requestId, analogRead(PIN_LINE_MIDDLE));
    } else if (sensor == 2) {
      printValue(requestId, analogRead(PIN_LINE_RIGHT));
    } else {
      Serial.print(F("{error_sensor}"));
    }
    return;
  }

  long subcommand = 0;
  if (command == 21 && readIntegerField(json, "D1", &subcommand) &&
      subcommand == 2) {
    printValue(requestId, readUltrasonicCm());
    return;
  }

  stopMotors();
  Serial.print(F("{error_command}"));
}

void readSerialFrames() {
  while (Serial.available() > 0) {
    const char incoming = static_cast<char>(Serial.read());
    if (incoming == '{') {
      receivingFrame = true;
      frameLength = 0;
      frameBuffer[frameLength++] = incoming;
    } else if (receivingFrame) {
      if (frameLength >= FRAME_CAPACITY - 1) {
        receivingFrame = false;
        frameLength = 0;
        stopMotors();
        Serial.print(F("{error_frame_length}"));
        continue;
      }
      frameBuffer[frameLength++] = incoming;
      if (incoming == '}') {
        frameBuffer[frameLength] = '\0';
        receivingFrame = false;
        handleCommand(frameBuffer);
        frameLength = 0;
      }
    }
  }
}

void enforceMotionDeadline() {
  if (motionActive &&
      static_cast<uint32_t>(millis() - motionStartedAt) >= motionDurationMs) {
    char completedRequestId[sizeof(motionRequestId)];
    strncpy(completedRequestId, motionRequestId, sizeof(completedRequestId));
    completedRequestId[sizeof(completedRequestId) - 1] = '\0';
    stopMotors();
    Serial.print('{');
    Serial.print(completedRequestId);
    Serial.print(F("_ok}"));
  }
}

void setup() {
  pinMode(PIN_LEFT_PWM, OUTPUT);
  pinMode(PIN_RIGHT_PWM, OUTPUT);
  pinMode(PIN_LEFT_DIR, OUTPUT);
  pinMode(PIN_RIGHT_DIR, OUTPUT);
  pinMode(PIN_MOTOR_STBY, OUTPUT);
  pinMode(PIN_LINE_LEFT, INPUT);
  pinMode(PIN_LINE_MIDDLE, INPUT);
  pinMode(PIN_LINE_RIGHT, INPUT);
  pinMode(PIN_ULTRASONIC_ECHO, INPUT);
  pinMode(PIN_ULTRASONIC_TRIGGER, OUTPUT);
  digitalWrite(PIN_ULTRASONIC_TRIGGER, LOW);
  stopMotors();
  Serial.begin(9600);
  Serial.print(F("{HR_READY}"));
  wdt_enable(WDTO_2S);
}

void loop() {
  wdt_reset();
  enforceMotionDeadline();
  readSerialFrames();
  enforceMotionDeadline();
}
