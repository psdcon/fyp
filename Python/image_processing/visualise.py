from __future__ import print_function
from __future__ import print_function

import json
from itertools import chain

import cv2
import h5py
import matplotlib.pyplot as plt
import numpy as np
import scipy.io
import sqlalchemy
from sqlalchemy.orm.exc import NoResultFound

from helpers import consts
from helpers import helper
from helpers.db_declarative import *
from image_processing import track


def play_skill(db, bounce_id, show_pose=False, show_full=False):
    bounce = db.query(Bounce).filter_by(id=bounce_id).one()
    routine = bounce.routine

    play_frames(db, routine, bounce.start_frame, bounce.end_frame, show_pose, show_full)


def play_frames(db, routine, start_frame=0, end_frame=-1, show_pose=False, show_full=False):
    waitTime = 40
    updateOne = False
    paused = False
    padding = 100

    hg_preds_file = h5py.File('preds.h5', 'r')
    hg_preds = hg_preds_file.get('preds')

    mat_preds_file = scipy.io.loadmat('preds.mat')
    mat_preds = mat_preds_file['preds_2d']

    cap = helper.open_video(routine.path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    if end_frame == -1:
        end_frame == cap.get(cv2.CAP_PROP_FRAME_COUNT)

    while True:
        if updateOne or not paused:

            _ret, frame = cap.read()

            try:
                frame_data = db.query(Frame).filter_by(routine_id=routine.id,
                                                       frame_num=cap.get(cv2.CAP_PROP_POS_FRAMES)).one()
            except NoResultFound:
                continue

            cx = frame_data.center_pt_x
            # cy = frame_data.center_pt_y
            cy = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) - frame_data.center_pt_y)

            if show_pose:
                # pose = np.array(json.loads(frame_data.pose))
                # pose = np.array(json.loads(frame_data.pose_hg))
                pose = mat_preds[:, :, frame_data.id-1]
                pose_hg = np.array(hg_preds['{0:04}'.format(frame_data.frame_num)].value).T

                # pose points are relative to the top left (cx cy = ix iy; 0 0 = ix-100 iy-100) of the 200x200 cropped frame
                # pose given by (0 + posex, 0 + posey) => cx-100+posex, cy-100+posey
                # Show full frame
                if show_full:
                    for p_idx in range(14):
                        posex = int((cx - padding) + pose[0, p_idx])
                        posey = int((cy - padding) + pose[1, p_idx])
                        cv2.circle(frame, (posex, posey), 5, consts.poseColors[p_idx],
                                   thickness=-1)  # -ve thickness = filled
                    cv2.imshow('bounce.skill_name', frame)

                # Show cropped
                else:
                    frameCropped = frame[cy - padding:cy + padding, cx - padding:cx + padding]  # [y1:y2, x1:x2]
                    frameCropped = np.copy(frameCropped)
                    cv2.putText(frameCropped, '{}'.format(frame_data.frame_num), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255))
                    for p_idx in range(16):
                        color = consts.poseColors[consts.poseAliai['hourglass'][p_idx]][1]
                        cv2.circle(frameCropped, (int(pose[0, p_idx]), int(pose[1, p_idx])), 5, color,
                                   thickness=-1)  # -ve thickness = filled
                    cv2.imshow('DC', frameCropped)

                    # padding = 105
                    frameCroppedCopy = frame[cy - padding:cy + padding, cx - padding:cx + padding]  # [y1:y2, x1:x2]
                    for p_idx in range(16):
                        color = consts.poseColors[consts.poseAliai['hourglass'][p_idx]][1]
                        cv2.circle(frameCroppedCopy, (int(pose_hg[0, p_idx]), int(pose_hg[1, p_idx])), 5, color,
                                   thickness=-1)  # -ve thickness = filled
                    cv2.imshow('HG', frameCroppedCopy)

            else:
                cv2.circle(frame, (cx, cy), 3, (0, 0, 255), -1)
                if show_full:
                    # (x, y), (MA, ma), angle
                    ellipse = ((cx, cy), (float(frame_data.ellipse_len_major), float(frame_data.ellipse_len_minor)), frame_data.ellipse_angle)
                    cv2.ellipse(frame, ellipse, color=(0, 255, 0), thickness=2)
                    cv2.imshow('bounce.skill_name', frame)
                else:
                    x1, x2, y1, y2 = track.bounding_square(int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), cx, cy, 120)
                    frameCropped = frame[y1:y2, x1:x2]
                    cv2.imshow('bounce.skill_name', frameCropped)

            if updateOne:
                updateOne = False

        k = cv2.waitKey(waitTime) & 0xff
        if k == ord('k'):  # play pause
            paused = not paused
        elif k == ord('j'):  # prev frame
            updateOne = True
            cap.set(cv2.CAP_PROP_POS_FRAMES, cap.get(cv2.CAP_PROP_POS_FRAMES) - 2)
        elif k == ord('l'):  # next frame
            updateOne = True
        elif k == ord('.'):  # speed up
            waitTime -= 5
            print(waitTime)
        elif k == ord(','):  # slow down
            waitTime += 5
            print(waitTime)
        elif k == ord('q') or k == 27:  # q/ESC
            print("Exiting...")
            exit()

        if cap.get(cv2.CAP_PROP_POS_FRAMES) == end_frame:
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            # break


def plot_data(routine):
    print("\nStarting plotting...")
    f, axarr = plt.subplots(4, sharex=True)

    # Plot bounce heights
    x_frames = [frame.frame_num / routine.video_fps for frame in routine.frames]
    y_travel = [frame.center_pt_x for frame in routine.frames]
    y_height = [frame.center_pt_y for frame in routine.frames]

    # List inside list gets flattened
    peaks_x = list(chain.from_iterable(
        (bounce.start_time, bounce.max_height_frame / routine.video_fps) for bounce in routine.bounces))
    peaks_x.append(routine.bounces[-1].end_time)
    peaks_y = list(chain.from_iterable((bounce.start_height, bounce.max_height) for bounce in routine.bounces))
    peaks_y.append(routine.bounces[-1].end_height)

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

    axarr[3].scatter(x_frames, y_major, color="g")
    axarr[3].scatter(x_frames, y_minor, color='b')
    axarr[3].set_ylim([0, 300])
    axarr[3].set_title("Ellipse Axes Length")
    axarr[3].set_ylabel('Length')
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
