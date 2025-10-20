//Curtin University
//Mechatronics Engineering
// Optimized Bang-Bang Line Follower with Dual Motor Speed Control
// UPDATED: Now uses speedPercentLeft and speedPercentRight for independent motor control
// Both outputs now have same polarity (both forward)
// Smart line recovery - remembers which sensor lost white first

// ============================================
// CONSTANTS - Hardware Configuration
// ============================================
const byte DACPIN1[8] = {9, 8, 7, 6, 5, 4, 3, 2};           // LSB → MSB
const byte DACPIN2[8] = {A2, A3, A4, A5, A1, A0, 11, 10};   // LSB → MSB
const byte SENSOR1 = A6;  // Left sensor
const byte SENSOR2 = A7;  // Right sensor

const byte START = 255;
const byte INPUT1 = 0;
const byte INPUT2 = 1;
const byte OUTPUT1 = 2;
const byte OUTPUT2 = 3;

const int WHITE_THRESHOLD = 30;  // Threshold for white detection
const unsigned long SEARCH_TIMEOUT = 2000;  // 2 seconds timeout for search direction switch

// ============================================
// SPEED & MOTOR CONTROL VARIABLES
// ============================================
// NEW: Separate speed control for left (Motor A6) and right (Motor A7) motors
int speedPercentLeft = 40;   // Default 40% - Left motor (Motor A6)
int speedPercentRight = 40;  // Default 40% - Right motor (Motor A7)

// Calculated DAC values for left motor (updated by calculateSpeeds())
byte forwardLeft = 179;
byte turnSpeedLeft = 205;
byte searchSpeedLeft = 230;

// Calculated DAC values for right motor (updated by calculateSpeeds())
byte forwardRight = 179;
byte turnSpeedRight = 205;
byte searchSpeedRight = 230;

// ============================================
// LINE TRACKING STATE VARIABLES
// ============================================
// Previous sensor states - critical for detecting line loss
bool prevLeftWhite = true;
bool prevRightWhite = true;

// Recovery direction memory
bool leftLostFirst = false;
bool rightLostFirst = false;

// Tracking variables
int lastOut = 0;  // -1 = left lost, +1 = right lost, 0 = unknown
bool searchingForLine = false;
unsigned long lineLostTime = 0;

// Wiggle search state (fallback when direction unknown)
unsigned long wiggleTimer = 0;
bool wiggleDir = false;

// ============================================
// SERIAL PROTOCOL VARIABLES
// ============================================
byte output1 = 255;
byte output2 = 255;
byte input1 = 0;
byte input2 = 0;

// ============================================
// DAC OUTPUT FUNCTIONS - Time Critical
// ============================================
inline void outputToDAC1(byte data) {
  // Motor A6 (Left) output
  for (int i = 0; i < 8; i++) {
    digitalWrite(DACPIN1[i], (data >> i) & 1);
  }
}

inline void outputToDAC2(byte data) {
  // Motor A7 (Right) output
  for (int i = 0; i < 8; i++) {
    digitalWrite(DACPIN2[i], (data >> i) & 1);
  }
}

// ============================================
// INITIALIZATION FUNCTIONS
// ============================================
void initDACs() {
  for (int i = 0; i < 8; i++) {
    pinMode(DACPIN1[i], OUTPUT);
    pinMode(DACPIN2[i], OUTPUT);
  }
}

void calculateSpeeds() {
  // LEFT MOTOR (A6) calculations
  forwardLeft = 128 + (127 * speedPercentLeft / 100);
  int turnPercentLeft = min(speedPercentLeft + 35, 100);
  turnSpeedLeft = 128 + (127 * turnPercentLeft / 100);
  int searchPercentLeft = min(speedPercentLeft + 40, 100);
  searchSpeedLeft = 128 + (127 * searchPercentLeft / 100);
  
  // RIGHT MOTOR (A7) calculations
  forwardRight = 128 + (127 * speedPercentRight / 100);
  int turnPercentRight = min(speedPercentRight + 35, 100);
  turnSpeedRight = 128 + (127 * turnPercentRight / 100);
  int searchPercentRight = min(speedPercentRight + 40, 100);
  searchSpeedRight = 128 + (127 * searchPercentRight / 100);
  
  Serial.print(F("Speed Left (A6): "));
  Serial.print(speedPercentLeft);
  Serial.print(F("% | Speed Right (A7): "));
  Serial.println(speedPercentRight);
  Serial.print(F("Fwd L: ")); Serial.print(forwardLeft);
  Serial.print(F(" | Fwd R: ")); Serial.print(forwardRight);
  Serial.print(F(" | Turn L: ")); Serial.print(turnSpeedLeft);
  Serial.print(F(" | Turn R: ")); Serial.println(turnSpeedRight);
}

// ============================================
// SERIAL COMMUNICATION HANDLER
// ============================================
void handleSerialCommand() {
  if (Serial.available() == 0) return;
  
  char incoming = Serial.read();

  // NEW: Speed commands now support left/right: 'L' or 'R' + number
  // Examples: L50 (set left motor to 50%), R75 (set right motor to 75%)
  // Or use single 'S' for both motors to same speed (legacy support)
  if (incoming == 'S' || incoming == 's') {
    delay(10);  // Wait for number
    if (Serial.available() > 0) {
      int newSpeed = Serial.parseInt();
      if (newSpeed >= 0 && newSpeed <= 100) {
        speedPercentLeft = newSpeed;
        speedPercentRight = newSpeed;
        calculateSpeeds();
      } else {
        Serial.println(F("ERROR: Speed must be 0-100%"));
      }
    }
  }
  // NEW: Set left motor speed only
  else if (incoming == 'L' || incoming == 'l') {
    delay(10);  // Wait for number
    if (Serial.available() > 0) {
      int newSpeed = Serial.parseInt();
      if (newSpeed >= 0 && newSpeed <= 100) {
        speedPercentLeft = newSpeed;
        calculateSpeeds();
      } else {
        Serial.println(F("ERROR: Speed must be 0-100%"));
      }
    }
  }
  // NEW: Set right motor speed only
  else if (incoming == 'R' || incoming == 'r') {
    delay(10);  // Wait for number
    if (Serial.available() > 0) {
      int newSpeed = Serial.parseInt();
      if (newSpeed >= 0 && newSpeed <= 100) {
        speedPercentRight = newSpeed;
        calculateSpeeds();
      } else {
        Serial.println(F("ERROR: Speed must be 0-100%"));
      }
    }
  }
  // Original 4-byte protocol
  else if (incoming == START && Serial.available() >= 3) {
    byte startByte = START;
    byte commandByte = Serial.read();
    byte dataByte = Serial.read();
    byte checkByte = Serial.read();
    byte checkSum = startByte + commandByte + dataByte;

    if (checkByte == checkSum) {
      switch (commandByte) {
        case INPUT1:
          input1 = digitalRead(SENSOR1);
          Serial.write(START);
          Serial.write(commandByte);
          Serial.write(input1);
          Serial.write(START + commandByte + input1);
          break;
        case INPUT2:
          input2 = digitalRead(SENSOR2);
          Serial.write(START);
          Serial.write(commandByte);
          Serial.write(input2);
          Serial.write(START + commandByte + input2);
          break;
        case OUTPUT1:
          output1 = dataByte;
          outputToDAC1(output1);
          break;
        case OUTPUT2:
          output2 = dataByte;
          outputToDAC2(output2);
          break;
      }
    }
  }
}

// ============================================
// SETUP - Run Once
// ============================================
void setup() {
  Serial.begin(9600);
  initDACs();
  calculateSpeeds();
  
  Serial.println(F("=== Dual Motor Line Follower Ready ==="));
  Serial.println(F("Commands:"));
  Serial.println(F("  S<num>  - Set both motors speed (e.g., S50)"));
  Serial.println(F("  L<num>  - Set LEFT motor (A6) speed (e.g., L60)"));
  Serial.println(F("  R<num>  - Set RIGHT motor (A7) speed (e.g., R40)"));
  Serial.println(F("Valid range: 0-100%"));
  Serial.println(F("========================================"));
}

// ============================================
// MAIN LOOP - Optimized Execution Order
// ============================================
void loop() {
  // ===== STEP 1: READ SENSORS (Time Critical) =====
  int leftRaw  = analogRead(SENSOR1);
  int rightRaw = analogRead(SENSOR2);
  bool leftWhite  = (leftRaw  <= WHITE_THRESHOLD);
  bool rightWhite = (rightRaw <= WHITE_THRESHOLD);

  // ===== STEP 2: DETECT LINE LOSS TRANSITIONS =====
  if (prevLeftWhite && !leftWhite && prevRightWhite) {
    leftLostFirst = true;
    rightLostFirst = false;
    lineLostTime = millis();
  }
  if (prevRightWhite && !rightWhite && prevLeftWhite) {
    rightLostFirst = true;
    leftLostFirst = false;
    lineLostTime = millis();
  }

  // ===== STEP 3: BANG-BANG CONTROL LOGIC (NOW WITH DUAL SPEEDS) =====
  if (leftWhite && rightWhite) {
    // CASE 1: Both on white → Go straight
    lastOut = 0;
    searchingForLine = false;
    outputToDAC1(forwardLeft);      // Left motor at left speed
    outputToDAC2(forwardRight);     // Right motor at right speed
  }
  else if (!leftWhite && rightWhite) {
    // CASE 2: Left off line → Turn RIGHT
    lastOut = -1;
    searchingForLine = false;
    outputToDAC1(turnSpeedLeft);    // Speed up left motor
    outputToDAC2(forwardRight);     // Keep right at normal speed
  }
  else if (leftWhite && !rightWhite) {
    // CASE 3: Right off line → Turn LEFT
    lastOut = 1;
    searchingForLine = false;
    outputToDAC1(forwardLeft);      // Keep left at normal speed
    outputToDAC2(turnSpeedRight);   // Speed up right motor
  }
  else {
    // CASE 4: Both on black → LINE LOST - Smart Recovery
    searchingForLine = true;
    
    if (leftLostFirst) {
      // Left lost first → Search RIGHT
      outputToDAC1(searchSpeedLeft);
      outputToDAC2(128);
    } 
    else if (rightLostFirst) {
      // Right lost first → Search LEFT
      outputToDAC1(128);
      outputToDAC2(searchSpeedRight);
    } 
    else if (lastOut != 0) {
      // Use lastOut as backup
      if (lastOut < 0) {
        outputToDAC1(searchSpeedLeft);
        outputToDAC2(128);
      } else {
        outputToDAC1(128);
        outputToDAC2(searchSpeedRight);
      }
    } 
    else {
      // Last resort: Wiggle search
      unsigned long now = millis();
      if (now - wiggleTimer > 300) {
        wiggleDir = !wiggleDir;
        wiggleTimer = now;
      }
      outputToDAC1(wiggleDir ? searchSpeedLeft : 128);
      outputToDAC2(wiggleDir ? 128 : searchSpeedRight);
    }
    
    // Timeout: Switch search direction if not found
    if (millis() - lineLostTime > SEARCH_TIMEOUT) {
      leftLostFirst = !leftLostFirst;
      rightLostFirst = !rightLostFirst;
      lineLostTime = millis();
    }
  }

  // ===== STEP 4: UPDATE STATE MEMORY =====
  prevLeftWhite = leftWhite;
  prevRightWhite = rightWhite;

  // ===== STEP 5: DEBUG OUTPUT =====
  Serial.print(F("L:")); Serial.print(leftRaw);
  Serial.print(leftWhite ? F("(W)") : F("(B)"));
  Serial.print(F(" R:")); Serial.print(rightRaw);
  Serial.print(rightWhite ? F("(W)") : F("(B)"));
  Serial.print(F(" Loss:"));
  if (leftLostFirst) Serial.print(F("L"));
  else if (rightLostFirst) Serial.print(F("R"));
  else Serial.print(F("-"));
  Serial.print(F(" Out:")); Serial.println(lastOut);

  // ===== STEP 6: HANDLE SERIAL COMMANDS =====
  handleSerialCommand();

  // ===== STEP 7: LOOP TIMING =====
  delay(15);  // ~67Hz loop rate
}