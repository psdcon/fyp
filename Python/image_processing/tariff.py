import json
import time
from operator import itemgetter

import numpy as np
from scipy import signal
from sqlalchemy import text

from helpers.db_declarative import Bounce, TariffMatches, Routine

CUTOFF = 20000


def do_tariff(db):
    routines = db.query(Routine).filter(Routine.use == 1, Routine.id < 89, Routine.level < 5).order_by(Routine.level).all()
    routinesToTariff = []
    for routine in routines:
        if routine.isPoseImported(db):  # and not os.path.exists(routine.tariffPath()):
            routinesToTariff.append(routine)

    # Tariff
    tariff_many_routines(db, routinesToTariff)
    # Print accuracy
    accuracy_of_many_routines(db, routinesToTariff)

    # Accuracy on a skill basis
    accuracy_per_skill(db)


def chose_reference_skills(db, reference_count_per_skill):
    shapedSkillCounter = {}
    # print('Changing reference set to have {} bounces as a reference for each skill'.format(referenceCountPerSkill))
    print('Num Refs = {}'.format(reference_count_per_skill))
    bounces = db.query(Bounce).filter(Bounce.angles != None).order_by(Bounce.match_count.desc()).all()

    # The bounces to exclude from the reference set should be bounce
    # What if I have more references of a bounce than examples of it.
    # excludeBounces = skill_names_count_below(db, referenceCountPerSkill+1)
    excludeBounces = [u'Back Half', u'Cody', u'Front Drop', u'Full Back', u'Full Front', u'Lazy Back', u'Rudolph / Rudi', u'To Feet from Front']
    print("Excluding {}".format(excludeBounces))

    # Reset the labels first
    for bounce in bounces:
        bounce.ref_or_test = None

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
        accuracy_of_bounces(db, routine)

    timeTaken = time.time() - startTime
    print("")
    print("Finished tariffing many. Took {:.2f}s = {:.2f}m.".format(timeTaken, timeTaken / 60))
    print("")


def tariff_bounces_test_set(db):
    startTime = time.time()

    # Setup
    # print("Setting up to tariff bounces...")
    refBounces = get_reference_set(db)
    timeTaken = time.time() - startTime
    # print("Took {:.2f}s = {:.2f}m to collect reference bounces.".format(timeTaken, timeTaken / 60))
    print("Reference set contains {} bounces".format(len(refBounces)))

    # testBounces = db.query(Bounce).filter(Bounce.ref_or_test == "test", Bounce.skill_name != 'Landing').all()
    testBounces = db.query(Bounce).filter(Bounce.angles != None, Bounce.skill_name != 'Landing').all()
    print("Test set contains {} bounces".format(len(testBounces)))

    # Do tariff
    tariff(db, testBounces, refBounces)
    # Print accuracy
    accuracy_of_bounces(db, testBounces)

    timeTaken = time.time() - startTime
    print("")
    print("Finished tariffing bounces. Took {:.2f}s = {:.2f}m.".format(timeTaken, timeTaken / 60))
    print("")


def tariff(db, this_bounces, ref_bounces, verbose=False):
    """
    This is designed to be used by tariff_many
    For this to work, all the posedBounces must be fetched and kept in memory before hand.
    This introduces the problem of comparing a bounce to itself the bounces in this routine
        havent been excluded because the routine wasnt known at the time of fetch.
    """
    startTime = time.time()

    # Start processing this routine
    # print("\n----------------------")
    # print('Tariffing {}'.format(thisRoutine))

    tariffedBounces = []  # List of matches for each bounce in thisRoutine
    for thisBounce in this_bounces:
        # Check that this bounce has angles. May have been skipped by pose estimator
        # if thisBounce.skill_name == 'Straight Bounce' or thisBounce.skill_name == 'Landing' or thisBounce.angles is None:
        if thisBounce.angles is None \
                or thisBounce.tariff_match \
                or thisBounce.angles_count == 1:
            # TODO Change this as desired
            print("No angles or already matched or angle count too low")
            continue

        if verbose:
            print('\nLooking for {}. There are {} of these in the posedBounces.'.format(thisBounce, get_num_available(ref_bounces, thisBounce) - 1))

        # Start looking
        skillStartTime = time.time()
        thisBounceJointAngles = np.array(json.loads(thisBounce.angles))

        # Compare the angles of this bounce to every other bounce's angles
        # Creates a dict {'bounce':Bounce(), 'MSE':0.0}. This makes sorting them convenient.
        # bounceMatches = [compareAngles(thisBounceJointAngles, refBounce.jointAngles, CUTOFF, refBounce)
        #                  for refBounce in refBounces if refBounce.routine_id != thisBounce.routine_id]
        bounceMatches = [compare_angles(thisBounceJointAngles, refBounce.jointAngles, CUTOFF, refBounce)
                         for refBounce in ref_bounces if refBounce.id != thisBounce.id]
        bounceMatches[:] = [bm for bm in bounceMatches if bm is not None]  # remove None results
        bounceMatches = sorted(bounceMatches, key=itemgetter('MSE'))

        # Store first 5 results into a TariffMatches object
        timeTaken = time.time() - skillStartTime
        matchedBouncesIds = [bounceMatch['bounce'].id for bounceMatch in bounceMatches[:5]]
        matchedBouncesDistances = [bounceMatch['MSE'] for bounceMatch in bounceMatches[:5]]
        tariffMatch = TariffMatches(thisBounce.id, matchedBouncesIds[0], json.dumps(matchedBouncesIds), json.dumps(matchedBouncesDistances), timeTaken)

        if verbose:
            print(bounceMatches[:5])
            print(tariffMatch)
            print("Took {:.2f}s = {:.2f}m to find this skill. ".format(timeTaken, timeTaken / 60))
            print("Found {} matches with error below {}.".format(len(bounceMatches), CUTOFF))

        tariffedBounces.append(tariffMatch)

    # Add matches to db
    db.add_all(tariffedBounces)
    db.commit()

    timeTaken = time.time() - startTime
    print("Took {:.2f}s = {:.2f}m to estimate the skills in this routine".format(timeTaken, timeTaken / 60))


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
        Bounce.ref_or_test == 'ref',
        # Bounce.angles_count > 18,
        # Bounce.routine_id != thisRoutineId,  # will be none
        # Bounce.skill_name != 'Straight Bounce',
        Bounce.skill_name != 'Landing',
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
        tariffed_bounce['bounce'] = ref_bounce
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
    print("Accuracy: {:.1f}%. Ignoring Straddle/Pike {:.1f}%. Ignoring somi shape {:.1f}%".format(accuracy, accuracyIgnoringStraddlePike, accuracyIgnoringSomiShape))
    print("Actual tariff: {:.1f}, Estimated tariff: {:.1f}, difference: {:.1f}, "
          "average tariff error {:.1f} in range {:.1f} to {:.1f}, average % error {:.1f}%"
          .format(actualTariff, estimatedTariff, tariffDifference,
                  tariffDifference / float(bounceCount), minTariff, maxTariff, (tariffDifference / actualTariff) * 100))

    return accuracy, accuracyIgnoringSomiShape, tariffDifference


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
def plot_tariff_confusion_matrix(tariff_matches):
    def plot_confusion_matrix(df_confusion, title='Confusion matrix'):
        # from matplotlib import rcParams
        # rcParams.update({'figure.autolayout': True})
        # http://stackoverflow.com/questions/24521296/matplotlib-function-conventions-subplots-vs-one-figure

        fig, ax = plt.subplots()
        fig.set_size_inches(6.4, 6)
        # ax.set_title(title)

        cmap = matplotlib.cm.get_cmap('Greys')
        im = ax.matshow(df_confusion, cmap=cmap)  # imshow
        # fig.colorbar(im, orientation='horizontal')

        tick_marks = np.arange(len(df_confusion.columns))
        # plt.xticks(tick_marks, df_confusion.columns, rotation='vertical', verticalalignment='top')
        plt.xticks(tick_marks, df_confusion.columns, rotation='vertical')
        plt.yticks(tick_marks, df_confusion.index)
        ax.xaxis.set_ticks_position('bottom')
        ax.set_ylabel(df_confusion.index.name)
        ax.set_xlabel(df_confusion.columns.name)

        fig.tight_layout(pad=0)

        imgName = consts.confImgPath + "confusion_matrix.pdf"
        print("Writing image to {}".format(imgName))
        plt.savefig(imgName)

        plt.show()
        return

    actual = []
    predicted = []
    excludedMatched = [u'Back Half', u'Cody', u'Front Drop', u'Full Back', u'Full Front', u'Lazy Back', u'Rudolph / Rudi', u'To Feet from Front']
    for thisMatch in tariff_matches:
        thisBounce = thisMatch.bounce
        matchedBounce = thisMatch.matched_bounce

        if thisBounce.skill_name in excludedMatched or matchedBounce.skill_name in excludedMatched:
            continue

        actual.append(thisBounce.code_name)
        predicted.append(matchedBounce.code_name)

        # visualise.play_frames_of_2(db, thisBounce.routine, matchedBounce.routine, thisBounce.start_frame, thisBounce.end_frame, matchedBounce.start_frame, matchedBounce.end_frame)
    y_actu = pd.Series(actual, name='Actual Skill Class')
    y_pred = pd.Series(predicted, name='Predicted Skill Class')
    df_confusion = pd.crosstab(y_actu, y_pred)
    # df_confusion = pd.crosstab(y_actu, y_pred, rownames=['Actual'], colnames=['Predicted'], margins=True)  # add's sum col and row

    df_conf_norm = df_confusion / df_confusion.sum(axis=1)
    df_conf_norm.columns.name = "Predicted Skill Class"

    # plot_confusion_matrix(df_confusion, 'Confusion Matrix')
    plot_confusion_matrix(df_conf_norm, 'Normalised Confusion Matrix')
    # plt.show()

    return
