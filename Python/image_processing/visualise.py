from __future__ import print_function
from __future__ import print_function

import json
import os
from itertools import chain

import cv2
import h5py
import matplotlib.pyplot as plt
import numpy as np
import scipy.io
from sqlalchemy.orm.exc import NoResultFound

import helpers.helper
from helpers import consts
from helpers import helper
from helpers.db_declarative import *
from image_processing import track


def play_skill(db, bounce_id, show_pose=False, show_full=False):
    bounce = db.query(Bounce).filter_by(id=bounce_id).one()
    routine = bounce.routine

    play_frames(db, routine, bounce.start_frame, bounce.end_frame, show_pose, show_full)


def play_frames(db, routine, start_frame=0, end_frame=-1, show_pose=None, show_full=False):
    waitTime = 40
    playOneFrame = False
    paused = False

    cap = helper.open_video(routine.path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    if end_frame == -1:
        end_frame = cap.get(cv2.CAP_PROP_FRAME_COUNT)

    firstFrame = db.query(Frame).filter_by(routine_id=routine.id, frame_num=1).one()
    firstFrameId = firstFrame.id
    if show_pose is not False:  # if not deliberately set to ellipse, then gracefully fallback to pose if available or ellipse if not
        show_pose = firstFrame.pose is not None  # if pose is none, show ellipse

    while True:
        if playOneFrame or not paused:

            _ret, frame = cap.read()

            try:
                frame_data = db.query(Frame).filter_by(routine_id=routine.id,
                                                       frame_num=cap.get(cv2.CAP_PROP_POS_FRAMES)).one()
            except NoResultFound:
                continue

            cx = frame_data.center_pt_x
            cy = frame_data.center_pt_y
            x1, x2, y1, y2 = helper.bounding_square(routine.video_height, routine.video_width, cx, cy, routine.padding)

            if show_pose:
                pose = np.array(json.loads(frame_data.pose))
                # pose_rough = np.array(json.loads(frame_data.pose_hg))
                # Show full frame
                if show_full:
                    cv2.putText(frame, '{}'.format(frame_data.frame_num), (10, 20), cv2.FONT_HERSHEY_SIMPLEX,
                                0.4, (255, 255, 255))
                    for p_idx in range(14):
                        pose_x = int((cx - routine.padding) + pose[0, p_idx])
                        pose_y = int((cy - routine.padding) + pose[1, p_idx])
                        color = consts.poseColors[consts.poseAliai['hourglass'][p_idx]][1]
                        cv2.circle(frame, (pose_x, pose_y), 5, color, thickness=-1)  # -ve thickness = filled
                    cv2.imshow('HG Smooth', frame)

                # Show cropped
                else:
                    frameCropped = frame[y1:y2, x1:x2]
                    # frameCroppedCopy = np.copy(frameCropped)
                    cv2.putText(frameCropped, '{}'.format(frame_data.frame_num), (10, 20), cv2.FONT_HERSHEY_SIMPLEX,
                                0.4, (255, 255, 255))
                    for p_idx in range(16):
                        color = consts.poseColors[consts.poseAliai['hourglass'][p_idx]][1]
                        cv2.circle(frameCropped, (int(pose[0, p_idx]), int(pose[1, p_idx])), 5, color,
                                   thickness=-1)  # -ve thickness = filled
                    cv2.imshow('HG Smooth', frameCropped)

                    # for p_idx in range(16):
                    #     color = consts.poseColors[consts.poseAliai['hourglass'][p_idx]][1]
                    #     cv2.circle(frameCroppedCopy, (int(pose_rough[0, p_idx]), int(pose_rough[1, p_idx])), 5, color,
                    #                thickness=-1)  # -ve thickness = filled
                    # cv2.imshow('HG', frameCroppedCopy)

            else:
                cv2.circle(frame, (cx, cy), 3, (0, 0, 255), -1)
                if show_full:
                    # (x, y), (MA, ma), angle
                    # ellipse = ((cx, cy), (float(frame_data.ellipse_len_major), float(frame_data.ellipse_len_minor)),
                    #            frame_data.ellipse_angle)
                    ellipse = ((cx, cy), (frame_data.ellipse_len_major, frame_data.ellipse_len_minor),frame_data.ellipse_angle)
                    cv2.ellipse(frame, ellipse, color=(0, 255, 0), thickness=2)
                    cv2.imshow('bounce.skill_name', frame)
                else:
                    frameCropped = frame[y1:y2, x1:x2]
                    cv2.imshow('bounce.skill_name', frameCropped)

            if playOneFrame:
                playOneFrame = False

        k = cv2.waitKey(waitTime) & 0xff
        if k == ord('k'):  # play pause
            paused = not paused
        elif k == ord('j'):  # prev frame
            playOneFrame = True
            cap.set(cv2.CAP_PROP_POS_FRAMES, cap.get(cv2.CAP_PROP_POS_FRAMES) - 2)
        elif k == ord('l'):  # next frame
            playOneFrame = True
        elif k == ord('.'):  # speed up
            waitTime -= 5
            print(waitTime)
        elif k == ord(','):  # slow down
            waitTime += 5
            print(waitTime)
        elif k == ord('q') or k == 27:  # q/ESC
            print("Exiting...")
            exit()

        # Loop forever
        if cap.get(cv2.CAP_PROP_POS_FRAMES) == end_frame:
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            # break


def plot_data(routine):
    print("\nStarting plotting...")
    f, axarr = plt.subplots(4, sharex=True)

    # Plot bounce heights
    x_frames = [frame.frame_num / routine.video_fps for frame in routine.frames]
    y_travel = [frame.center_pt_x for frame in routine.frames]
    y_height = [routine.video_height - frame.center_pt_y for frame in routine.frames]

    # List inside list gets flattened
    peaks_x = list(chain.from_iterable(
        (bounce.start_time, bounce.max_height_frame / routine.video_fps) for bounce in routine.bounces))
    peaks_x.append(routine.bounces[-1].end_time)
    peaks_y = list(chain.from_iterable((bounce.start_height, bounce.max_height) for bounce in routine.bounces))
    peaks_y.append(routine.bounces[-1].end_height)
    # peaks_y = [routine.video_height - p for p in peaks_y]

    axarr[0].set_title("Height")
    axarr[0].plot(x_frames, y_height, color="g")
    axarr[0].plot(peaks_x, peaks_y, 'r+')
    axarr[0].set_ylabel('Height (Pixels)')

    # Plot bounce travel
    axarr[1].set_title("Travel")
    axarr[1].set_ylabel('Rightwardness (Pixels)')
    axarr[1].plot(x_frames, y_travel, color="g")
    axarr[1].axhline(y=routine.trampoline_center, xmin=0, xmax=1000, c="blue")
    axarr[1].axhline(y=routine.trampoline_center + 80, xmin=0, xmax=1000, c="red")
    axarr[1].axhline(y=routine.trampoline_center - 80, xmin=0, xmax=1000, c="red")

    # Ellipse angles
    x_frames = np.array([frame.frame_num / routine.video_fps for frame in routine.frames])
    y_angle = np.array([frame.ellipse_angle for frame in routine.frames])
    # Changes angles
    y_angle = np.unwrap(y_angle, discont=90, axis=0)

    axarr[2].plot(x_frames, y_angle, color="g")
    axarr[2].set_title("Angle")
    axarr[2].set_ylabel('Angle (deg)')

    # Ellipse lengths
    y_major = np.array([frame.ellipse_len_major for frame in routine.frames])
    y_minor = np.array([frame.ellipse_len_minor for frame in routine.frames])

    # axarr[3].scatter(x_frames, y_major, color="g")
    # axarr[3].scatter(x_frames, y_minor, color='b')
    # axarr[3].set_ylim([0, 300])
    # axarr[3].set_title("Ellipse Axes Length")
    # axarr[3].set_ylabel('Length')
    # axarr[3].set_xlabel('Time (s)')

    axarr[3].plot(x_frames, y_major/y_minor, color="g")
    axarr[3].set_title("Ellipse Axes Ratio")
    axarr[3].set_ylabel('Length Ratio')
    axarr[3].set_xlabel('Time (s)')

    plt.show()


def skill_into_filmstrip(cap, routine):
    capWidth = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    capHeight = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    bounces = json.loads(routine['bounces'])
    print('\nChoose a skill:')
    for i, b in enumerate(bounces):
        print('%d) %s' % (i + 1, b['name']))
    choice = 10
    # choice = readNum(len(bounces))

    bounce = bounces[choice - 1]
    start = bounce['startFrame'] + 6
    end = bounce['endFrame'] - 6
    step = (end - start) / 6
    step = int(step)
    framesToSave = range(start, end, step)

    whitespace = 4
    width = 255

    startPixel = int((capWidth * 0.55) - width / 2)
    endPixel = startPixel + width
    filmStrip = np.ones(shape=(capHeight * 0.8, (width * len(framesToSave)) + (whitespace * len(framesToSave) - 1), 3),
                        dtype=np.uint8)

    for i, frameNum in enumerate(framesToSave):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frameNum)
        _ret, frame = cap.read()

        # possible improvement
        trackPerson = frame[0:capHeight * 0.8, startPixel:endPixel]
        start = ((whitespace + width) * i)
        filmStrip[0:capHeight * 0.8, start:start + width] = trackPerson

    imgName = "C:/Users/psdco/Videos/{}/{}.png".format(routine['name'][:-4], bounce['name'])
    print("Writing frame to {}".format(imgName))
    ret = cv2.imwrite(imgName, filmStrip)
    if not ret:
        print("Couldn't write image {}\nAbort!".format(imgName))
        exit()


def plot_skill_pose(db, routine):
    def rel_pose_to_abs_pose(pose, cx, cy, padding=100):
        # pose points are relative to the top left (cx cy = ix iy; 0 0 = ix-100 iy-100) of the 200x200 cropped frame
        # pose given by (0 + posex, 0 + posey) => cx-100+posex, cy-100+posey
        for p_idx in range(14):
            pose[0, p_idx] = int((cx - padding) + pose[0, p_idx])
            pose[1, p_idx] = int((cy - padding) + pose[1, p_idx])
        return pose

    def pose_as_point(pose, p_idx):
        pt = np.array([pose[0, p_idx], pose[1, p_idx]])
        return pt

    def angle(A, B, C):
        from math import acos, degrees
        from scipy.spatial import distance
        a = distance.euclidean(C, B)
        b = distance.euclidean(A, C)
        c = distance.euclidean(A, B)
        num = a ** 2 + b ** 2 - c ** 2
        demon = (2.0 * a * b)
        ang = acos(num / demon)
        return degrees(ang)

    # Get a skill
    skill = routine.bounces[15]
    play_skill(db, skill.id, show_pose=True)

    # Save all poses from
    skillFrames = []
    poses = []
    for frame in routine.frames:
        if frame.frame_num > skill.start_frame and frame.frame_num < skill.end_frame:
            skillFrames.append(frame)
            # absPose = rel_pose_to_abs_pose(np.array(json.loads(frame.pose)), frame.center_pt_x, routine.video_height - frame.center_pt_y)
            # poses.append(absPose)
            poses.append(np.array(json.loads(frame.pose)))
            # poses.append(np.array(json.loads(frame.pose_hg)))

    # Make a list for each of the joints to be plotted
    jointNames = consts.getAngleIndices('deepcut')
    # jointNames = consts.getAngleIndices('hourglass')
    angleValues = {key: [] for key in jointNames.keys()}
    # Calculate an array of angles
    for pose in poses:
        for key in jointNames.keys():
            part_idx = jointNames[key]
            #
            angleVal = angle(pose_as_point(pose, part_idx[0]), pose_as_point(pose, part_idx[1]),
                             pose_as_point(pose, part_idx[2]))
            angleValues[key].append(angleVal)

    # Plot angles
    f, axarr = plt.subplots(4, sharex=True)

    # use angleIndexKeys rahter than jointNames.keys() because order matters here
    for i, key in enumerate(consts.angleIndexKeys):
        plti = int(i / 2)  # when i=0,1; plti = 0. when i=2,3; plti = 1. when i=4,5; plti = 2. when i=6,7; plti = 3
        axarr[plti].plot(range(len(poses)), angleValues[key], c=consts.jointAngleColors[i % 2], label=key)
        axarr[plti].scatter(range(len(poses)), angleValues[key], c=consts.jointAngleColors[i % 2])
        axarr[plti].legend(loc='best')
    plt.show()


def pose_error(routine):
    hg_preds_file = h5py.File('preds.h5', 'r')
    hg_preds = hg_preds_file.get('preds')

    mat_preds_file = scipy.io.loadmat('preds.mat')
    mat_preds = mat_preds_file['preds_2d']

    x_mat = [[] for _ in range(16)]
    x_hg = [[] for _ in range(16)]
    y_mat = [[] for _ in range(16)]
    y_hg = [[] for _ in range(16)]

    for i, frame_data in enumerate(routine.frames):
        pose_mat = mat_preds[:, :, i]
        pose_hg = np.array(
            json.loads(frame_data.pose_hg))  # np.array(hg_preds['{0:04}'.format(frame_data.frame_num)].value).T
        for p_idx in range(16):
            x_mat[p_idx].append(int(pose_mat[0, p_idx]))
            x_hg[p_idx].append(int(pose_hg[0, p_idx]))
            y_mat[p_idx].append(int(pose_mat[1, p_idx]))
            y_hg[p_idx].append(int(pose_hg[1, p_idx]))

    plt.figure(1)
    for i in range(16):
        diff = np.diff([x_mat[i], x_hg[i]], axis=0)
        plt.plot(diff[0])

    plt.figure(2)
    for i in range(16):
        diff = np.diff([y_mat[i], y_hg[i]], axis=0)
        plt.plot(diff[0])
    plt.show()
