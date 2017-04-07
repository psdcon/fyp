from __future__ import print_function

import re
from itertools import chain

import cv2
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from sqlalchemy.orm.exc import NoResultFound

from helpers import helper_funcs
from helpers.db_declarative import *
#
# Functions for playing videos
#
from image_processing import calc_angles


def _draw_pose_on_frame(pose, frame):
    for p_idx in range(16):
        color = consts.poseColors[calc_angles.pose_aliai['hourglass'][p_idx]][1]
        cv2.circle(frame, (int(pose[0, p_idx]), int(pose[1, p_idx])), 5, color, thickness=cv2.FILLED)
    return frame


def play_bounce(db, bounce_id, show_pose=True, show_full=False):
    bounce = db.query(Bounce).filter_by(id=bounce_id).one()
    routine = bounce.routine

    play_frames(db, routine, bounce.start_frame, bounce.end_frame, show_pose, show_full)


def play_frames(db, routine, start_frame=1, end_frame=-1, show_pose=True, show_full=False):
    waitTime = 40
    playOneFrame = False
    paused = False
    prevBounceName = ''

    cap = helper_funcs.open_video(routine.path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    if end_frame == -1:
        end_frame = cap.get(cv2.CAP_PROP_FRAME_COUNT)

    # f, axarr = plt.subplots(12, sharex=True)
    # f.canvas.set_window_title(routine.prettyName())

    while True:
        if playOneFrame or not paused:

            _ret, frame = cap.read()

            # Loop forever
            if cap.get(cv2.CAP_PROP_POS_FRAMES) >= end_frame:
                cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

            try:
                frame_data = db.query(Frame).filter_by(routine_id=routine.id, frame_num=cap.get(cv2.CAP_PROP_POS_FRAMES)).one()
            except NoResultFound:
                continue

            thisBounce = frame_data.bounce
            if thisBounce and prevBounceName != thisBounce.skill_name:
                # plot_frame_angles(thisBounce.skill_name, thisBounce.getFrames(db), axarr)
                prevBounceName = thisBounce.skill_name

            cx = frame_data.center_pt_x
            cy = frame_data.center_pt_y

            x1, x2, y1, y2 = helper_funcs.crop_points_constrained(routine.video_height, routine.video_width, cx, cy, routine.crop_length)

            if frame_data.pose is not None:
                pose = np.array(json.loads(frame_data.pose))
                # Show full frame
                if show_full:
                    cv2.putText(frame, '{}'.format(frame_data.frame_num), (10, 20), cv2.FONT_HERSHEY_SIMPLEX,
                                0.4, (255, 255, 255))
                    for p_idx in range(14):
                        pose_x = int((cx - routine.padding) + pose[0, p_idx])
                        pose_y = int((cy - routine.padding) + pose[1, p_idx])
                        color = consts.poseColors[calc_angles.pose_aliai['hourglass'][p_idx]][1]
                        cv2.circle(frame, (pose_x, pose_y), 5, color, thickness=cv2.FILLED)
                    cv2.imshow('HG Smooth', frame)

                # Show cropped
                else:
                    frameCropped = frame[y1:y2, x1:x2]
                    frameCropped = cv2.resize(frameCropped, (256, 256))
                    cv2.putText(frameCropped, '{}'.format(prevBounceName), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255))
                    cv2.putText(frameCropped, '{}'.format(frame_data.frame_num), (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255))
                    frameCropped = _draw_pose_on_frame(pose, frameCropped)
                    cv2.imshow(routine.prettyName(), frameCropped)

            else:
                # Ignore frames that haven't got pose info
                if show_pose:
                    continue

                cv2.circle(frame, (cx, cy), 3, (0, 0, 255), cv2.FILLED)
                if show_full:
                    cv2.imshow(routine.prettyName(), frame)
                else:
                    frameCropped = frame[y1:y2, x1:x2]
                    cv2.imshow(routine.prettyName(), frameCropped)

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
            playOneFrame = True
        elif k == ord('\n') or k == ord('\r'):  # return/enter key
            cv2.destroyAllWindows()
            break
        elif k == ord('q') or k == 27:  # q/ESC
            print("Exiting...")
            exit()

        elif k == ord('p'):
            thisBounce.shape = 'Pike'
            db.commit()
            print('Changed shape to Pike')
        elif k == ord('t'):
            thisBounce.shape = 'Tuck'
            db.commit()
            print('Changed shape to Tuck')
        elif k == ord('s'):
            thisBounce.shape = 'Straight'
            db.commit()
            print('Changed shape to Straight')


# For comparing the track of two skills. Ideally this would be n rather than 2
def play_frames_of_2_bounces(db, bounce1, bounce2):
    print("\nCreating angle comparison plot")
    # Create plot
    fig, axes = plt.subplots(nrows=6, ncols=2, sharex=True, sharey=True)

    b1Angles = np.array(json.loads(bounce1.angles))
    b1Angles = np.delete(b1Angles, 8, 0)  # delete "head" angle
    numFrames = len(b1Angles[0])

    # Prepare b2 angles
    b2Angles = json.loads(bounce2.angles)
    b2Angles = np.delete(b2Angles, 8, 0)  # delete "head" angle
    b2ResampAngles = np.array([signal.resample(ang, numFrames) for ang in b2Angles])

    # Get distances for label
    distances = [np.sum(np.absolute(np.subtract(ang1, ang2))) for ang1, ang2 in zip(b1Angles, b2ResampAngles)]

    b1Handle = _plot_angles_6x2(axes, b1Angles)
    b2Handle = _plot_angles_6x2(axes, b2ResampAngles)

    # Add labels
    labels = list(calc_angles.extended_angle_keys)  # make a copy
    labels.remove('Head')
    for ax, label, dist in zip(axes.flat, labels, distances):
        ax.set_ylim([0, 180])
        ax.yaxis.set_ticks([0, 30, 60, 90, 120, 150, 180])
        ax.set_title("{} ({:.0f})".format(label, dist))

    fig.suptitle("Angle Comparison (Total Error: {:.0f})".format(sum(distances)), fontsize=16)
    fig.legend((b1Handle, b2Handle), (bounce1.skill_name, bounce2.skill_name))
    fig.tight_layout()

    plt.show(block=False)

    #
    print("Starting video")
    play_frames_of_2(db, bounce1.routine, bounce2.routine,
                     bounce1.start_frame, bounce1.end_frame,
                     bounce2.start_frame, bounce2.end_frame)


def play_frames_of_2(db, routine1, routine2, start_frame1=1, end_frame1=-1, start_frame2=1, end_frame2=-1, show_full=False):
    waitTime = 80
    playOneFrame = False
    paused = False

    cap1 = helper_funcs.open_video(routine1.path)
    if end_frame1 == -1:
        end_frame1 = cap1.get(cv2.CAP_PROP_FRAME_COUNT)

    cap2 = helper_funcs.open_video(routine2.path)
    if end_frame2 == -1:
        end_frame2 = cap2.get(cv2.CAP_PROP_FRAME_COUNT)

    show_pose = True

    bothFrames = np.zeros(shape=(256, 256 * 2, 3), dtype=np.uint8)

    # Create a list of frames from each to be played
    frame_datas1 = db.query(Frame).filter(Frame.routine_id == routine1.id, Frame.frame_num >= start_frame1, Frame.frame_num < end_frame1, Frame.pose != None).all()
    frame_datas2 = db.query(Frame).filter(Frame.routine_id == routine2.id, Frame.frame_num >= start_frame2, Frame.frame_num < end_frame2, Frame.pose != None).all()
    frame_nums1 = [frame_data.frame_num for frame_data in frame_datas1]
    frame_nums2 = [frame_data.frame_num for frame_data in frame_datas2]
    num_frames1 = len(frame_datas1)
    num_frames2 = len(frame_datas2)
    frame_data1_ptr = 0
    frame_data2_ptr = 0

    cap1.set(cv2.CAP_PROP_POS_FRAMES, frame_nums1[0])
    cap2.set(cv2.CAP_PROP_POS_FRAMES, frame_nums2[0])
    _ret, frame1 = cap1.read()
    _ret, frame2 = cap2.read()

    while True:
        if playOneFrame or not paused:

            frame_data_ptr_video = [cap1.get(cv2.CAP_PROP_POS_FRAMES), cap2.get(cv2.CAP_PROP_POS_FRAMES)]
            frame_data1 = frame_datas1[frame_data1_ptr]
            frame_data2 = frame_datas2[frame_data2_ptr]

            cx1 = frame_data1.center_pt_x
            cy1 = frame_data1.center_pt_y

            cx2 = frame_data2.center_pt_x
            cy2 = frame_data2.center_pt_y

            if show_pose:
                # if pose is None, skip showing this frame
                try:
                    pose1 = np.array(json.loads(frame_data1.pose))
                    pose2 = np.array(json.loads(frame_data2.pose))
                except TypeError:
                    continue

                # Show full frame
                if show_full:
                    pass

                # Show cropped
                else:
                    x1, x2, y1, y2 = helper_funcs.crop_points_constrained(routine1.video_height, routine1.video_width, cx1, cy1, routine1.crop_length)
                    frameCropped1 = frame1[y1:y2, x1:x2]
                    frameCropped1 = cv2.resize(frameCropped1, (256, 256))

                    x1, x2, y1, y2 = helper_funcs.crop_points_constrained(routine2.video_height, routine2.video_width, cx2, cy2, routine2.crop_length)
                    frameCropped2 = frame2[y1:y2, x1:x2]
                    frameCropped2 = cv2.resize(frameCropped2, (256, 256))

                    frameCropped1 = _draw_pose_on_frame(pose1, frameCropped1)
                    bothFrames[0:256, 0:256] = frameCropped1
                    cv2.putText(bothFrames, '{}'.format(frame_nums1[frame_data1_ptr]), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255))

                    frameCropped2 = _draw_pose_on_frame(pose2, frameCropped2)
                    bothFrames[0:256, 256:512] = frameCropped2
                    cv2.putText(bothFrames, '{}'.format(frame_nums2[frame_data2_ptr]), (266, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255))

                    cv2.putText(bothFrames, '{}'.format(max(frame_data1_ptr, frame_data2_ptr)), (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255))
                    cv2.imshow('Pose', bothFrames)

            frame_data1_ptr += 1
            frame_data2_ptr += 1
            if playOneFrame:
                playOneFrame = False

        k = cv2.waitKey(waitTime) & 0xff
        if k == ord('k'):  # play pause
            paused = not paused
        elif k == ord('j'):  # prev frame
            playOneFrame = True
            frame_data1_ptr = helper_funcs.clip_wrap(frame_data1_ptr - 2, 0, num_frames1 - 1)
            frame_data2_ptr = helper_funcs.clip_wrap(frame_data2_ptr - 2, 0, num_frames2 - 1)
            cap1.set(cv2.CAP_PROP_POS_FRAMES, frame_nums1[frame_data1_ptr])
            cap2.set(cv2.CAP_PROP_POS_FRAMES, frame_nums2[frame_data2_ptr])
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

        # Loop forever, allowing shorter sequence to pause for longer sequence
        if frame_data1_ptr >= num_frames1 and frame_data2_ptr >= num_frames2:
            frame_data1_ptr = 0
            frame_data2_ptr = 0
            cap1.set(cv2.CAP_PROP_POS_FRAMES, frame_nums1[frame_data1_ptr])
            cap2.set(cv2.CAP_PROP_POS_FRAMES, frame_nums2[frame_data2_ptr])
        elif frame_data1_ptr >= num_frames1:
            frame_data1_ptr -= 1
        elif frame_data2_ptr >= num_frames2:
            frame_data2_ptr -= 1

        # Let video capture catch up
        if frame_data1_ptr <= num_frames1:
            while True:
                desiredFNum = frame_nums1[frame_data1_ptr]
                vidFNum = cap1.get(cv2.CAP_PROP_POS_FRAMES)
                if vidFNum < desiredFNum:
                    _ret, frame1 = cap1.read()
                elif vidFNum == desiredFNum:
                    break
                elif vidFNum > desiredFNum:  # if the video is further ahead than we want, force it back. This is slow...
                    cap1.set(cv2.CAP_PROP_POS_FRAMES, desiredFNum)

        if frame_data2_ptr <= num_frames2:
            while True:
                desiredFNum = frame_nums2[frame_data2_ptr]
                vidFNum = cap2.get(cv2.CAP_PROP_POS_FRAMES)
                if vidFNum < desiredFNum:
                    _ret, frame2 = cap2.read()
                elif vidFNum == desiredFNum:
                    break
                elif vidFNum > desiredFNum:  # if the video is further ahead than we want, force it back. This is slow...
                    cap2.set(cv2.CAP_PROP_POS_FRAMES, desiredFNum)


# Play matlab images like a video
def compare_pose_tracking_techniques(routine):
    # Get all folders that have __ suffixes.
    # Load all the smoothed_frame_xxx.png matlab pose files in these folders

    poseDirSuffixes = []
    imagesLists = []
    matPoses = []
    frameNumbers = set()
    for poseDirName in routine.getPoseDirPaths():
        # matFile = poseDirName + os.sep + "monocap_preds_2d.mat"
        # if os.path.exists(matFile):
        imageFiles = glob.glob(poseDirName + os.sep + "smoothed_pose_frame_*.png")
        if len(imageFiles) > 0:
            print('Found monocap images in ', poseDirName)

            poseDirSuffixes.append(os.path.basename(poseDirName.replace(routine.prettyName(), '_')))
            imagesLists.append(imageFiles)
            for f in imageFiles:
                m = re.search('smoothed_pose_frame_(\d+)\.png', f)
                frameNumbers.add(int(m.group(1)))

                # matPoses.append(scipy.io.loadmat(matFile)['preds_2d'])
        else:
            print('No MATLAB monocap files found ', poseDirName)

    # Set up pointers
    frameNumbers = list(frameNumbers)  # set() makes sure all unique frames get played.
    frameNumberPtr = 0
    imageListPtrs = [0 for _ in range(len(imagesLists))]

    # Do angles stuff
    # myPoses = [[] for _ in matPoses]
    # for imgFiles, matPose, myPose in zip(imagesLists, matPoses, myPoses):
    #     for i, _ in enumerate(imgFiles):
    #         myPose.append(matPose[:, :, i])
    # manyRoutineAngles = [visualise.gen_pose_angles(myPose, average=True) for myPose in myPoses]
    # visualise.compare_many_angles_plot(manyRoutineAngles, labels=poseDirSuffixes, block=False)

    techniqueCount = len(poseDirSuffixes)

    # "Video" control variables
    waitTime = 80
    playOneFrame = False
    paused = False
    scaleFactor = 0.5
    resizeWidth = int(1630 * scaleFactor)
    resizeHeight = int(400 * scaleFactor)

    frames = np.zeros(shape=(resizeHeight * techniqueCount, resizeWidth, 3), dtype=np.uint8)  # (h * 3, w, CV_8UC3);
    while 1:
        if playOneFrame or not paused:

            for techniqueIndex, imagesList, label in zip(range(techniqueCount), imagesLists, poseDirSuffixes):

                thisImageListsPtr = imageListPtrs[techniqueIndex]
                imageFilename = imagesList[thisImageListsPtr]

                currentFrameNumber = frameNumbers[frameNumberPtr]
                frameIndexKey = "{0:04}".format(currentFrameNumber)

                if frameIndexKey in imageFilename:  # if the number is in the file name string, it's an image for the current frame
                    # Show the img
                    frame = cv2.imread(imageFilename)
                    if frame is None:
                        frame = np.zeros((resizeHeight, resizeWidth, 3), np.uint8)
                    else:
                        height, width = frame.shape[:2]
                        frame = frame[65:height - 79, 210:width - 180]
                        frame = cv2.resize(frame, (resizeWidth, resizeHeight))
                    cv2.putText(frame, "{:4}".format(currentFrameNumber), (10, resizeHeight - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255))

                    # Increment the pointer
                    imageListPtrs[techniqueIndex] += 1
                else:
                    continue
                    # Black frame
                    # frame = np.zeros((resizeHeight, resizeWidth, 3), np.uint8)

                cv2.putText(frame, label, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255))
                frames[resizeHeight * techniqueIndex:resizeHeight * (techniqueIndex + 1), 0:resizeWidth] = frame

            cv2.imshow(routine.prettyName(), frames)
            frameNumberPtr += 1
            if playOneFrame:
                playOneFrame = False

        k = cv2.waitKey(waitTime) & 0xff
        if k == ord('k'):  # play pause
            paused = not paused
        elif k == ord('j'):  # prev frame
            frameNumberPtr = helper_funcs.clip_wrap(frameNumberPtr - 2, 0, len(frameNumbers) - 1)
            imageListPtrs = [helper_funcs.clip_wrap(imagesListPointer - 2, 0, len(imagesLists[i]) - 1) for i, imagesListPointer in enumerate(imageListPtrs)]
            playOneFrame = True
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

        if frameNumberPtr >= len(frameNumbers):
            frameNumberPtr = 0
            imageListPtrs = [0 for _ in range(len(imagesLists))]

    print("Finished comparing tracking techniques")
    return


#
# Matplotlib Plots for various datas.
#
def plot_height(routine):
    print("\nStarting plotting...")
    f, axarr = plt.subplots(4, sharex=True)

    # Plot bounce heights
    x_frames = [frame.frame_num / routine.video_fps for frame in routine.frames]
    y_travel = [frame.center_pt_x for frame in routine.frames]
    y_height = [routine.video_height - frame.center_pt_y for frame in routine.frames]

    # List inside list gets flattened
    peaks_x = list(chain.from_iterable((bounce.start_time, bounce.max_height_frame / routine.video_fps) for bounce in routine.bounces))
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


# Called by play_frames_of_2_bounces
def _plot_angles_6x2(axes, framesInEachAngle):
    # angles = []
    # xTicks = []
    # for frame in frames:
    #     if frame.angles:
    #         xTicks.append(frame.frame_num)
    #         angles.append(np.array(json.loads(frame.angles)))
    #         # else:
    #         #     angles.append(None)
    # anglesInEachFrame = np.array(angles)
    # framesInEachAngle = anglesInEachFrame.T

    """[
        "Right elbow",
        "Left elbow",
        "Right shoulder",
        "Left shoulder",
        "Right knee",
        "Left knee",
        "Right hip",
        "Left hip",
        "Head"
        "Right leg with horz",
        "Left leg with horz",
        "Torso with horz",
        "Twist Angle"
    ]"""

    numFrames = len(framesInEachAngle[0])
    handle = None

    # Plot angles
    for jointAngles, ax in zip(framesInEachAngle, axes.flat):
        handle, = ax.plot(range(numFrames), jointAngles)

    return handle


def plot_angles_1x6_save_image(bounce):
    imgName = "{path}{filename}_angles.jpg".format(path=consts.bouncesRootPath, filename=bounce.id)
    # if os.path.exists(imgName):
    #     print('File exists: {}'.format(imgName))
    #     return

    print("\nCreating angle comparison plot")
    # Create plot
    fig, axes = plt.subplots(nrows=1, ncols=6, sharex=True, sharey=True, figsize=(16, 2))

    framesInEachAngle = np.array(json.loads(bounce.angles))
    framesInEachAngle = framesInEachAngle[:, :30]
    framesInEachAngle = np.delete(framesInEachAngle, 8, 0)  # delete "head" angle
    numFrames = len(framesInEachAngle[0])
    xTicks = np.arange(numFrames)

    # indexOrders = [0, 6, 1, 7, 2, 8, 3, 9, 4, 10, 5, 11]
    # indexOrders = [0, 2, 4, 6, 8, 10, 1, 3, 5, 7, 9, 11]
    indexOrders = [0, 2, 4, 6, 8, 10]

    # Plot angles
    rHandle = None
    lHandle = None
    for i, ax in zip(indexOrders, axes.flat[:5]):
        jointAngles = framesInEachAngle[i]
        rHandle, = ax.plot(xTicks, jointAngles, label="Right")
        jointAngles = framesInEachAngle[i + 1]
        lHandle, = ax.plot(xTicks, jointAngles, label="Left")
    # add other 2
    torsoHandle, = axes[5].plot(xTicks, framesInEachAngle[10], c='purple', label="Torso with Vertical")
    twistHandle, = axes[5].plot(xTicks, framesInEachAngle[11], c='green', label="Twist Angle")

    # Place a legend to the right of this smaller subplot.
    plt.legend(handles=[rHandle, lHandle, torsoHandle, twistHandle], bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)

    # Add labels
    # labels = list(consts.extendedAngleIndexKeys)  # make a copy
    # labels.remove('Head')
    for label, ax in zip(calc_angles.labels, axes.flat):
        ax.set_title(label)

    axes[0].set_ylim([0, 180])
    # axes[0].set_xlim([0, 1])
    axes[0].yaxis.set_ticks([0, 45, 90, 135, 180])
    # axes[0].xaxis.set_ticks([.5, 1])
    # ax.xaxis.set_ticks([0, 60, 120, 180])
    # ax.yaxis.set_ticks([0, 30, 60, 90, 120, 150, 180])

    # axes[0].set_ylabel('Angle (deg)')
    # fig.text(0.5, 0.01, 'Time (s)', ha='center')

    # fig.suptitle("Angle Comparison (Total Error: {:.0f})".format(sum(distances)), fontsize=16)
    # fig.legend((b1Handle, b2Handle), (bounce1.skill_name, bounce2.skill_name))
    fig.tight_layout(pad=0)
    # fig.subplots_adjust(bottom=.2, right=0.82)  # make room for xlabel and legend
    fig.subplots_adjust(right=0.85)  # make room for legend

    print("Writing image to {}".format(imgName))
    plt.savefig(imgName)
    # plt.show()
    plt.close(fig)
    return

# def compare_many_angles_plot(manyRoutineAngles, labels, block=True):
#     # Plot angles
#     f, axarr = plt.subplots(len(manyRoutineAngles[0]), sharex=True)
#
#     # Get number of data points in each one for resampling.
#     # dataPointLens = [len(routineAngles.values()[0]) for routineAngles in manyRoutineAngles]
#     # sampleCount = min(dataPointLens)
#
#     # Loop through
#     error = [[label, 0] for label in labels]
#     for i, label, routineAngles in zip(range(len(manyRoutineAngles)), labels, manyRoutineAngles):
#         # use angleIndexKeys rather than jointNames.keys() because order matters here
#         # AngleIndexKeys are grouped in left right pairs. Want to add to average the two and add it to the plot
#         for plti, key in enumerate(routineAngles):
#             axarr[plti].set_title(key)
#
#             angles = routineAngles[key]
#             # angles = signal.resample(angles, sampleCount)
#             goodIndices = find_outlier_indices(angles, 50)
#             f = interpolate.interp1d(goodIndices, angles[goodIndices], kind='cubic')
#             newAngles = f(range(len(angles)))
#             # error[i][1] += sum(np.absolute(angles))
#
#             # all_idx = 1:length(x)
#             # outlier_idx = abs(x - median(x)) > 3 * std(x) | abs(y - median(y)) > 3 * std(y) # Find outlier idx
#             # x(outlier_idx) = interp1(all_idx(~outlier_idx), x(~outlier_idx), all_idx(outlier_idx))
#
#             axarr[plti].plot(range(len(angles)), newAngles, label=label)
#             axarr[plti].plot(range(len(angles)), angles, label=label, marker='o', linestyle="-")
#
#     print(error)
#     plt.legend(loc='best')
#     # plt.savefig('C:/Users/psdco/Pictures/Tucks/' + path.basename(routine.path)[:-4] + "_{}".format(frames[0].frame_num))
#     plt.show(block=block)
# def find_outlier_indices(arr, cutoff=40):
#     diff = np.diff(arr)
#     outliers = np.nonzero(diff < -cutoff)[0]
#     if len(outliers) == 0:
#         return range(len(arr))
#
#     if outliers[0] == 0:
#         outliers = outliers[1:]
#
#     tweenOutliers = []
#     for oli in outliers:
#         if oli in tweenOutliers:
#             continue
#         normalRef = arr[oli]
#         i = oli + 1
#         while 1:
#             thisDif = normalRef - arr[i]
#             if abs(thisDif) > cutoff:
#                 tweenOutliers.append(i)
#             else:  # found a point close to normal ref, go to next outlier
#                 break
#             i += 1
#             # Dont go off the end
#             if i == len(arr):
#                 tweenOutliers = tweenOutliers[:-1]
#                 break
#
#     goodIndices = [i for i in range(len(arr)) if i not in tweenOutliers]
#     return goodIndices
#
#     # for i in range(len(diff)):
#     #     pt1 = diff[i]
#     #     pt2 = diff[i+1]
#     #     if
#     #
#     # badPts = []
#     # outliers = False
#     # lastGoodVal = 0
#     # for i in range(1, len(arr)):
#     #     pt1 = arr[i-1]
#     #     pt2 = arr[i]
#     #     diff = pt2-pt2
#     #     if abs(diff) > cutoff:
#     #         outliers = True
#     #         lastGoodVal = pt1
#     #         badPts.append(i)
#
#
#     # from scipy import interpolate
#     # x = [a for a in range(len(angles)) if a not in np.nonzero(diff > 40)[0][1:]]
#     # # x = [x for x in x if x not in np.nonzero(np.diff(angles[x])>40)[0][1:]]
#     # y = angles[x]
#     # # x = range(len(angles))
#     # xnew = range(len(angles))
#     #
#     # f = interpolate.interp1d(x, y, kind='cubic')
#     #
#     # spl = interpolate.UnivariateSpline(x, y)
#     # # spl.set_smoothing_factor(200)
#     #
#     # b, a = signal.butter(3, 0.1)
#     # # b, a = signal.ellip(4, 0.01, 120, 0.091)
#     # yfilt = signal.filtfilt(b, a, angles, padlen=50)
#     #
#     # plt.figure()
#     # plt.plot(x, y, 'o', xnew, f(xnew), '-')
#     # plt.plot(xnew, spl(xnew), 'r')
#     # plt.plot(xnew, yfilt)
#     # plt.show()
#
#
# def is_outlier(points, thresh=3.5):
#     """
#     Returns a boolean array with True if points are outliers and False otherwise.
#
#     Parameters:
#     -----------
#         points : An numobservations by numdimensions array of observations
#         thresh : The modified z-score to use as a threshold. Observations with
#             a modified z-score (based on the median absolute deviation) greater
#             than this value will be classified as outliers.
#
#     Returns:
#     --------
#         mask : A numobservations-length boolean array.
#     """
#     if len(points.shape) == 1:
#         points = points[:, None]
#     median = np.median(points, axis=0)
#     diff = np.sum((points - median) ** 2, axis=-1)
#     diff = np.sqrt(diff)
#     med_abs_deviation = np.median(diff)
#
#     modified_z_score = 0.6745 * diff / med_abs_deviation
#
#     return modified_z_score > thresh
#
#
# def pose_error(routine):
#     # Original hg output
#     hg_preds_file = h5py.File('preds.h5', 'r')
#     hg_preds = hg_preds_file.get('preds')
#
#     # Smoothed monocap output
#     mat_preds_file = scipy.io.loadmat('preds.mat')
#     mat_preds = mat_preds_file['preds_2d']
#
#     x_mat = [[] for _ in range(16)]
#     x_hg = [[] for _ in range(16)]
#     y_mat = [[] for _ in range(16)]
#     y_hg = [[] for _ in range(16)]
#
#     for i, frame_data in enumerate(routine.frames):
#         pose_mat = mat_preds[:, :, i]
#         pose_hg = np.array(json.loads(frame_data.pose_hg))
#         # pose_hg = np.array(hg_preds['{0:04}'.format(frame_data.frame_num)].value).T
#         for p_idx in range(16):
#             x_mat[p_idx].append(int(pose_mat[0, p_idx]))
#             x_hg[p_idx].append(int(pose_hg[0, p_idx]))
#             y_mat[p_idx].append(int(pose_mat[1, p_idx]))
#             y_hg[p_idx].append(int(pose_hg[1, p_idx]))
#
#     plt.figure(1)
#     for i in range(16):
#         diff = np.diff([x_mat[i], x_hg[i]], axis=0)
#         plt.plot(diff[0])
#
#     plt.figure(2)
#     for i in range(16):
#         diff = np.diff([y_mat[i], y_hg[i]], axis=0)
#         plt.plot(diff[0])
#     plt.show()
