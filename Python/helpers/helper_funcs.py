from __future__ import print_function

import cPickle
import gzip
import json
import os
import sys
from math import acos, degrees

import cv2
import numpy as np
from scipy.spatial import distance

from helpers import consts


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
    num = ''
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


def calcContourCenter(contour):
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
    spacing = len(a) / float(num)
    for i in range(num):
        b.append(a[int(round(spacing * i))])
    return b


def prettyPrintRoutine(bounces):
    if not bounces:
        return "No bounces"

    str = ""
    count = 0
    paddingLen = max([len(b.skill_name) for b in bounces]) + 2
    for b in bounces:
        if b.skill_name != "In/Out Bounce":
            count += 1
        # Print any associated juding info
        if b.deductions:
            str += "\n\t{:2}. {:{padding}} {}".format(count, b.skill_name, b.deductions[0], padding=paddingLen)
        else:
            str += "\n\t{:2}. {}".format(count, b.skill_name)
    return str


def save_zipped_pickle(obj, filename, protocol=-1):
    with gzip.open(filename, 'wb') as f:
        cPickle.dump(obj, f, protocol)


def load_zipped_pickle(filename):
    with gzip.open(filename, 'rb') as f:
        loaded_object = cPickle.load(f)
        return loaded_object


def save_pickle(obj, filename):
    cPickle.dump(obj, open(filename, 'wb'))


def load_pickle(filename):
    return cPickle.load(open(filename, 'rb'))


def roundListFloatsIntoStr(mList, precision):
    return json.dumps(json.loads(json.dumps(mList), parse_float=lambda x: round(float(x), precision)))


def trimTouches(trampolineTouches):
    touchTransitions = np.diff(trampolineTouches)
    for i in range(len(touchTransitions)):
        thisTransition = touchTransitions[i]
        if thisTransition > 0:  # spike up
            trampolineTouches[i + 1] = 0
            trampolineTouches[i + 2] = 0
        elif thisTransition < 0:  # spike down
            trampolineTouches[i] = 0
            trampolineTouches[i - 1] = 0
    return trampolineTouches


def printPoseStatus(paths):
    from collections import OrderedDict
    import glob

    class Colors:
        BLUE = '\033[94m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        RED = '\033[91m'
        ENDC = '\033[0m'

    def colour_str(s, color):
        return color + s + Colors.ENDC

    mdict = OrderedDict([
        ('f', 'frame_*.png'),
        ('HG', 'hg_heatmaps.h5'),
        ('MATLAB', 'monocap_preds_2d.h5'),
        ('HGIMG', 'posed_*'),
        ('MATIMG', 'smoothed_*'),
    ])

    for path in paths:
        # Print the number of savedFrame files found
        for key in mdict:
            nFiles = len(glob.glob(path + os.sep + mdict[key]))
            if nFiles == 0:
                print(colour_str(key, Colors.RED), end=' ')
            else:
                print(colour_str(key, Colors.GREEN), end=' ')

            if nFiles > 1:
                print('{:3}'.format(nFiles), end='   ')
            else:
                print('{:3}'.format(nFiles), end='   ')

        # Print the dir/routine name at the end
        print(os.path.basename(path))


def getPoseStatuses(paths, routinePrettyName):
    import glob
    '''
    [
        {
            path:'VID_0000__technique',
            hourglass_pose: True,
            monocap_pose: True,
            frames: 200,
            hourglass_frames: 200,
            monocap_frames: 200
        },
        {...},
        ...
    ]
    '''
    pathsData = []
    for path in paths:
        # Print the number of savedFrame files found
        thisPathData = dict()
        thisPathData['path'] = os.path.basename(path.replace(routinePrettyName, '_'))
        thisPathData['hourglass_pose'] = os.path.exists(path + os.sep + 'hg_heatmaps.h5')
        thisPathData['monocap_pose'] = os.path.exists(path + os.sep + 'monocap_preds_2d.h5')
        for key, globLookup in zip(['frames', 'hourglass_frames', 'monocap_frames'], ['frame_*.png', 'posed_*', 'smoothed_*', ]):
            nFiles = len(glob.glob(path + os.sep + globLookup))
            thisPathData[key] = nFiles
        pathsData.append(thisPathData)
    return pathsData


def selectListOption(lst):
    for i, li in enumerate(lst):
        print('{}) {}'.format(i + 1, li))
    return read_num(len(lst)) - 1


def pose2OrderedAngles(pose):
    angles = gen_pose_angles([pose])
    orderedAngles = []
    for key in consts.extendedAngleIndexKeys:
        angle = angles[key][0]
        orderedAngles.append(angle)
    return orderedAngles


def gen_pose_angles(poses, average=False):
    def rel_pose_to_abs_pose(pose, cx, cy, padding=100):
        # pose points are relative to the top left (cx cy = ix iy; 0 0 = ix-100 iy-100) of the 200x200 cropped frame
        # pose given by (0 + posex, 0 + posey) => cx-100+posex, cy-100+posey
        for p_idx in range(14):
            pose[0, p_idx] = int((cx - padding) + pose[0, p_idx])
            pose[1, p_idx] = int((cy - padding) + pose[1, p_idx])
        return pose

    def pose2pt(pose, p_idx):
        pt = np.array([pose[0, p_idx], pose[1, p_idx]])
        return pt

    def calc_angle(A, B, C):
        a = distance.euclidean(C, B)
        b = distance.euclidean(A, C)
        c = distance.euclidean(A, B)
        num = a ** 2 + b ** 2 - c ** 2
        demon = (2.0 * a * b)
        ang = acos(num / demon)
        return degrees(ang)

    # Make a list for each of the joints to be plotted
    jointNames = consts.getAngleIndices('hourglass')
    jointSpecial = consts.getSpecialAngleIndices('hourglass')
    jointAngles = {key: [] for key in jointNames.keys() + jointSpecial.keys()}

    for pose in poses:
        # Calculate an angle for each joint
        # Add to the dict for that joint
        for key in jointNames.keys():
            # Get the 3 pose points that make up this joint
            jointIndexs = jointNames[key]
            # Calculate the angle between them
            angle = calc_angle(pose2pt(pose, jointIndexs[0]), pose2pt(pose, jointIndexs[1]), pose2pt(pose, jointIndexs[2]))
            # Append it to the appropriate dict
            jointAngles[key].append(angle)

        # Special angles
        for key in jointSpecial.keys():
            jointIndexs = jointSpecial[key]
            specialsOffset = np.array(consts.specialOffsets[key])
            # Calculate the angle between them
            angle = calc_angle(pose2pt(pose, jointIndexs[0]) + specialsOffset, pose2pt(pose, jointIndexs[1]), pose2pt(pose, jointIndexs[2]))
            # Append it to the appropriate dict
            jointAngles[key].append(angle)

    if not average:
        return jointAngles
    else:
        averagedJointAngles = {}
        for i in range(0, len(consts.angleIndexKeys), 2):  # step from 0 to 8 in increments of 2
            rightKey = consts.angleIndexKeys[i]
            leftKey = consts.angleIndexKeys[i + 1]
            jointName = rightKey.split(' ')[1].title()  # take the last word and set it to title case
            averagedJointAngles[jointName] = np.average([jointAngles[rightKey], jointAngles[leftKey]], axis=0)
        return averagedJointAngles


def clip_wrap(num, lower, upper):
    if num < lower:
        return upper
    elif num > upper:
        return lower
    else:
        return num
