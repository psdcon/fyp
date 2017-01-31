from __future__ import print_function

import os
import sys

import cv2

import consts


# Helper functions
# Opens video with error handling
def open_video(videoName):
    pathToVideo = os.path.join(consts.videoPath, videoName)
    print("\nOpening " + pathToVideo)

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
