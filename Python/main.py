from __future__ import division
from __future__ import print_function

import json
from collections import OrderedDict

import cv2
import os

import h5py
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
import scipy.io
from scipy.spatial.distance import euclidean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from gui.showRoutineSelectDialog import show_selection_menu
from helpers import helper, consts
from helpers.db_declarative import *
from image_processing import visualise, track, trampoline, segment_bounces
from libs.fastdtw import fastdtw

# https://github.com/opencv/opencv/issues/6055
cv2.ocl.setUseOpenCL(False)


def import_pose(db, routine):
    # TODO this assumes there is a file with all poses for each frame in it
    # posePath = videoPath + routine['name'][:-4] + "/pose.npz"
    # poses = np.load(posePath)['poses']

    for frame in routine.frames:
        posePath = consts.videoPath + routine.path[:-4] + "/frame {}_pose.npz".format(frame.frame_num)
        try:
            pose = np.load(posePath)['pose']
        except IOError:
            continue
        frame.pose = json.dumps(pose.tolist())
    db.commit()


def import_pose_matlab(db, routine):
    mat = scipy.io.loadmat('preds_2d.mat')
    pose = mat['preds_2d']

    # Not all frames get data extracted so have to use i...
    for i, frame in enumerate(routine.frames):
        frame.pose_hg = json.dumps(pose[:, :, i].tolist())
    db.commit()


def crop_video(cap, routine, db):
    outPath = routine.path.replace('.mp4', '_cropped.avi')
    padding = 100  # padding (in pixels) from the center point

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(consts.videoPath+outPath, fourcc, 30.0, (padding*2, padding*2))

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


def save_cropped_frames(cap, routine, db):
    outDir = routine.path.replace('.mp4', '/')
    outPath = consts.videoPath+outDir
    padding = 110  # padding (in pixels) from the center point

    if not os.path.exists(outPath):
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
        cy = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) - frame_data.center_pt_y)
        x1, x2, y1, y2 = track.bounding_square(int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                                               int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), cx, cy, 120)
        frameCropped = frame[y1:y2, x1:x2]
        imgName = outPath+"frame_{0:04}.png".format(int(cap.get(cv2.CAP_PROP_POS_FRAMES)))
        print("Writing frame to {}".format(imgName))
        ret = cv2.imwrite(imgName, frameCropped)
        if not ret:
            print("Couldn't write image {}\nAbort!".format(imgName))
            exit()

        # Finish playing the video when we get to the end.
        if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
            break
    # Done


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
        pose_hg = np.array(json.loads(frame_data.pose_hg))  #np.array(hg_preds['{0:04}'.format(frame_data.frame_num)].value).T
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


def main():
    # engine = create_engine('sqlite:///'+consts.dbPath)
    engine = create_engine('sqlite:///db.sqlite3')
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    db = DBSession()

    ask = False
    # Ask the user to select routine from database
    routines = db.query(Routine).all()
    if ask:
        routinesAsDict = []
        for routine in routines:
            routinesAsDict.append(OrderedDict([
                ('id', str(routine.id)),
                ('path', routine.path),
                ('competition', routine.competition),
                ('level', routine.level),
                ('tracked', 'Yes' if routine.isTracked() else 'No'),
                ('note', routine.note)
            ]))

        selectedRoutineIndices = show_selection_menu(routinesAsDict)
    else:
        selectedRoutineIndices = [1]
    selectedRoutines = [routines[i] for i in selectedRoutineIndices]

    # Import pose
    # import_pose(db, selectedRoutines[0])
    # import_pose_matlab(db, selectedRoutines[0])
    # visualise_pose(selectedRoutines[0])

    # visualise.play_frames(db, selectedRoutines[0], 0, -1, show_pose=True)
    # visualise.play_frames(db, selectedRoutines[0], 0, -1, show_pose=False, show_full=False)
    # plot_skill_pose(db, selectedRoutines[0])
    save_cropped_frames(helper.open_video(selectedRoutines[0].path), selectedRoutines[0], db)
    # pose_error(selectedRoutines[0])
    exit()


    # Execute
    for i, routine in enumerate(selectedRoutines):
        # Open the video with some error handling
        cap = helper.open_video(routine.path)

        '''
        If the routine is not tracked:
            detect trampoline
            track
            find bounces
        Else is tracked, present with option to:
            detect trampoline
            track and save
            track without save
            find bounces
            plot
        '''
        if not routine.isTracked():
            # Detect Trampoline
            trampoline.detect_trampoline(db, cap, routine)

            # Track gymnast and save
            track.track_and_save(db, cap, routine)

            # Find bounces and save
            segment_bounces.segment_bounces_and_save(db, routine)

            # Plot
            visualise.plot_data(routine)

        else:
            # Show options loop
            options = [
                "Detect Trampoline",
                "Track and Save",
                "Track without Save",
                "Segment Bounces",
                "Plot",
                "Exit",
            ]
            while True:
                print("This routine has already been tracked. What would you like to do?")
                for ii, op in enumerate(options):
                    print('%d) %s' % (ii + 1, op))
                choiceInt = helper.read_num(len(options))
                choiceStr = options[choiceInt - 1]

                if choiceStr == "Detect Trampoline":
                    trampoline.detect_trampoline(db, cap, routine)
                elif choiceStr == "Track and Save":
                    track.track_and_save(db, cap, routine)
                elif choiceStr == "Track without Save":
                    track.track_gymnast(cap, routine)
                elif choiceStr == "Segment Bounces":
                    segment_bounces.segment_bounces_and_save(db, routine)
                elif choiceStr == "Plot":
                    visualise.plot_data(routine)
                elif choiceStr == "Exit":
                    break
                else:
                    print("No such choice")

        print("Finished routine {} of {}".format(i + 1, len(routines)))

    db.close()
    print("Done")


def judge_skill(db):
    # Get all straddle jumps, plot their sequences
    desiredSkill = 'Tuck Jump'
    straddles = db.query(Bounce).filter_by(skill_name=desiredSkill)
    plt.title(desiredSkill)
    skillRatios = []
    for i, skill in enumerate(straddles[0:7]):
        if i == 6:
            visualise.play_skill(db, skill.id)

        skillFrames = db.query(Frame).filter(Frame.routine_id == skill.routine_id, Frame.frame_num > skill.start_frame,
                                             Frame.frame_num < skill.end_frame)
        frame_nums = [f.frame_num for f in skillFrames]
        print("start", skill.start_frame, "end", skill.end_frame, "num frame", skill.end_frame - skill.start_frame,
              len(frame_nums), frame_nums)
        print(skill.deductions)

        ellipseLenRatios = [f.ellipse_len_major / f.ellipse_len_minor for f in skillFrames]
        skillRatios.append(ellipseLenRatios)

    distance, path = fastdtw(skillRatios[0], skillRatios[1], dist=euclidean)
    print(distance, path)
    for sk in skillRatios:
        plt.plot(signal.resample(sk, 43))
    plt.plot()

    plt.ylabel('Height (Pixels)')
    plt.show()


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
        num = a**2 + b**2 - c**2
        demon = (2.0 * a * b)
        ang = acos(num/demon)
        return degrees(ang)

    # Get a skill
    skill = routine.bounces[15]
    visualise.play_skill(db, skill.id, show_pose=True)

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
            angleVal = angle(pose_as_point(pose, part_idx[0]), pose_as_point(pose, part_idx[1]), pose_as_point(pose, part_idx[2]))
            angleValues[key].append(angleVal)

    # Plot angles
    f, axarr = plt.subplots(4, sharex=True)

    # use angleIndexKeys rahter than jointNames.keys() because order matters here
    for i, key in enumerate(consts.angleIndexKeys):
        plti = int(i/2)  # when i=0,1; plti = 0. when i=2,3; plti = 1. when i=4,5; plti = 2. when i=6,7; plti = 3
        axarr[plti].plot(range(len(poses)), angleValues[key], c=consts.jointAngleColors[i%2], label=key)
        axarr[plti].scatter(range(len(poses)), angleValues[key], c=consts.jointAngleColors[i%2])
        axarr[plti].legend(loc='best')
    plt.show()


def create_video():
    import re

    def atoi(text):
        return int(text) if text.isdigit() else text

    def natural_keys(text):
        '''
        alist.sort(key=natural_keys) sorts in human order
        http://nedbatchelder.com/blog/200712/human_sorting.html
        (See Toothy's implementation in the comments)
        '''
        return [atoi(c) for c in re.split('(\d+)', text)]

    cap = cv2.VideoCapture(0)
    mypath = 'C:/Users/psdco/Videos/Trainings/480p/0 day1 rout2 720x480/'
    videoFramesPaths = [mypath + f for f in listdir(mypath) if (isfile(join(mypath, f)) and '_vis' in f)]
    print(videoFramesPaths.sort(key=natural_keys))

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter('C:/Users/psdco/Videos/Trainings/480p/output.avi', fourcc, 30.0, (200, 200))

    for vfp in videoFramesPaths:
        frame = cv2.imread(vfp)
        out.write(frame)
        # cv2.imshow('frame', frame)
        # if cv2.waitKey(10) & 0xFF == ord('q'):
        #     break

    # Release everything if job is finished
    out.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
