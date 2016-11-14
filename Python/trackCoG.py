from __future__ import print_function
import numpy as np
import cv2
import matplotlib.pyplot as plt
import json
import sys
import sqlite3

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
showTheStuff = 1

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


def main():
    db = sqlite3.connect(dbPath)
    db.row_factory = sqlite3.Row

    print('\nChoose a comp:')
    for i, c in enumerate(comps):
        print('%d) %s' % (i + 1, c))
    compChoice = 0
    compChoice = comps[compChoice] # comps[readNum(len(comps)) - 1]

    print('\nChoose a level:')
    for i, l in enumerate(levels):
        print('%d) %s' % (i + 1, l))
    levelChoice = 6 #readNum(len(levels)) - 1
    levelChoice = levels[levelChoice]

    selectedVids = None
    if levelChoice == 'All':
        selectedVids = db.execute('SELECT * FROM videos WHERE name LIKE ?', ('%'+compChoice+'%',))
    else:
        selectedVids = db.execute('SELECT * FROM videos WHERE name LIKE ? AND level=?', ('%'+compChoice+'%', levelChoice,))
    selectedVids = selectedVids.fetchall()  # copy everything pointed to by the cursor into an object.

    print('\nChoose a video:')
    for i, v in enumerate(selectedVids):
        str = "{} - {}".format(v['name'], v['level'])
        print('%d) %s' % (i + 1, str))
    vidChoice = 0  # readNum(len(selectedVids)) - 1
    vidChoice = selectedVids[vidChoice]

    #
    # Open the video
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

    if True: # trampoline['top'] == -1:
        print("Warning: Trampoline Top has not yet been set!")
        cap = cv2.VideoCapture(vidPath)

        trampoline['top'] = 305
        while(1):
            _ret, frame = cap.read()
            maskAroundTrampoline = np.zeros(shape=(capHeight, capWidth), dtype=np.uint8)
            maskAroundTrampoline[0:trampoline['top'], int(capWidth * 0.3):int(capWidth * 0.7)] = 255  # [y1:y2, x1:x2]
            frameCropped = cv2.bitwise_and(frame, frame, mask=maskAroundTrampoline)
            cv2.line(frame, (0, trampoline['top']), (capWidth, trampoline['top']), (255, 0, 0), 1)
            cv2.line(frame, (trampoline['center'], 0), (trampoline['center'], capHeight), (0, 255, 0), 1)
            cv2.imshow(vidChoice['name'], frame)
            cv2.imshow("frameCropped", frameCropped)

            k = cv2.waitKey(100)
            print(k)
            if k == ord('u'):
                trampoline['top'] += 1
            elif k == ord('d'):
                trampoline['top'] -= 1
            elif k == ord('q') or k == 27: # ESC
                break
        print("Trampoline Top has been set to {}".format(trampoline['top']))

    # Create windows
    KNNImages = np.zeros(shape=(resizeHeight * 3, resizeWidth, 3), dtype=np.uint8)  # (h * 3, w, CV_8UC3);

    # Create mask around trampoline
    maskAroundTrampoline = np.zeros(shape=(capHeight, capWidth), dtype=np.uint8)  # cv2.CV_8U
    maskAroundTrampoline[0:trampoline['top'], int(capWidth * 0.3):int(capWidth * 0.7)] = 255  # [y1:y2, x1:x2]

    pKNN = cv2.createBackgroundSubtractorKNN()
    pKNN.setShadowValue(0)

    # Center point stuff
    centroids = []
    elipseoids = []
    # plt.ion()
    # plt.axhline(y=capHeight-trampoline['top'], xmin=0, xmax=1000, hold=None)

    # Average background
    print("Averaging background, please wait...")
    cap.set(cv2.CAP_PROP_POS_FRAMES, cap.get(cv2.CAP_PROP_FRAME_COUNT) * 0.5)
    for i in range(framesToAverage):
        ret, frame = cap.read()
        pKNN.apply(frame)

    cap.set(cv2.CAP_PROP_POS_FRAMES, startFrame)
    print("Starting video at frame: ", startFrame)
    while 1:
        ret, frame = cap.read()

        fgMaskKNN = pKNN.apply(frame)
        KNNErodeDilated = erodeDilate(fgMaskKNN)
        KNNErodeDilated = cv2.bitwise_and(KNNErodeDilated, KNNErodeDilated, mask=maskAroundTrampoline)

        if showTheStuff:  # show the thing
            KNNImages[0:resizeHeight, 0:resizeWidth] = cv2.resize(pKNN.getBackgroundImage(), (resizeWidth, resizeHeight))
            cv2.putText(KNNImages, 'Current bg model', (10, 20), font, 0.4, (255, 255, 255))

            fgMaskKNNSmall = cv2.resize(fgMaskKNN, (resizeWidth, resizeHeight))
            KNNImages[resizeHeight:resizeHeight * 2, 0:resizeWidth] = cv2.cvtColor(fgMaskKNNSmall, cv2.COLOR_GRAY2RGB)
            cv2.putText(KNNImages, 'Subtracted', (10, 20 + resizeHeight), font, 0.4, (255, 255, 255))

            KNNErodeDilatedSmall = cv2.resize(KNNErodeDilated, (resizeWidth, resizeHeight))
            KNNImages[resizeHeight * 2:resizeHeight * 3, 0:resizeWidth] = cv2.cvtColor(KNNErodeDilatedSmall, cv2.COLOR_GRAY2RGB)
            cv2.putText(KNNImages, 'ErodeDilated', (10, 20 + resizeHeight * 2), font, 0.4, (255, 255, 255))

            cv2.imshow('frame masked', KNNImages)

        #
        # Find contours in masked image
        #
        _im2, contours, _hierarchy = cv2.findContours(KNNErodeDilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) != 0:
            # Sort so biggest contours first
            contours = sorted(contours, key=cv2.contourArea, reverse=True)

            biggestContour = np.zeros(shape=(capHeight, capWidth, 3), dtype=np.uint8)
            cv2.drawContours(biggestContour, contours, 0, (255, 255, 255), cv2.FILLED)
            biggestContourSmaller = cv2.resize(biggestContour, (int(capWidth * 0.5), int(capHeight * 0.5)))
            cv2.imshow("biggestContour", biggestContourSmaller)

            M = cv2.moments(contours[0])
            if M['m00'] > 0:
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])

                cv2.circle(frame, (cx, cy), 1, (0, 0, 255), -1)
                centroids.append([int(cap.get(cv2.CAP_PROP_POS_FRAMES)), cx, capHeight-cy])
                # plt.scatter(cap.get(cv2.CAP_PROP_POS_FRAMES), capHeight-cy)

                # Fit ellipse
                if len(contours[0]) > 5:
                    ellipse = cv2.fitEllipse(contours[0])
                    elipseoids.append([int(cap.get(cv2.CAP_PROP_POS_FRAMES))] + list(ellipse))
                    cv2.ellipse(frame, ellipse, (0, 255, 0), 2)
                    # plt.scatter(cap.get(cv2.CAP_PROP_POS_FRAMES), cx)  # angle ellipse[2]

                    # plt.pause(0.005)

        #
        # End hard stuff
        #
        # frame[::, 355+80:355+82:] = 0
        # frame = cv2.bitwise_and(frame, frame, mask=maskAroundTrampoline)
        if showTheStuff:
            cv2.imshow('frame', frame)
            frameCropped = cv2.bitwise_and(frame, frame, mask=maskAroundTrampoline)
            cv2.imshow('frameCropped', frameCropped)
        k = cv2.waitKey(waitTime) & 0xff
        if k == 27 or k == 113:
            break

        if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
            # cap.set(cv2.CAP_PROP_POS_FRAMES, startFrame)
            break

    print(elipseoids)
    print(centroids)

    cap.release()
    cv2.destroyAllWindows()


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
