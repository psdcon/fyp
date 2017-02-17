from __future__ import print_function
from __future__ import print_function
from math import acos, degrees
from scipy import interpolate

from scipy.spatial import distance
import json
from itertools import chain
from os import path

import cv2
import h5py
import matplotlib.pyplot as plt
import scipy.io
from scipy import signal
from sqlalchemy.orm.exc import NoResultFound

from helpers import consts
from helpers import helper_funcs
from helpers.db_declarative import *


def play_skill(db, bounce_id, show_pose=None, show_full=False):
    bounce = db.query(Bounce).filter_by(id=bounce_id).one()
    routine = bounce.routine

    play_frames(db, routine, bounce.start_frame, bounce.end_frame, show_pose, show_full)


def play_frames(db, routine, start_frame=1, end_frame=-1, show_pose=None, show_full=False):
    waitTime = 40
    playOneFrame = False
    paused = False

    cap = helper_funcs.open_video(routine.path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    if end_frame == -1:
        end_frame = cap.get(cv2.CAP_PROP_FRAME_COUNT)

    firstFrame = db.query(Frame).filter_by(routine_id=routine.id, frame_num=start_frame).one()
    # firstFrameId = firstFrame.id
    if show_pose is None:  # if not deliberately set to ellipse, then gracefully fallback to pose if available or ellipse if not
        show_pose = False if firstFrame.pose is None else True  # if pose is none, show ellipse

    while True:
        if playOneFrame or not paused:

            _ret, frame = cap.read()

            try:
                frame_data = db.query(Frame).filter_by(routine_id=routine.id, frame_num=cap.get(cv2.CAP_PROP_POS_FRAMES)).one()
            except NoResultFound:
                continue

            cx = frame_data.center_pt_x
            cy = frame_data.center_pt_y
            # Graceful degredation
            if frame_data.crop_length:
                cropLength = frame_data.crop_length
            elif routine.crop_length:
                cropLength = routine.crop_length
            else:
                cropLength = 256

            x1, x2, y1, y2 = helper_funcs.crop_points_constrained(routine.video_height, routine.video_width, cx, cy, cropLength)

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
                        cv2.circle(frame, (pose_x, pose_y), 5, color, thickness=cv2.FILLED)
                    cv2.imshow('HG Smooth', frame)

                # Show cropped
                else:
                    frameCropped = frame[y1:y2, x1:x2]
                    # frameCropped = cv2.resize(frameCropped, (256, 256))
                    cv2.putText(frameCropped, '{}'.format(frame_data.frame_num), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255))
                    # frameCroppedCopy = np.copy(frameCropped)
                    for p_idx in range(16):
                        color = consts.poseColors[consts.poseAliai['hourglass'][p_idx]][1]
                        cv2.circle(frameCropped, (int(pose[0, p_idx]), int(pose[1, p_idx])), 5, color, thickness=cv2.FILLED)
                    cv2.imshow('HG Smooth', frameCropped)

                    # for p_idx in range(16):
                    #     color = consts.poseColors[consts.poseAliai['hourglass'][p_idx]][1]
                    #     cv2.circle(frameCroppedCopy, (int(pose_rough[0, p_idx]), int(pose_rough[1, p_idx])), 5, color, thickness=cv2.FILLED)  # -ve thickness = filled
                    # cv2.imshow('HG Rough', frameCroppedCopy)

            else:
                cv2.circle(frame, (cx, cy), 3, (0, 0, 255), cv2.FILLED)
                ellipse = ((cx, cy), (frame_data.ellipse_len_major, frame_data.ellipse_len_minor), frame_data.ellipse_angle)
                cv2.ellipse(frame, ellipse, color=(0, 255, 0), thickness=2)
                if show_full:
                    # (x, y), (MA, ma), angle
                    # ellipse = ((cx, cy), (float(frame_data.ellipse_len_major), float(frame_data.ellipse_len_minor)), frame_data.ellipse_angle)
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
        elif k >= ord('0') and k <= ord('9'):
            num = k - ord('0')
            frameToJumpTo = (cap.get(cv2.CAP_PROP_FRAME_COUNT) / 10) * num
            cap.set(cv2.CAP_PROP_POS_FRAMES, frameToJumpTo)
            updateOne = True
        elif k == ord('\n') or k == ord('\r'):  # return/enter key
            break
        elif k == ord('q') or k == 27:  # q/ESC
            print("Exiting...")
            exit()

        # Loop forever
        if cap.get(cv2.CAP_PROP_POS_FRAMES) == end_frame:
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            # break


def play_frames_of_2(db, routine1, routine2, start_frame1=1, end_frame1=-1, start_frame2=1, end_frame2=-1, show_full=False):
    waitTime = 40
    playOneFrame = False
    paused = False

    cap1 = helper_funcs.open_video(routine1.path)
    cap1.set(cv2.CAP_PROP_POS_FRAMES, start_frame1)
    if end_frame1 == -1:
        end_frame1 = cap1.get(cv2.CAP_PROP_FRAME_COUNT)
    # TODO
    # frameIndexes = [f.frame_num for f in fr]

    cap2 = helper_funcs.open_video(routine2.path)
    cap2.set(cv2.CAP_PROP_POS_FRAMES, start_frame2)
    if end_frame2 == -1:
        end_frame2 = cap2.get(cv2.CAP_PROP_FRAME_COUNT)

    firstFrame = db.query(Frame).filter_by(routine_id=routine1.id, frame_num=start_frame1).one()
    show_pose = False if firstFrame.pose is None else True  # if pose is none, show ellipse

    bothFrames = np.zeros(shape=(256, 256 * 2, 3), dtype=np.uint8)

    while True:
        if playOneFrame or not paused:

            _ret, frame1 = cap1.read()
            _ret, frame2 = cap2.read()

            try:
                frame_data1 = db.query(Frame).filter_by(routine_id=routine1.id, frame_num=cap1.get(cv2.CAP_PROP_POS_FRAMES)).one()
                frame_data2 = db.query(Frame).filter_by(routine_id=routine2.id, frame_num=cap2.get(cv2.CAP_PROP_POS_FRAMES)).one()
            except NoResultFound:
                continue

            cx1 = frame_data1.center_pt_x
            cy1 = frame_data1.center_pt_y
            if frame_data1.crop_length:
                cropLength1 = frame_data1.crop_length
            elif routine1.crop_length:
                cropLength1 = routine1.crop_length
            else:
                cropLength1 = 256

            cx2 = frame_data2.center_pt_x
            cy2 = frame_data2.center_pt_y
            if frame_data2.crop_length:
                cropLength2 = frame_data2.crop_length
            elif routine2.crop_length:
                cropLength2 = routine2.crop_length
            else:
                cropLength2 = 256

            if show_pose:
                pose1 = np.array(json.loads(frame_data1.pose))
                pose2 = np.array(json.loads(frame_data2.pose))

                # Show full frame
                if show_full:
                    pass
                    # cv2.putText(frame1, '{}'.format(frame_data.frame_num), (10, 20), cv2.FONT_HERSHEY_SIMPLEX,
                    #             0.4, (255, 255, 255))
                    # for p_idx in range(14):
                    #     pose_x = int((cx - routine.padding) + pose[0, p_idx])
                    #     pose_y = int((cy - routine.padding) + pose[1, p_idx])
                    #     color = consts.poseColors[consts.poseAliai['hourglass'][p_idx]][1]
                    #     cv2.circle(frame1, (pose_x, pose_y), 5, color, thickness=cv2.FILLED)
                    # cv2.imshow('HG Smooth', frame1)

                # Show cropped
                else:
                    x1, x2, y1, y2 = helper_funcs.crop_points_constrained(routine1.video_height, routine1.video_width, cx1, cy1, cropLength1)
                    frameCropped1 = frame1[y1:y2, x1:x2]
                    x1, x2, y1, y2 = helper_funcs.crop_points_constrained(routine2.video_height, routine2.video_width, cx2, cy2, cropLength2)
                    frameCropped2 = frame2[y1:y2, x1:x2]

                    for p_idx in range(16):
                        color = consts.poseColors[consts.poseAliai['hourglass'][p_idx]][1]
                        cv2.circle(frameCropped1, (int(pose1[0, p_idx]), int(pose1[1, p_idx])), 5, color, thickness=cv2.FILLED)
                    bothFrames[0:256, 0:256] = cv2.resize(frameCropped1, (256, 256))

                    for p_idx in range(16):
                        color = consts.poseColors[consts.poseAliai['hourglass'][p_idx]][1]
                        cv2.circle(frameCropped2, (int(pose2[0, p_idx]), int(pose2[1, p_idx])), 5, color, thickness=cv2.FILLED)
                    frameCropped2 = cv2.resize(frameCropped2, (256, 256))
                    bothFrames[0:256, 256:512] = cv2.resize(frameCropped2, (256, 256))

                    cv2.putText(bothFrames, '{}'.format(frame_data1.frame_num-start_frame1), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255))
                    cv2.imshow('Pose', bothFrames)

            else:
                pass
                # cv2.circle(frame1, (cx, cy), 3, (0, 0, 255), cv2.FILLED)
                # ellipse = ((cx, cy), (frame_data.ellipse_len_major, frame_data.ellipse_len_minor), frame_data.ellipse_angle)
                # cv2.ellipse(frame1, ellipse, color=(0, 255, 0), thickness=2)
                # if show_full:
                #     # (x, y), (MA, ma), angle
                #     # ellipse = ((cx, cy), (float(frame_data.ellipse_len_major), float(frame_data.ellipse_len_minor)), frame_data.ellipse_angle)
                #     cv2.imshow('bounce.skill_name', frame1)
                # else:
                #     frameCropped = frame1[y1:y2, x1:x2]
                #     cv2.imshow('bounce.skill_name', frameCropped)

            if playOneFrame:
                playOneFrame = False

        k = cv2.waitKey(waitTime) & 0xff
        if k == ord('k'):  # play pause
            paused = not paused
        elif k == ord('j'):  # prev frame
            playOneFrame = True
            cap1.set(cv2.CAP_PROP_POS_FRAMES, cap1.get(cv2.CAP_PROP_POS_FRAMES) - 2)
            cap2.set(cv2.CAP_PROP_POS_FRAMES, cap2.get(cv2.CAP_PROP_POS_FRAMES) - 2)
        elif k == ord('l'):  # next frame
            playOneFrame = True
        elif k == ord('.'):  # speed up
            waitTime -= 5
            print(waitTime)
        elif k == ord(','):  # slow down
            waitTime += 5
            print(waitTime)
        elif k == ord('\n') or k == ord('\r'):  # return/enter key
            break
        elif k == ord('q') or k == 27:  # q/ESC
            print("Exiting...")
            exit()

        # Loop forever
        if cap1.get(cv2.CAP_PROP_POS_FRAMES) == end_frame1 or cap2.get(cv2.CAP_PROP_POS_FRAMES) == end_frame2:
            cap1.set(cv2.CAP_PROP_POS_FRAMES, start_frame1)
            cap2.set(cv2.CAP_PROP_POS_FRAMES, start_frame2)


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

    axarr[3].plot(x_frames, y_major / y_minor, color="g")
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


def gen_pose_angles(poses, average=False):
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

    def calc_angle(A, B, C):
        a = distance.euclidean(C, B)
        b = distance.euclidean(A, C)
        c = distance.euclidean(A, B)
        num = a ** 2 + b ** 2 - c ** 2
        demon = (2.0 * a * b)
        ang = acos(num / demon)
        return degrees(ang)

    # Make a list for each of the joints to be plotted
    # jointNames = consts.getAngleIndices('deepcut')
    jointNames = consts.getAngleIndices('hourglass')
    jointAngles = {key: [] for key in jointNames.keys()}

    for pose in poses:
        # pose = rel_pose_to_abs_pose(np.array(json.loads(frame.pose)), frame.center_pt_x, routine.video_height - frame.center_pt_y)
        # pose = np.array(json.loads(frame.pose))
        # pose = np.array(json.loads(frame.pose_hg))

        # Calculate an angle for each joint
        # Add to the dict for that joint
        for key in jointNames.keys():
            # Get the 3 pose points that make up this joint
            joint_pose_pts_idxs = jointNames[key]
            # Calculate the angle between them
            angle = calc_angle(pose_as_point(pose, joint_pose_pts_idxs[0]), pose_as_point(pose, joint_pose_pts_idxs[1]), pose_as_point(pose, joint_pose_pts_idxs[2]))
            # Append it to the appropriate dict
            jointAngles[key].append(angle)

    if not average:
        return jointAngles
    else:
        averagedJointAngles = {}
        for i in range(0, len(consts.angleIndexKeys), 2):  # step from 0 to 8 in increments of 2
            rightKey = consts.angleIndexKeys[i]
            leftKey = consts.angleIndexKeys[i+1]
            jointName = rightKey.split(' ')[1].title()  # take the last word and set it to title case
            averagedJointAngles[jointName] = np.average([jointAngles[rightKey], jointAngles[leftKey]], axis=0)
        return averagedJointAngles


# def plot_frame_angles(db, routine, frames=None):
#     if frames is None:
#         frames = routine.frames
#
#     angleValues = gen_frame_angles(frames)
#     count = len(angleValues.values()[0])
#
#     # Plot angles
#     f, axarr = plt.subplots(4, sharex=True)
#
#     # use angleIndexKeys rather than jointNames.keys() because order matters here
#     for i, key in enumerate(consts.angleIndexKeys):
#         plti = int(i / 2)  # when i=0,1; plti = 0. when i=2,3; plti = 1. when i=4,5; plti = 2. when i=6,7; plti = 3
#         axarr[plti].plot(range(count), angleValues[key], c=consts.jointAngleColors[i % 2], label=key)
#         axarr[plti].scatter(range(count), angleValues[key], c=consts.jointAngleColors[i % 2])
#         if i % 2 == 0:
#             axarr[plti].set_title(key.split(' ')[1].title())
#             nextKey = consts.angleIndexKeys[i + 1]
#             axarr[plti].plot(range(count), np.average([angleValues[key], angleValues[nextKey]], axis=0), c='yellow')
#             # axarr[plti].legend(loc='best')
#     plt.savefig('C:/Users/psdco/Pictures/Tucks/' + path.basename(routine.path)[:-4] + "_{}".format(frames[0].frame_num))
#     plt.show()


def compare_many_angles_plot(manyRoutineAngles, labels, block=True):
    # Plot angles
    f, axarr = plt.subplots(len(manyRoutineAngles[0]), sharex=True)

    # Get number of data points in each one for resampling.
    # dataPointLens = [len(routineAngles.values()[0]) for routineAngles in manyRoutineAngles]
    # sampleCount = min(dataPointLens)

    # Loop through
    error = [[label, 0] for label in labels]
    for i, label, routineAngles in zip(range(len(manyRoutineAngles)), labels, manyRoutineAngles):
        # use angleIndexKeys rather than jointNames.keys() because order matters here
        # AngleIndexKeys are grouped in left right pairs. Want to add to average the two and add it to the plot
        for plti, key in enumerate(routineAngles):
            axarr[plti].set_title(key)

            angles = routineAngles[key]
            # angles = signal.resample(angles, sampleCount)
            goodIndices = find_outlier_indices(angles, 50)
            f = interpolate.interp1d(goodIndices, angles[goodIndices], kind='cubic')
            newAngles = f(range(len(angles)))
            # error[i][1] += sum(np.absolute(angles))

            # all_idx = 1:length(x)
            # outlier_idx = abs(x - median(x)) > 3 * std(x) | abs(y - median(y)) > 3 * std(y) # Find outlier idx
            # x(outlier_idx) = interp1(all_idx(~outlier_idx), x(~outlier_idx), all_idx(outlier_idx))

            axarr[plti].plot(range(len(angles)), newAngles, label=label)
            axarr[plti].plot(range(len(angles)), angles, label=label, marker='o', linestyle="-")

    print(error)
    plt.legend(loc='best')
    # plt.savefig('C:/Users/psdco/Pictures/Tucks/' + path.basename(routine.path)[:-4] + "_{}".format(frames[0].frame_num))
    plt.show(block=block)


def find_outlier_indices(arr, cutoff=40):
    diff = np.diff(arr)
    outliers = np.nonzero(diff < -cutoff)[0]
    if len(outliers) == 0:
        return range(len(arr))

    if outliers[0] == 0:
        outliers = outliers[1:]

    tweenOutliers = []
    for oli in outliers:
        if oli in tweenOutliers:
            continue
        normalRef = arr[oli]
        i = oli+1
        while 1:
            thisDif = normalRef - arr[i]
            if abs(thisDif) > cutoff:
                tweenOutliers.append(i)
            else:  # found a point close to normal ref, go to next outlier
                break
            i += 1
            # Dont go off the end
            if i == len(arr):
                tweenOutliers = tweenOutliers[:-1]
                break

    goodIndices = [i for i in range(len(arr)) if i not in tweenOutliers]
    return goodIndices

    # for i in range(len(diff)):
    #     pt1 = diff[i]
    #     pt2 = diff[i+1]
    #     if
    #
    # badPts = []
    # outliers = False
    # lastGoodVal = 0
    # for i in range(1, len(arr)):
    #     pt1 = arr[i-1]
    #     pt2 = arr[i]
    #     diff = pt2-pt2
    #     if abs(diff) > cutoff:
    #         outliers = True
    #         lastGoodVal = pt1
    #         badPts.append(i)


    # from scipy import interpolate
    # x = [a for a in range(len(angles)) if a not in np.nonzero(diff > 40)[0][1:]]
    # # x = [x for x in x if x not in np.nonzero(np.diff(angles[x])>40)[0][1:]]
    # y = angles[x]
    # # x = range(len(angles))
    # xnew = range(len(angles))
    #
    # f = interpolate.interp1d(x, y, kind='cubic')
    #
    # spl = interpolate.UnivariateSpline(x, y)
    # # spl.set_smoothing_factor(200)
    #
    # b, a = signal.butter(3, 0.1)
    # # b, a = signal.ellip(4, 0.01, 120, 0.091)
    # yfilt = signal.filtfilt(b, a, angles, padlen=50)
    #
    # plt.figure()
    # plt.plot(x, y, 'o', xnew, f(xnew), '-')
    # plt.plot(xnew, spl(xnew), 'r')
    # plt.plot(xnew, yfilt)
    # plt.show()

def is_outlier(points, thresh=3.5):
    """
    Returns a boolean array with True if points are outliers and False otherwise.

    Parameters:
    -----------
        points : An numobservations by numdimensions array of observations
        thresh : The modified z-score to use as a threshold. Observations with
            a modified z-score (based on the median absolute deviation) greater
            than this value will be classified as outliers.

    Returns:
    --------
        mask : A numobservations-length boolean array.
    """
    if len(points.shape) == 1:
        points = points[:,None]
    median = np.median(points, axis=0)
    diff = np.sum((points - median)**2, axis=-1)
    diff = np.sqrt(diff)
    med_abs_deviation = np.median(diff)

    modified_z_score = 0.6745 * diff / med_abs_deviation

    return modified_z_score > thresh

def pose_error(routine):
    # Original hg output
    hg_preds_file = h5py.File('preds.h5', 'r')
    hg_preds = hg_preds_file.get('preds')

    # Smoothed monocap output
    mat_preds_file = scipy.io.loadmat('preds.mat')
    mat_preds = mat_preds_file['preds_2d']

    x_mat = [[] for _ in range(16)]
    x_hg = [[] for _ in range(16)]
    y_mat = [[] for _ in range(16)]
    y_hg = [[] for _ in range(16)]

    for i, frame_data in enumerate(routine.frames):
        pose_mat = mat_preds[:, :, i]
        pose_hg = np.array(json.loads(frame_data.pose_hg))
        # pose_hg = np.array(hg_preds['{0:04}'.format(frame_data.frame_num)].value).T
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
