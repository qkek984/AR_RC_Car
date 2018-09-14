#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include<SoftwareSerial.h>
#include<String.h>

#define BUFF_SIZE 3
#define SERVOMIN 150 // 서보모터 최소각(0)일 때 펄스값(4096 범위 중에..)
#define SERVOMID 375 // 서보모터 중앙값
#define SERVOMAX 600 // 서보모터 최대각(180)일 때 펄스값(4096 범위 중에..)

int bluetoothTx = 2;
int bluetoothRx = 3;
SoftwareSerial bluetooth(bluetoothTx, bluetoothRx);
                      
uint8_t servoNum[2] =  {0, 1}; // PCA9685의 0, 1번핀 사용 // 0번핀 : 상하조정, 1번핀 : 좌우조정
int xPos = 0; // x축 절대좌표
int yPos = 0; // y축 절대좌표
char buffers[3];
int index = 0;

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(); //Adafruit_PWMServoDriver객체 생성

void setup() {
  Serial.begin(9600); // 시리얼 통신속도 9600 보드레이트로 설정
  bluetooth.begin(9600); //블루투스 통신속도 9600 보드레이트로 설정
  
  Serial.println("16 channel Servo test!"); //정상 출력 확인용

  pwm.begin(); // Adafruit_PWMServoDriver객체 Wire통신 사용 시작
  
  pwm.setPWMFreq(60);  //아날로그 서보모터 작동 주기를 60해르츠 마다 업데이트하도록 설정
  pwm.setPWM(0, 0, SERVOMID); // 카메라 중앙 설정
  yield(); // task를 다른 작업으로 제어권을 넘긴다.
}

void setServoPulse(uint8_t n, double pulse) {
  double pulselength;
  
  pulselength = 1000000;   // 1,000,000 us per second , 초당 펄스 길이
  pulselength /= 60;   // 60 Hz, 60헤르츠로 나누어 60헤르츠당 펄스가 몇번 오는지 측정
  Serial.print(pulselength); Serial.println(" us per period"); 
  pulselength /= 4096;  // 12 bits of resolution 12비트의 가지수
  Serial.print(pulselength); Serial.println(" us per bit"); 
  pulse *= 1000;
  pulse /= pulselength;
  Serial.println(pulse);
  pwm.setPWM(n, 0, pulse); // 펄스 길이로 재 설정
}

void loop() {
  char data;
  int i;
  int xAngle, yAngle;
  
  //Serial.println("==================================");
  while(bluetooth.available()) {
    data = bluetooth.read();
    buffers[index++] = data;
    /*
    Serial.print("data : ");
    Serial.print(data);
    Serial.println();
    */
    delay(1); //통신속도 9600기준 1ms를 줘야함, read기준
    if(data == '\n'  || index == BUFF_SIZE) {
      xPos += atoi(buffers);
      delay(1); //통신속도 9600기준 1ms를 줘야함, read기준
      break;
    }
  }
  
  /*
  for(i=0; i<index; i++) {
    Serial.write(buffers[i]);
  }
  Serial.println();
  Serial.print("index : ");
  Serial.println(index);
  Serial.print("xPos : ");
  Serial.println(xPos);
  Serial.println("==================================");
  index = 0;
  Serial.print("index : ");
  Serial.println(index);
  */
  
  /*
  if (bluetooth.available()) {
     char data = bluetooth.read();
     Serial.print("data : ");
     Serial.println(data);
     
     while(data == '-') {
      data = bluetooth.read();
      Serial.print("data : ");
      Serial.println(data);
      delay(10);
      if(data != '-') {
        xPos -= data;
      }
     }
     
     xPos += data;
     
  }
  */

  /*
  if (bluetooth.available()) {
     char data = bluetooth.read();
     if(data == '-') {
        //Serial.print("minus y : ");
        data= bluetooth.read();
        y = data-'0';
        yPos -= y;
     }else {
        //Serial.print("y : ");
        y = data-'0';
        yPos += y;
    }
  }
  */
  
  if(xPos <= 0 ) 
    xAngle = map(xPos, -90, 0, 150, 375);
  else if(xPos > 0) 
    xAngle = map(xPos, 0, 90, 375, 600);
    
  pwm.setPWM(servoNum[0], 0, xAngle);
  
  Serial.print("xAngle : ");
  Serial.println(xAngle);
 // Serial.print("yAngle : ");
 // Serial.println(yAngle);
}
