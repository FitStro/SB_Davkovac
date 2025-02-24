#include <Stepper.h>
#include <Servo.h>

Servo myservo;
int pos = 0;

const int stepsPerRevolution = 2048; // 28BYJ motor má 2048 krokov na otočenie
// Stepper myStepper(stepsPerRevolution, 3, 5, 4, 6);

const int motorPin1 = 12;  
const int motorPin2 = 13;  

const int vibrPin1= 1;
const int vibrPin2 = 2; 

const int irSensorPin = 7;
const int vibrators[] = {8, 9, 10, 11}; 

int itemCount = 0;  
bool lastSensorState = LOW;  

void setup() {
  myservo.attach(3);
  pinMode(motorPin1, OUTPUT);
  pinMode(motorPin2, OUTPUT);
  pinMode(vibrPin1, OUTPUT);
  pinMode(vibrPin2, OUTPUT);

  digitalWrite(motorPin2, LOW);
  analogWrite(motorPin2, 0);
  digitalWrite(vibrPin1, LOW);
  digitalWrite(vibrPin2, LOW);

  // myStepper.setSpeed(10); 
  itemCount--;

  pinMode(irSensorPin, INPUT);
  for (int i = 0; i < 4; i++) {
    pinMode(vibrators[i], OUTPUT);
    digitalWrite(vibrators[i], LOW); 
  }

  Serial.begin(9600);
}

void loop() {
  // Čítanie sériových dát
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');

    if (command.startsWith("TURN:")) {
      int degrees = command.substring(5).toInt();
      int steps = (stepsPerRevolution / 360) * degrees;
      // myStepper.step(steps);
      Serial.println("Stepper moved: " + String(degrees) + " degrees.");
    }
    
    if (command.startsWith("MOTORPIN2:")) {
      int state = command.substring(10).toInt();
      analogWrite(motorPin2, state);
      Serial.println("MotorPin2 set to: " + String(state));
    }

    if (command.startsWith("VIBRATE:")) {
      int index = command.substring(8).toInt(); 
      if (index >= 0 && index < 4) {
        digitalWrite(vibrators[index], !digitalRead(vibrators[index]));
        Serial.println("Vibrator " + String(index) + " toggled.");
      }
    }
    if (command.startsWith("VibrPin2:")) {
      int state1 = command.substring(10).toInt();
      digitalWrite(vibrPin2, state1);
      Serial.println("vibrPin2 set to: " + String(state1));
      }
    if (command.startsWith("SERVO:")) {
      int pos = command.substring(6).toInt();
      myservo.write(pos);
      delay(15);
    }
    }
  bool sensorState = digitalRead(irSensorPin);
  if (sensorState == HIGH && lastSensorState == LOW) {
    itemCount++;
    delay(350);
    Serial.println("Item count: " + String(itemCount));
  }
  lastSensorState = sensorState;
}
