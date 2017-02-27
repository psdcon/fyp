# Import statements
import json

import cv2
import h5py
import matplotlib.pyplot as plt
import numpy as np
import scipy.io
from sqlalchemy.orm.exc import NoResultFound

from helpers import helper_funcs
from helpers.db_declarative import *


def import_pose_deepcut(db, routine):
    # TODO this assumes there is a file with all poses for each frame in it
    # posePath = videoPath + routine['name'][:-4] + "/pose.npz"
    # poses = np.load(posePath)['poses']
    for frame in routine.frames:
        posePath = consts.videosRootPath + routine.path[:-4] + "/frame {}_pose.npz".format(frame.frame_num)
        try:
            pose = np.load(posePath)['pose']
        except IOError:
            continue
        frame.pose = json.dumps(pose.tolist())
    db.commit()
    print("Imported rough deepcut pose")


# Import raw hourglass pose from
def import_pose_hg(db, routine):
    hg_preds_file = h5py.File(routine.getAsDirPath() + 'preds.h5', 'r')
    hg_preds = hg_preds_file.get('preds')

    # Not all frames get data extracted so have to use i...
    for i, frame in enumerate(routine.frames):
        pose = np.array(hg_preds['{0:04}'.format(frame.frame_num)].value).T
        frame.pose_hg = json.dumps(pose.tolist())
    db.commit()
    print("Imported rough hourglass pose")


# Imports into pose, because it's better.
def import_pose_hg_smooth(db, routine, frames):
    mat_preds_file = scipy.io.loadmat(routine.getAsDirPath() + 'preds_2d.mat')
    mat_preds = mat_preds_file['preds_2d']

    # Not all frames get data extracted so have to use i...
    for i, frame in enumerate(frames):
        frame.pose = json.dumps(mat_preds[:, :, i].tolist())
    db.commit()
    print("Imported smooth hourglass pose")


# Outputs
# Not used because it didn't work with hg
def save_cropped_video(cap, routine, db):
    outPath = routine.path.replace('.mp4', '_cropped.avi')
    padding = 100  # padding (in pixels) from the center point

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(consts.videosRootPath + outPath, fourcc, 30.0, (padding * 2, padding * 2))

    while 1:
        _ret, frame = cap.read()
        try:
            frame_data = db.query(Frame).filter_by(routine_id=routine.id,
                                                   frame_num=cap.get(cv2.CAP_PROP_POS_FRAMES)).one()
        except NoResultFound:
            print("No frame data found for frame {}".format(cap.get(cv2.CAP_PROP_POS_FRAMES)))
            continue

        cx = frame_data.center_pt_x
        cy = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) - frame_data.center_pt_y)

        frameCropped = frame[cy - padding:cy + padding, cx - padding:cx + padding]  # [y1:y2, x1:x2]
        out.write(frameCropped)
        # cv2.imshow('frame', frame)
        # if cv2.waitKey(10) & 0xFF == ord('q'):
        #     break
        # Finish playing the video when we get to the end.
        if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
            break

    # Release everything if job is finished
    out.release()
    cv2.destroyAllWindows()


def save_cropped_frames(db, routine, frames):
    # TODO suggest a reasonable padding width based on ellipse axes.
    # Discard outliers. Anything above 140*2. Then take the median or average?
    # Discard the top 10 % and the bottom 20%. Then take the average of this + margin of 20 Save this to the db.
    # HG would give better predictions with a fixed with but scalling based on each frame becomes tedious to keep track of. TODO Does it??
    # Hoping that monocap takes care of smoothing?
    routineDirPath = routine.getAsDirPath()
    # import glob
    # nFiles = len(glob.glob(routineDirPath + 'frame_*'))
    # if nFiles > 0:
    #     print("Found {} frames in {!r}. Stopping".format(nFiles, routineDirPath))
    #     return

    plt.figure()
    position = np.array([routine.video_height - frame_data.center_pt_y for frame_data in frames])
    # scaleWithPerson = frames[0].hull_max_length is not None
    scaleWithPerson = False
    stretchPositionMinima = False
    cropLengths = []
    cropLength = 0
    if scaleWithPerson:  # hull length
        # Compensate... something
        cropLengths = np.array([frame_data.hull_max_length for frame_data in frames])

        cropLengths[np.nonzero(position < np.median(position))] = int(np.average(cropLengths) * 1.1)
        plt.plot(cropLengths, label="Hull Length", color="blue")
        # plt.axhline(np.average(cropLengths), label="Average Length", color="blue")
        # plt.axhline(np.median(cropLengths), label="Med Length", color="purple")
    else:  # Ellipse lengths
        hullLens = [frame_data.hull_max_length for frame_data in frames]
        plt.plot(hullLens, label="Hull Length", color="blue")

        scaler = 1.2
        # cropLength = int(np.average(hullLens)*averageScaler)
        cropLength = int(np.percentile(hullLens, 95) * scaler)
        # Average should be trusted more because median can be skewed by poor ellipse fitting
        # plt.axhline(np.average(hullLens), label="Average Length", color="blue")
        plt.axhline(cropLength, label="Percentile", color="blue")
        plt.axhline(routine.crop_length, label="routine.crop_length", color="orange")
        # plt.axhline(np.median(hullLens), label="Med Length", color="purple")

    if stretchPositionMinima:
        # Get cutoff for where scaling below this point should occur
        scalingCutoff = np.median(position) * 0.8
        # Create line that returns scaling values from 1 to 0.75 from the cutoff to the global minimum
        coefficients = np.polyfit([scalingCutoff, position.min()], [1, 0.75], 1)
        scalingLine = np.poly1d(coefficients)  # create np polynomial object

        if False:
            x_axis = np.linspace(position.min(), scalingCutoff, 10)
            y_axis = scalingLine(x_axis)

            # ...and plot the points and the line
            plt.plot(x_axis, y_axis)
            plt.show()
            exit()

        # Get index for each position that falls below the cutoff
        indices = np.nonzero(position < scalingCutoff)
        newPositions = position.copy()
        for i in indices:
            # Evaluate the scaling line at each x to return the ammount to scale by (1 to 0.75). Multiply existing value by this scalar
            newPositions[i] = position[i] * scalingLine(position[i])

        plt.plot(newPositions, label="New position", color="red")
        # plt.axhline(scalingCutoff, label="Position Scaling Start", color="blue")
        # plt.axhline(position.min(), label="Position Scaling End", color="green")

    plt.plot(position, label="Position", color="green")

    # plt.axhline(np.average(position), label="Average Position", color="green")
    # plt.axhline(np.median(position), label="Med Position", color="red")
    plt.xlabel("Time (s)")
    plt.legend(loc="best")
    plt.show(block=False)

    trampolineTouches = np.array([frame.trampoline_touch for frame in routine.frames])
    touchTransitions = np.diff(trampolineTouches)
    for i in range(len(touchTransitions)):
        thisTransition = touchTransitions[i]
        if thisTransition > 0:  # spike up
            trampolineTouches[i + 1] = 0
            trampolineTouches[i + 2] = 0
        elif thisTransition < 0:  # spike down
            trampolineTouches[i] = 0
            trampolineTouches[i - 1] = 0

    cap = helper_funcs.open_video(routine.path)
    for i, frame_data in enumerate(frames):
        # ignore frames where trampoline is touched
        # if frame_data.frame_num in blacklistedFrames:
        if trampolineTouches[i] == 1:
            continue
        # ignore any frame that aren't tracked
        while frame_data.frame_num != cap.get(cv2.CAP_PROP_POS_FRAMES):
            _ret, frame = cap.read()

        cx = frame_data.center_pt_x
        if stretchPositionMinima:
            cy = routine.video_height - newPositions[i]
        else:
            cy = frame_data.center_pt_y

        if cropLengths != []:  # otherwise the ellipse len will be used
            cropLength = cropLengths[i]

        x1, x2, y1, y2 = helper_funcs.crop_points_constrained(routine.video_height, routine.video_width, cx, cy, cropLength)

        frameCropped = frame[y1:y2, x1:x2]
        cropScaled = cv2.resize(frameCropped, (256, 256))

        cv2.imshow('Track ', cropScaled)
        k = cv2.waitKey(50) & 0xff

        imgName = routineDirPath + "frame_{0:04}.png".format(frame_data.frame_num)
        # print("Writing frame to {}".format(imgName))
        # cv2.imwrite(imgName, cropScaled)

    # Done
    cap.release()
    db.commit()
    print("Done saving frames")
