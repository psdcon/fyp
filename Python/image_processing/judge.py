from __future__ import print_function

from operator import itemgetter

import numpy as np
from scipy import signal

import helpers.helper_funcs
from helpers.db_declarative import *
from image_processing import visualise


def judge_skill(db):
    # Get all straddle jumps, plot their sequences
    desiredSkill = 'Tuck Jump'
    reference = db.query(Reference).filter_by(name=desiredSkill).one()
    refBounce = reference.bounce
    refBounceAngles = np.array(json.loads(refBounce.angles))
    bounces = db.query(Bounce).filter(Bounce.skill_name == desiredSkill, Bounce.angles != None).all()

    labelsAndDistances = []
    weights = [0.3, 0.3, 0.5, 0.5, 1, 1, 1, 1, 0.3, 1, 1, 1, 1]
    numAngles = 13
    for bounce in bounces:
        # if bounce.id = referenceBounce.id:
        #     continue
        # Don't included bounces that ain't been judged
        deductionLabel = bounce.getDeduction()
        if not deductionLabel:
            continue

        thisBounceJointAngles = np.array(json.loads(bounce.angles))
        thisBounceFrameCount = len(thisBounceJointAngles[0])
        absDiff = 0
        sqErr = 0
        for i in range(numAngles):  # the number of different angles = 13
            weight = weights[i]
            thisJoint = thisBounceJointAngles[i]
            posedJoint = refBounceAngles[i]

            alignedPosedJoint = signal.resample(posedJoint, thisBounceFrameCount)
            distance = np.sum(np.absolute(np.subtract(thisJoint, alignedPosedJoint)))

            # distance, _path = fastdtw(thisJoint, posedJoint, dist=euclidean)
            distance *= weight
            absDiff += distance
            sqErr += distance ** 2

        mse = int(round(sqErr, 0)) / numAngles
        labelAndDistance = [deductionLabel, mse]
        labelsAndDistances.append(labelAndDistance)

    sortedLabelsAndDistances = sorted(labelsAndDistances, key=itemgetter(1))
    labelsAndDistances


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
