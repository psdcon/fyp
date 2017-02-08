import json
from copy import deepcopy

import cv2
import numpy as np

from helpers.db_declarative import Frame
from helpers.helper import bounding_square

centerPoints = {}
ellipses = {}


def track_and_save(db, cap, routine):
    track_gymnast(cap, routine)

    print("Saving points...")

    # Add data for routine to db frame-by-frame
    frames = []
    for frameNum in ellipses.keys():
        cpt = centerPoints[frameNum]  # [cx, cy]
        ell = ellipses[frameNum]  # [(cx, cy), (MA, ma), angle]
        frames.append(Frame(routine.id, frameNum, cpt[0], cpt[1], ell[1][0], ell[1][1], ell[2]))

    db.add_all(frames)
    db.commit()


def track_gymnast(cap, routine):
    def erode_dilate(image):
        kernel = np.ones((2, 2), np.uint8)
        # erosion = cv2.erode(input, kernel, iterations=1)
        # dilation = cv2.dilate(erosion, kernel, iterations=1)
        opening = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)

        openingSmall = cv2.resize(opening, (resizeWidth, resizeHeight))
        # ErrodeImages[0:resizeHeight, resizeWidth:resizeWidth * 2] = cv2.cvtColor(openingSmall, cv2.COLOR_GRAY2RGB)

        opening = cv2.dilate(opening, kernel, iterations=10)

        openingSmall = cv2.resize(opening, (resizeWidth, resizeHeight))
        # ErrodeImages[0:resizeHeight, resizeWidth * 2:resizeWidth * 3] = cv2.cvtColor(openingSmall, cv2.COLOR_GRAY2RGB)

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
    # ErrodeImages = np.zeros(shape=(resizeHeight, resizeWidth * 3, 3), dtype=np.uint8)  # (h * 3, w, CV_8UC3);

    # Create mask around trampoline
    maskAroundTrampoline = np.zeros(shape=(capHeight, capWidth), dtype=np.uint8)  # cv2.CV_8U
    maskAroundTrampoline[0:routine.trampoline_top, maskLeftBorder:maskRightBorder] = 255  # [y1:y2, x1:x2]

    # Background extractor. Ignore shadow
    pKNN = cv2.createBackgroundSubtractorKNN()
    pKNN.setShadowValue(0)

    # Average background
    framesToAverageStart = (cap.get(cv2.CAP_PROP_FRAME_COUNT) * 0.5) - (framesToAverage / 2)
    framesToAverageEnd = (cap.get(cv2.CAP_PROP_FRAME_COUNT) * 0.5) + (
        framesToAverage / 2)  # Variable only for printing purposes
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

    lastContours = None  # used to remember last contour if area goes too small
    paused = False
    updateOne = False
    while 1:
        if updateOne or not paused:

            _ret, frame = cap.read()

            fgMaskKNN = pKNN.apply(frame)
            KNNErodeDilated = erode_dilate(fgMaskKNN)
            KNNErodeDilated = cv2.bitwise_and(KNNErodeDilated, KNNErodeDilated, mask=maskAroundTrampoline)

            if visualise:  # show the thing
                KNNImages[0:resizeHeight, 0:resizeWidth] = cv2.resize(pKNN.getBackgroundImage(),
                                                                      (resizeWidth, resizeHeight))
                cv2.putText(KNNImages, 'Current bg model', (10, 20), font, 0.4, (255, 255, 255))

                fgMaskKNNSmall = cv2.resize(fgMaskKNN, (resizeWidth, resizeHeight))
                KNNImages[0:resizeHeight, resizeWidth:resizeWidth * 2] = cv2.cvtColor(fgMaskKNNSmall,
                                                                                      cv2.COLOR_GRAY2RGB)
                cv2.putText(KNNImages, 'Subtracted', (10 + resizeWidth, 20), font, 0.4, (255, 255, 255))

                # For report
                # KNNImages[0:resizeHeight, 0:resizeWidth] = cv2.resize(frame, (resizeWidth, resizeHeight))
                # KNNImages[0:resizeHeight, resizeWidth:resizeWidth * 2] = cv2.resize(pKNN.getBackgroundImage(),
                #                                                                     (resizeWidth, resizeHeight))
                # KNNImages[0:resizeHeight, resizeWidth * 2:resizeWidth * 3] = cv2.cvtColor(fgMaskKNNSmall,
                #                                                                           cv2.COLOR_GRAY2RGB)
                #
                # Erode dilate for report
                # ErrodeImages[0:resizeHeight, 0:resizeWidth] = cv2.cvtColor(fgMaskKNNSmall, cv2.COLOR_GRAY2RGB)

            #
            # Find contours in masked image
            #
            _im2, contours, _hierarchy = cv2.findContours(deepcopy(KNNErodeDilated), cv2.RETR_TREE,
                                                          cv2.CHAIN_APPROX_SIMPLE)
            if len(contours) != 0:
                # TODO
                # Find the biggest contour first but when you're sure you have the person
                # Then find the contour closest to that one and track that way. Prevent jumping around when person disappears.
                # Also do something about combining legs. Check the distance of every point in the contour to every point int the closest contour.
                # If the distance between then is small enough, combine them.

                # Sort DESC, so biggest contour's first
                contours = sorted(contours, key=cv2.contourArea, reverse=True)

                # If contour is less than given area, replace it with previous contour
                area = cv2.contourArea(contours[0])
                # print(area)
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
                    # cv2.imshow('big', biggestContour)
                    KNNImages[0:resizeHeight, resizeWidth * 2:resizeWidth * 3] = biggestContourSmaller
                    cv2.putText(KNNImages, 'ErodeDilated', (10 + resizeWidth * 2, 20), font, 0.4, (255, 255, 255))
                    cv2.imshow('KNNImages', KNNImages)
                    # cv2.imshow('ErrodeImages', ErrodeImages)

                M = cv2.moments(contours[0])
                if M['m00'] > 0:
                    cx = int(M['m10'] / M['m00'])
                    cy = int(M['m01'] / M['m00'])

                    cv2.circle(frame, (cx, cy), 3, (0, 0, 255), -1)
                    centerPoints[int(cap.get(cv2.CAP_PROP_POS_FRAMES))] = [cx, cy]

                    # Fit ellipse
                    frameNoEllipse = deepcopy(frame)
                    if len(contours[0]) > 5:  # ellipse requires contour to have at least 5 points
                        # (x, y), (MA, ma), angle
                        ellipse = cv2.fitEllipse(contours[0])
                        # {frame: [(cx, cy), (MA, ma), angle]}
                        ellipses[int(cap.get(cv2.CAP_PROP_POS_FRAMES))] = json.loads(json.dumps(list(ellipse)),
                                                                                     parse_float=lambda x: int(
                                                                                         float(x)))

                        # Draw it
                        cv2.ellipse(frame, ellipse, color=(0, 255, 0), thickness=2)

                    else:
                        print("Couldn't find enough points for ellipse. Need 5, found {}".format(len(contours[0])))

                    x1, x2, y1, y2 = bounding_square(capHeight, capWidth, cx, cy, 120)
                    if visualise:
                        # finerPersonMask = cv2.bitwise_and(fgMaskKNN, fgMaskKNN, mask=personMask)
                        # personMasked = cv2.bitwise_and(frameNoEllipse, frameNoEllipse, mask=finerPersonMask)
                        trackPerson = frameNoEllipse[y1:y2, x1:x2]  # was personMasked. now it's not
                        cv2.imshow('track', trackPerson)

                    # Save frames
                    if saveCroppedFrames:
                        imgName = "C:/Users/psdco/Videos/{}/frame {:.0f}.png".format(routine.path[:-4],
                                                                                     cap.get(cv2.CAP_PROP_POS_FRAMES))
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

            if updateOne:
                updateOne = False

        k = cv2.waitKey(waitTime) & 0xff
        if k == ord('v'):
            visualise = not visualise
            if not visualise:  # destroy any open windows
                cv2.destroyAllWindows()
        elif k == ord('k'):  # play pause
            paused = not paused
        elif k == ord('j'):  # prev frame
            updateOne = True
            cap.set(cv2.CAP_PROP_POS_FRAMES, cap.get(cv2.CAP_PROP_POS_FRAMES) - 2)
        elif k == ord('l'):  # next frame
            updateOne = True
        elif k == ord('q') or k == 27:  # q/ESC
            print("Exiting...")
            exit()

        # Finish playing the video when we get to the end.
        if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
            break

    cap.release()
    cv2.destroyAllWindows()

    # return centerPoints, ellipses
    return
