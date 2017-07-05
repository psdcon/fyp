import json
import time
from collections import Counter
from operator import itemgetter

import numpy as np
import pandas as pd
from scipy import signal
from sqlalchemy import text, func

from helpers.db_declarative import Bounce, TariffMatches
from image_processing.visualise import plot_confusion_matrix

CUTOFF = 30000

skill_count_cutoff = 10
skill_class_test_size = 10
ref_split = 0.5
ref_size = int(skill_class_test_size * ref_split)
test_size = skill_class_test_size - ref_size


def tariff_epochs(db):
    from time import gmtime, strftime
    now_str = strftime("%Y%m%d_%H%M%S", gmtime())

    num_epochs = 20
    accuracies = []
    confustion_matrices = []
    for i in range(0, num_epochs):
        print("\nEpoch {} of {}".format(i, num_epochs))
        accuracy, conf_matrix = tariff_bounces_test_proper(db)
        # Save between epochs
        accuracies.append(accuracy)
        confustion_matrices.append(conf_matrix)

    accuracies = np.array(accuracies)
    np.savetxt('tariff//{}_tariff_accuracies.csv'.format(now_str), accuracies, delimiter=",", fmt='%10.5f')
    scores = accuracies.mean(axis=0)
    print(scores)

    conf_matrix = confustion_matrices[0]
    for df in confustion_matrices[1:]:
        conf_matrix = conf_matrix.add(df)
    conf_matrix.to_csv('tariff//{}_tariff_confusion.csv'.format(now_str))
    plot_confusion_matrix(conf_matrix)


def open_epoch_save_data():
    timestamp = '20170523_220642'
    accuracies_fpath = 'tariff//{}_tariff_accuracies.csv'.format(timestamp)
    conf_matrix_fpath = 'tariff//{}_tariff_confusion.csv'.format(timestamp)

    accuracies = np.loadtxt(accuracies_fpath, delimiter=',')
    scores = accuracies.mean(axis=0)
    print(scores)

    conf_matrix = pd.read_csv(conf_matrix_fpath, index_col=0)
    conf_matrix.index.name = 'Ground Truth Skill'
    conf_matrix.columns.name = 'Identified Skill'
    plot_confusion_matrix(conf_matrix)




def get_skills_dataset_proper(db):
    bounces = db.query(Bounce).filter(Bounce.angles != None, Bounce.code_name != None, Bounce.skill_name != 'Landing'
                                      ).order_by(func.random()).all()
    # ).order_by(Bounce.match_count.desc()).all()

    skill_names = []
    for bounce in bounces:
        skill_names.append(bounce.shapedSkillName())
    skill_class_counts = Counter(skill_names).most_common()

    skills_dataset_by_class = {}
    skills_excluded = []
    for skill_class_count in skill_class_counts:
        if skill_class_count[1] >= skill_count_cutoff:
            skills_dataset_by_class[skill_class_count[0]] = []
        else:
            skills_excluded.append(skill_class_count)
    print("Skills excluded", skills_excluded)

    dataset_size = 0
    for bounce in bounces:
        bounce_shape_name = bounce.shapedSkillName()
        if bounce_shape_name in skills_dataset_by_class.keys() and len(skills_dataset_by_class[bounce_shape_name]) < skill_class_test_size:
            # Add bounce to dataset after adding angles
            bounce.jointAngles = np.array(json.loads(bounce.angles))
            skills_dataset_by_class[bounce_shape_name].append(bounce)
            dataset_size += 1

    print("The size of the dataset is {} with {} individual bounce classes".format(dataset_size, len(skills_dataset_by_class)))

    return skills_dataset_by_class


def set_reference_skills(db, reference_count_per_skill):
    print('Changing reference set to have {} bounces as a reference for each skill'.format(reference_count_per_skill))
    print('Num Refs = {}'.format(reference_count_per_skill))

    bounces = db.query(Bounce).filter(Bounce.angles != None, Bounce.code_name != None, Bounce.skill_name != 'Landing'
                                      ).order_by(Bounce.match_count.desc()).all()

    excludeBounces = skill_names_count_below(db, reference_count_per_skill + 1)
    print("Excluding {}".format(excludeBounces))

    # Reset the labels first in case num refs, or skills to include has changed.
    for bounce in bounces:
        bounce.ref_or_test = None

    shapedSkillCounter = {}
    for bounce in bounces:
        # Don't assign skill's that've too few examples to be tested
        if bounce.skill_name in excludeBounces:
            continue

        # Get a name which includes the bounces shape
        shapedName = bounce.skill_name + " {}".format(bounce.shape)
        # If the reference set is full, it goes in the test set
        if shapedSkillCounter.get(shapedName, 0) >= reference_count_per_skill:
            bounce.ref_or_test = 'test'
        else:
            shapedSkillCounter[shapedName] = shapedSkillCounter.get(shapedName, 0) + 1
            bounce.ref_or_test = 'ref'
    db.commit()


def tariff_many_routines(db, routines):
    startTime = time.time()

    # Setup
    print("Setting up for tariff...")
    refBounces = get_reference_set(db)
    timeTaken = time.time() - startTime
    print("Took {:.2f}s = {:.2f}m to coordinate bounces.".format(timeTaken, timeTaken / 60))
    print("Found {} bounces with pose".format(len(refBounces)))

    print("Looking at {} routines".format(len(routines)))
    # Tariff all the routines in the list
    # refBounces that belong to the routine being tariffed are ignored when finding matches
    for routine in routines:
        # Do tariff
        tariff(db, routine.bounces, refBounces)
        # Print accuracy
        accuracy_of_bounces(db, routine.bounces)

    timeTaken = time.time() - startTime
    print("")
    print("Finished tariffing many. Took {:.2f}s = {:.2f}m.".format(timeTaken, timeTaken / 60))
    print("")


def tariff_bounces_test_proper(db):
    start_time = time.time()

    # Setup
    bounces_dataset = get_skills_dataset_proper(db)

    # Order skill class labels
    bounce_labels = []
    for skill_class in bounces_dataset:
        bounce = bounces_dataset[skill_class][0]
        bounce_labels.append((bounce.getSkillSortId(db), bounce.shapedCodeName()))
    bounce_labels = [label for order, label in sorted(bounce_labels)]

    conf_matrix = pd.DataFrame(np.zeros((len(bounce_labels), len(bounce_labels))), index=bounce_labels, columns=bounce_labels)
    conf_matrix.index.name = 'Ground Truth Skill'
    conf_matrix.columns.name = 'Classified Skill'

    accuracies = []
    for i in range(0, skill_class_test_size):
        # Split
        test_bounces = []
        ref_bounces = []
        ref_start = i
        ref_end_test_start = i + ref_size
        test_end = ref_end_test_start + test_size
        print("\nRun {}. Ref set [{}:{}], test set [{}:{}]".format(i + 1, ref_start, ref_end_test_start, ref_end_test_start, test_end))
        for bounce_class in bounces_dataset:
            bounces = bounces_dataset[bounce_class]
            bounces_extended = bounces + bounces
            ref_bounces += bounces_extended[ref_start:ref_end_test_start]
            test_bounces += bounces_extended[ref_end_test_start:test_end]

        db.execute("DELETE FROM tariff_matches")
        db.commit()
        # Do tariff
        tariff(db, test_bounces, ref_bounces)
        # Print accuracy
        accs = accuracy_of_bounces(db, test_bounces)
        accuracies.append(accs)
        # Do confusion
        for actual_bounce in test_bounces:
            predicted_bounce = actual_bounce.tariff_match[0].matched_bounce
            # col(index), row
            # predicted, actual
            # conf_matrix['Back Drop']['Tuck Jump'] += 1
            conf_matrix[predicted_bounce.shapedCodeName()][actual_bounce.shapedCodeName()] += 1

    accuracies = np.array(accuracies)
    scores = accuracies.mean(axis=0)
    print("accuracy, accuracyIgnoringStraddlePike, accuracyIgnoringSomiShape, tariffAccuracy")
    print(scores)
    print("")

    timeTaken = time.time() - start_time
    print("Finished tariffing bounces dataset. Took {:.2f}s = {:.2f}m.".format(timeTaken, timeTaken / 60))

    return scores, conf_matrix


def tariff_bounces_test_set(db):
    startTime = time.time()

    # Setup
    refBounces = get_reference_set(db)
    print("Reference set contains {} bounces".format(len(refBounces)))

    testBounces = db.query(Bounce).filter(Bounce.angles != None, Bounce.code_name != None, Bounce.ref_or_test == 'test').all()
    print("Test set contains {} bounces".format(len(testBounces)))

    # Do tariff
    tariff(db, testBounces, refBounces)
    # Print accuracy
    accuracy_of_bounces(db, testBounces)

    timeTaken = time.time() - startTime
    print("Finished tariffing bounces. Took {:.2f}s = {:.2f}m.".format(timeTaken, timeTaken / 60))
    print("")


def tariff(db, test_bounces, ref_bounces, verbose=False):
    start_time = time.time()

    tariffed_bounces = []  # List of matches for each bounce in thisRoutine
    for test_bounce in test_bounces:
        # Check that this bounce has angles. May have been skipped by pose estimator
        # if test_bounce.skill_name == 'Straight Bounce' or test_bounce.skill_name == 'Landing' or test_bounce.angles is None:
        if test_bounce.angles is None \
                or test_bounce.tariff_match \
                or test_bounce.angles_count == 1:
            # TODO Change this as desired
            print("No angles or already matched or angle count too low")
            continue

        if verbose:
            print('\nLooking for {}. There are {} of these in the posedBounces.'.format(test_bounce, get_num_available(ref_bounces, test_bounce) - 1))

        # Start looking
        skill_start_time = time.time()

        # Compare the angles of this bounce to every other bounce's angles
        # Creates a dict {'bounce':Bounce(), 'MSE':0.0}. This makes sorting them convenient.
        # bounce_matches = [compareAngles(thisBounceJointAngles, ref_bounce.jointAngles, CUTOFF, ref_bounce)
        #                  for ref_bounce in refBounces if ref_bounce.routine_id != test_bounce.routine_id]
        bounce_matches = [compare_angles(test_bounce.jointAngles, ref_bounce.jointAngles, CUTOFF, ref_bounce)
                          for ref_bounce in ref_bounces if ref_bounce.id != test_bounce.id]
        bounce_matches[:] = [bm for bm in bounce_matches if bm is not None]  # remove None results
        bounce_matches = sorted(bounce_matches, key=itemgetter('MSE'))

        # Store first 5 results into a TariffMatches object
        time_taken = time.time() - skill_start_time
        matched_bounces_ids = [bounce_match['matched_bounce'].id for bounce_match in bounce_matches[:5]]
        matched_bounces_distances = [bounce_match['MSE'] for bounce_match in bounce_matches[:5]]
        tariff_match = TariffMatches(test_bounce.id, matched_bounces_ids[0], json.dumps(matched_bounces_ids), json.dumps(matched_bounces_distances), time_taken)

        if verbose:
            print(bounce_matches[:5])
            print(tariff_match)
            print("Took {:.2f}s = {:.2f}m to find this skill. ".format(time_taken, time_taken / 60))
            print("Found {} matches with error below {}.".format(len(bounce_matches), CUTOFF))

        tariffed_bounces.append(tariff_match)

    # Add matches to db
    db.add_all(tariffed_bounces)
    db.commit()

    time_taken = time.time() - start_time
    print("Took {:.2f}s = {:.2f}m to estimate the skill class labels".format(time_taken, time_taken / 60))


###############################
# Helper functions used in Tariff_lean & Tariff_verbose
###############################
def skill_names_count_below(db, count):
    sql = text("SELECT skill_name, count(1) FROM bounces WHERE skill_name NOTNULL AND angles NOTNULL GROUP BY skill_name")
    results = db.execute(sql)

    skillsWithCountsBelow = []
    for res in results:
        if res[1] < count:
            skillsWithCountsBelow.append(res[0])

    return skillsWithCountsBelow


def get_reference_set(db):
    # Get all bounces that have pose in this level
    refBounces = db.query(Bounce).filter(
        # Bounce.angles != None,
        Bounce.ref_or_test == 'ref',  # excludes bounces with too few samples
        # Bounce.angles_count > 18,
        # Bounce.routine_id != thisRoutineId,  # will be none
        # Bounce.skill_name != 'Straight Bounce',
    ).all()

    for bounce in refBounces:
        bounce.jointAngles = np.array(json.loads(bounce.angles))

    return refBounces


def get_num_available(posed_bounces, this_bounce):
    num_available_to_find = 0
    for posed_bounce in posed_bounces:
        if posed_bounce.skill_name == this_bounce.skill_name:
            num_available_to_find += 1
    return num_available_to_find


def compare_angles(this_bounce_joint_angles, ref_joint_angles, cutoff, ref_bounce):
    thisBounceFrameCount = len(this_bounce_joint_angles[0])
    tariffed_bounce = {}

    # Two different error metrics
    absolute_diff = 0
    squared_error = 0

    save_bounce_match = True
    weights = [0.3, 0.3, 0.5, 0.5, 1, 1, 1, 1, 0.3, 1, 1, 1, 1]
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
    for i in range(num_angles):  # the number of different angles = 13
        weight = weights[i]
        thisJoint = this_bounce_joint_angles[i]
        posedJoint = ref_joint_angles[i]

        alignedPosedJoint = signal.resample(posedJoint, thisBounceFrameCount)
        distance = np.sum(np.absolute(np.subtract(thisJoint, alignedPosedJoint)))

        # distance, _path = fastdtw(thisJoint, posedJoint, dist=euclidean)
        distance *= weight
        # Keeping two error metrics
        absolute_diff += distance
        squared_error += distance ** 2

        # Early exit clause
        if absolute_diff > cutoff:
            save_bounce_match = False
            break

    # Only store as a match if we didn't exit early
    if save_bounce_match:
        tariffed_bounce['SAD'] = int(round(absolute_diff, 0))
        tariffed_bounce['MSE'] = int(round(squared_error, 0)) / num_angles
        tariffed_bounce['matched_bounce'] = ref_bounce
        return tariffed_bounce
    else:
        return None


################################
# Accuracy
################################
def accuracy_of_many_routines(db, routines):
    averageAccuracy = 0
    averageAccuracyIgnoringShape = 0
    averageTariffError = 0

    for routine in routines:
        accuracy, accuracyIgnoringShape, tariffError = accuracy_of_bounces(db, routine.bounces)
        averageAccuracy += accuracy
        averageAccuracyIgnoringShape += accuracyIgnoringShape
        averageTariffError += tariffError

    print('')
    print('Average accuracy {:.2f}%'.format(averageAccuracy / len(routines)))
    print('Average accuracy ignoring somi shape {:.2f}%'.format(averageAccuracyIgnoringShape / len(routines)))
    print('Average tariff error {:.3f}'.format(averageTariffError / len(routines)))


def accuracy_of_bounces(db, bounces):
    bounceCount = 0
    correctCount = 0
    correctIgnoringShapeCount = 0
    ignoreStraddlePikeCount = 0

    actualTariff = 0.0
    estimatedTariff = 0.0

    straddlePike = ['Straddle Jump', 'Pike Jump']

    maxTariff = 0
    minTariff = 99

    for thisBounce in bounces:
        # Ignore Straight Bounce and Landings
        if not thisBounce.tariff_match:
            continue

        bounceCount += 1
        thisBounceName = thisBounce.skill_name
        matchedBounce = thisBounce.tariff_match[0].matched_bounce
        matchedBounceName = matchedBounce.skill_name

        thisTariff = thisBounce.getTariff(db)
        if thisTariff > maxTariff:
            maxTariff = thisTariff
        elif thisTariff < minTariff:
            minTariff = thisTariff

        actualTariff += thisTariff
        estimatedTariff += matchedBounce.getTariff(db)

        if thisBounceName == matchedBounceName:
            correctIgnoringShapeCount += 1
            # If the move has a shape, then they should match
            if thisBounce.shape and thisBounce.shape == matchedBounce.shape:
                correctCount += 1
                ignoreStraddlePikeCount += 1
            # it makes sense, alright!..
            elif not thisBounce.shape:
                correctCount += 1
                ignoreStraddlePikeCount += 1
        elif thisBounceName in straddlePike and matchedBounceName in straddlePike:
            ignoreStraddlePikeCount += 1

    accuracy = (correctCount / float(bounceCount)) * 100
    accuracyIgnoringSomiShape = (correctIgnoringShapeCount / float(bounceCount)) * 100
    accuracyIgnoringStraddlePike = (ignoreStraddlePikeCount / float(bounceCount)) * 100
    tariffDifference = abs(actualTariff - estimatedTariff)
    tariffAccuracy = 100 - ((tariffDifference / actualTariff) * 100)
    print("Accuracy: {:.1f}%. Ignoring Straddle/Pike {:.1f}%. Ignoring somi shape {:.1f}%".format(accuracy, accuracyIgnoringStraddlePike, accuracyIgnoringSomiShape))
    print("Actual tariff: {:.1f}, Estimated tariff: {:.1f}, difference: {:.1f}, "
          "average tariff error {:.1f} in range {:.1f} to {:.1f}, average accuracy {:.1f}%"
          .format(actualTariff, estimatedTariff, tariffDifference,
                  tariffDifference / float(bounceCount), minTariff, maxTariff, tariffAccuracy))

    # return accuracy, accuracyIgnoringSomiShape, tariffDifference
    return accuracy, accuracyIgnoringStraddlePike, accuracyIgnoringSomiShape, tariffAccuracy


def accuracy_per_skill(db):
    totalOfEachBounce = {}
    hitsForEachBounce = {}

    tariffMatches = db.query(TariffMatches).all()
    for thisMatch in tariffMatches:
        thisBounce = thisMatch.bounce
        matchedBounce = thisMatch.matched_bounce

        totalOfEachBounce[thisBounce.skill_name] = totalOfEachBounce.get(thisBounce.skill_name, 0) + 1

        if thisBounce.skill_name == matchedBounce.skill_name:
            if thisBounce.shape and thisBounce.shape == matchedBounce.shape:
                hitsForEachBounce[thisBounce.skill_name] = hitsForEachBounce.get(thisBounce.skill_name, 0) + 1
            elif not thisBounce.shape:
                hitsForEachBounce[thisBounce.skill_name] = hitsForEachBounce.get(thisBounce.skill_name, 0) + 1

    accuracyPerSkill = {}
    for bounceNameKey in totalOfEachBounce:
        bounceCount = totalOfEachBounce[bounceNameKey]
        hitCount = hitsForEachBounce.get(bounceNameKey, 0)  # may not have got any hits on this skill
        accuracyPerSkill[bounceNameKey] = (hitCount / float(bounceCount)) * 100

    accuracySorted = sorted(accuracyPerSkill.items(), key=itemgetter(1))
    print(accuracySorted)
    print('wait')

#     (u'Back Half', 0.0), (u'Rudolph / Rudi', 0.0), (u'Landing', 0.0), (u'Full Front', 0.0), (u'Front Drop', 0.0), (u'Cody', 0.0), (u'To Feet from Front', 20.0), (u'Half Twist Jump', 22.22222222222222), (u'Half Twist to Seat Drop', 30.0), (u'Lazy Back', 33.33333333333333), (u'Full Twist Jump', 36.84210526315789), (u'To Feet from Back', 42.857142857142854), (u'Full Back', 50.0), (u'Half Twist to Feet from Back', 53.84615384615385), (u'Front S/S', 63.63636363636363), (u'Barani', 71.15384615384616), (u'Straddle Jump', 71.42857142857143), (u'Barani Ball Out', 71.42857142857143), (u'To Feet from Seat', 72.72727272727273), (u'Seat Drop', 76.92307692307693), (u'Crash Dive', 77.77777777777779), (u'Back Drop', 80.0), (u'Pike Jump', 82.5), (u'Back S/S', 85.52631578947368), (u'Half Twist to Feet from Seat', 87.5), (u'Tuck Jump', 93.10344827586206), (u'Straight Bounce', 96.85314685314685), (u'Back S/S to Seat', 100.0), (u'Swivel Hips/Seat Half Twist to Seat Drop', 100.0)]

#
# Visualise the errors.
#
# def plot_tariff_confusion_matrix(db):
#     tariff_matches = db.query(TariffMatches).all()
#
#     actual = []
#     predicted = []
#     excludedMatched = [u'Back Half', u'Cody', u'Front Drop', u'Full Back', u'Full Front', u'Lazy Back', u'Rudolph / Rudi', u'To Feet from Front']
#     for thisMatch in tariff_matches:
#         thisBounce = thisMatch.bounce
#         matchedBounce = thisMatch.matched_bounce
#
#         if thisBounce.skill_name in excludedMatched or matchedBounce.skill_name in excludedMatched:
#             continue
#
#         actual.append(thisBounce.code_name)
#         predicted.append(matchedBounce.code_name)
#
#         # visualise.play_frames_of_2(db, thisBounce.routine, matchedBounce.routine, thisBounce.start_frame, thisBounce.end_frame, matchedBounce.start_frame, matchedBounce.end_frame)
#     y_actu = pd.Series(actual, name='Actual Skill Class')
#     y_pred = pd.Series(predicted, name='Predicted Skill Class')
#     df_confusion = pd.crosstab(y_actu, y_pred)
#     # df_confusion = pd.crosstab(y_actu, y_pred, rownames=['Actual'], colnames=['Predicted'], margins=True)  # add's sum col and row
#
#     df_conf_norm = df_confusion / df_confusion.sum(axis=1)
#     df_conf_norm.columns.name = "Predicted Skill Class"
#
#     # plot_confusion_matrix(df_confusion, 'Confusion Matrix')
#     plot_confusion_matrix(df_conf_norm, 'Normalised Confusion Matrix')
#     # plt.show()
#
#     return
