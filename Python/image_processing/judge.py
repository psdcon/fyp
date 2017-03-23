from __future__ import print_function

import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from scipy.spatial.distance import euclidean

import helpers.helper_funcs
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
    plt.show(block=False)


def judge(db):
    # Get all straddle jumps, plot their sequences
    desiredSkill = 'Tuck Jump'
    skills = db.query(Bounce).filter_by(skill_name=desiredSkill)

    idealFrames = skills[5].getFrames(db)
    poses = []
    for frame in idealFrames:
        poses.append(json.loads(frame.pose))
    idealTuckAngles = helpers.helper_funcs.gen_pose_angles(np.array(poses), average=True)

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
            theseAngles = helpers.helper_funcs.gen_pose_angles(np.array(poses), average=True)
            visualise.compare_many_angles_plot([idealTuckAngles, theseAngles], ['Ideal', 'Moe'], block=False)
            visualise.play_frames_of_2(db, skills[5].routine, skill.routine, skills[5].start_frame + 5, skills[5].end_frame - 5, skill.start_frame + 5, skill.end_frame - 5)
