from __future__ import print_function
import numpy as np
import cv2
import matplotlib.pyplot as plt
import json
import sys
import sqlite3
from peakdetect import peakdetect
from copy import deepcopy


# https://github.com/opencv/opencv/issues/6055
cv2.ocl.setUseOpenCL(False)

# Window vars
scalingFactor = 0.5

# Mask vars
startFrame = 0
framesToAverage = 100
x = 0
y = 0

# Keyboard vars
waitTime = 20


font = cv2.FONT_HERSHEY_SIMPLEX

# want to add converted videos to the dictionary
# want to have a option to add tacking vids, priority of ones that haven't got it yet.

# select competition
#     choose to add meta data
#         add skill level
#         add trampoline top/crop region
#         add routines
#         track cog


dictPath = 'C:/Users/psdco/Documents/Project Code/dictionary.json'
dbPath = 'C:/Users/psdco/Documents/Project Code/videos.db'
comps = [
    'Trainings',
    'Inhouse'
]
levels = [
    'Novice',
    'Intermediate',
    'Intervanced',
    'Advanced',
    'Elite',
    'idk',
    "All"
]

def skillLevel():
    # !!!
    # this function is out of date
    # !!!
    dictionary = json.load(open(dictPath, 'r'))
    for vid in dictionary:
        if 'level' not in vid:
            cap = cv2.VideoCapture("C:/Users/psdco/Videos/"+vid['video_name'])
            ret, frame = cap.read()
            cv2.imshow(vid['video_name'], frame)
            cv2.waitKey(1)

            print('\nChoose a level:')
            for i, l in enumerate(levels):
                print('%d) %s' % (i + 1, l))

            levelChoice = readNum(len(levels)) - 1
            vid['level'] = levels[levelChoice]

            json.dump(dictionary, open(dictPath, 'w'))
            cap.release()
            cv2.destroyAllWindows()


def readNum(limitMax, limitMin=0):
    while (1):
        print('> ', end="")
        num = sys.stdin.readline()
        try:
            num = int(num)
        except Exception:
            print('Enter a number. \'%s\' is not an int' % (num[0:-1]))
            continue

        if (num < 0 or num > limitMax):
            print('Enter a number between 1 and %s. \'%d\' is out of bounds' % (limitMax, num))
        else:
            break

    return num


def trampolineTopBestGuess(img):
    coloursToShow = [np.array([152, 82, 83], dtype=np.uint8), np.array([94, 55, 47], dtype=np.uint8), np.array([60, 46, 40], dtype=np.uint8), np.array([132, 86, 18], dtype=np.uint8), np.array([131, 79, 43], dtype=np.uint8), np.array([117, 62, 31], dtype=np.uint8), np.array([109, 64, 31], dtype=np.uint8), np.array([106, 62, 33], dtype=np.uint8), np.array([140, 79, 45], dtype=np.uint8), np.array([93, 57, 33], dtype=np.uint8), np.array([103, 60, 41], dtype=np.uint8), np.array([98, 61, 39], dtype=np.uint8), np.array([116, 67, 45], dtype=np.uint8), np.array([130, 73, 47], dtype=np.uint8), np.array([90, 58, 52], dtype=np.uint8), np.array([136, 74, 50], dtype=np.uint8), np.array([109, 62, 31], dtype=np.uint8), np.array([109, 62, 31], dtype=np.uint8), np.array([181, 92, 42], dtype=np.uint8), np.array([144, 53, 22], dtype=np.uint8), np.array([166, 68, 34], dtype=np.uint8), np.array([211, 102, 46], dtype=np.uint8), np.array([119, 49, 26], dtype=np.uint8),
                     np.array([210, 99, 51], dtype=np.uint8), np.array([213, 106, 55], dtype=np.uint8), np.array([195, 97, 57], dtype=np.uint8), np.array([193, 101, 54], dtype=np.uint8), np.array([166, 68, 38], dtype=np.uint8), np.array([144, 60, 34], dtype=np.uint8), np.array([78, 25, 15], dtype=np.uint8), np.array([132, 61, 28], dtype=np.uint8), np.array([52, 23, 16], dtype=np.uint8), np.array([191, 124, 121], dtype=np.uint8), np.array([123, 64, 55], dtype=np.uint8), np.array([189, 118, 128], dtype=np.uint8), np.array([152, 82, 83], dtype=np.uint8), np.array([180, 112, 119], dtype=np.uint8), np.array([120, 57, 67], dtype=np.uint8), np.array([127, 64, 74], dtype=np.uint8), np.array([146, 92, 21], dtype=np.uint8), np.array([143, 90, 21], dtype=np.uint8), np.array([130, 82, 19], dtype=np.uint8), np.array([83, 26, 0], dtype=np.uint8), np.array([231, 174, 141], dtype=np.uint8), np.array([197, 162, 143], dtype=np.uint8), np.array([214, 182, 168], dtype=np.uint8),
                     np.array([202, 160, 127], dtype=np.uint8), np.array([183, 131, 74], dtype=np.uint8), np.array([214, 156, 76], dtype=np.uint8), np.array([230, 172, 89], dtype=np.uint8), np.array([169, 109, 0], dtype=np.uint8), np.array([172, 110, 3], dtype=np.uint8), np.array([177, 110, 5], dtype=np.uint8), np.array([173, 106, 3], dtype=np.uint8), np.array([169, 107, 3], dtype=np.uint8), np.array([176, 110, 9], dtype=np.uint8), np.array([184, 118, 15], dtype=np.uint8), np.array([181, 117, 3], dtype=np.uint8), np.array([163, 98, 0], dtype=np.uint8), np.array([192, 116, 72], dtype=np.uint8), np.array([216, 135, 89], dtype=np.uint8), np.array([116, 71, 15], dtype=np.uint8), np.array([168, 116, 33], dtype=np.uint8), np.array([97, 33, 0], dtype=np.uint8), np.array([96, 32, 0], dtype=np.uint8), np.array([98, 33, 0], dtype=np.uint8), np.array([93, 27, 0], dtype=np.uint8), np.array([101, 34, 0], dtype=np.uint8), np.array([98, 35, 0], dtype=np.uint8),
                     np.array([216, 157, 107], dtype=np.uint8), np.array([214, 164, 119], dtype=np.uint8), np.array([194, 136, 87], dtype=np.uint8), np.array([212, 149, 95], dtype=np.uint8), np.array([194, 125, 66], dtype=np.uint8), np.array([160, 86, 32], dtype=np.uint8), np.array([173, 109, 6], dtype=np.uint8)]

    mask = np.zeros((img.shape[0], img.shape[1]), np.uint8)
    for c in coloursToShow:
        lower = c - 20
        lower.clip(0)  # lower[lower<0] = 0
        upper = c + 20
        upper.clip(max=255)  # upper[upper>255] = 255
        thisMask = cv2.inRange(img, lower, upper)
        mask = mask | thisMask

    imgMasked = cv2.bitwise_and(img, img, mask=mask)

    return findBlue(imgMasked, mask)


def findBlue(img, mask):
    binmask = mask/255  # binary mask
    rowSums = np.sum(binmask, 1)  # sum across axis 1 = row
    # Get the start and end index of a clump of rows that have more than 30 unmasked (blue) pixels in them.
    blueRows = []
    insideClump = -1
    for i in range(0, rowSums.size):
        if insideClump == -1 and rowSums[i] > 30:
            insideClump = i
        elif insideClump > -1 and rowSums[i] < 30:
            blueRows.append([insideClump, i])
            insideClump = -1

    # Find if there are any horizontal breaks by summing vertically
    blueAreas = []
    for i in range(0, len(blueRows)):
        y1 = blueRows[i][0]
        y2 = blueRows[i][1]
        colSums = np.sum(binmask[y1:y2], 0)  # sum axis 0, columns
        # print colSums
        insideClump = -1
        for k in range(0, colSums.size):
            colVal = colSums[k]
            if insideClump == -1 and colVal > 2:
                insideClump = k
            elif insideClump > -1 and (colVal < 2 or k == colSums.size-1):
                # y1 y2 x1 x2
                if k - insideClump > 10:  # obj more than 10 pixels wide
                    blueAreas.append([y1, y2, insideClump, k])
                insideClump = -1

    # Show the areas found
    for i in range(0, len(blueAreas)):
        y1 = blueAreas[i][0]
        y2 = blueAreas[i][1]
        x1 = blueAreas[i][2]
        x2 = blueAreas[i][3]
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 1)
    cv2.imshow("Best Guess ", img)

    # Find the largest area and assume that is the trampoline
    biggestArea = 0
    trampolineTop = 0
    for i in range(0, len(blueAreas)):
        y1 = blueAreas[i][0]
        y2 = blueAreas[i][1]
        x1 = blueAreas[i][2]
        x2 = blueAreas[i][3]

        w = x1 - x2
        h = y1 - y2
        area = w * h
        if area > biggestArea:
            biggestArea = area
            trampolineTop = min(y1, y2)  # the lower of the two points will be the top because of (0, 0) top left

    return trampolineTop


def main():
    db = sqlite3.connect(dbPath)
    db.row_factory = sqlite3.Row

    print('\nChoose a comp:')
    for i, c in enumerate(comps):
        print('%d) %s' % (i + 1, c))
    compChoice = 1  # readNum(len(comps))
    compChoice = comps[compChoice - 1]

    print('\nChoose a level:')
    for i, l in enumerate(levels):
        print('%d) %s' % (i + 1, l))
    levelChoice = 7 #readNum(len(levels))
    levelChoice = levels[levelChoice - 1]

    if levelChoice == 'All':
        selectedVids = db.execute('SELECT * FROM videos WHERE name LIKE ?', ('%'+compChoice+'%',))
    else:
        selectedVids = db.execute('SELECT * FROM videos WHERE name LIKE ? AND level=?', ('%'+compChoice+'%', levelChoice,))
    selectedVids = selectedVids.fetchall()  # copy everything pointed to by the cursor into an object.

    print('\nChoose a video:')
    for i, v in enumerate(selectedVids):
        str = "{} - {}".format(v['name'], v['level'])
        print('%d) %s' % (i + 1, str))
    vidChoice = 1# readNum(len(selectedVids))
    vidChoice = selectedVids[vidChoice-1]

    #
    # Open the video file
    vidPath = "C:/Users/psdco/Videos/{}".format(vidChoice['name'])
    cap = cv2.VideoCapture(vidPath)
    if not cap.isOpened():
        print("Unable to open video file: %s", vidPath)

    capWidth = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    capHeight = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    resizeWidth = int(capWidth * scalingFactor)
    resizeHeight = int(capHeight * scalingFactor)

    #
    # Do trampoline top stuff
    trampoline = json.loads(vidChoice['trampoline'])

    if trampoline['top'] == -1:
        print("Trampoline Top has not yet been set!")
        print("Use the arrow keys to adjust the crosshairs.\nPress ENTER to save, 'c' to continue without save, and ESC/'q' to quit,")
        cap = cv2.VideoCapture(vidPath)
        _ret, frame = cap.read()

        trampoline['top'] = trampolineTopBestGuess(frame)
        trampoline['center'] = capWidth/2
        while 1:
            _ret, frame = cap.read()

            maskAroundTrampoline = np.zeros(shape=(capHeight, capWidth), dtype=np.uint8)
            maskAroundTrampoline[0:trampoline['top'], int(capWidth * 0.3):int(capWidth * 0.7)] = 255  # [y1:y2, x1:x2]
            frameCropped = cv2.bitwise_and(frame, frame, mask=maskAroundTrampoline)

            cv2.line(frame, (0, trampoline['top']), (capWidth, trampoline['top']), (0, 255, 0), 1)
            cv2.line(frame, (trampoline['center'], 0), (trampoline['center'], capHeight), (0, 255, 0), 1)

            cv2.imshow(vidChoice['name']+' ', frame)
            cv2.imshow(vidChoice['name']+" frameCropped ", frameCropped)

            k = cv2.waitKey(100)
            if k == 2490368:  # up
                trampoline['top'] -= 1
            elif k == 2621440:  # down
                trampoline['top'] += 1
            elif k == 2424832:  # left
                trampoline['center'] -= 1
            elif k == 2555904:  # right
                trampoline['center'] += 1
            elif k == ord('\n') or k == ord('\r'):  # return/enter key
                db.execute("UPDATE `videos` SET `trampoline`=? WHERE id=?", (json.dumps(trampoline), vidChoice['id'],))
                db.commit()
                print("Trampoline Top has been set to {}".format(json.dumps(trampoline)))
                break
            elif k == ord('c'):  # ESC
                print("Trampoline data not updated, continuing to tracking")
                break
            elif k == ord('q') or k == 27:  # ESC
                print("Exiting...")
                exit()

            # Loop until keypress
            if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
                cap.set(cv2.CAP_PROP_POS_FRAMES, startFrame)

        cv2.destroyAllWindows()

    #
    # Do background detection
    #
    centerPoints = []
    ellipses = []
    if vidChoice['center_points'] != "[]":
        print("Track points found, do you want to continue to track anyway? [y/n]")
        track = "n"  # raw_input('> ')  # in python 2, input = eval(raw_input)
        track = (track == 'y')
        dontSavePoints = True
        if not track:
            centerPoints = json.loads(vidChoice['center_points'])
            ellipses = json.loads(vidChoice['ellipses'])

    if vidChoice['center_points'] == "[]":
        print("Gymnast has not yet been tracked")
        track = True

    if track:
        print("Press s to toggle visuals, 'c' to continue without saving, and ESC/'q' to quit")

        # Create windows
        KNNImages = np.zeros(shape=(resizeHeight, resizeWidth * 3, 3), dtype=np.uint8)  # (h * 3, w, CV_8UC3);

        # Create mask around trampoline
        maskAroundTrampoline = np.zeros(shape=(capHeight, capWidth), dtype=np.uint8)  # cv2.CV_8U
        maskAroundTrampoline[0:trampoline['top'], int(capWidth * 0.3):int(capWidth * 0.65)] = 255  # [y1:y2, x1:x2]

        pKNN = cv2.createBackgroundSubtractorKNN()
        pKNN.setShadowValue(0)

        # Center point stuff

        # plt.ion()
        # plt.axhline(y=capHeight-trampoline['top'], xmin=0, xmax=1000, hold=None)

        dontSavePoints = False
        showTheStuff = True

        # Average background
        print("Averaging background, please wait...")
        cap.set(cv2.CAP_PROP_POS_FRAMES, cap.get(cv2.CAP_PROP_FRAME_COUNT) * 0.5)
        for i in range(framesToAverage):
            ret, frame = cap.read()
            pKNN.apply(frame)

        cap.set(cv2.CAP_PROP_POS_FRAMES, startFrame)
        print("Starting video at frame {}".format(startFrame))
        print("Press s to toggle showing stuff")
        lastContours = None
        while 1:
            ret, frame = cap.read()

            fgMaskKNN = pKNN.apply(frame)
            KNNErodeDilated = erodeDilate(fgMaskKNN)
            KNNErodeDilated = cv2.bitwise_and(KNNErodeDilated, KNNErodeDilated, mask=maskAroundTrampoline)

            if showTheStuff:  # show the thing
                KNNImages[0:resizeHeight, 0:resizeWidth] = cv2.resize(pKNN.getBackgroundImage(), (resizeWidth, resizeHeight))
                cv2.putText(KNNImages, 'Current bg model', (10, 20), font, 0.4, (255, 255, 255))

                fgMaskKNNSmall = cv2.resize(fgMaskKNN, (resizeWidth, resizeHeight))
                KNNImages[0:resizeHeight, resizeWidth:resizeWidth*2] = cv2.cvtColor(fgMaskKNNSmall, cv2.COLOR_GRAY2RGB)
                cv2.putText(KNNImages, 'Subtracted', (10+resizeWidth, 20), font, 0.4, (255, 255, 255))

                # this has moved down below
                # KNNErodeDilatedSmall = cv2.resize(KNNErodeDilated, (resizeWidth, resizeHeight))
                # KNNImages[resizeHeight * 2:resizeHeight * 3, 0:resizeWidth] = cv2.cvtColor(KNNErodeDilatedSmall, cv2.COLOR_GRAY2RGB)
                # cv2.putText(KNNImages, 'ErodeDilated', (10, 20 + resizeHeight * 2), font, 0.4, (255, 255, 255))

            #
            # Find contours in masked image
            #
            KNNErodeDilatedcopy = deepcopy(KNNErodeDilated)
            _im2, contours, _hierarchy = cv2.findContours(KNNErodeDilatedcopy, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            if len(contours) != 0:
                #  TODO
                # Find the biggest contour first but when you're sure you have the person
                # Then find the contour closest to that one and track that way. Prevent jumping around when person disappears.
                # Also do something about combining legs. Check the distance of every point in the contour to every point int the closest contour.
                # If the distance between then is small enough, combine them.

                # Sort so biggest contours first
                contours = sorted(contours, key=cv2.contourArea, reverse=True)

                area = cv2.contourArea(contours[0])
                # print(area)
                # If contour is less than given area, replace it with previous contour
                if area < 800 and lastContours is not None:
                    contours = lastContours
                else:
                    lastContours = contours

                if showTheStuff:
                    # KNNErodeDilated has all the contours of interest
                    biggestContour = cv2.cvtColor(KNNErodeDilated, cv2.COLOR_GRAY2RGB)
                    personMask = np.zeros(shape=(capHeight, capWidth), dtype=np.uint8)
                    cv2.drawContours(personMask, contours, 0, 255, cv2.FILLED)
                    # Draw the biggest one in red
                    cv2.drawContours(biggestContour, contours, 0, (0, 0, 255), cv2.FILLED)
                    # Resize and show it
                    biggestContourSmaller = cv2.resize(biggestContour, (resizeWidth, resizeHeight))
                    KNNImages[0:resizeHeight, resizeWidth*2:resizeWidth*3] = biggestContourSmaller
                    cv2.putText(KNNImages, 'ErodeDilated', (10 + resizeWidth * 2, 20), font, 0.4, (255, 255, 255))

                    cv2.imshow('KNNImages', KNNImages)


                M = cv2.moments(contours[0])
                if M['m00'] > 0:
                    cx = int(M['m10'] / M['m00'])
                    cy = int(M['m01'] / M['m00'])

                    cv2.circle(frame, (cx, cy), 1, (0, 0, 255), -1)
                    centerPoints.append([int(cap.get(cv2.CAP_PROP_POS_FRAMES)), cx, capHeight-cy])
                    # plt.scatter(cap.get(cv2.CAP_PROP_POS_FRAMES), capHeight-cy)

                    # Fit ellipse
                    if len(contours[0]) > 5:
                        ellipse = cv2.fitEllipse(contours[0])
                        ellipses.append([int(cap.get(cv2.CAP_PROP_POS_FRAMES))] + list(ellipse))
                        frameNoEllipse = deepcopy(frame)
                        cv2.ellipse(frame, ellipse, (0, 255, 0), 2)
                        # plt.scatter(cap.get(cv2.CAP_PROP_POS_FRAMES), cx)  # angle ellipse[2]
                        # plt.pause(0.005)

                if showTheStuff:
                    padding = 100
                    y1 = cy - padding
                    y2 = cy + padding
                    x1 = cx - padding
                    x2 = cx + padding
                    if y2 > capHeight:
                        y2 = capHeight
                    if y1 < 0:
                        y1 = 0
                    if x2 > capWidth:
                        x2 = capWidth
                    if x1 < 0:
                        x1 = 0
                    finerPersonMask = cv2.bitwise_and(fgMaskKNN, fgMaskKNN, mask=personMask)
                    personMasked = cv2.bitwise_and(frameNoEllipse, frameNoEllipse, mask=finerPersonMask)
                    trackPerson = personMasked[y1:y2, x1:x2]
                    cv2.imshow('track', trackPerson)

            #
            # End stuff
            #
            if showTheStuff:
                cv2.imshow('frame ', frame)
                # frameCropped = cv2.bitwise_and(frame, frame, mask=maskAroundTrampoline)
                # cv2.imshow('frameCropped ', frameCropped)

            k = cv2.waitKey(waitTime) & 0xff
            if k == ord('s'):
                showTheStuff = not showTheStuff
                if not showTheStuff:  # destroy any open windows
                    cv2.destroyAllWindows()
            elif k == ord('c'):  # ESC
                print("Trampoline data not updated, continuing to graphing")
                dontSavePoints = True
                break
            elif k == ord('q') or k == 27:  # ESC
                print("Exiting...")
                exit()

            if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
                # cap.set(cv2.CAP_PROP_POS_FRAMES, startFrame)
                break
        cap.release()
        cv2.destroyAllWindows()

        if not dontSavePoints:
            print("Saving points...")
            db.execute("UPDATE `videos` SET `center_points`=?, `ellipses`=? WHERE id=?", (json.dumps(centerPoints), json.dumps(ellipses), vidChoice['id'],))
            db.commit()
        else:
            print("Data not saved")

    #
    # Create plot
    print("Starting plotting...")
    f, axarr = plt.subplots(3, sharex=True)

    # Plot bounces
    # Plot bounce height against frame num
    npCenterPoints = np.array(centerPoints)
    trampoline['top'] = capHeight - trampoline['top']
    # npCenterPoints consists of [frame num, x, y]
    x = npCenterPoints[:, 0]
    y = npCenterPoints[:, 2]

    maxima, minima = peakdetect(y, x, 3, 30)
    peaks = maxima + minima  # concat the two

    bounces = []
    bounceIndex = 11
    for i in range(1, len(minima)):
        thisPt = minima[-i]
        prevPt = minima[-(i - 1)]  # previous point in time is next point in the list because working backwards through list
        midlPt = maxima[-i]
        bodyLanding = 1 if (thisPt['y'] < trampoline['top'] + 20) else 0
        bounce = {
            'end': (thisPt['x'], thisPt['y']),
            'start': (prevPt['x'], prevPt['y']),
            'maxHeight': (midlPt['x'], midlPt['y']),
            'index': bounceIndex,
            'isBodyLanding': bodyLanding,
            'title': "",
        }
        bounces.append(bounce)
        bounceIndex -= 1

    # print(json.dumps(bounces[::-1]))  # print reversed

    peaksx = [pt['x'] for pt in peaks]
    peaksy = [pt['y'] for pt in peaks]

    # Two subplots, the axes array is 1-d
    # axarr[0].set_title("<0 in bounces,  0 tap,  >0 skills,  >10 out bounce.  red = body landing")
    axarr[0].set_title("Height")
    axarr[0].plot(x, y, color="g")
    axarr[0].plot(peaksx, peaksy, 'r+')
    axarr[0].set_ylabel('Height (Pixels)')
    axarr[0].axhline(y=trampoline['top'], xmin=0, xmax=1000, c="blue")
    # for bounce in bounces:
    #     c = "r" if bounce['isBodyLanding'] else "black"
    #     c = c if (bounce['index'] >= 1 and bounce['index'] <= 10) else "grey"
    #     axarr[0].annotate(bounce['index'],
    #                       xy=(bounce['maxHeight'][0], bounce['maxHeight'][1]),
    #                       xytext=(bounce['maxHeight'][0], bounce['maxHeight'][1] + 10), color=c)

    #
    # Plot bounce travel
    #
    x = npCenterPoints[:, 0]
    y = npCenterPoints[:, 1]

    axarr[1].set_title("Travel")
    axarr[1].set_ylabel('Rightwardness (Pixels)')
    axarr[1].scatter(x, y, color="g")
    axarr[1].axhline(y=trampoline['center'], xmin=0, xmax=1000, c="blue")
    axarr[1].axhline(y=trampoline['center'] + 80, xmin=0, xmax=1000, c="red")
    axarr[1].axhline(y=trampoline['center'] - 80, xmin=0, xmax=1000, c="red")

    #
    # Plot ellipsoid's angles
    #
    x = np.array([pt[0] for pt in ellipses])
    y = np.array([pt[3] for pt in ellipses])
    # Changes angles
    y += 90
    y %= 180
    y = np.unwrap(y, discont=90, axis=0)

    axarr[2].scatter(x, y)
    # axarr[2].set_title("0deg Ground plane. 90deg is standing up.")
    axarr[2].set_title("Angle")
    axarr[2].set_ylabel('Angle (deg)')

    axarr[2].set_xlabel('Time (s)')

    axarr[0].set_xlim(xmin=-10)
    axarr[1].set_xlim(xmin=-10)
    axarr[2].set_xlim(xmin=-10)

    f.canvas.draw()

    labels = [num(item.get_text()) for item in axarr[2].get_xticklabels()]
    labels = np.array(labels)/ 25
    axarr[2].set_xticklabels(labels)


    plt.show()

def num(s):
    try:
        return int(s)
    except ValueError:
        return 0

def erodeDilate(input):
    kernel = np.ones((2, 2), np.uint8)
    # erosion = cv2.erode(input, kernel, iterations=1)
    # dilation = cv2.dilate(erosion, kernel, iterations=1)
    opening = cv2.morphologyEx(input, cv2.MORPH_OPEN, kernel)
    opening = cv2.dilate(opening, kernel, iterations=10)
    # opening = cv2.dilate(opening, np.ones((3, 3), np.uint8), iterations=10)
    return opening

# def drawBoundingBox():

if __name__ == '__main__':
    main()
    # skillLevel()

# Save a video http://docs.opencv.org/3.1.0/dd/d43/tutorial_py_video_display.html