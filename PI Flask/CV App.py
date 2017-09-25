#-*- coding: cp949 -*-
#-*- coding: utf-8 -*-
from flask import Flask, render_template, Response, request
from picamera.array import PiRGBArray
from picamera import PiCamera
import io
import time
import cv2
import numpy as np
import threading
import thread
import serial,time
import sqlite3

global frame, bestContour, mdistance, r_ap,r_flag,minute,sec
global render_text,tx
global tspeed,start_btn
global msg1,msg2
global nickname,score
global left,right,Line_Bit
global speed## delete in future
speed=9 

## init
frame = bestContour = r_ap = tspeed = None
mdistance=r_flag=minute=sec=tspeed=score=right=left=Line_Bit=0
render_text=msg1=msg2=nickname=start_btn=""
tx=0.45

global time_score, stop_score, line_score, slow_score, red_score, cross_score
time_score=10
stop_score=10
red_score=20
line_score=40
slow_score=10
cross_score=10


app = Flask(__name__)
lock = thread.allocate_lock()
WIDTH=320#320
HEIGHT=288#288
camera = PiCamera()
camera.resolution = (WIDTH, HEIGHT)
camera.framerate = 40
camera.brightness = 57
rawCapture = PiRGBArray(camera, size=(WIDTH, HEIGHT))

lower_red = np.array([0,130,100])#Red
upper_red = np.array([4,200,250])
lower_blue = np.array([100,80,50])#blue
upper_blue = np.array([108,200,210])
lower_yellow = np.array([24,140,140])#yellow
upper_yellow = np.array([30,250,240])

lower_rwhite = np.array([170,5,150])#red white
upper_rwhite = np.array([180,50,255])
lower_bwhite = np.array([95,15,150])#blue white
upper_bwhite = np.array([108,65,255])
lower_yblack = np.array([10,150,50])#yellow black
upper_yblack = np.array([30,250,170])

lower_rlight = np.array([165,50,200])#Red Light
upper_rlight = np.array([175,220,255])
lower_glight = np.array([60,180,190])#green Light
upper_glight = np.array([70,255,255])

lower_rrs = np.array([155,10,50])#red road sign
upper_rrs = np.array([180,150,255])
'''Serials Class'''
class Serials(threading.Thread):#Arduino Port Connection
    def __init__(self):
        global start_btn
        threading.Thread.__init__(self)
        try:
            port="/dev/ttyUSB0"
            self.serialFromArduino = serial.Serial(port,9600)
            self.serialFromArduino.flushInput()
        except:
            try:
                port="/dev/ttyUSB1"
                self.serialFromArduino = serial.Serial(port,9600)
                self.serialFromArduino.flushInput()
            except:
                print "Arduino Port is Disconnected"
                start_btn=False
    def run(self):
        global tspeed,start_btn
        while True:
            speed=""
            input = self.serialFromArduino.readline()
            #print str(input)
            len_input=len(input)
            #test_code
            ms = input.find('Esm')
            ems = input.find('Em')
            #print input[ms+3:ems]
            Ebs = input.find('Ebs')
            bs = input.find('Esm')
            #print input[Ebs+3:bs]
            speed=input[ms+3:ems]
            start_btn=input[Ebs+3:bs]
            try:
                tspeed=int(speed)
            except:
                pass
class Score(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.stack=0
        self.check2=0
        self.check3=0
        self.check4=0
        self.end=False
    def sql(self,nickname,score,minute,sec):
        conn = sqlite3.connect("data/rank.db")
        conn.execute('CREATE TABLE IF NOT EXISTS score(name TEXT,score INTEGER, minute INTEGER, sec INTEGER)')
        cur = conn.cursor()
        sql_text="INSERT INTO score (name,score,minute,sec) VALUES ('"+nickname+"',"+str(score)+","+str(minute)+","+str(sec)+")"
        cur.execute(sql_text)
        cur.execute("SELECT * FROM score ORDER BY score DESC, minute ASC, sec ASC")
        row= cur.fetchall()
        print row
        conn.commit()
        conn.close()
    def run(self):
        global time_score, time_score, line_score,slow_score,red_score, total_score, cross_score
        global render_text
        global tspeed, r_flag
        global msg1,msg2
        global nickname,minute,sec
        while self.end==False:#STOP
            if r_flag==1:
                while r_flag ==1 and self.end==False:
                    #print self.stack
                    self.stack=self.stack+1
                    if self.stack==3 and speed<10:
                        slow_score = slow_score*self.check2
                        red_score = red_score*self.check3
                        cross_score = cross_score*self.check4
                        print "total",line_score + time_score + stop_score + slow_score*self.check2 + red_score*self.check3 + cross_score*self.check4
                        total_score = line_score + time_score + stop_score + slow_score*self.check2 + red_score*self.check3 + cross_score*self.check4
                        self.end=True
                        self.sql(nickname,total_score,minute,sec)#sqlite write
                        render_text="Total Score"
                    time.sleep(1)
                self.stack=0
            elif r_flag==2:#SLow 
                while r_flag ==2 and slow_score>0:
                    self.stack=self.stack+1
                    while self.stack>3 and self.stack<7 and slow_score>0:
                        if tspeed>200:
                            slow_score=0
                            msg1="Slow Score"
                            msg2="-10"
                        self.stack=self.stack+1
                    time.sleep(1)
                self.stack=0
                self.check2=1
                #print "slow_score:",slow_score
            elif r_flag==3:#Red light
                while r_flag ==3 and red_score>0:
                    #print self.stack
                    self.stack=self.stack+1
                    if self.stack>2 and tspeed>25:
                        red_score=0
                        msg1="Red Score"
                        msg2="-30"
                    time.sleep(1)
                self.stack=0
                self.check3=1
                #print "Red Light_Score:",red_score
            elif r_flag==4:
                self.check4=1
            elif r_flag==5:#red light
                self.check3=1
            time.sleep(1)
            msg1=""
            msg2=""
'''Line score Class'''
class Line_score(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.Line_Stack=5
    def run(self):
        global Line_Bit,line_score, msg1, msg2,render_text
        while line_score>0:
            #print Line_Bit
            if Line_Bit==0:
                self.Line_Stack=self.Line_Stack-1
                if self.Line_Stack==0:
                    if render_text=="Total Score":
                        time.sleep(100000)
                    line_score=line_score-5
                    self.Line_Stack=5
                    for i in range(0,20):
                        msg1="Line Score"
                        msg2="-5"
                        time.sleep(0.1)
            elif Line_Bit==2:
                self.Line_Stack=5
            time.sleep(1)
            msg1=""
            msg2=""
'''Countion Class'''
class Counting(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.count=4
    def run(self):
        global render_text,tx,start_btn,frame , time_score
        global minute,sec
        global msg1,msg2
        while start_btn != "0":
            sec = sec+1
            time.sleep(0.1)
            #print start_btn
            if start_btn==False:# Arduino desconnected
                time.sleep(5)
                start_btn="0"
            
        sec=0
        while render_text !=None:
            self.count= self.count-1
            if render_text=="Start":
                render_text=None
            elif self.count!=0:
                render_text=str(self.count)
            else :
                render_text="Start"
                tx=0.28
            time.sleep(1)
        t1=Score()# starting score thread 
        t1.start()
        t2=Line_score()
        t2.start()
        while True:
            sec= sec+1
            if sec==60:
                sec=0
                minute=minute+1
            if minute==1 and sec>=0 and sec<4:
                
                if render_text=="Total Score":
                    time.sleep(100000)
                time_score=0
                msg1="Time Score"
                msg2="-10"
                if sec==3:
                    msg1=""
                    msg2=""
                #print "time_score:",time_score
            time.sleep(1)

'''Line Detection'''
class Line_Detection(threading.Thread):
    def __init__(self):
        global WIDTH,HEIGHT
        threading.Thread.__init__(self)
        self.verticesL = np.array([[(-30,HEIGHT*0.8),(WIDTH*0.1, HEIGHT*0.3), (WIDTH*0.4, HEIGHT*0.3), (WIDTH*0.2,HEIGHT*0.8)]], dtype=np.int32)
        self.verticesR = np.array([[(WIDTH*0.8,HEIGHT*0.8),(WIDTH*0.6, HEIGHT*0.3), (WIDTH*0.9, HEIGHT*0.3), (WIDTH+30,HEIGHT*0.8)]], dtype=np.int32)
    def region_of_interest2(self,img, verticesL, verticesR, color3=(255,255,255), color1=255):#ROI
        mask = np.zeros_like(img)
        if len(img.shape) > 2:
            color = color3
        else: 
            color = color1
        cv2.fillPoly(mask, verticesL, color)
        cv2.fillPoly(mask, verticesR, color)
        #cv2.imshow("mask", mask)
        ROI_image = cv2.bitwise_and(img, mask)
        return ROI_image
    def draw_lines(self,img, lines, color, thickness, h_width, RL): # 선 그리기
        global left, right
        for line in lines:
            for x1,y1,x2,y2 in line:
                if h_width > x1 and RL==True:
                    left=1
                    #cv2.line(img, (x1, y1), (x2, y2), [255, 255, 255], 9)
                    #cv2.line(img, (x1, y1), (x2, y2), color, thickness)
                elif h_width < x1 and RL==False:
                    right=1
                    #cv2.line(img, (x1, y1), (x2, y2), [255, 255, 255], 9)
                    #cv2.line(img, (x1, y1), (x2, y2), color, thickness)
    def run(self):
        global frame, Line_Bit, right, left
        temp = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # 흑백이미지로 변환
        temp = cv2.GaussianBlur(temp,(3,3),0) # Blur 효과    
        canny_img = cv2.Canny(temp, 250, 400) # Canny edge 알고리즘
        ROI_img = self.region_of_interest2(canny_img, self.verticesL, self.verticesR)
        line_arr = cv2.HoughLinesP(ROI_img, 1, 1 * np.pi/180, 30,np.array([]), minLineLength=10, maxLineGap=20) # 허프 변환
        line_img = np.zeros((ROI_img.shape[0], ROI_img.shape[1], 3), dtype=np.uint8)
        left=right=0
        try:
            line_arr = np.squeeze(line_arr)
            # 기울기 구하기
            slope_degree = (np.arctan2(line_arr[:,1] - line_arr[:,3], line_arr[:,0] - line_arr[:,2]) * 180) / np.pi
            # 수평 기울기 제한
            line_arr = line_arr[np.abs(slope_degree)<160]
            slope_degree = slope_degree[np.abs(slope_degree)<160]
            # 수직 기울기 제한
            line_arr = line_arr[np.abs(slope_degree)>95]
            slope_degree = slope_degree[np.abs(slope_degree)>95]
            # 필터링된 직선 버리기
            L_lines, R_lines = line_arr[(slope_degree>0),:], line_arr[(slope_degree<0),:]
            temp = np.zeros((frame.shape[0], frame.shape[1], 3), dtype=np.uint8)
            L_lines, R_lines = L_lines[:,None], R_lines[:,None]
            # 직선 그리기
            
            self.draw_lines(temp, L_lines, [255, 0, 0], 8, WIDTH/2, True)
            self.draw_lines(temp, R_lines, [255, 0, 0], 8, WIDTH/2, False)
            Line_Bit=right+left
        except:
            temp= line_img
            left=right=0
        frame = cv2.addWeighted(frame, 1, temp, 1, 0)
'''RGB Detection'''
class Rgb_Detection(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def region_of_interest(self,img, vertices, color3=(255,255,255), color1=255):#ROI
        mask = np.zeros_like(img)
        if len(img.shape) > 2:
            color = color3
        else: 
            color = color1
        cv2.fillPoly(mask, vertices, color)
        ROI_image = cv2.bitwise_and(img, mask)
        return ROI_image

    def rgb_preprocessing(self,hsv,lower_rgb,upper_rgb,render_text_flag):# Trffic light rgb preprocessing
        element = cv2.getStructuringElement(cv2.MORPH_RECT,(3,3))
        mask_rgb = cv2.inRange(hsv, lower_rgb, upper_rgb)
        if render_text_flag != 1:
            mask_rgb = cv2.dilate(mask_rgb,element,iterations=7)
            mask_rgb = cv2.erode(mask_rgb,element, iterations=7)
        else:
            mask_rgb = cv2.dilate(mask_rgb,element,iterations=7)
            
        contours, _ = cv2.findContours(mask_rgb, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        maximumArea = 0
        bestContour = None
        for contour in contours:
            currentArea = cv2.contourArea(contour)
            if currentArea > maximumArea:
                bestContour = contour
                maximumArea = currentArea
        if bestContour==None:
            return bestContour,0
        _,_,w,h = cv2.boundingRect(bestContour)
        return bestContour,w*h
    def Rendering_Data(self,bestContour,mdistance):
        global frame,r_ap,r_flag
        global lx,ly,lm
        x,y,w,h = cv2.boundingRect(bestContour)
        m=w
        if w<h:
            m=h
        if mdistance=="d" or mdistance=="e":
            vertices = np.array([[(x-m,y-m), (x-m,y+m*2),(x+m*2,y+m*2), (x+m*2,y-m)]], dtype=np.int32)
            ROI_image = self.region_of_interest(frame,vertices)
            #cv2.imshow("1",ROI_image)
        else:
            vertices = np.array([[(x,y), (x,y+m), (x+m,y+m), (x+m,y)]], dtype=np.int32)
            ROI_image = self.region_of_interest(frame,vertices)
            #cv2.imshow("2",ROI_image)
        hsv = cv2.cvtColor(ROI_image, cv2.COLOR_BGR2HSV)
        if mdistance=="a":
            _,t = self.rgb_preprocessing(hsv, lower_rwhite, upper_rwhite,1)
            if t>500:
                lx=x
                ly=y
                lm=m
                r_flag=1
                r_ap="  STOP  "
        elif mdistance=="b":
            _,t = self.rgb_preprocessing(hsv, lower_bwhite, upper_bwhite,1)
            if t>500:
                lx=x
                ly=y
                lm=m
                r_flag=4
                r_ap="Cross Walk"
        elif mdistance=="c":
            _,t = self.rgb_preprocessing(hsv, lower_yblack, upper_yblack,1)
            if t>500:
                lx=x
                ly=y
                lm=m
                r_flag=2
                r_ap="Slow Down"
        elif mdistance=="d":
            _,t = self.rgb_preprocessing(hsv, lower_rrs, upper_rrs,1)
            if t>2000:
                lx=x
                ly=y
                lm=m
                r_flag=3
                r_ap="Red Light"
        elif mdistance=="e":
            lx=x
            ly=y
            lm=m
            r_flag=5
            r_ap="Green Light"
        else:
            r_flag=0
    def run(self):
        global frame, mdistance,r_flag
        global lx,ly,lm
        try:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            distance={"a":0,"b":0,"c":0,"d":0,"e":0,"f":100}
            bestContour1,distance["a"] = self.rgb_preprocessing(hsv, lower_red, upper_red,0)
            bestContour2,distance["b"] = self.rgb_preprocessing(hsv, lower_blue, upper_blue,0)
            bestContour3,distance["c"] = self.rgb_preprocessing(hsv, lower_yellow, upper_yellow,0)
            bestContour4,distance["d"] = self.rgb_preprocessing(hsv, lower_rlight, upper_rlight,0)
            bestContour5,distance["e"] = self.rgb_preprocessing(hsv, lower_glight, upper_glight,0)
        except:
            pass
        mdistance = max(distance,key=distance.__getitem__)
        if mdistance == "a":
            self.Rendering_Data(bestContour1,mdistance)
        elif mdistance == "b":
            self.Rendering_Data(bestContour2,mdistance)
        elif mdistance == "c":
            self.Rendering_Data(bestContour3,mdistance)
        elif mdistance == "d":
            self.Rendering_Data(bestContour4,mdistance)
        elif mdistance == "e":
            self.Rendering_Data(bestContour5,mdistance)
        else:
            r_flag=0
'''Rendering Method'''
def Rendering():
    global frame, tx,minute,sec,r_flag
    global lx,ly,lm
    global tspeed
    global time_score,stop_score,line_score,slow_score,red_score,cross_score
    lxp=0
    if r_flag>0 and render_text==None:#Object Detection
        if lx > WIDTH/2:
            lxp=50
        x=lx+lm/2
        y=ly+lm/2
        x2=int(lx-lxp)
        y2=int(ly+lm+20)
        cv2.circle(frame,(x,y),lm/2+15,(200,200,200),1)
        cv2.circle(frame,(x,y),lm/2+5,(255,178,75),2)
        cv2.circle(frame,(x,y),lm/2,(200,200,200),1)
        cv2.putText(frame, r_ap,(x2,y2),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,125,55),3)
        cv2.putText(frame, r_ap,(x2,y2),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,255,255),1)
        
    if render_text ==None:# time 
        global msg1,msg2
        x=int(WIDTH*0.2)
        x2=int(WIDTH*0.65)
        y=int(HEIGHT*0.75)
        total = time_score + stop_score + red_score + line_score + slow_score + cross_score

        cv2.putText(frame, msg1 ,(x2,int(HEIGHT*0.4)),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,0,0),3)
        cv2.putText(frame, msg1 ,(x2,int(HEIGHT*0.4)),cv2.FONT_HERSHEY_SIMPLEX,0.4,(255,255,255),1)
        cv2.putText(frame, msg2 ,(x2,int(HEIGHT*0.5)),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),5)
        cv2.putText(frame, msg2 ,(x2,int(HEIGHT*0.5)),cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),3)
        
        cv2.putText(frame, "Score" ,(x2,y),cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255))
        cv2.putText(frame, str(total) ,(int(WIDTH*0.75),y),cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,50,25))
        cv2.putText(frame, "Speed" ,(x,y),cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255))
        cv2.putText(frame, str(tspeed) ,(int(WIDTH*0.35),y),cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,50,25),1)
        cv2.putText(frame, "Operation" ,(x,int(HEIGHT*0.8)),cv2.FONT_HERSHEY_SIMPLEX,0.3,(255,255,255))
        cv2.putText(frame, "time",(int(WIDTH*0.24),int(HEIGHT*0.84)),cv2.FONT_HERSHEY_SIMPLEX,0.3,(255,255,255))
        cv2.putText(frame, str(minute)+":"+str(sec) ,(int(WIDTH*0.35),int(HEIGHT*0.82)),cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,50,25),1)
    elif render_text == "":# How to start
        if sec%4==0:
            lxp=1
        else:
            lxp=2
        cv2.rectangle(frame, (int(WIDTH*0.15),int(HEIGHT*0.15)),(int(WIDTH*0.85),int(HEIGHT*0.85)), (245,245,245), 3)#Edge
        cv2.rectangle(frame, (int(WIDTH*0.15),int(HEIGHT*0.15)),(int(WIDTH*0.85),int(HEIGHT*0.85)), (255,100,50), 2)
        cv2.putText(frame, "Push !",(int(WIDTH*0.43),int(HEIGHT*0.35)),cv2.FONT_HERSHEY_SIMPLEX,0.6,(255,255,255),lxp*2)
        cv2.putText(frame, "Push !",(int(WIDTH*0.43),int(HEIGHT*0.35)),cv2.FONT_HERSHEY_SIMPLEX,0.6,(255,100,50),2)
        #controller
        cv2.rectangle(frame, (int(WIDTH*0.3),int(HEIGHT*0.5)),(int(WIDTH*0.32),int(HEIGHT*0.8)), (30,30,160), -1)# L
        cv2.rectangle(frame, (int(WIDTH*0.32),int(HEIGHT*0.5)),(int(WIDTH*0.33),int(HEIGHT*0.8)), (40,40,180), -1)
        cv2.rectangle(frame, (int(WIDTH*0.33),int(HEIGHT*0.5)),(int(WIDTH*0.37),int(HEIGHT*0.8)), (50,50,200), -1)
        cv2.rectangle(frame, (int(WIDTH*0.37),int(HEIGHT*0.5)),(int(WIDTH*0.38),int(HEIGHT*0.8)), (40,40,180), -1)
        cv2.rectangle(frame, (int(WIDTH*0.38),int(HEIGHT*0.5)),(int(WIDTH*0.4),int(HEIGHT*0.8)), (30,30,160), -1)
        cv2.rectangle(frame, (int(WIDTH*0.3),int(HEIGHT*0.5)),(int(WIDTH*0.4),int(HEIGHT*0.8)), (0,0,0), 1)
        cv2.rectangle(frame, (int(WIDTH*0.4),int(HEIGHT*0.55)),(int(WIDTH*0.6),int(HEIGHT*0.7)), (50,50,200), -1)#C
        cv2.rectangle(frame, (int(WIDTH*0.4),int(HEIGHT*0.55)),(int(WIDTH*0.6),int(HEIGHT*0.7)), (0,0,0), 1)
        cv2.rectangle(frame, (int(WIDTH*0.4),int(HEIGHT*0.55)),(int(WIDTH*0.6),int(HEIGHT*0.7)), (0,0,0), 1)
        cv2.rectangle(frame, (int(WIDTH*0.6),int(HEIGHT*0.5)),(int(WIDTH*0.62),int(HEIGHT*0.8)), (30,30,160), -1)# R
        cv2.rectangle(frame, (int(WIDTH*0.62),int(HEIGHT*0.5)),(int(WIDTH*0.63),int(HEIGHT*0.8)), (40,40,180), -1)
        cv2.rectangle(frame, (int(WIDTH*0.63),int(HEIGHT*0.5)),(int(WIDTH*0.67),int(HEIGHT*0.8)), (50,50,200), -1)
        cv2.rectangle(frame, (int(WIDTH*0.68),int(HEIGHT*0.5)),(int(WIDTH*0.7),int(HEIGHT*0.8)), (30,30,180), -1)
        cv2.rectangle(frame, (int(WIDTH*0.67),int(HEIGHT*0.5)),(int(WIDTH*0.68),int(HEIGHT*0.8)), (40,40,160), -1)        
        cv2.rectangle(frame, (int(WIDTH*0.6),int(HEIGHT*0.5)),(int(WIDTH*0.7),int(HEIGHT*0.8)), (0,0,0), 1)
        cv2.circle(frame,(int(WIDTH*0.45),int(HEIGHT*0.65)),10,(0,0,0),-1)#L Button
        cv2.circle(frame,(int(WIDTH*0.45),int(HEIGHT*0.65)),7,(50,50,50),-1)
        cv2.circle(frame,(int(WIDTH*0.55),int(HEIGHT*0.65)),10,(0,0,0),-1)#R Button
        cv2.circle(frame,(int(WIDTH*0.55),int(HEIGHT*0.65)),7,(50,50,50),-1)
        cv2.circle(frame,(int(WIDTH*0.55),int(HEIGHT*0.65)),15,(34,238,238),lxp)#R Button emphasis

        cv2.line(frame,(int(WIDTH*0.55),int(HEIGHT*0.4)),(int(WIDTH*0.55),int(HEIGHT*0.55)),(255,255,255),lxp*2)#Arrow
        cv2.line(frame,(int(WIDTH*0.54),int(HEIGHT*0.5)),(int(WIDTH*0.55),int(HEIGHT*0.55)),(255,255,255),lxp*2)
        cv2.line(frame,(int(WIDTH*0.56),int(HEIGHT*0.5)),(int(WIDTH*0.55),int(HEIGHT*0.55)),(255,255,255),lxp*2)
        cv2.line(frame,(int(WIDTH*0.55),int(HEIGHT*0.4)),(int(WIDTH*0.55),int(HEIGHT*0.55)),(255,100,50),2)
        cv2.line(frame,(int(WIDTH*0.54),int(HEIGHT*0.5)),(int(WIDTH*0.55),int(HEIGHT*0.55)),(255,100,50),2)
        cv2.line(frame,(int(WIDTH*0.56),int(HEIGHT*0.5)),(int(WIDTH*0.55),int(HEIGHT*0.55)),(255,100,50),2)
    elif render_text=="Total Score":# Finish
        global total_score
        if total_score==100:
            lxp=-WIDTH*0.1
        cv2.rectangle(frame, (int(WIDTH*0.15),int(HEIGHT*0.15)),(int(WIDTH*0.85),int(HEIGHT*0.85)), (245,245,245), 3)#Edge
        cv2.rectangle(frame, (int(WIDTH*0.15),int(HEIGHT*0.15)),(int(WIDTH*0.85),int(HEIGHT*0.85)), (255,100,50), 2)

        cv2.putText(frame, render_text ,(int(WIDTH*0.4),int(HEIGHT*0.25)),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,0,0),3)#total
        cv2.putText(frame, render_text ,(int(WIDTH*0.4),int(HEIGHT*0.25)),cv2.FONT_HERSHEY_SIMPLEX,0.4,(255,255,255),1)
            
        cv2.putText(frame, str(total_score),(int(WIDTH*0.4+lxp)-5,int(HEIGHT*0.45)-5),cv2.FONT_HERSHEY_SIMPLEX,2,(0,0,0),10)#score
        cv2.putText(frame, str(total_score),(int(WIDTH*0.4+lxp),int(HEIGHT*0.45)),cv2.FONT_HERSHEY_SIMPLEX,2,(252,128,0),5)
        cv2.putText(frame, str(total_score),(int(WIDTH*0.4+lxp),int(HEIGHT*0.45)),cv2.FONT_HERSHEY_SIMPLEX,2,(255,187,0),2)

        cv2.line(frame,(int(WIDTH*0.2),int(HEIGHT*0.48)),(int(WIDTH*0.8),int(HEIGHT*0.48)),(50,50,255),1)

        cv2.rectangle(frame, (int(WIDTH*0.3),int(HEIGHT*0.52)),(int(WIDTH*0.7),int(HEIGHT*0.56)), (150,150,150), -1)
        cv2.rectangle(frame, (int(WIDTH*0.3),int(HEIGHT*0.57)),(int(WIDTH*0.7),int(HEIGHT*0.61)), (150,150,150), -1)
        cv2.rectangle(frame, (int(WIDTH*0.3),int(HEIGHT*0.62)),(int(WIDTH*0.7),int(HEIGHT*0.66)), (150,150,150), -1)
        cv2.rectangle(frame, (int(WIDTH*0.3),int(HEIGHT*0.67)),(int(WIDTH*0.7),int(HEIGHT*0.71)), (150,150,150), -1)
        cv2.rectangle(frame, (int(WIDTH*0.3),int(HEIGHT*0.72)),(int(WIDTH*0.7),int(HEIGHT*0.76)), (150,150,150), -1)
        cv2.rectangle(frame, (int(WIDTH*0.3),int(HEIGHT*0.77)),(int(WIDTH*0.7),int(HEIGHT*0.81)), (150,150,150), -1)
        cv2.putText(frame, "Line Score  : " ,(int(WIDTH*0.35),int(HEIGHT*0.55)),cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
        cv2.putText(frame, "Sign Score  : " ,(int(WIDTH*0.35),int(HEIGHT*0.6)),cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
        cv2.putText(frame, "Slow Score  : " ,(int(WIDTH*0.35),int(HEIGHT*0.65)),cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
        cv2.putText(frame, "Cross Score : " ,(int(WIDTH*0.35),int(HEIGHT*0.7)),cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
        cv2.putText(frame, "Time Score  : " ,(int(WIDTH*0.35),int(HEIGHT*0.75)),cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
        cv2.putText(frame, "Come Score : " ,(int(WIDTH*0.35),int(HEIGHT*0.8)),cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
        cv2.putText(frame, str(line_score) ,(int(WIDTH*0.6),int(HEIGHT*0.55)),cv2.FONT_HERSHEY_SIMPLEX,0.3,(255,50,0),1)
        cv2.putText(frame, str(red_score) ,(int(WIDTH*0.6),int(HEIGHT*0.6)),cv2.FONT_HERSHEY_SIMPLEX,0.3,(255,50,0),1)
        cv2.putText(frame, str(slow_score) ,(int(WIDTH*0.6),int(HEIGHT*0.65)),cv2.FONT_HERSHEY_SIMPLEX,0.3,(255,50,0),1)
        cv2.putText(frame, str(cross_score) ,(int(WIDTH*0.6),int(HEIGHT*0.7)),cv2.FONT_HERSHEY_SIMPLEX,0.3,(255,50,0),1)
        cv2.putText(frame, str(time_score) ,(int(WIDTH*0.6),int(HEIGHT*0.75)),cv2.FONT_HERSHEY_SIMPLEX,0.3,(255,50,0),1)
        cv2.putText(frame, str(stop_score) ,(int(WIDTH*0.6),int(HEIGHT*0.8)),cv2.FONT_HERSHEY_SIMPLEX,0.3,(255,50,0),1)
    else:# Start to count
        x=int(WIDTH*tx)
        y=int(HEIGHT*0.6)
        cv2.putText(frame, render_text,(x-5,y-5),cv2.FONT_HERSHEY_SIMPLEX,2,(0,0,0),10)
        cv2.putText(frame, render_text,(x,y),cv2.FONT_HERSHEY_SIMPLEX,2,(255,255,255),10)
        cv2.putText(frame, render_text,(x,y),cv2.FONT_HERSHEY_SIMPLEX,2,(50,150,250),5)
        cv2.putText(frame, render_text,(x,y),cv2.FONT_HERSHEY_SIMPLEX,2,(50,200,250),2)
        

@app.route('/')
def index():
    conn = sqlite3.connect("data/rank.db")
    conn.execute('CREATE TABLE IF NOT EXISTS score(name TEXT,score INTEGER, minute INTEGER, sec INTEGER)')
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM score ORDER BY score DESC, minute ASC, sec ASC")
    except:
        pass
    row= cur.fetchall()
    array=[]
    for i in range(0,len(row)):
        for j in range(0,4):
            if j==0:
                array.append(str(row[i][j]))
            elif j==1:
                array.append(row[i][j])
            elif j==2:
                tmp=row[i][j]
            else:
                tmp=str(tmp)+":"+str(row[i][j])
                array.append(tmp)
    conn.commit()
    conn.close()
    """Video streaming home page."""
    return render_template('index.html', array=array)

@app.route('/config')
def config():
    global nickname,score
    nickname = request.args.get('nickname', '')
    try:
        score = int(request.args.get('score', ''))
    except:
        score=0
    print nickname
    print score
    
def gen():
    t0=Serials()
    if start_btn != False:
        t0.start()
        left=right=0
    
    t1=Counting()
    t1.start()
    global frame, canny_img, bestContour, mdistance,r_ap,r_flag,minute,sec,score
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        try:
            frame = frame.array
            if score==1:
                t2=Rgb_Detection()
                t3=Line_Detection()
                t2.daemon  = t3.daemon = True
                t2.start()
                t3.start()
                Rendering()
            cv2.imwrite('data/f.jpg', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: frame/jpeg\r\n\r\n' + open('data/f.jpg', 'rb').read() + b'\r\n')
            rawCapture.truncate(0)
        except:
            pass
@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5001, threaded=True)
