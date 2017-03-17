import json

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


def judge_real_basic():
    # Started 22:54
    # Open the database and find all the straddle jumps
    db = sqlite3.connect(c.dbPath)
    db.row_factory = sqlite3.Row

    # Get all the routines with straddle jumps
    routines = db.execute("SELECT * FROM routines WHERE bounces LIKE '%Straddle%'")
    routines = routines.fetchall()  # copy everything pointed to by the cursor into an object.

    deductionCats = {
        "0.0": {"x": [], "y": []},
        "0.1": {"x": [], "y": []},
        "0.2": {"x": [], "y": []},
        "0.3": {"x": [], "y": []},
        "0.4": {"x": [], "y": []},
        "0.5": {"x": [], "y": []}
    }
    colors = ['r', 'g', 'b', 'cyan', 'magenta', 'yellow']

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    deductionColors = {
        "0.0": 'r',
        "0.1": 'g',
        "0.2": 'b',
        "0.3": 'cyan',
        "0.4": 'magenta',
        "0.5": 'yellow'
    }

    # For each one, get the frame no for midpoint, its major and minor ellipse axis at that frame, it's deduction
    for ri, routine in enumerate(routines):
        if ri == 3:
            continue
        deductionsQuery = db.execute("SELECT * FROM judgements WHERE routine_id=? ORDER BY id ASC LIMIT 1", (routine['id'],))
        deductionsQuery = deductionsQuery.fetchone()

        deductions = json.loads(deductionsQuery[2])
        bounces = json.loads(routine['bounces'])
        ellipses = json.loads(routine['ellipses'])

        for i, bounce in enumerate(bounces):
            if bounce['name'] == "Straddle Jump":
                startFrame = bounce['startFrame']
                endFrame = bounce['endFrame']
                # (frame, (cx, cy), (MA, ma), angle)
                ellipsePts = ellipses[startFrame: endFrame]
                cx = np.array([float(pt[1][0]) for pt in ellipsePts])
                cx /= cx[0] # normalise
                cy = np.array([float(pt[1][1]) for pt in ellipsePts])
                cy /= cy[0] # normalise
                z = range(len(ellipsePts))

                deduction = deductions[i]
                color = deductionColors[deduction]
                # deductionCats[deduction]["x"].append(major)
                # deductionCats[deduction]["y"].append(minor)

                ax.scatter(z, cx, cy, c=color)

        if ri == 5:
            break

    # print(deductionCats)
    # Plot

    # handles = []
    # for i, cat in enumerate(deductionCats):
    #     handles.append(mpatches.Patch(color=colors[i], label=cat))
    #     thisdict = deductionCats[cat]
    #     plt.scatter(thisdict['x'], thisdict['y'], color=colors[i], marker='o')
    # plt.legend(handles=handles)
    ax.set_ylabel('Horizontal Travel')
    ax.set_zlabel('Height')
    ax.set_xlabel('Time (Frames)')

    plt.show()
