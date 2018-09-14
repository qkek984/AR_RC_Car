# AR_RC_Car

<hr/>

## 0.Demonstration video

>[![AR RC Car](https://github.com/qkek984/AR_RC_Car/blob/master/readme_Img/youtube_Img.png?raw=true)](https://youtu.be/IAszPYRVv5c) 

<hr/>

## 1.Project introduction
> * RC카의 1인칭 시점을 VR로 보며 조종함으로써 실제 주행을 체험하는 것 같은 재미 제공

> * Score Mode를 통하여 트랙 내에서 주행 할 시, 주행 중 인식한 정보를 증강현실 객
체화 하며 그 정보를 토대로 주행점수를 평가

> * Normal Mode는 영상 처리가 없는 실시간 영상만을 제공하며, 트랙 외에서도 자유롭
게 주행이 가능

## 2.Design
> ### 2.1 Overall design
  >> <img src="https://github.com/qkek984/AR_RC_Car/blob/master/readme_Img/total_design.png?raw=true" width="70%" height="70%">

> ### 2.2 RC Car design
  >> <img src="https://github.com/qkek984/AR_RC_Car/blob/master/readme_Img/arduino_design.png?raw=true" width="80%" height="80%">
  
  >> <img src="https://github.com/qkek984/AR_RC_Car/blob/master/readme_Img/arduino_design2.png?raw=true" width="80%" height="80%">

## 4.Core technology
> ### 4.1. object detection
  * road sign & traffic light object detection
>><img src="https://github.com/qkek984/AR_RC_Car/blob/master/readme_Img/run.png?raw=true" width="80%" height="80%">

> ### 4.2. Line detection
  * using slope filtering, ROI and so on..
>><img src="https://github.com/qkek984/AR_RC_Car/blob/master/readme_Img/line.PNG?raw=true" width="80%" height="80%">

> ### 4.3. Score game Algorithm
  * Score evaluation based on driving
>><img src="https://github.com/qkek984/AR_RC_Car/blob/master/readme_Img/resultScreen.JPG?raw=true" width="80%" height="80%">

## 4.How to run SW in Raspberry pi
> * pip install -r requrements.txt
> * python CV App.py
> * connect http://***.***.***.***:5001 in your android app 
>> <img src="https://github.com/qkek984/AR_RC_Car/blob/master/readme_Img/connection.png?raw=true" width="50%" height="50%">
