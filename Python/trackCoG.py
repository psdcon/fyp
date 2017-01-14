from __future__ import print_function

import json
import sqlite3
import sys
from copy import deepcopy

import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from scipy import signal

import FindTrampoline
from libs.peakdetect import peakdetect

from os import listdir
from os.path import isfile, join

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

videoPath = 'C:/Users/psdco/Videos/'
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

def createVideo():
    import re

    def atoi(text):
        return int(text) if text.isdigit() else text

    def natural_keys(text):
        '''
        alist.sort(key=natural_keys) sorts in human order
        http://nedbatchelder.com/blog/200712/human_sorting.html
        (See Toothy's implementation in the comments)
        '''
        return [atoi(c) for c in re.split('(\d+)', text)]

    cap = cv2.VideoCapture(0)
    mypath = 'C:/Users/psdco/Videos/Trainings/480p/0 day1 rout2 720x480/'
    videoFramesPaths = [mypath+f for f in listdir(mypath) if (isfile(join(mypath, f)) and '_vis' in f)]
    print(videoFramesPaths.sort(key=natural_keys))

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter('C:/Users/psdco/Videos/Trainings/480p/output.avi', fourcc, 30.0, (200, 200))

    for vfp in videoFramesPaths:
        frame = cv2.imread(vfp)
        out.write(frame)
        # cv2.imshow('frame', frame)
        # if cv2.waitKey(10) & 0xFF == ord('q'):
        #     break

    # Release everything if job is finished
    out.release()
    cv2.destroyAllWindows()

def judgeRealBasic():
    # Started 22:54
    # Open the database and find all the straddle jumps
    db = sqlite3.connect(dbPath)
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

    # For each one, get the frame no for midpoint, its major and minor ellipse axis at that frame, it's deduction
    for routine in routines:
        deductionsQuery = db.execute("SELECT * FROM judgements WHERE routine_id=? ORDER BY id ASC LIMIT 1", (routine['id'],))
        deductionsQuery = deductionsQuery.fetchone()

        deductions = json.loads(deductionsQuery[2])
        bounces = json.loads(routine['bounces'])
        ellipses = json.loads(routine['ellipses'])

        for i, bounce in enumerate(bounces):
            if bounce['name'] == "Straddle Jump":
                midFrame = bounce['maxHeightFrame']
                pt1 = ellipses[midFrame + 1][1]
                pt2 = ellipses[midFrame + 1][2]
                major = abs(pt1[0]-pt2[0])
                minor = abs(pt1[1]-pt2[1])
                deduction = deductions[i]
                deductionCats[deduction]["x"].append(major)
                deductionCats[deduction]["y"].append(minor)

    # print(deductionCats)
    # Plot
    colors = ['r', 'g', 'b', 'cyan', 'magenta', 'yellow']
    handles = []
    for i, cat in enumerate(deductionCats):
        handles.append(mpatches.Patch(color=colors[i], label=cat))
        thisdict = deductionCats[cat]
        plt.scatter(thisdict['x'], thisdict['y'], color=colors[i], marker='o')
    plt.legend(handles=handles)
    plt.show()


def severalFramesOfSkill(cap, routine):
    capWidth = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    capHeight = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    bounces = json.loads(routine['bounces'])
    print('\nChoose a skill:')
    for i, b in enumerate(bounces):
        print('%d) %s' % (i + 1, b['name']))
    choice = 10
    # choice = readNum(len(bounces))

    bounce = bounces[choice - 1]
    start = bounce['startFrame'] + 6
    end = bounce['endFrame'] - 6
    step = (end - start) / 6
    step = int(step)
    framesToSave = range(start, end, step)

    whitespace = 4
    width = 255

    startPixel = int((capWidth * 0.55) - width / 2)
    endPixel = startPixel + width
    filmStrip = np.ones(shape=(capHeight * 0.8, (width * len(framesToSave)) + (whitespace * len(framesToSave) - 1), 3), dtype=np.uint8)

    for i, frameNum in enumerate(framesToSave):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frameNum)
        _ret, frame = cap.read()

        # possible improvement
        trackPerson = frame[0:capHeight * 0.8, startPixel:endPixel]
        start = ((whitespace + width) * i)
        filmStrip[0:capHeight * 0.8, start:start + width] = trackPerson

    imgName = "C:/Users/psdco/Videos/{}/{}.png".format(routine['name'][:-4], bounce['name'])
    print("Writing frame to {}".format(imgName))
    ret = cv2.imwrite(imgName, filmStrip)
    if not ret:
        print("Couldn't write image {}\nAbort!".format(imgName))
        exit()


def main():
    db = sqlite3.connect(dbPath)
    db.row_factory = sqlite3.Row

    # Ask the user to select routine from database
    routines = askWhichRoutineFromDb(db)

    for i, routine in enumerate(routines):

        # Open the routine file
        cap = openVideo(routine['name'])
        fps = cap.get(cv2.CAP_PROP_FPS)

        # spit out several frames of a tuck jump
        visualisePose(cap, routine)
        # severalFramesOfSkill(cap, routine)
        exit()

        # Do trampoline top stuff
        routine['trampoline'] = json.loads(routine['trampoline'])
        if not routine['trampoline']:
            routine['trampoline'] = FindTrampoline.findTrampolineIfNone(cap, routine)

            db.execute("UPDATE routines SET trampoline=? WHERE id=?", (json.dumps(routine['trampoline']), routine['id'],))
            db.commit()
            print("Trampoline Top has been set to {}".format(json.dumps(routine['trampoline'])))

        # Do background subtraction
        routine['center_points'] = json.loads(routine['center_points'])
        routine['ellipses'] = json.loads(routine['ellipses'])
        if askToTrackGymnast(routine['center_points']):
            centerPoints, ellipses = trackGymnast(cap, routine)

            savePoints = askToOverwriteTrackingData(routine['center_points'])
            if savePoints:
                print("Saving points...")
                routine['center_points'] = centerPoints
                routine['ellipses'] = json.loads(json.dumps(ellipses), parse_float=lambda x: int(float(x)))
                db.execute("UPDATE routines SET center_points=?, ellipses=? WHERE id=?", (json.dumps(routine['center_points']), json.dumps(routine['ellipses']), routine['id'],))
                db.commit()
            else:
                print("Data not saved")

        # Calculate bounces
        routine['bounces'] = calculateBounces(routine, fps)
        db.execute("UPDATE routines SET bounces=? WHERE id=?", (json.dumps(routine['bounces']), routine['id'],))
        db.commit()

        # Create plot
        plotData(routine, fps)

        print("Finished routine {} of {}".format(i + 1, len(routines)))

    db.close()
    print("Done")


def visualisePose(cap, routine, padding=100):
    # colours = [red, green, blue, yellow, purple, cyan,  red, green, blue, cyan, purple, yellow, red, green] bgr
    # [rfoot, rknee, rhip, lhip, lknee, lfoot, rhand, relbow, rshoulder, lshoulder, lelbow, lhand, neck, head top]
    colours = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (0, 255, 255), (255, 0, 255), (255, 255, 0), (0, 0, 255),
               (0, 255, 0), (255, 0, 0), (255, 255, 0), (255, 0, 255), (0, 255, 255), (0, 0, 255), (0, 255, 0)]

    # TODO this assumes there is a file with all poses for each frame in it
    # posePath = videoPath + routine['name'][:-4] + "/pose.npz"
    # poses = np.load(posePath)['poses']
    poses = {}
    for frameNo in range(1, int(cap.get(cv2.CAP_PROP_FRAME_COUNT)+1)):
        posePath = videoPath + routine['name'][:-4] + "/frame {}_pose.npz".format(frameNo)
        try:
            pose = np.load(posePath)['pose']
        except IOError:
            continue
        poses.update({frameNo: pose})

    # # Filter pose
    # frameNos = [frameNo for frameNo in poses]  # frame no
    # x = [poses[frameNo][0, 0] for frameNo in poses]  # rfoot x
    # y = [poses[frameNo][1, 0] for frameNo in poses]  # rfoot y
    #
    # b, a = signal.ellip(4, 0.01, 120, 0.055)  # Filter to be applied.
    # xFilt = signal.filtfilt(b, a, x, method="gust")
    # yFilt = signal.filtfilt(b, a, y, method="gust")
    #
    # for idx, frameNo in enumerate(frameNos):
    #     # Save rfoot pts in rknee
    #     poses[frameNo][0, 1] = poses[frameNo][0, 0]  # x
    #     poses[frameNo][1, 1] = poses[frameNo][1, 0]  # y
    #     # Overwrite rfoot with filtered sig
    #     poses[frameNo][0, 0] = xFilt[idx]
    #     poses[frameNo][1, 0] = yFilt[idx]

    routine['center_points'] = json.loads(routine['center_points'])
    routine['center_points'] = {cp[0]: [cp[1], cp[2]] for cp in routine['center_points']}
    # while 1:
    #     ret, frame = cap.read()
    #     frameNo = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
    #     if frameNo not in routine['center_points']:
    #         continue
    #
    #     cpt = routine['center_points'][frameNo]
    #     cx = cpt[0]
    #     cy = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) - cpt[1])
    #
    #     # pose points are relative to the top left (cx cy = ix iy; 0 0 = ix-100 iy-100) of the 200x200 cropped frame
    #     # pose given by (0 + posex, 0 + posey) => cx-100+posex, cy-100+posey
    #     pose = poses[frameNo]
    #     for p_idx in [0, 1]:  # range(14):
    #         posex = int((cx - padding) + pose[0, p_idx])
    #         posey = int((cy - padding) + pose[1, p_idx])
    #         cv2.circle(frame, (posex, posey), 5, colours[p_idx], thickness=-1)  # -ve thickness = filled
    #
    #     # Lines between points
    #     #  Could loop in pairs and link skipping ones that shouldnt be linked.
    #     # cv2.line(trackPerson,
    #     #          (int(thisFramePose[0, 0]), int(thisFramePose[1, 0])),
    #     #          (int(thisFramePose[0, 1]), int(thisFramePose[1, 1])),
    #     #          colours[0], 4)
    #
    #     cv2.imshow('frame', frame)
    #     if cv2.waitKey(50) & 0xFF == ord('q'):
    #         break
    #
    #     # Finish playing the video when we get to the end.
    #     if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
    #         break

    cv2.destroyAllWindows()
    # print(poses)
    # x = [frameNo for frameNo in poses]  # frame no
    # y = [480-poses[frameNo][1, 0] for frameNo in poses]  # rfoot
    #
    # b, a = signal.ellip(4, 0.01, 120, 0.055)  # Filter to be applied.
    # fgust = signal.filtfilt(b, a, y, method="gust")
    #
    # plt.plot(x, y, label="Original")
    # plt.plot(x, fgust, label="fgust")

    frameNos = [frameNo for frameNo in poses]  # frame no
    # x = [poses[frameNo][0, 0] for frameNo in poses]  # rfoot x
    y = [poses[frameNo][1, 0] for frameNo in poses]  # rfoot y
    diffy = np.diff(y)
    myDiff = []
    newY = y
    for i, _ in enumerate(newY[:-2]):
        thisPt = newY[i]
        nextPt = newY[i+1]
        diff = nextPt-thisPt
        myDiff.append(diff)
        if abs(diff) > 20:
            avg = (newY[i]+newY[i+2])/2
            newY[i+1] = avg
    y = np.array(y) - 10

    plt.plot(frameNos, y, label="y original")
    plt.plot(frameNos, newY, label="newY")
    plt.plot(frameNos[:-1], diffy, label="diff y")
    plt.plot(frameNos[:-2], myDiff, label="my diff y")
    plt.legend(loc='best')
    plt.show()


def trackGymnast(cap, routine):
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
    maskLeftBorder = int(capWidth * 0.35)  # TODO use routine['trampoline']['center'] +- trampoline Width
    maskRightBorder = int(capWidth * 0.65)

    # Create array for tiled window
    KNNImages = np.zeros(shape=(resizeHeight, resizeWidth * 3, 3), dtype=np.uint8)  # (h * 3, w, CV_8UC3);

    # Create mask around trampoline
    maskAroundTrampoline = np.zeros(shape=(capHeight, capWidth), dtype=np.uint8)  # cv2.CV_8U
    maskAroundTrampoline[0:routine['trampoline']['top'], maskLeftBorder:maskRightBorder] = 255  # [y1:y2, x1:x2]

    # Background extractor. Exclude shadow
    pKNN = cv2.createBackgroundSubtractorKNN()
    pKNN.setShadowValue(0)

    # Average background
    framesToAverageStart = (cap.get(cv2.CAP_PROP_FRAME_COUNT) * 0.5) - (framesToAverage / 2)
    framesToAverageEnd = (cap.get(cv2.CAP_PROP_FRAME_COUNT) * 0.5) + (framesToAverage / 2)  # Variable only for printing purposes
    print("Averaging frames {:.0f} - {:.0f}, please wait...".format(framesToAverageStart, framesToAverageEnd))
    cap.set(cv2.CAP_PROP_POS_FRAMES, framesToAverageStart)
    for i in range(framesToAverage):
        _ret, frame = cap.read()
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
        _ret, frame = cap.read()

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
                # TODO don't invert y axis
                # TODO Save as dict with frame number as key
                centerPoints.append([int(cap.get(cv2.CAP_PROP_POS_FRAMES)), cx, capHeight - cy])

                # Fit ellipse
                frameNoEllipse = deepcopy(frame)
                if len(contours[0]) > 5:  # ellipse requires contour to have at least 5 points
                    ellipse = cv2.fitEllipse(contours[0])
                    # frame, major, minor, angle
                    # TODO Save as dict with frame number as key
                    ellipses.append([int(cap.get(cv2.CAP_PROP_POS_FRAMES))] + list(ellipse))
                    cv2.ellipse(frame, ellipse, color=(0, 255, 0), thickness=2)
                else:
                    print("Couldn't find enough points for ellipse. Need 5, found {}".format(len(contours[0])))

                x1, x2, y1, y2 = boundingSquare(capHeight, capWidth, cx, cy)
                if visualise:
                    # finerPersonMask = cv2.bitwise_and(fgMaskKNN, fgMaskKNN, mask=personMask)
                    # personMasked = cv2.bitwise_and(frameNoEllipse, frameNoEllipse, mask=finerPersonMask)
                    trackPerson = frameNoEllipse[y1:y2, x1:x2]  # was personMasked. now it's not
                    cv2.imshow('track', trackPerson)

                # Save frames
                if saveCroppedFrames:
                    imgName = "C:/Users/psdco/Videos/{}/frame {:.0f}.png".format(routine['name'][:-4], cap.get(cv2.CAP_PROP_POS_FRAMES))
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


def plotData(routine, fps):
    print("\nStarting plotting...")
    f, axarr = plt.subplots(3, sharex=True)

    # Plot bounces
    # center_points consists of [frame num, x, y]
    x_frames = [pt[0] / fps for pt in routine['center_points']]
    y_travel = [pt[1] for pt in routine['center_points']]
    y_height = [pt[2] for pt in routine['center_points']]

    peaks_x = [[bounce['startFrame'] / fps, bounce['maxHeightFrame'] / fps] for bounce in routine['bounces']]
    peaks_y = [[bounce['startHeightInPixels'], bounce['maxHeightInPixels']] for bounce in routine['bounces']]

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
    axarr[1].axhline(y=routine['trampoline']['center'], xmin=0, xmax=1000, c="blue")
    axarr[1].axhline(y=routine['trampoline']['center'] + 80, xmin=0, xmax=1000, c="red")
    axarr[1].axhline(y=routine['trampoline']['center'] - 80, xmin=0, xmax=1000, c="red")

    #
    # Plot ellipsoid's angles
    #
    x_frames = np.array([pt[0] / fps for pt in routine['ellipses']])
    y_angle = np.array([pt[3] for pt in routine['ellipses']])
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


def calculateBounces(routine, fps):
    npCenterPoints = np.array(routine['center_points'])

    # npCenterPoints consists of [frame num, x, y]
    x = npCenterPoints[:, 0]
    y = npCenterPoints[:, 2]
    maxima, minima = peakdetect(y, x, lookahead=8, delta=20)

    bounces = []
    for i in range(len(minima)):
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


def askWhichRoutineFromDb(db):
    def dict_gen(result):
        dictItems = []
        for item in result:
            dictItems.append(dict(item))
        return dictItems

    print('\nTrack all untracked videos? [y/n]')
    if False and inputWasYes():
        # videos = db.execute("SELECT * FROM videos WHERE center_points='[]'")
        routines = db.execute("SELECT * FROM routines WHERE bounces='[]'")
        return dict_gen(routines.fetchall())  # copy everything pointed to by the cursor into an object.

    print('\nChoose a comp:')
    for i, c in enumerate(comps):
        print('%d) %s' % (i + 1, c))
    compChoice = 1
    # compChoice = readNum(len(comps))
    compChoice = comps[compChoice - 1]

    print('\nChoose a level:')
    for i, l in enumerate(levels):
        print('%d) %s' % (i + 1, l))
    levelChoice = 7  # readNum(len(levels))
    # levelChoice = readNum(len(levels))
    levelChoice = levels[levelChoice - 1]

    if levelChoice == 'All':
        selectedVids = db.execute("SELECT * FROM routines WHERE name LIKE ?", ('%' + compChoice + '%',))
    else:
        selectedVids = db.execute("SELECT * FROM routines WHERE name LIKE ? AND level=?", ('%' + compChoice + '%', levelChoice,))
    selectedVids = selectedVids.fetchall()  # copy everything pointed to by the cursor into an object.

    print('\nChoose a video:')
    for i, v in enumerate(selectedVids):
        str = "{} - {}".format(v['name'], v['level'])
        print('%d) %s' % (i + 1, str))
    # vidChoice = readNum(len(selectedVids))
    vidChoice = 1
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
    pathToVideo = videoPath + videoName
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
    # judgeRealBasic()
    # createVideo()
    main()
