#include <SPI.h>
#include <MFRC522.h>
#include <TM1637Display.h>
#include <TimerOne.h>

String inputString = "";
String data = "";
int display_num = 0;

// pin za kapacitivni senzor dodira
const int touchPin = 2;

volatile byte state = LOW;

// pinovi za rfid
#define SDA_PIN 10
#define RST_PIN 7

// pinovi za displej
const int CLK = 9;
const int DIO = 8;

// pinovi za ultrazvucni senzor
const int trigPin = 5;
const int echoPin = 6;

long trajanje;
int rastojanje;

volatile int voltage = 0;

// rfid citac kartica
MFRC522 mfrc522(SDA_PIN, RST_PIN);
// displej
TM1637Display display(CLK, DIO);

void setup() {
  Serial.begin(9600);
  
  SPI.begin();
  mfrc522.PCD_Init();

  // kapacitivni senzor
  pinMode(touchPin, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(touchPin), touch, CHANGE);

  // diode
  pinMode(3, OUTPUT);
  pinMode(4, OUTPUT);

  // ultrazvuk
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  // ekran
  display.setBrightness(7);

  Timer1.initialize(1000000);
  Timer1.attachInterrupt(voltageIsr);
}

void loop() {
  String out_data = "";
  // read ids
  out_data.concat(read_mfrcIDs());
  out_data.concat(',');

  // pokazuje broj 
  display.showNumberDec(get_num());

  out_data.concat(ultrasound());
  out_data.concat(',');

  // senzor dodira
  out_data.concat(state);
  out_data.concat(',');

  // voltmetar
  out_data.concat(voltage);

  Serial.println(out_data);

  if (data[0] == '1') {
    digitalWrite(3, HIGH);
  } else {
    digitalWrite(3, LOW);
  }

  if (data[1] == '1') {
    digitalWrite(4, HIGH);
  } else {
    digitalWrite(4, LOW);
  }
}

int get_num() {
  String n;
  int i = 2;
  while (data[i]) {
    n.concat(data[i]);
    i++;
  }
  return n.toInt();
}

// read serial data
void serialEvent() {
  while(Serial.available()) {
    char inChar = (char)Serial.read();
    if (inChar == '\n') {
      data = inputString;
      inputString = "";
    }
    else {
      inputString += inChar;
    }
  }
}

void voltageIsr() {
  voltage = analogRead(A0);
  voltage = voltage * (5 / 1023.0);
}

// Ultrasound sensor
int ultrasound() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  trajanje = pulseIn(echoPin, HIGH);

  rastojanje = trajanje*0.034/2;

  return rastojanje;
}

// RFID CARD
String read_mfrcIDs() {
  if (!mfrc522.PICC_IsNewCardPresent()) {
    return "0";
  }
  if (!mfrc522.PICC_ReadCardSerial()) {
    return "0";
  }
  
  String content = "";
  for (byte i =0; i < mfrc522.uid.size; i++) {
    content.concat(String(mfrc522.uid.uidByte[i], HEX));
    content.concat(" ");
  }
  return content;
}

// funkcija za prekid
void touch() {
  state = !state;
  // upisati to u serial nekako
}
