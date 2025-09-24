#include <Servo.h>

// Eyelid servos
Servo servoUpperRight;
Servo servoLowerRight;
Servo servoLowerLeft;
Servo servoUpperLeft;

// Eye rotation servos
Servo servoEyesX;
Servo servoEyesY;

// Neutral positions
const int neutralUpperRight = 90;
const int neutralUpperLeft  = 100;
const int neutralLowerRight = 90;
const int neutralLowerLeft  = 80;
const int neutralEyesX      = 90;
const int neutralEyesY      = 90;

// Blink positions
const int closedUpperRight = 130;
const int closedUpperLeft  = 61;
const int closedLowerRight = 40;
const int closedLowerLeft  = 130;

// Eye rotation range
const int eyesXLeft  = 10;
const int eyesXRight = 170;
const int eyesYUp    = 10;
const int eyesYDown  = 165;

// Sleep flag
bool asleep = false;

void setup() {
  Serial.begin(9600);

  // Attach servos
  servoUpperRight.attach(6);
  servoLowerRight.attach(7);
  servoLowerLeft.attach(9);
  servoUpperLeft.attach(11);
  servoEyesX.attach(5);
  servoEyesY.attach(3);

  // Start in neutral position
  openEyelids();
  servoEyesX.write(neutralEyesX);
  servoEyesY.write(neutralEyesY);
  delay(200);
}

// Function to close eyelids briefly (blink)
void blinkEyes() {
  if (asleep) return; // don’t blink when asleep

  servoUpperRight.write(closedUpperRight);
  servoUpperLeft.write(closedUpperLeft);
  servoLowerRight.write(closedLowerRight);
  servoLowerLeft.write(closedLowerLeft);

  delay(200);
  openEyelids();
}

// Function to keep eyelids closed (sleep)
void sleepEyes() {
  servoUpperRight.write(closedUpperRight);
  servoUpperLeft.write(closedUpperLeft);
  servoLowerRight.write(closedLowerRight);
  servoLowerLeft.write(closedLowerLeft);
  asleep = true;  // lock sleep mode
  Serial.println("ASLEEP"); // acknowledgement to host
}

// Function to open eyelids to neutral (wake)
void openEyelids() {
  servoUpperRight.write(neutralUpperRight);
  servoUpperLeft.write(neutralUpperLeft);
  servoLowerRight.write(neutralLowerRight);
  servoLowerLeft.write(neutralLowerLeft);
  asleep = false; // wake up
  delay(200);
}

// Helper to wake (explicit from host)
void wakeEyes() {
  openEyelids();
  Serial.println("AWAKE"); // acknowledgement to host
}

void loop() {
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    cmd.toUpperCase();

    if (cmd == "SLEEP") {
      sleepEyes();
    }
    else if (cmd == "WAKE") {
      // explicit wake command
      wakeEyes();
    }
    else if (cmd == "OPEN") {
      // only open if not asleep (guard)
      if (!asleep) openEyelids();
    }
    else if (cmd == "BLINK") {
      blinkEyes();
    }
    else if (!asleep) {
      // Handle servo X,Y positions only if awake
      int commaIndex = cmd.indexOf(',');
      if (commaIndex > 0) {
        int x = cmd.substring(0, commaIndex).toInt();
        int y = cmd.substring(commaIndex + 1).toInt();

        x = constrain(x, eyesXLeft, eyesXRight);
        y = constrain(y, eyesYUp, eyesYDown);

        servoEyesX.write(x);
        servoEyesY.write(y);
      }
    }
    // anything else ignored when asleep
  }
}
