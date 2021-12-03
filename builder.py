#!/usr/bin/env python

import cv2 
import numpy as np 

def get_circles(filename):
    img = cv2.imread(filename, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) 
    gray_blurred = cv2.blur(gray, (3, 3)) 
 
    circles = cv2.HoughCircles(gray_blurred,  
               cv2.HOUGH_GRADIENT, 1, 20, param1 = 50, 
               param2 = 30, minRadius = 20, maxRadius = 40) 
    if circles is None:
        return None
    # round values
    circles = np.uint16(np.around(circles)) 
    # extract mean radius
    radius = []
    for pt in circles[0, :]:
        radius.append(pt[2])
    r = int(np.around(np.mean(radius)))
    r += 1
    # extract circles
    defs = []
    for pt in circles[0, :]:
        x, y = int(pt[0]), int(pt[1])
        defs.append((x,y,r))
    return defs

def get_connections(circles):
    cnxs = []
    r = 2*circles[0][2]+6
    r2 = r*r
    for i1,c1 in enumerate(circles):
        for i2, c2 in enumerate(circles):
            if c1 == c2: continue
            x1,y1,_ = c1
            x2,y2,_ = c2
            d = (x2-x1)*(x2-x1)+(y2-y1)*(y2-y1) 
            if d<r2:
                cnxs.append((i1,i2))
    return cnxs

if __name__ == "__main__":
    filename = 'dunai.jpg'
    img = cv2.imread(filename, cv2.IMREAD_COLOR)
    circles = get_circles(filename)
    get_connections(circles)
    for x,y,r in circles:
        cv2.circle(img, (x, y), r, (0, 255, 0), 2) 
        cv2.circle(img, (x, y), 1, (0, 0, 255), 3) 
    cv2.imshow("Detected Circle", img) 
    cv2.waitKey(0)
