from __future__ import print_function

import json

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from sklearn import svm

import helpers.helper_funcs
from helpers.db_declarative import Reference, Bounce, Routine, Deduction
from image_processing import visualise
from image_processing.calc_angles import angle_l_knee, angle_r_leg_with_vertical, angle_r_knee, angle_l_hip, angle_r_hip, angle_l_leg_with_vertical
from image_processing.calc_angles import extended_angle_keys


def calc_distance(this_bounce_joint_angles, ref_joint_angles):
    this_bounce_frame_count = len(this_bounce_joint_angles[0])

    # Two different error metrics
    # absolute_diff = 0
    # squared_error = 0

    # weights = [0.3, 0.3, 0.5, 0.5, 1, 1, 1, 1, 0.3, 1, 1, 1, 1]
    """[
        "Right elbow",
        "Left elbow",
        "Right shoulder",
        "Left shoulder",
        "Right knee",
        "Left knee",
        "Right hip",
        "Left hip",
        "Head"
        "Right leg with horz",
        "Left leg with horz",
        "Torso with horz",
        "Twist Angle"
    ]"""
    from image_processing.calc_angles import num_angles
    distances = []
    for i in range(num_angles):  # the number of different angles = 13
        # weight = weights[i]
        this_joint = this_bounce_joint_angles[i]
        ref_joint = ref_joint_angles[i]

        aligned_posed_joint = signal.resample(ref_joint, this_bounce_frame_count)
        distance = np.sum(np.absolute(np.subtract(this_joint, aligned_posed_joint)))
        distances.append(distance)

        # distance, _path = fastdtw(this_joint, ref_joint, dist=euclidean)
        # distance *= weight

        # Keeping two error metrics
        # absolute_diff += distance
        # squared_error += distance ** 2

    # sum_abs_diff = int(round(absolute_diff, 0))
    # mean_sq_err = int(round(squared_error, 0)) / num_angles

    # return sum_abs_diff, mean_sq_err
    return distances


def judge_deductions(deductionsJSONs, refBounceAngles):
    # Counter({u'body': 37, u'line_out': 32, u'legs_toes': 12, u'arms-windmill': 4, u'legs_apart': 1})

    # Detect body deduction: 0.0, 0.1, 0.2
    # Need to get the bounces which had body deductions
    # From these make a test set of 3 * {0.0, 0.1, 0.2}. Remainder is test set ( 28 )
    bouncesBodyDeductions = [(deductionsJSON['bounceAngles'], "{}".format(deductionsJSON['body'])) for deductionsJSON in deductionsJSONs if 'body' in deductionsJSON.keys()]

    # Train SVM
    allLabels = []
    allFeatures = []
    trainingLabels = []
    testLabels = []
    trainingFeatures = []
    testFeatures = []
    datasetCounts = {
        '0.0': 0,
        '0.1': 0,
        '0.2': 0,
    }
    # Counter({'0.1': 13, '0.4': 12, '0.3': 7, '0.2': 6, '0.0': 5, '0.5': 4})
    for thisBounceAngles, deductionLabel in bouncesBodyDeductions:
        # _sad, mse = calc_distance(thisBounceAngles, refBounceAngles)
        # features = calc_distance(thisBounceAngles, refBounceAngles)

        # Pull out max of angles
        num_frames = len(thisBounceAngles[0])
        num_frames_25 = int(num_frames * 0.25)
        num_frames_75 = int(num_frames * 0.75)
        max_hip = np.concatenate([
            thisBounceAngles[extended_angle_keys.index(angle_r_hip)][num_frames_25:num_frames_75],
            thisBounceAngles[extended_angle_keys.index(angle_l_hip)][num_frames_25:num_frames_75]
        ]).min()
        max_knee = np.concatenate([thisBounceAngles[extended_angle_keys.index(angle_r_knee)], thisBounceAngles[extended_angle_keys.index(angle_l_knee)]]).min()
        max_leg_vert = np.concatenate([
            thisBounceAngles[extended_angle_keys.index(angle_r_leg_with_vertical)][num_frames_25:num_frames_75],
            thisBounceAngles[extended_angle_keys.index(angle_l_leg_with_vertical)][num_frames_25:num_frames_75]
        ]).max()

        features = [max_hip, max_leg_vert]

        allLabels.append(deductionLabel)
        allFeatures.append(features)

        if datasetCounts[deductionLabel] <= 4:
            datasetCounts[deductionLabel] += 1
            trainingLabels.append(deductionLabel)
            trainingFeatures.append(features)
        else:
            testLabels.append(deductionLabel)
            testFeatures.append(features)

            # labelAndDistance = [deductionLabel, mse, bounce]
            # labelsAndDistances.append(labelAndDistance)

    # SVM
    clf = svm.SVC()
    # scores = cross_val_score(clf, allFeatures, allLabels, cv=5, scoring="accuracy")
    # print(scores)
    # print()

    clf.fit(trainingFeatures, trainingLabels)
    score = clf.score(testFeatures, testLabels) * 100
    predictions = clf.predict(testFeatures)

    print("Test Size: {}".format(len(testLabels)))
    print("Accuracy: {:.2f}%".format(score))

    cmap = plt.cm.get_cmap('viridis')
    norm = matplotlib.colors.Normalize(vmin=0.0, vmax=0.2)

    trainingFeatures = np.array(trainingFeatures)
    testFeatures = np.array(testFeatures)
    plt.figure()
    plt.title("Training Samples")
    trainingLabelColors = [cmap(norm(float(label))) for label in trainingLabels]
    plt.scatter(trainingFeatures[:, 0], trainingFeatures[:, 1], c=trainingLabelColors, cmap=cmap)
    # plt.colorbar(ticks=[0.0, 0.1, 0.2])
    testLabelColors = [cmap(norm(float(label))) for label in testLabels]
    plt.scatter(testFeatures[:, 0], testFeatures[:, 1], marker='x', c=testLabelColors, cmap=cmap)
    plt.xlabel("Max Angle w Vert")
    plt.ylabel("Min Hip Angle")
    plt.show(block=False)

    # Find SVM boundaries
    trainingFeatures = np.array(trainingFeatures)
    x_min, x_max = np.concatenate([testFeatures[:, 0], trainingFeatures[:, 0]]).min() - 5, np.concatenate([testFeatures[:, 0], trainingFeatures[:, 0]]).max() + 5
    y_min, y_max = np.concatenate([testFeatures[:, 1], trainingFeatures[:, 1]]).min() - 5, np.concatenate([testFeatures[:, 1], trainingFeatures[:, 1]]).max() + 5
    h = (x_max / x_min)
    xx, yy = np.meshgrid(np.arange(x_min, x_max, h), np.arange(y_min, y_max, h))
    Z = clf.predict(np.c_[xx.ravel(), yy.ravel()])
    Z = Z.reshape(xx.shape)

    plt.figure()
    plt.title("SVM Boundaries")
    plt.contourf(xx, yy, Z, cmap=cmap, alpha=0.6)
    trainingLabelColors = [cmap(norm(float(label))) for label in trainingLabels]
    sc = plt.scatter(trainingFeatures[:, 0], trainingFeatures[:, 1], c=trainingLabelColors, cmap=cmap)
    # m = matplotlib.cm.ScalarMappable(cmap=cmap, norm=norm)
    # m.set_array()
    # plt.colorbar(sc)
    testLabelColors = [cmap(norm(float(label))) for label in testLabels]
    plt.scatter(testFeatures[:, 0], testFeatures[:, 1], marker='x', c=testLabelColors, cmap=cmap)
    plt.xlabel("Max Angle w Vert")
    plt.ylabel("Min Hip Angle")
    plt.show()

    return



def judge_skill(db):
    # Get reference bounce information
    desiredSkill = 'Tuck Jump'
    reference = db.query(Reference).filter_by(name=desiredSkill).one()
    refBounce = reference.bounce
    refBounceAngles = np.array(json.loads(refBounce.angles))

    # Get all bounces, not in Elite
    bounces = db.query(Bounce).join(Routine, Deduction).filter(
        Bounce.skill_name == desiredSkill,
        Bounce.angles != None,
        Bounce.id != refBounce.id,
        Routine.level < 4,
        Deduction.deduction_cats != None).all()

    deductionsJSONs = []
    deductionsJSONKeys = []
    for bounce in bounces:
        deductionLabel, deductionJSON = bounce.getNewDeduction()
        deductionsJSONKeys += deductionJSON.keys()

        deductionJSON['bounceAngles'] = np.array(json.loads(bounce.angles))
        deductionsJSONs.append(deductionJSON)

    from collections import Counter
    counts = Counter(deductionsJSONKeys)

    # I want an svm foreach of the 5 deductions, right?

    # So 5 cases
    # Each case has training and test code = 5, 2
    # OR
    # 2, 5. there trainings and test. Method one now because I can verify their usefulness. Production would look lik this.

    judge_deductions(deductionsJSONs, refBounceAngles)
    return

    #
    labelsAndDistances = []
    trainingLabels = []
    testLabels = []
    trainingFeatures = []
    testFeatures = []
    datasetCounts = {
        '0.0': 0,
        '0.1': 0,
        '0.2': 0,
        '0.3': 0,
        '0.4': 0,
        '0.5': 0,
    }
    # Counter({'0.1': 13, '0.4': 12, '0.3': 7, '0.2': 6, '0.0': 5, '0.5': 4})
    for bounce in bounces:
        # Don't included bounces that ain't been judged
        deductionLabel, deductionJSON = bounce.getNewDeduction()
        deductionLabel = "{}".format(deductionLabel)

        # Get features
        thisBounceAngles = np.array(json.loads(bounce.angles))
        # _sad, mse = calc_distance(thisBounceAngles, refBounceAngles)
        distances = calc_distance(thisBounceAngles, refBounceAngles)

        if datasetCounts[deductionLabel] <= 1:
            datasetCounts[deductionLabel] += 1
            trainingLabels.append(deductionLabel)
            trainingFeatures.append(distances)
        else:
            testLabels.append(deductionLabel)
            testFeatures.append(distances)

            # labelAndDistance = [deductionLabel, mse, bounce]
            # labelsAndDistances.append(labelAndDistance)

    # SVM
    clf = svm.SVC()
    clf.fit(trainingFeatures, trainingLabels)
    score = clf.score(testFeatures, testLabels) * 100
    predictions = clf.predict(testFeatures)

    print("Test Size: {}".format(len(testLabels)))
    print("Accuracy: {:.2f}%".format(score))

    # plt.figure()
    # plt.title("Training Samples")
    # plt.scatter(trainingLabels, trainingFeatures)
    # plt.xlabel("Deduction Value")
    # plt.ylabel("Error (SAD)")
    # plt.show(block=False)
    #
    # # Find SVM boundaries
    # trainingFeatures = np.array(trainingFeatures)
    # x_min, x_max = trainingFeatures[:, 0].min() - 1, trainingFeatures[:, 0].max() + 1
    # h = (x_max / x_min)
    # xx = np.arange(x_min, x_max, h)
    # xx = xx.reshape(xx.shape[0], 1)
    # predicted_xx_labels = clf.predict(xx)
    #
    # plt.figure()
    # plt.title("SVM Boundaries")
    # plt.scatter(predicted_xx_labels, xx)
    # plt.xlabel("Deduction Value")
    # plt.ylabel("Error (SAD)")
    # plt.show()

    # sortedLabelsAndDistances = sorted(labelsAndDistances, key=itemgetter(1))
    # sortedLabelsAndDistances = np.array(sortedLabelsAndDistances)
    #
    # x = np.array(sortedLabelsAndDistances[:, 0])
    # y = np.array(sortedLabelsAndDistances[:, 1])
    # # x = np.arange(len(y))
    #
    # # print(scipy.stats.pearsonr(x=x, y=y))
    #
    # plt.scatter(x, y)
    # plt.show()
    #
    # labelsAndDistances

    return


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
