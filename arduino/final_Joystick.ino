#include<SoftwareSerial.h>

int bluetoothTx = 2;
int bluetoothRx = 3;

SoftwareSerial bluetooth(bluetoothTx, bluetoothRx);

int X = A0;
int Y = A1;
int A = A2;
int B = A3;
int S = 7;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  bluetooth.begin(38400);
  pinMode(X, INPUT);
  pinMode(Y, INPUT);
  pinMode(A, INPUT);
  pinMode(B, INPUT);
  pinMode(S, INPUT);
  digitalWrite(S, HIGH);

}

void loop() {
  // put your main code here, to run repeatedly:
  int x,y,s;
  int a, b;


  x = analogRead(X);
  delay(1);
  y = analogRead(Y);
  delay(1);
  a = analogRead(A);
  delay(1);
  b = analogRead(B);
  delay(1);
  s = digitalRead(S);
  delay(1);

    
  Serial.print("   X =  ");
  Serial.print(x,DEC);
  
  Serial.print("   Y =  ");
  Serial.print(y,DEC);

  Serial.print("   A =  ");
  Serial.print(a,DEC);
  
  Serial.print("   B =  ");
  Serial.print(b,DEC);
  
  Serial.print("   S =  ");
  Serial.println(s,DEC);

  bluetooth.print("   X =  ");
  bluetooth.print(x,DEC);
  
  bluetooth.print("   Y =  ");
  bluetooth.print(y,DEC);

  bluetooth.print("   A =  ");
  bluetooth.print(a,DEC);
  
  bluetooth.print("   B =  ");
  bluetooth.print(b,DEC);
  
  bluetooth.print("   S =  ");
  bluetooth.println(s,DEC);

  delay(100);
}
