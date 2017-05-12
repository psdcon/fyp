# Import statements
import json
import os

import h5py
import numpy as np
import scipy
import scipy.io

from helpers import helper_funcs
# <legacy> ###############################################
# Imports preds.h5 HourGlass Lua/Torch pose
# Knows about frame number.
from image_processing import calc_angles


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


# </legacy> ###############################################


def import_monocap_preds_2d(db, routine):
    # Select which pose to import, if there are many
    poseDirNames = [os.path.basename(poseDir) for poseDir in routine.getPoseDirPaths()]
    poseDirSuffixes = [poseDirName.replace(routine.prettyName(), '') for poseDirName in poseDirNames]
    poseDirHasMonocap = [routine.hasMonocapImgs(poseDirSuffix) for poseDirSuffix in poseDirSuffixes]

    if not any(poseDirHasMonocap):
        print('No MATLAB images found for routine ' + routine.getAsDirPath())
        return

    if len(poseDirNames) > 1:
        choiceIndex = helper_funcs.select_list_option(poseDirNames + ['Quit'])
        if choiceIndex == len(poseDirNames):  # Option was Quit
            return
        suffix = poseDirSuffixes[choiceIndex]
    else:
        suffix = poseDirSuffixes[0]

    # Load chosen tracking technique
    preds_file = h5py.File(routine.getAsDirPath(suffix) + 'monocap_preds_2d.h5', 'r')
    preds = preds_file.get('monocap_preds_2d')

    frames = []
    poses = []
    maxShoulderWidth = 0
    pjls = calc_angles.pose_aliai['hourglass']  # poseJointLabels
    for frame in routine.frames:
        frameNumKey = '{0:04}'.format(frame.frame_num)
        try:
            pose = preds[frameNumKey].value.T
        except KeyError:
            continue
        frame.pose = helper_funcs.round_list_floats_into_str(pose.tolist(), 1)
        poses.append(pose)
        frames.append(frame)

        # Get the distances between the shoulders
        lspt = calc_angles.pose_2_pt(pose, pjls.index('lshoulder'))
        rspt = calc_angles.pose_2_pt(pose, pjls.index('rshoulder'))
        shoulderWidth = np.linalg.norm(lspt - rspt)
        if shoulderWidth > maxShoulderWidth:
            maxShoulderWidth = shoulderWidth
    db.flush()

    # Calculate all the angles
    framesAngles = calc_angles.angles_from_poses(poses, maxShoulderWidth, False)
    # Add the angles to db
    for frame, angles in zip(frames, zip(*framesAngles)):
        frame.angles = helper_funcs.round_list_floats_into_str(angles, 1)
    db.flush()

    # Update bounces with their angles
    for bounce in routine.bounces:
        anglesInEachFrame = [json.loads(frame.angles) for frame in bounce.frames if frame.angles is not None]
        if not anglesInEachFrame:
            continue
        framesInEachAngle = zip(*anglesInEachFrame)  # * = transpose. > list = 13*frame_numbers

        bounce.angles = json.dumps(framesInEachAngle)
        bounce.angles_count = len(framesInEachAngle[0])

    routine.has_pose = 1

    db.commit()

    print("Pose Imported")
    return


# Written to allow comparision of pose before an d after filtering.
# Does it make much difference... the moment of truth... :/
def import_pose_unfiltered(db, routine):
    suffix = "_blur_dark_0.6"
    preds_file = h5py.File(routine.getAsDirPath(suffix) + 'hg_preds_2d.h5', 'r')
    preds = preds_file.get('hg_preds_2d')

    frames = []
    poses = []
    maxShoulderWidth = 0
    pjls = calc_angles.pose_aliai['hourglass']  # poseJointLabels
    for frame in routine.frames:
        frameNumKey = '{0:04}'.format(frame.frame_num)
        try:
            pose = preds[frameNumKey].value.T
        except KeyError:
            continue
        frame.pose_unfiltered = helper_funcs.round_list_floats_into_str(pose.tolist(), 1)

        poses.append(pose)
        frames.append(frame)

        # Get the distances between the shoulders
        lspt = calc_angles.pose_2_pt(pose, pjls.index('lshoulder'))
        rspt = calc_angles.pose_2_pt(pose, pjls.index('rshoulder'))
        shoulderWidth = np.linalg.norm(lspt - rspt)
        if shoulderWidth > maxShoulderWidth:
            maxShoulderWidth = shoulderWidth
    db.flush()

    # Calculate all the angles
    framesAngles = calc_angles.angles_from_poses(poses, maxShoulderWidth, False)
    # Add the angles to db
    for frame, angles in zip(frames, zip(*framesAngles)):
        frame.angles_unfiltered = helper_funcs.round_list_floats_into_str(angles, 1)
    db.flush()

    # Update bounces with their angles
    for bounce in routine.bounces:
        anglesInEachFrame = [json.loads(frame.angles_unfiltered) for frame in bounce.frames if frame.angles_unfiltered is not None]
        if not anglesInEachFrame:
            continue
        framesInEachAngle = zip(*anglesInEachFrame)  # * = transpose. > list = 13*frame_numbers

        bounce.angles_unfiltered = json.dumps(framesInEachAngle)
        # bounce.angles_count = len(framesInEachAngle[0])

    # routine.has_pose = 1

    db.commit()

    print("Imported rough hourglass pose")
