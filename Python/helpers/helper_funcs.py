from __future__ import print_function

import os
import sys

import cv2

import consts
import numpy as np

# Helper functions
# Opens video with error handling
def open_video(videoName):
    pathToVideo = os.path.join(consts.videosRootPath, videoName)
    print("Opening " + pathToVideo)

    if not os.path.exists(pathToVideo):
        print("No such directory " + pathToVideo)
        exit()

    cap = cv2.VideoCapture(pathToVideo)
    if not cap.isOpened():
        print("Unable to open video file " + pathToVideo)
        exit()

    return cap


def input_was_yes():
    input = raw_input('> ')  # in python 2, input = eval(raw_input("> "))
    # Returns true for y or Y. Will return false for any other input
    return input.lower() == 'y'


def read_num(limitMax, limitMin=0):
    while (1):
        print('> ', end="")
        num = sys.stdin.readline()
        try:
            num = int(num)
        except Exception:
            print('Enter a number. \'%s\' is not an int' % (num[0:-1]))
            continue

        if (num < limitMin or num > limitMax):
            print('Enter a number between 1 and %s. \'%d\' is out of bounds' % (limitMax, num))
        else:
            break

    return num


def parse_num(s):
    try:
        return int(s)
    except ValueError:
        return 0


def crop_points_constrained(frame_height, frame_width, cx, cy, crop_length):
    y1 = cy - crop_length / 2
    y2 = cy + crop_length / 2
    x1 = cx - crop_length / 2
    x2 = cx + crop_length / 2
    if y2 > frame_height:
        y1 = frame_height - crop_length
        y2 = frame_height
    if y1 < 0:
        y1 = 0
        y2 = crop_length
    if x2 > frame_width:
        x1 = frame_width - crop_length
        x2 = frame_width
    if x1 < 0:
        x1 = 0
        x2 = crop_length
    return x1, x2, y1, y2


def contourCenter(contour):
    M = cv2.moments(contour)
    if M['m00'] > 0:
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])
        return int(cx), int(cy)
    else:
        return

# http://dsp.stackexchange.com/questions/2564/opencv-c-connect-nearby-contours-based-on-distance-between-them
def find_if_close(cnt1, cnt2):
    # minDist = 9999
    row1, row2 = cnt1.shape[0], cnt2.shape[0]
    for i in xrange(row1):
        for j in xrange(row2):
            dist = np.linalg.norm(cnt1[i] - cnt2[j])
            # if abs(dist) < minDist:
            #     minDist = abs(dist)
            if abs(dist) < consts.contourDistance:
                return True
            elif i == row1 - 1 and j == row2 - 1:
                # print("Minimum contour distance was", minDist)
                return False


def simple_downsample(a, num):
    if len(a) < num:
        print("No can do. Cannot upsample list with {} elements to one with {}".format(len(a), num))
        return a
    b = []
    spacing = len(a)/float(num)
    for i in range(num):
        b.append(a[int(round(spacing*i))])
    return b