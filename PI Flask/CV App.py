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
global frame, canny_img, bestContour, mdistance, r_ap,r_falg,minute,sec
## main
app = Flask(__name__)

frame = canny_img = bestContour = r_ap = None
mdistance=r_falg=minute=sec=0
lock = thread.allocate_lock()
WIDTH=320
HEIGHT=280
camera = PiCamera()
camera.resolution = (WIDTH*2, HEIGHT*2)
camera.framerate = 40
camera.brightness = 57
rawCapture = PiRGBArray(camera, size=(WIDTH*2, HEIGHT*2))

lower_red = np.array([0,100,100])#Red
upper_red = np.array([1,200,200])
lower_blue = np.array([106,80,80])#blue
upper_blue = np.array([108,200,200])
lower_yellow = np.array([26,100,100])#yellow
upper_yellow = np.array([28,200,200])

def region_of_interest(img, vertices, color3=(255,255,255), color1=255):#ROI
    mask = np.zeros_like(img)
    if len(img.shape) > 2:
        color = color3
    else: 
        color = color1
    cv2.fillPoly(mask, vertices, color)
    ROI_image = cv2.bitwise_and(img, mask)
    return ROI_image

def rgb_preprocessing(hsv,lower_rgb,upper_rgb):# Trffic light rgb preprocessing
    #Create a binary frame, where anything green appears white and everything else is black
    element = cv2.getStructuringElement(cv2.MORPH_RECT,(3,3))
    #Get rid of background noise using erosion and fill in the holes using dilation and erode the final frame on last time
    mask_rgb = cv2.inRange(hsv, lower_rgb, upper_rgb)
    mask_rgb = cv2.dilate(mask_rgb,element,iterations=7)
    mask_rgb = cv2.erode(mask_rgb,element, iterations=7)
    
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

def Rendering_Data(local_bestContour,mdistance, canny_img):
    global frame,r_ap,r_falg
    x,y,w,h = cv2.boundingRect(local_bestContour)
    m=w
    if w<h:
        m=h
    cv2.circle(frame,(x+m/2,y+m/2),m/2+10,(200,200,200),1)
    cv2.circle(frame,(x+m/2,y+m/2),m/2+5,(255,200,75),2)
    cv2.circle(frame,(x+m/2,y+m/2),m/2,(200,200,200),1)

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
                r_falg=1
                r_ap="   STOP"
            elif len(approx)==5 and mdistance=="b":
                #cv2.drawContours( frame1, [approx], -1, (255 , 50, 0 ), 2 )
                r_falg=1
                r_ap="Cross Walk"
            elif len(approx)==4 and mdistance=="c":
                #cv2.drawContours( frame1, [approx], -1, (255 , 50, 0 ), 2 )
                r_falg=1
                r_ap="Slow Down"

def rgb_detection():
    global frame, canny_img, bestContour, mdistance
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    distance={"a":0,"b":0,"c":0,"d":100}
    bestContour1,distance["a"] = rgb_preprocessing(hsv, lower_red, upper_red)
    bestContour2,distance["b"] = rgb_preprocessing(hsv, lower_blue, upper_blue)
    bestContour3,distance["c"] = rgb_preprocessing(hsv, lower_yellow, upper_yellow)
    mdistance = max(distance,key=distance.__getitem__)
    
    if mdistance == "a":
        bestContour=bestContour1
    elif mdistance == "b":
        bestContour=bestContour2
    elif mdistance == "c":
        bestContour=bestContour3
    else:
        bestContour=None
    

def draw_object():
    global frame,canny_img,bestContour,mdistance,r_falg
    if bestContour !=None:
        Rendering_Data(bestContour,mdistance , canny_img)

def operation_time():
    global minute,sec
    while True:
        sec= sec+1
        if sec==60:
            sec=0
            minute=minute+1
        time.sleep(1)
        
t0=threading.Thread(target = operation_time)
t0.start()    
@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')

def gen():
    global frame, canny_img, bestContour, mdistance,r_ap,r_falg,minute,sec
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
        if r_falg==1:
            cv2.rectangle(frame, (int(WIDTH*0.35),int(HEIGHT*0.7)),(int(WIDTH*0.64),int(HEIGHT*0.75)), (10,10,10), -1)
            cv2.putText(frame, r_ap,(int(WIDTH*0.36),int(HEIGHT*0.74)),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,255,255))
        r_falg=0
        cv2.putText(frame, "Operation" ,(int(WIDTH*0.05),int(HEIGHT*0.8)),cv2.FONT_HERSHEY_SIMPLEX,0.3,(255,255,255))
        cv2.putText(frame, str(minute)+":"+str(sec) ,(int(WIDTH*0.20),int(HEIGHT*0.8)),cv2.FONT_HERSHEY_SIMPLEX,0.3,(255,100,50))
        cv2.putText(frame, "Time",(int(WIDTH*0.09),int(HEIGHT*0.84)),cv2.FONT_HERSHEY_SIMPLEX,0.3,(255,255,255))
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
