import json
import time
from operator import itemgetter

import numpy as np
from scipy import signal

from helpers.db_declarative import Bounce, TariffMatches

CUTOFF = 30000


def tariff_verbose(db, thisRoutine):
    startTime = time.time()

    # Setup
    print('Setting up for tariff...')
    posedBounces = getPosedBounces(db, thisRoutine.id)
    # Set up angles with the right dimensions.
    # for posedBounce in posedBounces:
    #     posedBounce.anglesAsCoords = posedBounce.getAnglesAsCoords(db)
    posedBounces[:] = [posedBounce for posedBounce in posedBounces if posedBounce.skill_name != 'In/Out Bounce']
    posedBounces[:] = [posedBounce for posedBounce in posedBounces if posedBounce.skill_name != 'Landing']
    timeTaken = time.time() - startTime
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
        print('Looking for {}. There are {} of these in the posedBounces.'.format(thisBounce, getNumAvailable(posedBounces, thisBounce)))
        skillStartTime = time.time()

        #
        # Compare the angles of this bounce to every other bounce's angles
        bounceMatches = [compareAngles(thisBounce.jointAngles, posedBounce.jointAngles, CUTOFF, posedBounce) for posedBounce in posedBounces]
        bounceMatches[:] = [bm for bm in bounceMatches if bm is not None]  # remove None results
        bounceMatches = sorted(bounceMatches, key=itemgetter('totalDistance'))

        print(bounceMatches)
        timeTaken = time.time() - skillStartTime
        print("Took {:.2f}s = {:.2f}m to find this skill. ".format(timeTaken, timeTaken / 60))
        print("Found {} matches with error below {}.".format(len(bounceMatches), CUTOFF))

        tariffedBounces.append({
            'bounceToMatch': thisBounce,
            'timeTaken': timeTaken,
            'matches': bounceMatches,
        })

    timeTaken = time.time() - startTime
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
    print("Accuracy: {:.0f}%. Ignoring Straddle <=> Pike {:.0f}%".format(accuracy1stDeg, accuracyIgnoringStraddlePike))
    print("Actual tariff: {:.1f}, Estimated tariff: {:.1f}, difference: {:.1f}".format(actualTariff, estimatedTariff, abs(actualTariff - estimatedTariff)))
    print("Finished tariff\n")


def tariff_many(db, routines):
    startTime = time.time()

    # Setup
    print("Setting up for tariff...")
    posedBounces = getPosedBounces(db, None)
    # posedBounces[:] = [posedBounce for posedBounce in posedBounces if posedBounce.skill_name != 'In/Out Bounce']
    # posedBounces[:] = [posedBounce for posedBounce in posedBounces if posedBounce.skill_name != 'Landing']
    timeTaken = time.time() - startTime
    print("Took {:.2f}s = {:.2f}m to coordinate bounces.".format(timeTaken, timeTaken / 60))
    print("Found {} bounces with pose".format(len(posedBounces)))

    print("Looking at {} routines".format(len(routines)))
    # Tariff all the routines in the list
    # posedBounces that belong to the routine being tariffed are ignored when finding matches
    for routine in routines:
        tariff_lean(db, routine, posedBounces)

    timeTaken = time.time() - startTime
    print("Finished tariffing many. Took {:.2f}s = {:.2f}m to coordinate bounces.".format(timeTaken, timeTaken / 60))


def tariff_lean(db, thisRoutine, posedBounces):
    """
    This is designed to be used by tariff_many
    For this to work, all the posedBounces must be fetched and kept in memory before hand.
    This introduces the problem of comparing a bounce to itself the bounces in this routine
        havent been excluded because the routine wasnt known at the time of fetch.
    """
    startTime = time.time()

    # Start processing this routine
    print("\n----------------------")
    print('Tariffing ' + thisRoutine.__repr__())

    tariffedBounces = []  # List of matches for each bounce in thisRoutine
    for thisBounce in thisRoutine.bounces:
        # Check that this bounce has angles. May have been skipped by pose estimator
        # if thisBounce.skill_name == 'In/Out Bounce' or thisBounce.skill_name == 'Landing' or thisBounce.angles is None:
        if thisBounce.angles is None:
            continue

        # Start looking
        skillStartTime = time.time()
        thisBounceJointAngles = np.array(json.loads(thisBounce.angles))

        # Compare the angles of this bounce to every other bounce's angles
        # Creates a dict {'bounce':Bounce(), 'totalDistance':0.0}. This makes sorting them convenient.
        bounceMatches = [compareAngles(thisBounceJointAngles, posedBounce.jointAngles, CUTOFF, posedBounce) for posedBounce in posedBounces if posedBounce.routine_id != thisRoutine.id]
        bounceMatches[:] = [bm for bm in bounceMatches if bm is not None]  # remove None results
        bounceMatches = sorted(bounceMatches, key=itemgetter('totalDistance'))

        # Store first 5 results into a TariffMatches object
        timeTaken = time.time() - skillStartTime
        matchedBouncesIds = [bounceMatch['bounce'].id for bounceMatch in bounceMatches[:5]]
        matchedBouncesDistances = [bounceMatch['totalDistance'] for bounceMatch in bounceMatches[:5]]
        tariffMatch = TariffMatches(thisBounce.id, matchedBouncesIds[0], json.dumps(matchedBouncesIds), json.dumps(matchedBouncesDistances), timeTaken)

        tariffedBounces.append(tariffMatch)

    # Add matches to db
    db.add_all(tariffedBounces)
    db.commit()

    timeTaken = time.time() - startTime
    print("Took {:.2f}s = {:.2f}m to estimate the skills in this routine".format(timeTaken, timeTaken / 60))


###############################
# Helper functions used in Tariff_lean & Tariff_verbose
###############################
def getPosedBounces(db, thisRoutineId):
    # Get all bounces that have pose in this level
    posedBounces = db.query(Bounce).filter(
        Bounce.angles != None,
        Bounce.routine_id != thisRoutineId
    ).all()

    for bounce in posedBounces:
        bounce.jointAngles = np.array(json.loads(bounce.angles))

    return posedBounces


def getNumAvailable(posedBounces, thisBounce):
    numAvailableToFind = 0
    for posedBounce in posedBounces:
        if posedBounce.skill_name == thisBounce.skill_name:
            numAvailableToFind += 1
    return numAvailableToFind


def compareAngles(thisAnglesAsCoords, posedAnglesAsCoords, cutoff, posedBounce):
    thisBounceFrameCount = len(thisAnglesAsCoords[0])
    tariffedBounce = {}
    totalDistance = 0
    saveBounceMatch = True
    for i in range(12):  # the number of different angles = 12
        thisJoint = thisAnglesAsCoords[i]
        posedJoint = posedAnglesAsCoords[i]
        if posedJoint.size < 15:
            continue

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
        tariffedBounce['totalDistance'] = int(round(totalDistance, 0))
        tariffedBounce['bounce'] = posedBounce
        return tariffedBounce
    else:
        return None


################################
# Accuracy
################################
def accuracy_of_many(db, routines):
    averageAccuracy = 0
    averageAccuracyIgnoringShape = 0
    averageTariffError = 0

    for routine in routines:
        accuracy, accuracyIgnoringShape, tariffError = tariff_routine_accuracy(db, routine)
        averageAccuracy += accuracy
        averageAccuracyIgnoringShape += accuracyIgnoringShape
        averageTariffError += tariffError

    print('')
    print('Average accuracy {:.2f}%'.format(averageAccuracy / len(routines)))
    print('Average accuracy {:.2f}%'.format(averageAccuracyIgnoringShape / len(routines)))
    print('Average tariff error {:.2f}%'.format(averageTariffError / len(routines)))


def tariff_routine_accuracy(db, routine):
    bounceCount = 0
    correctCount = 0
    correctIgnoringShapeCount = 0
    ignoreStraddlePikeCount = 0

    actualTariff = 0.0
    estimatedTariff = 0.0

    straddlePike = ['Straddle Jump', 'Pike Jump']

    for thisBounce in routine.bounces:
        # Ignore In/Out Bounce and Landings
        if not thisBounce.tariff_match:
            continue

        bounceCount += 1
        thisBounceName = thisBounce.skill_name
        matchedBounce = thisBounce.tariff_match[0].matched_bounce
        matchedBounceName = matchedBounce.skill_name

        actualTariff += thisBounce.getTariff(db)
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
    accuracyIgnoringShape = (correctIgnoringShapeCount / float(bounceCount)) * 100
    accuracyIgnoringStraddlePike = (ignoreStraddlePikeCount / float(bounceCount)) * 100
    tariffDifference = abs(actualTariff - estimatedTariff)
    print("Accuracy: {:.0f}%. Ignoring Straddle <=> Pike {:.0f}%".format(accuracy, accuracyIgnoringStraddlePike))
    print("Actual tariff: {:.1f}, Estimated tariff: {:.1f}, difference: {:.1f}"
          .format(actualTariff, estimatedTariff, tariffDifference))

    return accuracy, accuracyIgnoringShape, tariffDifference
