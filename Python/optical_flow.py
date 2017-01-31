# import cv2
# import numpy as np
# # cap = cv2.VideoCapture(0)
# cap = cv2.VideoCapture('C:/Users/psdco/Videos/Trainings/480p/0 day1 rout2 720x480.mp4')

# ret, frame1 = cap.read()
# prvs = cv2.cvtColor(frame1,cv2.COLOR_BGR2GRAY)
# hsv = np.zeros_like(frame1)
# hsv[...,1] = 255

# while(1):
#     ret, frame2 = cap.read()
#     next = cv2.cvtColor(frame2,cv2.COLOR_BGR2GRAY)

#     flow = cv2.calcOpticalFlowFarneback(prvs,next, None, 0.5, 3, 15, 3, 5, 1.2, 0)

#     mag, ang = cv2.cartToPolar(flow[...,0], flow[...,1])
#     hsv[...,0] = ang*180/np.pi/2
#     hsv[...,2] = cv2.normalize(mag,None,0,255,cv2.NORM_MINMAX)
#     bgr = cv2.cvtColor(hsv,cv2.COLOR_HSV2BGR)

#     cv2.imshow('frame2',bgr)
#     k = cv2.waitKey(30) & 0xff
#     if k == 27:
#         break
#     elif k == ord('s'):
#         cv2.imwrite('opticalfb.png',frame2)
#         cv2.imwrite('opticalhsv.png',bgr)
#     prvs = next

# cap.release()
# cv2.destroyAllWindows()


##########################################################################################################
##########################################################################################################
##########################################################################################################
import numpy as np
import cv2

cap = cv2.VideoCapture('C:/Users/psdco/Videos/Trainings/480p/0 day1 rout2 720x480.mp4')


# params for ShiTomasi corner detection
feature_params = dict( maxCorners = 100,
                       qualityLevel = 0.3,
                       minDistance = 7,
                       blockSize = 7 )

# Parameters for lucas kanade optical flow
lk_params = dict( winSize  = (15,15),
                  maxLevel = 2,
                  criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

# Create some random colors
color = np.random.randint(0,255,(100,3))

# Take first frame and find corners in it
ret, old_frame = cap.read()
old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
p0 = cv2.goodFeaturesToTrack(old_gray, mask = None, **feature_params)

# Create a mask image for drawing purposes
mask = np.zeros_like(old_frame)

while(1):
    ret,frame = cap.read()
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # calculate optical flow
    p1, st, err = cv2.calcOpticalFlowPyrLK(old_gray, frame_gray, p0, None, **lk_params)

    # Select good points
    good_new = p1[st==1]
    good_old = p0[st==1]

    # draw the tracks
    for i,(new,old) in enumerate(zip(good_new,good_old)):
        a,b = new.ravel()
        c,d = old.ravel()
        mask = cv2.line(mask, (a,b),(c,d), color[i].tolist(), 2)
        frame = cv2.circle(frame,(a,b),5,color[i].tolist(),-1)
    img = cv2.add(frame,mask)

    cv2.imshow('frame',img)
    k = cv2.waitKey(30) & 0xff
    if k == 27:
        break

    # Now update the previous frame and previous points
    old_gray = frame_gray.copy()
    p0 = good_new.reshape(-1,1,2)

cv2.destroyAllWindows()
cap.release()

##########################################################################################################
##########################################################################################################
##########################################################################################################


'''
example to show optical flow
USAGE: opt_flow.py [<video_source>]
Keys:
 1 - toggle HSV flow visualization
 2 - toggle glitch
Keys:
    ESC    - exit
'''

# Python 2/3 compatibility
# from __future__ import print_function

# import numpy as np
# import cv2
# # import video


# def draw_flow(img, flow, step=16):
#     h, w = img.shape[:2]
#     y, x = np.mgrid[step/2:h:step, step/2:w:step].reshape(2,-1).astype(int)
#     fx, fy = flow[y,x].T
#     lines = np.vstack([x, y, x+fx, y+fy]).T.reshape(-1, 2, 2)
#     lines = np.int32(lines + 0.5)
#     vis = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
#     cv2.polylines(vis, lines, 0, (0, 255, 0))
#     for (x1, y1), (x2, y2) in lines:
#         cv2.circle(vis, (x1, y1), 1, (0, 255, 0), -1)
#     return vis


# def draw_hsv(flow):
#     h, w = flow.shape[:2]
#     fx, fy = flow[:,:,0], flow[:,:,1]
#     ang = np.arctan2(fy, fx) + np.pi
#     v = np.sqrt(fx*fx+fy*fy)
#     hsv = np.zeros((h, w, 3), np.uint8)
#     hsv[...,0] = ang*(180/np.pi/2)
#     hsv[...,1] = 255
#     hsv[...,2] = np.minimum(v*4, 255)
#     bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
#     return bgr


# def warp_flow(img, flow):
#     h, w = flow.shape[:2]
#     flow = -flow
#     flow[:,:,0] += np.arange(w)
#     flow[:,:,1] += np.arange(h)[:,np.newaxis]
#     res = cv2.remap(img, flow, None, cv2.INTER_LINEAR)
#     return res

# if __name__ == '__main__':
#     import sys
#     print(__doc__)
#     try:
#         fn = sys.argv[1]
#     except IndexError:
#         fn = 0

#     # cam = video.create_capture(fn)
#     cam = cv2.VideoCapture('C:/Users/psdco/Videos/Trainings/480p/0 day1 rout2 720x480.mp4')
#     ret, prev = cam.read()
#     prevgray = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
#     show_hsv = False
#     show_glitch = False
#     cur_glitch = prev.copy()

#     while True:
#         ret, img = cam.read()
#         gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#         flow = cv2.calcOpticalFlowFarneback(prevgray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
#         prevgray = gray

#         cv2.imshow('flow', draw_flow(gray, flow))
#         if show_hsv:
#             cv2.imshow('flow HSV', draw_hsv(flow))
#         if show_glitch:
#             cur_glitch = warp_flow(cur_glitch, flow)
#             cv2.imshow('glitch', cur_glitch)

#         ch = cv2.waitKey(5)
#         if ch == 27:
#             break
#         if ch == ord('1'):
#             show_hsv = not show_hsv
#             print('HSV flow visualization is', ['off', 'on'][show_hsv])
#         if ch == ord('2'):
#             show_glitch = not show_glitch
#             if show_glitch:
#                 cur_glitch = img.copy()
#             print('glitch is', ['off', 'on'][show_glitch])
#     cv2.destroyAllWindows()
