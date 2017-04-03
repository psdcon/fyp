# Import statements
import json
import os

import cv2
import h5py
import numpy as np
import scipy
import scipy.io

from helpers import consts
from helpers import helper_funcs
from image_processing import track


# <legacy> ###############################################
# Imports preds.h5 HourGlass Lua/Torch pose
# Knows about frame number.
def import_pose_hg(db, routine):
    hg_preds_file = h5py.File(routine.getAsDirPath(create=True) + 'preds.h5', 'r')
    hg_preds = hg_preds_file.get('preds')

    # Not all frames get data extracted so have to use i...
    for i, frame in enumerate(routine.frames):
        pose = np.array(hg_preds['{0:04}'.format(frame.frame_num)].value).T
        frame.pose_hg = json.dumps(pose.tolist())
    db.commit()
    print("Imported rough hourglass pose")


# Imports preds_2d.mat matlab smoothed pose
# Has no concept of frame number in the .mat
def import_pose_hg_smooth(db, routine, frames):
    mat_preds_file = scipy.io.loadmat(routine.getAsDirPath(create=True) + 'preds_2d.mat')
    mat_preds = mat_preds_file['preds_2d']

    # Not all frames get data extracted so have to use i...
    for i, frame in enumerate(frames):
        frame.pose = json.dumps(mat_preds[:, :, i].tolist())
    db.commit()
    print("Imported smooth hourglass pose")


# <!legacy> ###############################################


def import_monocap_preds_2d(db, routine):
    # Select which pose to import, if there are many
    poseDirNames = [os.path.basename(poseDir) for poseDir in routine.getPoseDirPaths()]
    poseDirSuffixes = [poseDirName.replace(routine.prettyName(), '') for poseDirName in poseDirNames]
    poseDirHasMonocap = [routine.hasMonocapImgs(poseDirSuffix) for poseDirSuffix in poseDirSuffixes]

    if not any(poseDirHasMonocap):
        print('No MATLAB images found for routine ' + routine.getAsDirPath())
        return

    if len(poseDirNames) > 1:
        choiceIndex = helper_funcs.selectListOption(poseDirNames + ['Quit'])
        if choiceIndex == len(poseDirNames):  # Option was Quit
            return
        suffix = poseDirSuffixes[choiceIndex]
    else:
        suffix = poseDirSuffixes[0]

    # Load chosen tracking technique
    preds_file = h5py.File(routine.getAsDirPath(suffix) + 'monocap_preds_2d.h5', 'r')
    preds = preds_file.get('monocap_preds_2d')

    for frame_data in routine.frames:
        frameNumKey = '{0:04}'.format(frame_data.frame_num)
        try:
            pose = preds[frameNumKey].value.T
        except KeyError:
            continue
        frame_data.pose = helper_funcs.roundListFloatsIntoStr(pose.tolist(), 1)
        angles = helper_funcs.pose2OrderedAngles(pose)
        frame_data.angles = helper_funcs.roundListFloatsIntoStr(angles, 1)
    db.commit()

    for bounce in routine.bounces:
        anglesInEachFrame = [json.loads(frame.angles) for frame in bounce.frames if frame.angles is not None]
        if not anglesInEachFrame:
            continue
        framesInEachAngle = zip(*anglesInEachFrame)  # * = transpose

        # TODO Make sure this doesn't add quotes to the db entry
        bounce.angles = json.dumps(framesInEachAngle)
        bounce.angles_count = len(framesInEachAngle[0])
    db.commit()

    shoulder_width_to_angle(db, routine)

    print("Pose Imported")
    return


#
# Outputs
#
def save_cropped_frames(db, routine, frames, suffix=None):
    routineDirPath = routine.getAsDirPath(suffix, create=True)

    # plt.figure()
    position = np.array([routine.video_height - frame_data.center_pt_y for frame_data in frames])
    scaleWithPerson = False
    # scaleWithPerson = frames[0].hull_max_length is not None
    cropLengths = []
    cropLength = 0
    if scaleWithPerson:  # hull length
        # Compensate... something
        cropLengths = np.array([frame_data.hull_max_length for frame_data in frames])

        cropLengths[np.nonzero(position < np.median(position))] = int(np.average(cropLengths) * 1.1)
        # plt.plot(cropLengths, label="Hull Length", color="blue")
        # # plt.axhline(np.average(cropLengths), label="Average Length", color="blue")
        # # plt.axhline(np.median(cropLengths), label="Med Length", color="purple")
    else:  # Ellipse lengths
        hullLengths = [frame_data.hull_max_length for frame_data in frames]
        # plt.plot(hullLengths, label="Hull Length", color="blue")

        cropLength = helper_funcs.getCropLength(hullLengths) + 10
        routine.crop_length = cropLength
        db.commit()

        # # plt.axhline(np.average(hullLengths), label="Average Length", color="blue")
        # plt.axhline(cropLength, label="Percentile", color="blue")
        # plt.axhline(routine.crop_length, label="routine.crop_length", color="orange")

    # plt.plot(position, label="Position", color="green")
    # plt.xlabel("Time (s)")
    # plt.legend(loc="best")
    # plt.show(block=False)

    trampolineTouches = np.array([frame.trampoline_touch for frame in routine.frames])
    trampolineTouches = helper_funcs.trimTouches(trampolineTouches)

    personMasks = helper_funcs.load_zipped_pickle(routine.personMasksPath())

    cap = helper_funcs.open_video(routine.path)
    frame = []
    for i, frame_data in enumerate(frames):
        # ignore frames where trampoline is touched
        if trampolineTouches[i] == 1:
            continue
        # ignore any frame that aren't tracked
        while frame_data.frame_num != cap.get(cv2.CAP_PROP_POS_FRAMES):
            ret, frame = cap.read()
            if not ret:
                print('Something went wrong')
                return

        cx = frame_data.center_pt_x
        cy = frame_data.center_pt_y
        # Use original background or darken
        if True:
            frameCropped = track.highlightPerson(frame, np.array(json.loads(personMasks[frame_data.frame_num]), dtype=np.uint8), cx, cy, cropLength)
        else:
            x1, x2, y1, y2 = helper_funcs.crop_points_constrained(routine.video_height, routine.video_width, cx, cy, cropLength)
            frameCropped = frame[y1:y2, x1:x2]
        frameCropped = cv2.resize(frameCropped, (256, 256))

        # cv2.imshow('Track ', frameCropped)
        # k = cv2.waitKey(50) & 0xff

        imgName = routineDirPath + "frame_{0:04}.png".format(frame_data.frame_num)
        # print("Writing frame to {}".format(imgName))
        cv2.imwrite(imgName, frameCropped)

    # Done
    cap.release()
    db.commit()
    print("Done saving frames")


def shoulder_width_to_angle(db, routine):
    # Check that this routine doesn't already have the new angle
    for bounce in routine.bounces:
        if bounce.angles:
            angles = json.loads(bounce.angles)
            if len(angles) == 13:
                print("Already has new angle: ", routine)
                return

    # poseJointLabels
    pjls = consts.poseAliai['hourglass']
    lsi = pjls.index('lshoulder')
    rsi = pjls.index('rshoulder')

    # Get the routines poses
    poses = []
    for frame in routine.frames:
        if frame.pose:
            poses.append(np.array(json.loads(frame.pose)))
        else:
            poses.append(None)

    # Get the distances between the shoulders
    shoulderWidths = []
    for pose in poses:
        if pose is not None:
            lspt = np.array((pose[0, lsi], pose[1, lsi]))
            rspt = np.array((pose[0, rsi], pose[1, rsi]))
            shoulderWidth = np.linalg.norm(lspt - rspt)
            shoulderWidths.append(shoulderWidth)
        else:
            shoulderWidths.append(None)

    # Normalise and scale the distances in to an angle
    maxShoulderWidth = max(shoulderWidths)
    twistAngles = []
    for sw in shoulderWidths:
        if sw is not None:
            twistAngle = (sw / maxShoulderWidth) * 180
            twistAngles.append(twistAngle)
        else:
            twistAngles.append(None)

    # Plot x,y and shoulder angle and print bounces
    # f, axarr = plt.subplots(1, sharex=True)
    #
    # # Plot bounce heights
    # x_frames = [frame.frame_num / routine.video_fps for frame in routine.frames]
    # y_height = [routine.video_height - frame.center_pt_y for frame in routine.frames]
    #
    # # List inside list gets flattened
    # peaks_x = list(chain.from_iterable((bounce.start_time, bounce.max_height_frame / routine.video_fps) for bounce in routine.bounces))
    # peaks_x.append(routine.bounces[-1].end_time)
    # peaks_y = list(chain.from_iterable((bounce.start_height, bounce.max_height) for bounce in routine.bounces))
    # peaks_y.append(routine.bounces[-1].end_height)
    #
    # axarr.set_title("Height")
    # axarr.plot(x_frames, y_height, color="g")
    # # axarr.plot(peaks_x, peaks_y, 'r+')
    # axarr.set_ylabel('Height (Pixels)')
    #
    # axarr.set_title("Twist Angle")
    # axarr.plot(x_frames, twistAngles, color="g")
    # axarr.set_ylabel('Angle (deg)')
    #
    # labels = [bounce.skill_name for bounce in routine.bounces[:-1]]
    # labels_x = [bounce.start_time for bounce in routine.bounces[:-1]]
    # plt.xticks(labels_x, labels, rotation='vertical')
    # for x in labels_x:
    #     plt.axvline(x)
    # # Pad margins so that markers don't get clipped by the axes
    # plt.margins(0.2)
    # # Tweak spacing to prevent clipping of tick-labels
    # plt.subplots_adjust(bottom=0.15)
    #
    # print(routine.bounces)
    # plt.show()

    # Append the new angle to the existing angles
    for twistAngle, frame in zip(twistAngles, routine.frames):
        if frame.angles:
            angles = json.loads(frame.angles)
            angles.append(twistAngle)
            newangles = helper_funcs.roundListFloatsIntoStr(angles, 1)
            frame.angles = newangles

    db.flush()

    # Update the bounces entry of angles
    for bounce in routine.bounces:
        anglesInEachFrame = [json.loads(frame.angles) for frame in bounce.frames if frame.angles is not None]
        if not anglesInEachFrame:
            continue
        framesInEachAngle = zip(*anglesInEachFrame)  # * = transpose

        # TODO Make sure this doesn't add quotes to the db entry
        bounce.angles = json.dumps(framesInEachAngle)
        bounce.angles_count = len(framesInEachAngle[0])

    db.commit()

    return
