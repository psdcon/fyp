# Import statements
import json
import os

import cv2
import h5py
import numpy as np
import scipy.io
from sqlalchemy.orm.exc import NoResultFound

import helpers.helper
from helpers import consts
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
    data_path = consts.videosRootPath + routine.path.replace('.mp4', os.sep)
    hg_preds_file = h5py.File(data_path + 'preds.h5', 'r')
    hg_preds = hg_preds_file.get('preds')

    # Not all frames get data extracted so have to use i...
    for i, frame in enumerate(routine.frames):
        pose = np.array(hg_preds['{0:04}'.format(frame.frame_num)].value).T
        frame.pose_hg = json.dumps(pose.tolist())
    db.commit()
    print("Imported rough hourglass pose")


# Imports into pose, because it's better.
def import_pose_hg_smooth(db, routine):
    data_path = consts.videosRootPath + routine.path.replace('.mp4', os.sep)
    mat_preds_file = scipy.io.loadmat(data_path + 'preds_2d.mat')
    mat_preds = mat_preds_file['preds_2d']

    # Not all frames get data extracted so have to use i...
    for i, frame in enumerate(routine.frames):
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


def save_cropped_frames(db, cap, routine):
    outPath = consts.videosRootPath + routine.path.replace('.mp4', os.sep)

    if not os.path.exists(outPath):
        print("Creating "+outPath)
        os.makedirs(outPath)

    while 1:
        _ret, frame = cap.read()
        try:
            frame_data = db.query(Frame).filter_by(routine_id=routine.id,
                                                   frame_num=cap.get(cv2.CAP_PROP_POS_FRAMES)).one()
        except NoResultFound:
            print("No frame data found for frame {}".format(cap.get(cv2.CAP_PROP_POS_FRAMES)))
            continue

        cx = frame_data.center_pt_x
        cy = frame_data.center_pt_y
        x1, x2, y1, y2 = helpers.helper.bounding_square(int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                                                        int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), cx, cy, routine.padding)
        frameCropped = frame[y1:y2, x1:x2]
        imgName = outPath + "frame_{0:04}.png".format(int(cap.get(cv2.CAP_PROP_POS_FRAMES)))
        # print("Writing frame to {}".format(imgName))
        ret = cv2.imwrite(imgName, frameCropped)
        if not ret:
            print("Couldn't write image {}\nAbort!".format(imgName))
            exit()

        # Finish playing the video when we get to the end.
        if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
            break
    # Done
    print("Done saving frames")
