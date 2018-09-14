#include<SoftwareSerial.h>

//모터 PFW 설정
#define ENA_LEFT 10
#define FW_LEFT 11
#define BW_LEFT 12

//모터 PFW 설정
#define ENA_RIGHT 9
#define FW_RIGHT 8
#define BW_RIGHT 7

int bluetoothTx = 2;
int bluetoothRx = 3;


SoftwareSerial bluetooth(bluetoothTx, bluetoothRx);

void setup() {
  //왼쪽 바퀴 설정
  pinMode(FW_LEFT, OUTPUT);
  pinMode(BW_LEFT, OUTPUT);
  pinMode(ENA_LEFT, OUTPUT);

  //오른쪽 바퀴 설정
  pinMode(FW_RIGHT, OUTPUT);
  pinMode(BW_RIGHT, OUTPUT);
  pinMode(ENA_RIGHT, OUTPUT);
  
  bluetooth.begin(9600);
  Serial.begin(9600);
}
void forward() {
  digitalWrite(FW_LEFT, HIGH);
  digitalWrite(FW_RIGHT, HIGH);
  digitalWrite(BW_LEFT, LOW);
  digitalWrite(BW_RIGHT, LOW);
}

void backward() {
  digitalWrite(FW_LEFT, LOW);
  digitalWrite(FW_RIGHT, LOW);
  digitalWrite(BW_LEFT, HIGH);
  digitalWrite(BW_RIGHT, HIGH);
}

void stop_all() {
  digitalWrite(FW_LEFT, LOW);
  digitalWrite(FW_RIGHT, LOW);
  digitalWrite(BW_LEFT, LOW);
  digitalWrite(BW_RIGHT, LOW);
}

void turn_right() {
  digitalWrite(FW_LEFT, LOW);
  digitalWrite(FW_RIGHT, HIGH);
  digitalWrite(BW_LEFT, HIGH);
  digitalWrite(BW_RIGHT, LOW);
}

void turn_left() {
  digitalWrite(FW_LEFT, HIGH);
  digitalWrite(FW_RIGHT, LOW);
  digitalWrite(BW_LEFT, LOW);
  digitalWrite(BW_RIGHT, HIGH);
}


void setMotorSpeed(unsigned char mode, unsigned char speed){
    analogWrite(mode, speed);
}

void loop() {
  int x, y, a, b, s;
  int motorSpeed;
  
  if(bluetooth.available()) {
    if(bluetooth.find('X')) {
      x = bluetooth.parseInt();
      y = bluetooth.parseInt();
      a = bluetooth.parseInt();
      b = bluetooth.parseInt();
      s = bluetooth.parseInt();
    }
  }else {
    x = 500;
    y = 500;
    a = 500;
    b = 500;
    s = 1;
  }

  //블루투스 파싱 데이터 확인

  String X, Y, A, B, S;
  X = 'x';
  X.concat(x);
  X.concat("Ex");

  Y = 'y';
  Y.concat(y);
  Y.concat("Ey");

  A = 'a';
  A.concat(a);
  A.concat("Ea");

  B = 'b';
  B.concat(b);
  B.concat("Eb");

  S = 's';
  S.concat(s);
  S.concat("Es");
  
  Serial.print(X); 
  Serial.print(Y);
  Serial.print(A); 
  Serial.print(B);
  Serial.print(S);

  //휠 변화에 따른 속도 매핑
  if(x >= 0 && x <= 460 ) {
    motorSpeed = (255 - map(x, 0, 460, 0, 255));
  }else if(x > 460 && x < 560) {
    motorSpeed = 0;
  } else if(x >= 560) {
    motorSpeed = map(x, 560, 1023, 0, 255);
  }

  String M;
  M = 'm';
  M.concat(motorSpeed);
  M.concat("Em");
  
  Serial.println(M);
/*  
  //휠러 값에 의한 모터속도 조절
  if(motorSpeed >= 0 && motorSpeed <= 10) {
    setMotorSpeed(ENA_RIGHT, motorSpeed);
    setMotorSpeed(ENA_LEFT, 1);
  }else if( motorSpeed > 10 && motorSpeed <= 255 ) {
    setMotorSpeed(ENA_RIGHT, motorSpeed);
    setMotorSpeed(ENA_LEFT, motorSpeed-10);
  }
*/
  setMotorSpeed(ENA_RIGHT, motorSpeed);
  setMotorSpeed(ENA_LEFT, motorSpeed);
  
  if(x > 560) { //forward
    if(b < 250) {
      turn_left();
      //Serial.println("forward and left");
    }else if( b > 850) {
      turn_right();
      //Serial.println("forward and right");
    }else if(b >= 250 && b <= 850) {
      forward();
    }
  }
  
  else if(x < 460) { //backward
    if(b < 250) {
      turn_left();
    }else if( b > 850) {
      turn_right();
    }else if(b >= 250 && b <= 850) {
      backward();
    }
  }

  else {
    stop_all();
    
  }
}

  
