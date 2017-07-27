 #-*- coding: cp949 -*-
#-*- coding: utf-8 -*-
from flask import Flask, render_template, Response
from picamera.array import PiRGBArray
from picamera import PiCamera
import io
import time
import cv2
import numpy as np
import threading
import thread
import serial,time

global frame, bestContour, mdistance, r_ap,r_flag,minute,sec
global text,tx
global tspeed,mode
## init
frame = bestContour = r_ap = tspeed = None
mdistance=r_flag=minute=sec=0
mode=text=""
tx=0.45

app = Flask(__name__)

lock = thread.allocate_lock()
WIDTH=320
HEIGHT=280
camera = PiCamera()
camera.resolution = (WIDTH*2, HEIGHT*2)
camera.framerate = 40
camera.brightness = 57
rawCapture = PiRGBArray(camera, size=(WIDTH*2, HEIGHT*2))

lower_red = np.array([0,130,100])#Red
upper_red = np.array([4,200,250])
lower_blue = np.array([100,100,50])#blue
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
lower_glight = np.array([60,200,200])#green Light
upper_glight = np.array([70,255,255])

lower_rrs = np.array([160,100,50])#red road sign
upper_rrs = np.array([180,150,130])

class serials(threading.Thread):#Arduino Port Connection
    def __init__(self):
        global mode
        threading.Thread.__init__(self)
        port="/dev/ttyACM1"
        try:
            self.serialFromArduino = serial.Serial(port,9600)
            self.serialFromArduino.flushInput()
        except:
            print "Arduino Port is Disconnected"
            mode=False
    def run(self):
        global tspeed,mode
        while True:
            speed=""
            input = self.serialFromArduino.readline()
            len_input=len(input)
            for i in range(0,len_input):
                if i != len_input-2:
                    speed=speed+str(input[i])
                elif i != len_input-1:
                    mode=str(input[i])
            try:
                tspeed=int(speed)
            except:
                pass

class counting(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.count=4
    def run(self):
        global text,tx,mode,frame
        global minute,sec
        
        #while mode != "0":
        while sec<50:#<---------------Delete in future
            sec = sec+1
            time.sleep(0.1)
        sec=0
        while text !=None:
            self.count= self.count-1
            if text=="Start":
                text=None
            elif self.count!=0:
                text=str(self.count)
            else :
                text="Start"
                tx=0.28
            time.sleep(1)
            
        while True:
            sec= sec+1
            if sec==60:
                sec=0
                minute=minute+1
            time.sleep(1)

def region_of_interest(img, vertices, color3=(255,255,255), color1=255):#ROI
    mask = np.zeros_like(img)
    if len(img.shape) > 2:
        color = color3
    else: 
        color = color1
    cv2.fillPoly(mask, vertices, color)
    ROI_image = cv2.bitwise_and(img, mask)
    return ROI_image

def rgb_preprocessing(hsv,lower_rgb,upper_rgb,text_flag):# Trffic light rgb preprocessing
    #Create a binary frame, where anything green appears white and everything else is black
    element = cv2.getStructuringElement(cv2.MORPH_RECT,(3,3))
    #Get rid of background noise using erosion and fill in the holes using dilation and erode the final frame on last time
    mask_rgb = cv2.inRange(hsv, lower_rgb, upper_rgb)
    if text_flag != 1:
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

def Rendering_Data(bestContour,mdistance):
    global frame,r_ap,r_flag
    global lx,ly,lm
    x,y,w,h = cv2.boundingRect(bestContour)
    m=w
    if w<h:
        m=h
    if mdistance=="d" or mdistance=="e":
        vertices = np.array([[(x-m,y-m), (x-m,y+m*2),(x+m*2,y+m*2), (x+m*2,y-m)]], dtype=np.int32)
        ROI_image = region_of_interest(frame,vertices)
        #cv2.imshow("1",ROI_image)
    else:
        vertices = np.array([[(x,y), (x,y+m), (x+m,y+m), (x+m,y)]], dtype=np.int32)
        ROI_image = region_of_interest(frame,vertices)
        #cv2.imshow("2",ROI_image)
    hsv = cv2.cvtColor(ROI_image, cv2.COLOR_BGR2HSV)
    if mdistance=="a":
        _,t = rgb_preprocessing(hsv, lower_rwhite, upper_rwhite,1)
        if t>500:
            lx=x
            ly=y
            lm=m
            r_flag=1
            r_ap="  STOP  "
    elif mdistance=="b":
        _,t = rgb_preprocessing(hsv, lower_bwhite, upper_bwhite,1)
        if t>500:
            lx=x
            ly=y
            lm=m
            r_flag=1
            r_ap="Cross Walk"
    elif mdistance=="c":
        _,t = rgb_preprocessing(hsv, lower_yblack, upper_yblack,1)
        if t>500:
            lx=x
            ly=y
            lm=m
            r_flag=1
            r_ap="Slow Down"
    elif mdistance=="d":
        _,t = rgb_preprocessing(hsv, lower_rrs, upper_rrs,1)
        if t>2000:
            lx=x
            ly=y
            lm=m
            r_flag=1
            r_ap="Red Light"
    elif mdistance=="e":
        lx=x
        ly=y
        lm=m
        r_flag=1
        r_ap="Green Light"

def rgb_detection():
    global frame, mdistance
    global lx,ly,lm
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    distance={"a":0,"b":0,"c":0,"d":0,"e":0,"f":100}
    bestContour1,distance["a"] = rgb_preprocessing(hsv, lower_red, upper_red,0)
    bestContour2,distance["b"] = rgb_preprocessing(hsv, lower_blue, upper_blue,0)
    bestContour3,distance["c"] = rgb_preprocessing(hsv, lower_yellow, upper_yellow,0)
    bestContour4,distance["d"] = rgb_preprocessing(hsv, lower_rlight, upper_rlight,0)
    bestContour5,distance["e"] = rgb_preprocessing(hsv, lower_glight, upper_glight,0)
    
    mdistance = max(distance,key=distance.__getitem__)
    if mdistance == "a":
        Rendering_Data(bestContour1,mdistance)
    elif mdistance == "b":
        Rendering_Data(bestContour2,mdistance)
    elif mdistance == "c":
        Rendering_Data(bestContour3,mdistance)
    elif mdistance == "d":
        Rendering_Data(bestContour4,mdistance)
    elif mdistance == "e":
        Rendering_Data(bestContour5,mdistance)

def Rendering():
    global frame, tx,minute,sec,r_flag
    global lx,ly,lm
    global tspeed
    lxp=0
    if r_flag==1 and text==None:
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
    r_flag=0
    if text ==None:
        x=int(WIDTH*0.2)
        y=int(HEIGHT*0.75)
        cv2.putText(frame, "speed" ,(x,y),cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255))
        cv2.putText(frame, str(tspeed) ,(int(WIDTH*0.35),y),cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,50,25),1)
        cv2.putText(frame, "Operation" ,(x,int(HEIGHT*0.8)),cv2.FONT_HERSHEY_SIMPLEX,0.3,(255,255,255))
        cv2.putText(frame, str(minute)+":"+str(sec) ,(int(WIDTH*0.35),int(HEIGHT*0.82)),cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,50,25),1)
        cv2.putText(frame, "Time",(int(WIDTH*0.24),int(HEIGHT*0.84)),cv2.FONT_HERSHEY_SIMPLEX,0.3,(255,255,255))
    elif text == "":
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

        cv2.circle(frame,(int(WIDTH*0.55),int(HEIGHT*0.65)),15,(34,238,238),lxp)

        cv2.line(frame,(int(WIDTH*0.55),int(HEIGHT*0.4)),(int(WIDTH*0.55),int(HEIGHT*0.55)),(255,255,255),lxp*2)
        cv2.line(frame,(int(WIDTH*0.54),int(HEIGHT*0.5)),(int(WIDTH*0.55),int(HEIGHT*0.55)),(255,255,255),lxp*2)
        cv2.line(frame,(int(WIDTH*0.56),int(HEIGHT*0.5)),(int(WIDTH*0.55),int(HEIGHT*0.55)),(255,255,255),lxp*2)

        cv2.line(frame,(int(WIDTH*0.55),int(HEIGHT*0.4)),(int(WIDTH*0.55),int(HEIGHT*0.55)),(255,100,50),2)
        cv2.line(frame,(int(WIDTH*0.54),int(HEIGHT*0.5)),(int(WIDTH*0.55),int(  HEIGHT*0.55)),(255,100,50),2)
        cv2.line(frame,(int(WIDTH*0.56),int(HEIGHT*0.5)),(int(WIDTH*0.55),int(HEIGHT*0.55)),(255,100,50),2)
    else:
        x=int(WIDTH*tx)
        y=int(HEIGHT*0.6)
        cv2.putText(frame, text,(x-5,y-5),cv2.FONT_HERSHEY_SIMPLEX,2,(0,0,0),10)
        cv2.putText(frame, text,(x,y),cv2.FONT_HERSHEY_SIMPLEX,2,(255,255,255),10)
        cv2.putText(frame, text,(x,y),cv2.FONT_HERSHEY_SIMPLEX,2,(50,150,250),5)
        cv2.putText(frame, text,(x,y),cv2.FONT_HERSHEY_SIMPLEX,2,(50,200,250),2)

t0=serials()
if mode != False:
    t.start()

t1=counting()
t1.start()

@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')

def gen():
    global frame, canny_img, bestContour, mdistance,r_ap,r_flag,minute,sec
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        frame = frame.array
        frame = cv2.resize(frame, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
        t2=threading.Thread(target = rgb_detection)
        t3=threading.Thread(target = Rendering)
        t2.daemon = t2.daemon = True
        t2.start()
        t3.start()
        #Rendering()
        cv2.imwrite('data/f.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: frame/jpeg\r\n\r\n' + open('data/f.jpg', 'rb').read() + b'\r\n')
        rawCapture.truncate(0)
        
@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5001, threaded=True)

