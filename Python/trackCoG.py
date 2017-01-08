from __future__ import print_function

import json
import sqlite3
import sys
from copy import deepcopy

import cv2
import matplotlib.pyplot as plt
import numpy as np

import FindTrampoline
from libs.peakdetect import peakdetect

# https://github.com/opencv/opencv/issues/6055
cv2.ocl.setUseOpenCL(False)

# want to add converted videos to the dictionary
# want to have a option to add tacking vids, priority to vids not yet tracked

# select competition
#     choose to add meta data
#         add skill level
#         add trampoline top/crop region
#         add routines
#         track cog

videosPath = 'C:/Users/psdco/Videos/'
dbPath = 'C:/Users/psdco/Documents/ProjectCode/Web/includes/videos.sqlite3'
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


# # Set the skill level of database entries that don't have one
# def setSkillLevel():
#     # !!!
#     # this function is out of date
#     # !!!
#     dictionary = json.load(open(dictPath, 'r'))
#     for vid in dictionary:
#         if 'level' not in vid:
#             cap = cv2.VideoCapture(videosPath+vid['video_name'])
#             ret, frame = cap.read()
#             cv2.imshow(vid['video_name'], frame)
#             cv2.waitKey(1)
#
#             print('\nChoose a level:')
#             for i, l in enumerate(levels):
#                 print('%d) %s' % (i + 1, l))
#
#             levelChoice = readNum(len(levels)) - 1
#             vid['level'] = levels[levelChoice]
#
#             json.dump(dictionary, open(dictPath, 'w'))
#             cap.release()
#             cv2.destroyAllWindows()


def main():
    db = sqlite3.connect(dbPath)
    db.row_factory = sqlite3.Row

    # Ask the user to select video from database
    videos = askWhichVideoFromDb(db)

    for i, video in enumerate(videos):

        # Open the video file
        cap = openVideo(video['name'])
        fps = cap.get(cv2.CAP_PROP_FPS)

        # Do trampoline top stuff
        video['trampoline'] = json.loads(video['trampoline'])
        if not video['trampoline']:
            video['trampoline'] = FindTrampoline.findTrampolineIfNone(cap, video)

            db.execute("UPDATE videos SET trampoline=? WHERE id=?", (json.dumps(video['trampoline']), video['id'],))
            db.commit()
            print("Trampoline Top has been set to {}".format(json.dumps(video['trampoline'])))

        # Do background subtraction
        video['center_points'] = json.loads(video['center_points'])
        video['ellipses'] = json.loads(video['ellipses'])
        if askToTrackGymnast(video['center_points']):
            centerPoints, ellipses = trackGymnast(cap, video)

            savePoints = askToOverwriteTrackingData(video['center_points'])
            if savePoints:
                print("Saving points...")
                video['center_points'] = centerPoints
                video['ellipses'] = json.loads(json.dumps(ellipses), parse_float=lambda x: int(float(x)))
                db.execute("UPDATE videos SET center_points=?, ellipses=? WHERE id=?", (json.dumps(video['center_points']), json.dumps(video['ellipses']), video['id'],))
                db.commit()
            else:
                print("Data not saved")

        # Calculate bounces
        video['bounces'] = calculateBounces(video, fps)
        db.execute("UPDATE videos SET bounces=? WHERE id=?", (json.dumps(video['bounces']), video['id'],))
        db.commit()

        # Create plot
        plotData(video, fps)

        print("Finished video {} of {}".format(i + 1, len(videos)))

    db.close()
    print("Done")


def visualisePose(cap, video, padding=100):
    # colours = [red, green, blue, yellow, purple, cyan,  red, green, blue, cyan, purple, yellow, red, green] bgr
    # [rfoot, rknee, rhip, lfoot, lknee, lhip, rhand, rerbow, rshoulder, lshoulder, lelbow, lhand, neck, head top]
    colours = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (0, 255, 255), (255, 0, 255), (255, 255, 0), (0, 0, 255),
               (0, 255, 0), (255, 0, 0), (255, 255, 0), (255, 0, 255), (0, 255, 255), (0, 0, 255), (0, 255, 0)]

    # TODO this assumes there is a file with all poses for each frame in it
    posePath = videosPath + video['name'][:-4] + "/pose.npz"
    poses = np.load(posePath)['poses']
    while 1:
        ret, frame = cap.read()
        frameNo = cap.get(cv2.CAP_PROP_POS_FRAMES)
        centerPoints = video['center_points'][frameNo]
        pose = poses[frameNo]
        # pose points are relative to the top left (cx cy = ix iy; 0 0 = ix-100 iy-100) of the 200x200 cropped frame
        # pose given by (0 + posex, 0 + posey) => cx-100+posex, cy-100+posey
        posex = int(centerPoints[0] - padding + pose[0, p_idx])
        posey = int(centerPoints[1] - padding + pose[1, p_idx])

        for p_idx in range(14):
            cv2.circle(frame, (posex, posey), 5, colours[p_idx], thickness=-1)  # -ve thickness = filled

        # Lines between points
        #  Could loop in pairs and link skipping ones that shouldnt be linked.
        # cv2.line(trackPerson,
        #          (int(thisFramePose[0, 0]), int(thisFramePose[1, 0])),
        #          (int(thisFramePose[0, 1]), int(thisFramePose[1, 1])),
        #          colours[0], 4)

        cv2.imshow('frame', frame)


def trackGymnast(cap, video):
    def erodeDilate(image):
        kernel = np.ones((2, 2), np.uint8)
        # erosion = cv2.erode(input, kernel, iterations=1)
        # dilation = cv2.dilate(erosion, kernel, iterations=1)
        opening = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        opening = cv2.dilate(opening, kernel, iterations=10)
        # opening = cv2.dilate(opening, np.ones((3, 3), np.uint8), iterations=10)
        return opening

    print("Starting to track gymnast")
    font = cv2.FONT_HERSHEY_SIMPLEX
    framesToAverage = 100
    startFrame = 0

    # Keyboard stuff
    saveCroppedFrames = False  # output each frame cropped to the performer
    visualise = True  # show windows rendering video
    waitTime = 15  # delay for keyboard input

    # Window vars
    scalingFactor = 0.5
    capWidth = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    capHeight = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    resizeWidth = int(capWidth * scalingFactor)
    resizeHeight = int(capHeight * scalingFactor)
    maskLeftBorder = int(capWidth * 0.35)  # TODO user video['trampoline']['center'] +- trampoline Width
    maskRightBorder = int(capWidth * 0.65)

    # Create array for tiled window
    KNNImages = np.zeros(shape=(resizeHeight, resizeWidth * 3, 3), dtype=np.uint8)  # (h * 3, w, CV_8UC3);

    # Create mask around trampoline
    maskAroundTrampoline = np.zeros(shape=(capHeight, capWidth), dtype=np.uint8)  # cv2.CV_8U
    maskAroundTrampoline[0:video['trampoline']['top'], maskLeftBorder:maskRightBorder] = 255  # [y1:y2, x1:x2]

    # Background extractor. Exclude shadow
    pKNN = cv2.createBackgroundSubtractorKNN()
    pKNN.setShadowValue(0)

    # Average background
    framesToAverageStart = cap.get(cv2.CAP_PROP_FRAME_COUNT) * 0.5
    framesToAverageEnd = cap.get(cv2.CAP_PROP_FRAME_COUNT) * 0.5 + framesToAverage  # Variable only for printing purposes
    print("Averaging frames {:.0f} - {:.0f}, please wait...".format(framesToAverageStart, framesToAverageEnd))
    cap.set(cv2.CAP_PROP_POS_FRAMES, framesToAverageStart)
    for i in range(framesToAverage):
        ret, frame = cap.read()
        pKNN.apply(frame)

    # Reset video to start
    cap.set(cv2.CAP_PROP_POS_FRAMES, startFrame)
    print("\nStarting video at frame {}".format(startFrame))
    print("Press v to toggle showing visuals")
    print("Press ESC/'q' to quit ")

    centerPoints = []
    ellipses = []
    lastContours = None  # used to remember last contour if area goes too small
    while 1:
        ret, frame = cap.read()

        fgMaskKNN = pKNN.apply(frame)
        KNNErodeDilated = erodeDilate(fgMaskKNN)
        KNNErodeDilated = cv2.bitwise_and(KNNErodeDilated, KNNErodeDilated, mask=maskAroundTrampoline)

        if visualise:  # show the thing
            KNNImages[0:resizeHeight, 0:resizeWidth] = cv2.resize(pKNN.getBackgroundImage(), (resizeWidth, resizeHeight))
            cv2.putText(KNNImages, 'Current bg model', (10, 20), font, 0.4, (255, 255, 255))

            fgMaskKNNSmall = cv2.resize(fgMaskKNN, (resizeWidth, resizeHeight))
            KNNImages[0:resizeHeight, resizeWidth:resizeWidth * 2] = cv2.cvtColor(fgMaskKNNSmall, cv2.COLOR_GRAY2RGB)
            cv2.putText(KNNImages, 'Subtracted', (10 + resizeWidth, 20), font, 0.4, (255, 255, 255))

            # this has moved down below
            # KNNErodeDilatedSmall = cv2.resize(KNNErodeDilated, (resizeWidth, resizeHeight))
            # KNNImages[resizeHeight * 2:resizeHeight * 3, 0:resizeWidth] = cv2.cvtColor(KNNErodeDilatedSmall, cv2.COLOR_GRAY2RGB)
            # cv2.putText(KNNImages, 'ErodeDilated', (10, 20 + resizeHeight * 2), font, 0.4, (255, 255, 255))

        #
        # Find contours in masked image
        #
        _im2, contours, _hierarchy = cv2.findContours(deepcopy(KNNErodeDilated), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) != 0:
            # TODO
            # Find the biggest contour first but when you're sure you have the person
            # Then find the contour closest to that one and track that way. Prevent jumping around when person disappears.
            # Also do something about combining legs. Check the distance of every point in the contour to every point int the closest contour.
            # If the distance between then is small enough, combine them.

            # Sort DESC, so biggest contour's first
            contours = sorted(contours, key=cv2.contourArea, reverse=True)

            area = cv2.contourArea(contours[0])
            # print(area)
            # If contour is less than given area, replace it with previous contour
            if area < 800 and lastContours is not None:
                contours = lastContours
            else:
                lastContours = contours

            if visualise:
                # KNNErodeDilated has all the contours of interest
                biggestContour = cv2.cvtColor(KNNErodeDilated, cv2.COLOR_GRAY2RGB)
                personMask = np.zeros(shape=(capHeight, capWidth), dtype=np.uint8)
                cv2.drawContours(personMask, contours, 0, 255, cv2.FILLED)
                # Draw the biggest one in red
                cv2.drawContours(biggestContour, contours, 0, (0, 0, 255), cv2.FILLED)
                # Resize and show it
                biggestContourSmaller = cv2.resize(biggestContour, (resizeWidth, resizeHeight))
                KNNImages[0:resizeHeight, resizeWidth * 2:resizeWidth * 3] = biggestContourSmaller
                cv2.putText(KNNImages, 'ErodeDilated', (10 + resizeWidth * 2, 20), font, 0.4, (255, 255, 255))

                cv2.imshow('KNNImages', KNNImages)

            M = cv2.moments(contours[0])
            if M['m00'] > 0:
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])

                cv2.circle(frame, (cx, cy), 1, (0, 0, 255), -1)
                centerPoints.append([int(cap.get(cv2.CAP_PROP_POS_FRAMES)), cx, capHeight - cy])

                # Fit ellipse
                frameNoEllipse = deepcopy(frame)
                if len(contours[0]) > 5:  # ellipse requires contour to have at least 5 points
                    ellipse = cv2.fitEllipse(contours[0])
                    # frame, major, minor, angle
                    ellipses.append([int(cap.get(cv2.CAP_PROP_POS_FRAMES))] + list(ellipse))
                    cv2.ellipse(frame, ellipse, color=(0, 255, 0), thickness=2)
                else:
                    print("Couldn't find enough points for ellipse")

                x1, x2, y1, y2 = boundingSquare(capHeight, capWidth, cx, cy)
                if visualise:
                    # finerPersonMask = cv2.bitwise_and(fgMaskKNN, fgMaskKNN, mask=personMask)
                    # personMasked = cv2.bitwise_and(frameNoEllipse, frameNoEllipse, mask=finerPersonMask)
                    trackPerson = frameNoEllipse[y1:y2, x1:x2]  # was personMasked. now it's not
                    cv2.imshow('track', trackPerson)

                # Save frames
                if saveCroppedFrames:
                    imgName = "C:/Users/psdco/Videos/{}/frame {:.0f}.png".format(video['name'][:-4], cap.get(cv2.CAP_PROP_POS_FRAMES))
                    print("Writing frame to {}".format(imgName))
                    ret = cv2.imwrite(imgName, trackPerson)
                    if not ret:
                        print("Couldn't write image {}\nAbort!".format(imgName))
                        exit()

            else:
                print("Skipping center point. No moment")

        #
        # End stuff
        #
        if visualise:
            cv2.imshow('frame ', frame)
            # frameCropped = cv2.bitwise_and(frame, frame, mask=maskAroundTrampoline)
            # cv2.imshow('frameCropped ', frameCropped)

        k = cv2.waitKey(waitTime) & 0xff
        if k == ord('v'):
            visualise = not visualise
            if not visualise:  # destroy any open windows
                cv2.destroyAllWindows()
        elif k == ord('q') or k == 27:  # q/ESC
            print("Exiting...")
            exit()

        # Finish playing the video when we get to the end.
        if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
            # cap.set(cv2.CAP_PROP_POS_FRAMES, startFrame)
            break

    cap.release()
    cv2.destroyAllWindows()

    return centerPoints, ellipses


def boundingSquare(capHeight, capWidth, cx, cy):
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
    return x1, x2, y1, y2


def plotData(video, fps):
    print("\nStarting plotting...")
    f, axarr = plt.subplots(3, sharex=True)

    # Plot bounces
    # center_points consists of [frame num, x, y]
    x_frames = [pt[0]/fps for pt in video['center_points']]
    y_travel = [pt[1] for pt in video['center_points']]
    y_height = [pt[2] for pt in video['center_points']]

    peaks_x = [[bounce['startFrame']/fps, bounce['maxHeightFrame']/fps] for bounce in video['bounces']]
    peaks_y = [[bounce['startHeightInPixels'], bounce['maxHeightInPixels']] for bounce in video['bounces']]

    axarr[0].set_title("Height")
    axarr[0].plot(x_frames, y_height, color="g")
    axarr[0].plot(peaks_x, peaks_y, 'r+')
    axarr[0].set_ylabel('Height (Pixels)')

    #
    # Plot bounce travel
    #
    axarr[1].set_title("Travel")
    axarr[1].set_ylabel('Rightwardness (Pixels)')
    axarr[1].scatter(x_frames, y_travel, color="g")
    axarr[1].axhline(y=video['trampoline']['center'], xmin=0, xmax=1000, c="blue")
    axarr[1].axhline(y=video['trampoline']['center'] + 80, xmin=0, xmax=1000, c="red")
    axarr[1].axhline(y=video['trampoline']['center'] - 80, xmin=0, xmax=1000, c="red")

    #
    # Plot ellipsoid's angles
    #
    x_frames = np.array([pt[0]/fps for pt in video['ellipses']])
    y_angle = np.array([pt[3] for pt in video['ellipses']])
    # Changes angles
    y_angle += 90
    y_angle %= 180
    y_angle = np.unwrap(y_angle, discont=90, axis=0)
    axarr[2].scatter(x_frames, y_angle)
    axarr[2].set_title("Angle")
    axarr[2].set_ylabel('Angle (deg)')
    axarr[2].set_xlabel('Time (s)')

    # axarr[0].set_xlim(xmin=-10)
    # axarr[1].set_xlim(xmin=-10)
    # axarr[2].set_xlim(xmin=-10)
    plt.show()


def calculateBounces(video, fps):
    npCenterPoints = np.array(video['center_points'])

    # npCenterPoints consists of [frame num, x, y]
    x = npCenterPoints[:, 0]
    y = npCenterPoints[:, 2]
    maxima, minima = peakdetect(y, x, lookahead=8, delta=20)

    bounces = []
    for i in range(len(minima) - 1):
        thisBedHit = minima[i]
        nextBedHit = minima[i + 1]
        jumpMaxHeight = maxima[i]
        bounces.append({
            'startFrame': thisBedHit['x'],
            'endFrame': nextBedHit['x'],
            'maxHeightFrame': jumpMaxHeight['x'],
            'startHeightInPixels': thisBedHit['y'],
            'endHeightInPixels': nextBedHit['y'],
            'maxHeightInPixels': jumpMaxHeight['y'],
            'startTime': round(float(thisBedHit['x'] / fps), 2),
            'endTime': round(float(nextBedHit['x'] / fps), 2),
            'name': "",
        })

    return bounces


def askWhichVideoFromDb(db):
    def dict_gen(result):
        dictItems = []
        for item in result:
            dictItems.append(dict(item))
        return dictItems

    print('\nTrack all untracked videos? [y/n]')
    if inputWasYes():
        # videos = db.execute("SELECT * FROM videos WHERE center_points='[]'")
        videos = db.execute("SELECT * FROM videos WHERE bounces='[]'")
        return dict_gen(videos.fetchall())  # copy everything pointed to by the cursor into an object.

    print('\nChoose a comp:')
    for i, c in enumerate(comps):
        print('%d) %s' % (i + 1, c))
    compChoice = 1  # readNum(len(comps))
    compChoice = comps[compChoice - 1]

    print('\nChoose a level:')
    for i, l in enumerate(levels):
        print('%d) %s' % (i + 1, l))
    levelChoice = 7  # readNum(len(levels))
    levelChoice = levels[levelChoice - 1]

    if levelChoice == 'All':
        selectedVids = db.execute("SELECT * FROM videos WHERE name LIKE ?", ('%' + compChoice + '%',))
    else:
        selectedVids = db.execute("SELECT * FROM videos WHERE name LIKE ? AND level=?", ('%' + compChoice + '%', levelChoice,))
    selectedVids = selectedVids.fetchall()  # copy everything pointed to by the cursor into an object.

    print('\nChoose a video:')
    for i, v in enumerate(selectedVids):
        str = "{} - {}".format(v['name'], v['level'])
        print('%d) %s' % (i + 1, str))
    vidChoice = 1  # readNum(len(selectedVids))
    vidRow = selectedVids[vidChoice - 1]

    return dict_gen([vidRow])


def askToTrackGymnast(centerPoints):
    if centerPoints:
        print("Track points found, do you want to track anyway? [y/n]")
        return inputWasYes()
    else:
        return True


def askToOverwriteTrackingData(centerPoints):
    if centerPoints:
        print("Track points found, do you want to overwrite? [y/n]")
        return inputWasYes()
    else:
        return True


def openVideo(videoName):
    pathToVideo = videosPath + videoName
    print("\nOpening " + pathToVideo)
    cap = cv2.VideoCapture(pathToVideo)
    if not cap.isOpened():
        print('Unable to open video file: %s', pathToVideo)
    return cap


# Random Helper functions
def inputWasYes():
    input = raw_input('> ')  # in python 2, input = eval(raw_input("> "))
    # Returns true for y or Y. Will return false for any other input
    return input.lower() == 'y'


def readNum(limitMax, limitMin=0):
    while (1):
        print('> ', end="")
        num = sys.stdin.readline()
        try:
            num = int(num)
        except Exception:
            print('Enter a number. \'%s\' is not an int' % (num[0:-1]))
            continue

        if (num < limitMin or num > limitMax):
            print('Enter a number between 1 and %s. \'%d\' is out of bounds' % (limitMax, num))
        else:
            break

    return num


def parseNum(s):
    try:
        return int(s)
    except ValueError:
        return 0


if __name__ == '__main__':
    main()
