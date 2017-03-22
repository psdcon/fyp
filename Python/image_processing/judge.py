from __future__ import print_function

from operator import itemgetter

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


def tariff(db, thisRoutine):
    import time

    def getPosedBounces(db, thisRoutine):
        # Get all bounces that have pose in this level
        posedBounces = db.query(Bounce).filter(
            Bounce.angles != None,
            Bounce.routine_id != thisRoutine.id
        ).all()

        for bounce in posedBounces:
            bounce.jointAngles = np.array(json.loads(bounce.angles))

        return posedBounces

    def getNumAvailable():
        numAvailableToFind = 0
        for posedBounce in posedBounces:
            if posedBounce.skill_name == thisBounce.skill_name:
                numAvailableToFind += 1
        return numAvailableToFind

    def compareAngles(thisAnglesAsCoords, posedAnglesAsCoords, cutoff):
        thisBounceFrameCount = len(thisAnglesAsCoords[0])
        tariffedBounce = {}
        totalDistance = 0
        saveBounceMatch = True
        for i in range(12):  # the number of different angles = 12
            thisJoint = thisAnglesAsCoords[i]
            posedJoint = posedAnglesAsCoords[i]

            alignedPosedJoint = signal.resample(posedJoint, thisBounceFrameCount)
            distance = np.sum(np.absolute(np.subtract(thisJoint, alignedPosedJoint)))

            # distance, _path = fastdtw(thisJoint, posedJoint, dist=euclidean)
            totalDistance += distance
            # Don't bother with skills that're way off
            if totalDistance > cutoff:
                saveBounceMatch = False
                break

        # Only store as a match if we didn't exit early
        if saveBounceMatch:
            tariffedBounce['totalDistance'] = totalDistance
            tariffedBounce['bounce'] = posedBounce
            return tariffedBounce
        else:
            return None

    start_time = time.time()

    # Setup
    print('Setting up for tariff...')
    posedBounces = getPosedBounces(db, thisRoutine)
    # Set up angles with the right dimensions.
    # for posedBounce in posedBounces:
    #     posedBounce.anglesAsCoords = posedBounce.getAnglesAsCoords(db)
    posedBounces[:] = [posedBounce for posedBounce in posedBounces if posedBounce.skill_name != 'In/Out Bounce']
    posedBounces[:] = [posedBounce for posedBounce in posedBounces if posedBounce.skill_name != 'Landing']
    timeTaken = time.time() - start_time
    print("Took {:.2f}s = {:.2f}m to coordinate bounces.".format(timeTaken, timeTaken / 60))

    #
    # Start processing this routine
    print('Found {} bounces with pose'.format(len(posedBounces)))
    print('\n----------------------')
    print('Tariffing ' + thisRoutine.__repr__())

    # Get angles per tariffedBounce in this routine
    tariffedBounces = []  # List matches for each bounce
    actualTariff = 0.0
    for thisBounce in thisRoutine.bounces:
        if thisBounce.skill_name == 'In/Out Bounce' or thisBounce.skill_name == 'Landing':
            continue

        # Check that this bounce has angles. May have been skipped by pose estimator
        # thisBounce.anglesAsCoords = thisBounce.getAnglesAsCoords(db)
        if thisBounce.angles is None:
            continue
        thisBounce.jointAngles = np.array(json.loads(thisBounce.angles))

        # Add up actual tariff
        actualTariff += thisBounce.getTariff(db)

        # Start looking
        print("")
        print('Looking for {}. There are {} of these in the posedBounces.'.format(thisBounce, getNumAvailable()))
        skill_start_time = time.time()

        #
        # Compare the angles of this bounce to every other bounce's angles
        cutoff = 30000
        bounceMatches = [compareAngles(thisBounce.jointAngles, posedBounce.jointAngles, cutoff) for posedBounce in posedBounces]
        bounceMatches[:] = [bm for bm in bounceMatches if bm is not None]  # remove None results
        bounceMatches = sorted(bounceMatches, key=itemgetter('totalDistance'))

        print(bounceMatches)
        timeTaken = time.time() - skill_start_time
        print("Took {:.2f}s = {:.2f}m to find this skill. ".format(timeTaken, timeTaken / 60))
        print("Found {} matches with error below {}.".format(len(bounceMatches), cutoff))

        tariffedBounces.append({
            'bounceToMatch': thisBounce,
            'timeTaken': timeTaken,
            'matches': bounceMatches,
        })

    timeTaken = time.time() - start_time
    print("---")
    print("Took {:.2f}s = {:.2f}m to estimate all skills".format(timeTaken, timeTaken / 60))

    # helper_funcs.save_pickle(tariffedBounces, thisRoutine.tariffPath())
    # tariffedBounces = helper_funcs.load_pickle(thisRoutine.tariffPath())
    # return

    foundCorrectlyCount = 0
    foundInFirst2Count = 0
    ignoreStraddlePikeCount = 0
    estimatedTariff = 0.0
    straddlePike = ['Straddle Jump', 'Pike Jump']
    for tariffedBounce in tariffedBounces:
        thisSkillName = tariffedBounce['bounceToMatch'].skill_name
        matches = tariffedBounce['matches']
        if not matches:
            continue
        matchedSkillName = matches[0]['bounce'].skill_name

        estimatedTariff += matches[0]['bounce'].getTariff(db)

        if thisSkillName == matchedSkillName:
            # If the move has a shape, then they should match
            if tariffedBounce['bounceToMatch'].shape and tariffedBounce['bounceToMatch'].shape == matches[0]['bounce'].shape:
                foundCorrectlyCount += 1
                ignoreStraddlePikeCount += 1
            # it makes sense, alright!..
            elif not tariffedBounce['bounceToMatch'].shape:
                foundCorrectlyCount += 1
                ignoreStraddlePikeCount += 1
        elif thisSkillName in straddlePike \
                and matchedSkillName in straddlePike:
            ignoreStraddlePikeCount += 1

            # if thisSkillName == matchedSkillName or thisSkillName == matches[1]['bounce'].skill_name:
            #     foundInFirst2Count += 1

    accuracy1stDeg = (foundCorrectlyCount / float(len(tariffedBounces))) * 100
    # accuracy2ndDeg = (foundInFirst2Count / float(len(tariffedBounces))) * 100
    accuracyIgnoringStraddlePike = (ignoreStraddlePikeCount / float(len(tariffedBounces))) * 100
    print('Accuracy: {:.0f}%. Ignoring Straddle <=> Pike {:.0f}%'.format(accuracy1stDeg, accuracyIgnoringStraddlePike))
    print('Actual tariff: {:.1f}, Estimated tariff: {:.1f}, difference: {:.1f}'.format(actualTariff, estimatedTariff, abs(actualTariff - estimatedTariff)))
    print("Finished tariff\n")
