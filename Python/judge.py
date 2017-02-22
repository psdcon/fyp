import json

import cv2
import matplotlib.pyplot as plt
import scipy
from scipy import signal
import os
from scipy.spatial.distance import euclidean

from helpers import consts
from helpers.db_declarative import *
from image_processing import visualise
from libs.fastdtw import fastdtw


def judge_skill(db):
    # Get all straddle jumps, plot their sequences
    desiredSkill = 'Tuck Jump'
    skills = db.query(Bounce).filter_by(skill_name=desiredSkill)
    plt.title(desiredSkill)
    skillRatios = []
    for i, skill in enumerate(skills[:]):
        visualise.play_skill(db, skill.id)

        skillFrames = db.query(Frame).filter(Frame.routine_id == skill.routine_id, Frame.frame_num > skill.start_frame, Frame.frame_num < skill.end_frame)
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
    plt.show(block=false)


def judge(db):
    # Get all straddle jumps, plot their sequences
    desiredSkill = 'Tuck Jump'
    skills = db.query(Bounce).filter_by(skill_name=desiredSkill)

    idealFrames = skills[5].getFrames(db)
    poses = []
    for frame in idealFrames:
        poses.append(json.loads(frame.pose))
    idealTuckAngles = visualise.gen_pose_angles(np.array(poses), average=True)

    for i, skill in enumerate(skills[:10]):

        skillFrames = skill.getFrames(db)
        # visualise.play_skill(db, skill.id)
        if False and skillFrames[0].pose is None:
            pass
            # routine.crop_length =
            # import_output.save_cropped_frames(db, skill.routine, skillFrames)
            # import_pose_hg_smooth(db, skill.routine, skillFrames)
        else:
            print(skill.deductions)
            # plot_frame_angles(db, skill.routine, skillFrames)
            poses = []
            for frame in skillFrames:
                poses.append(json.loads(frame.pose))
            theseAngles = visualise.gen_pose_angles(np.array(poses), average=True)
            visualise.compare_many_angles_plot([idealTuckAngles, theseAngles], ['Ideal', 'Moe'], block=False)
            visualise.play_frames_of_2(db, skills[5].routine, skill.routine, skills[5].start_frame+5, skills[5].end_frame-5, skill.start_frame+5, skill.end_frame-5)


def compare_pose_tracking(routine):
    # Get all folders that have __ affixes.
    # Load all the smoothed matlab pose files in these folders
    # Get the angles and plot them
    # Then show all the frames with next frame prev frame.
    import glob

    poseDirs = glob.glob(consts.videosRootPath + routine.path[:-4] + '*')
    matFiles = []
    for pDir in list(poseDirs):  # copy list because otherwise it gets updated under our feet
        matFile = pDir+os.sep+"preds_2d.mat"
        if os.path.exists(matFile):
            print('Found', matFile)
            matFiles.append(matFile)
        else:
            print('No file', pDir)
            poseDirs.remove(pDir)
    dirLabels = [pDir.replace(consts.videosRootPath + routine.path[:-4] + '', 'rout') for pDir in poseDirs]
    imgFileses = [glob.glob(pDir+os.sep+"smoothed_pose_frame_*.png") for pDir in poseDirs]
    matPoses = [scipy.io.loadmat(matFile)['preds_2d'] for matFile in matFiles]
    myPoses = [[] for _ in matPoses]
    for imgFiles, matPose, myPose in zip(imgFileses, matPoses, myPoses):
        for i, _ in enumerate(imgFiles):
            myPose.append(matPose[:, :, i])
    # manyRoutineAngles = [visualise.gen_pose_angles(myPose, average=True) for myPose in myPoses]
    # visualise.compare_many_angles_plot(manyRoutineAngles, labels=dirLabels, block=False)

    i = 0
    numFrames = len(imgFileses[0])
    waitTime = 80
    playOneFrame = False
    paused = False
    resizeWidth = int(1630*0.3)
    resizeHeight = int(400*0.3)
    frames = np.zeros(shape=(resizeHeight*len(dirLabels), resizeWidth, 3), dtype=np.uint8)  # (h * 3, w, CV_8UC3);
    while 1:
        if playOneFrame or not paused:
            for imgi, label, imgFiles in zip(range(len(dirLabels)), dirLabels, imgFileses):
                if not imgFiles:
                    frame = np.zeros((resizeHeight, resizeWidth, 3), np.uint8)
                else:
                    frame = cv2.imread(imgFiles[i])
                    if frame is None:
                        frame = np.zeros((resizeHeight, resizeWidth, 3), np.uint8)
                    else:
                        height, width = frame.shape[:2]
                        frame = frame[65:height-79, 210:width-180]
                        frame = cv2.resize(frame, (resizeWidth, resizeHeight))
                cv2.putText(frame, label, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255))
                frames[resizeHeight*imgi:resizeHeight*(imgi+1), 0:resizeWidth] = frame
            cv2.imshow("Frames", frames)
            i += 1
            if playOneFrame:
                playOneFrame = False

        k = cv2.waitKey(waitTime) & 0xff
        if k == ord('k'):  # play pause
            paused = not paused
        elif k == ord('j'):  # prev frame
            i -= 2
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

        if i == numFrames:
            i = 0


    print("wait")


