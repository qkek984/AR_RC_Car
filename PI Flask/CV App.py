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
global frame, canny_img, bestContour, mdistance, r_ap,r_flag,minute,sec
global x,y,m
x=y=m=0
## main
app = Flask(__name__)

frame = canny_img = bestContour = r_ap = None
mdistance=r_flag=minute=sec=0
lock = thread.allocate_lock()
WIDTH=320
HEIGHT=280
camera = PiCamera()
camera.resolution = (WIDTH*2, HEIGHT*2)
camera.framerate = 40
camera.brightness = 57
rawCapture = PiRGBArray(camera, size=(WIDTH*2, HEIGHT*2))

lower_red = np.array([0,150,100])#Red
upper_red = np.array([3,200,200])
lower_blue = np.array([102,130,50])#blue
upper_blue = np.array([108,200,150])
lower_yellow = np.array([24,150,140])#yellow
upper_yellow = np.array([28,250,240])

lower_rwhite = np.array([170,5,150])#red white
upper_rwhite = np.array([180,50,255])

lower_bwhite = np.array([100,5,130])#blue white
upper_bwhite = np.array([180,100,210])

lower_yblack = np.array([10,170,50])#yellow black
upper_yblack = np.array([30,250,150])

lower_rlight = np.array([165,50,200])#Red Light
upper_rlight = np.array([175,220,255])
lower_glight = np.array([60,200,200])#green Light
upper_glight = np.array([70,255,255])

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
    #Create Contours for all green objects
    contours, _ = cv2.findContours(mask_rgb, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    maximumArea = 0
    local_bestContour = None
    for contour in contours:
        currentArea = cv2.contourArea(contour)
        if currentArea > maximumArea:
            local_bestContour = contour
            maximumArea = currentArea
            
    if local_bestContour==None:
        return local_bestContour,0
    x,y,w,h = cv2.boundingRect(local_bestContour)
    return local_bestContour,w*h

def Rendering_Data(local_bestContour,mdistance):
    global frame,canny_img,r_ap,r_flag
    global lx,ly,lm
    x,y,w,h = cv2.boundingRect(local_bestContour)
    m=w
    if w<h:
        m=h
        
    if mdistance=="d" or mdistance=="e":
        vertices = np.array([[(x-m*0.5,y-m*0.5), (x-m*0.5,y+m*1.5), (x+m*1.5,y+m*1.5), (x+m*1.5,y-m*0.5)]], dtype=np.int32)
        ROI_image = region_of_interest(frame,vertices)
    else:
        vertices = np.array([[(x,y), (x,y+m), (x+m,y+m), (x+m,y)]], dtype=np.int32)
        ROI_image = region_of_interest(frame,vertices)
    hsv = cv2.cvtColor(ROI_image, cv2.COLOR_BGR2HSV)

    if mdistance=="a":
        bestContourRW,_ = rgb_preprocessing(hsv, lower_rwhite, upper_rwhite,1)
        if bestContourRW !=None:
            lx=x
            ly=y
            lm=m
            r_flag=1
            r_ap="  STOP  "
    elif mdistance=="b":
        bestContourBW,_ = rgb_preprocessing(hsv, lower_bwhite, upper_bwhite,1)
        if bestContourBW !=None:
            lx=x
            ly=y
            lm=m
            r_flag=1
            r_ap="Cross Walk"
    elif mdistance=="c":
        bestContourYB,_ = rgb_preprocessing(hsv, lower_yblack, upper_yblack,1)
        if bestContourYB !=None:
            lx=x
            ly=y
            lm=m
            r_flag=1
            r_ap="Slow Down"
    elif mdistance=="d":
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
    else:
        lx=ly=lm=0
    '''
    vertices = np.array([[(x-m*0.5,y-m*0.5), (x-m*0.5,y+m*1.5), (x+m*1.5,y+m*1.5), (x+m*1.5,y-m*0.5)]], dtype=np.int32)
    ROI_image = region_of_interest(canny_img,vertices)
    #cv2.imshow("mask4", ROI_image)
    contours, _ = cv2.findContours(ROI_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE )
    for cnt in contours:
        if cv2.contourArea( cnt ) > 2000:    
            approx = cv2.approxPolyDP( cnt, 0.01 * cv2.arcLength(cnt,True), True )
            #m = cv2.moments(cnt)
            #x2 = int(m["m10"]/ m["m00"])
            #y2 = int(m["m01"]/ m["m00"])
            #print len(approx)
            if len(approx)==8 and mdistance=="a":
                #cv2.drawContours( frame, [approx], -1, (255 , 50, 0 ), 2 )
                r_flag=1
                r_ap="   STOP"
            elif len(approx)==5 and mdistance=="b":
                #cv2.drawContours( frame1, [approx], -1, (255 , 50, 0 ), 2 )
                r_flag=1
                r_ap="Cross Walk"
            elif len(approx)==4 and mdistance=="c":
                #cv2.drawContours( frame1, [approx], -1, (255 , 50, 0 ), 2 )
                r_flag=1
                r_ap="Slow Down"
    '''

def rgb_detection():
    global frame, bestContour, mdistance
    global lx,ly,lm
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    distance={"a":0,"b":0,"c":0,"d":100}
    bestContour1,distance["a"] = rgb_preprocessing(hsv, lower_red, upper_red,0)
    bestContour2,distance["b"] = rgb_preprocessing(hsv, lower_blue, upper_blue,0)
    bestContour3,distance["c"] = rgb_preprocessing(hsv, lower_yellow, upper_yellow,0)
    bestContour4,distance["d"] = rgb_preprocessing(hsv, lower_rlight, upper_rlight,0)
    bestContour5,distance["e"] = rgb_preprocessing(hsv, lower_glight, upper_glight,0)
    
    mdistance = max(distance,key=distance.__getitem__)
    if mdistance == "a":
        bestContour=bestContour1
    elif mdistance == "b":
        bestContour=bestContour2
    elif mdistance == "c":
        bestContour=bestContour3
    elif mdistance == "d":
        bestContour=bestContour4
    elif mdistance == "e":
        bestContour=bestContour5
    else:
        bestContour=None
        x=y=m=0
    
def draw_object():
    global bestContour,mdistance
    if bestContour !=None:
        Rendering_Data(bestContour,mdistance)

global text,tx
text=""
tx=0.45
class counting(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.count=4
    def run(self):
        global text,tx
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
            global minute,sec
        while True:
            sec= sec+1
            if sec==60:
                sec=0
                minute=minute+1
            time.sleep(1.5)
t00=counting()
t00.start()
def Rendering():
    global frame, tx,minute,sec,r_flag
    global lx,ly,lm
    lxp=0
    if r_flag==1:
        if lx > WIDTH/2:
            lxp=50
        cv2.circle(frame,(lx+lm/2,ly+lm/2),lm/2+15,(200,200,200),1)
        cv2.circle(frame,(lx+lm/2,ly+lm/2),lm/2+5,(255,178,75),2)
        cv2.circle(frame,(lx+lm/2,ly+lm/2),lm/2,(200,200,200),1)
        cv2.putText(frame, r_ap,(int(lx-lxp),int(ly+lm+20)),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,125,55),3)
        cv2.putText(frame, r_ap,(int(lx-lxp),int(ly+lm+20)),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,255,255),1)
        
        
    r_flag=0
    
    if text ==None:
        cv2.putText(frame, "Operation" ,(int(WIDTH*0.05),int(HEIGHT*0.8)),cv2.FONT_HERSHEY_SIMPLEX,0.3,(255,255,255))
        cv2.putText(frame, str(minute)+":"+str(sec) ,(int(WIDTH*0.20),int(HEIGHT*0.8)),cv2.FONT_HERSHEY_SIMPLEX,0.3,(255,100,50))
        cv2.putText(frame, "Time",(int(WIDTH*0.09),int(HEIGHT*0.84)),cv2.FONT_HERSHEY_SIMPLEX,0.3,(255,255,255))
    else:
        cv2.putText(frame, text,(int(WIDTH*tx-5),int(HEIGHT*0.6-5)),cv2.FONT_HERSHEY_SIMPLEX,2,(0,0,0),10)
        cv2.putText(frame, text,(int(WIDTH*tx),int(HEIGHT*0.6)),cv2.FONT_HERSHEY_SIMPLEX,2,(255,255,255),10)
        cv2.putText(frame, text,(int(WIDTH*tx),int(HEIGHT*0.6)),cv2.FONT_HERSHEY_SIMPLEX,2,(50,150,250),5)
        cv2.putText(frame, text,(int(WIDTH*tx),int(HEIGHT*0.6)),cv2.FONT_HERSHEY_SIMPLEX,2,(50,200,250),2)

@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')

def gen():
    global frame, canny_img, bestContour, mdistance,r_ap,r_flag,minute,sec
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        frame = frame.array
        frame = cv2.resize(frame, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
        temp = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # 흑백이미지로 변환
        temp = cv2.GaussianBlur(temp,(3,3),0) # Blur 효과    
        canny_img = cv2.Canny(temp, 20, 210) # Canny edge 알고리즘
        t1=threading.Thread(target = rgb_detection)
        t2=threading.Thread(target = draw_object)
        t1.daemon = t2.daemon = True
        t1.start()
        t2.start()
        '''**********Rendering**********'''
        Rendering()
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
