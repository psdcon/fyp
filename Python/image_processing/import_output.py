# Import statements
import json
import os

import cv2
import h5py
import numpy as np
import scipy
import scipy.io

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
            frame_data.pose = helper_funcs.roundListFloatsIntoStr(pose.tolist(), 1)
            frame_data.angles = helper_funcs.roundListFloatsIntoStr(helper_funcs.pose2OrderedAngles(pose), 1)
        except KeyError:
            continue
    db.commit()

    for bounce in routine.bounces:
        angles = [json.loads(frame.angles, parse_float=lambda x: round(float(x), 1)) for frame in bounce.frames]
        anglesPerFrameAsBounceAngles = zip(*angles)
        # TODO Make sure this doesn't add quotes to the db entry
        bounce.angles = json.dumps(anglesPerFrameAsBounceAngles)

    print("Pose Imported")
    return


# Outputs
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
        hullLens = [frame_data.hull_max_length for frame_data in frames]
        # plt.plot(hullLens, label="Hull Length", color="blue")

        scaler = 1.2
        cropLength = int(np.percentile(hullLens, 95) * scaler)
        routine.crop_length = cropLength
        db.commit()

        # # plt.axhline(np.average(hullLens), label="Average Length", color="blue")
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
