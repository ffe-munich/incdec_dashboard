from types import DynamicClassAttribute
import plotly.express as px

import numpy as np
import cv2 as cv
import base64
from scipy import ndimage
# Create a black image
def dynamic_plot(p=0):
    img_1 = cv.imread('Capture.PNG')
    filename = './assets/image.jpg'
    font                   = cv.FONT_HERSHEY_SIMPLEX
    position_1              = (100,120)
    position_2              = (100,270) 
    position_3               = (340,80)
    position_4               = (340,170)
    position_5               = (500,60)
    position_6               = (500,190)
    position_7               = (480,330)
    fontScale              = 0.6
    fontColor              = (0,0,0)
    thickness              = 1
    img_1 =cv.putText(img_1,'Game',
        position_1,
        font,
        fontScale,
        fontColor,thickness)
    img_1 =cv.putText(img_1,'No Game',
        position_2,
        font,
        fontScale,
        fontColor,thickness)
    img_1 =cv.putText(img_1,"1-p",
        position_3,
        font,
        fontScale,
        fontColor,thickness)
    img_1 =cv.putText(img_1,"p",
        position_4,
        font,
        fontScale,
        fontColor,thickness)
    img_1 =cv.putText(img_1,"Payoffs with attribution",
        position_5,
        font,
        fontScale,
        fontColor,thickness)
    img_1 =cv.putText(img_1,"Payoffs with non-attribution",
        position_6,
        font,
        fontScale,
        fontColor,thickness)
    img_1 =cv.putText(img_1,"Payoffs with no-gaming",
        position_7,
        font,
        fontScale,
        fontColor,thickness)
    
    cv.imwrite(filename, img_1) 
