import json
import os

import cv2
import numpy as np
from scipy.spatial import distance

from helpers import consts
from helpers import helper_funcs
from helpers.db_declarative import Frame
from helpers.helper_funcs import crop_points_constrained, contourCenter
from image_processing import trampoline

centerPoints = {}
ellipses = {}
cropLengths = {}


def track_and_save(db, routine):
    track_gymnast(routine)

    print("Saving points...")

    # Add data for routine to db frame-by-frame
    frames = []
    for frameNum in ellipses.keys():
        cpt = centerPoints[frameNum]  # [cx, cy]
        ell = ellipses[frameNum]  # [(cx, cy), (MA, ma), angle]
        crop_length = cropLengths[frameNum]  # [(cx, cy), (MA, ma), angle]
        frames.append(Frame(routine.id, frameNum, cpt[0], cpt[1], ell[1][0], ell[1][1], ell[2], crop_length))

    db.add_all(frames)
    db.commit()


def track_gymnast(routine):
    def alphaMask(src, mask):
        scalar = mask/255.0
        dst = np.zeros_like(src)
        for channel in range(3):
            dst[:, :, channel] = src[:, :, channel] * scalar
        return dst.astype(np.uint8)
        # return dst.astype(np.uint8)

    def erode_dilate(image):
        kernel = np.ones((2, 2), np.uint8)
        # erosion = cv2.erode(input, kernel, iterations=1)
        # dilation = cv2.dilate(erosion, kernel, iterations=1)
        opening = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)

        # openingSmall = cv2.resize(opening, (resizeWidth, resizeHeight))
        # ErrodeImages[0:resizeHeight, resizeWidth:resizeWidth * 2] = cv2.cvtColor(openingSmall, cv2.COLOR_GRAY2RGB)

        opening = cv2.dilate(opening, kernel, iterations=10)

        # openingSmall = cv2.resize(opening, (resizeWidth, resizeHeight))
        # ErrodeImages[0:resizeHeight, resizeWidth * 2:resizeWidth * 3] = cv2.cvtColor(openingSmall, cv2.COLOR_GRAY2RGB)

        # opening = cv2.dilate(opening, np.ones((3, 3), np.uint8), iterations=10)
        return opening

    print("Starting to track gymnast")
    cap = helper_funcs.open_video(routine.path)

    font = cv2.FONT_HERSHEY_SIMPLEX
    framesToAverage = 200
    startFrame = 0

    # Keyboard stuff
    visualise = True  # show windows rendering video
    waitTime = 15  # delay for keyboard input

    # Window vars
    scalingFactor = 0.4
    capWidth = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    capHeight = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    resizeWidth = int(capWidth * scalingFactor)
    resizeHeight = int(capHeight * scalingFactor)
    maskLeftBorder = int(routine.trampoline_center - (trampoline.calcTrampolineEnds(routine.trampoline_width) / 2))
    maskRightBorder = int(routine.trampoline_center + (trampoline.calcTrampolineEnds(routine.trampoline_width) / 2))

    # Create array for tiled window
    KNNImages = np.zeros(shape=(resizeHeight, resizeWidth * 3, 3), dtype=np.uint8)  # (h * 3, w, CV_8UC3);
    # ErrodeImages = np.zeros(shape=(resizeHeight, resizeWidth * 3, 3), dtype=np.uint8)  # (h * 3, w, CV_8UC3);

    # Create mask around trampoline
    maskAroundTrampoline = np.zeros(shape=(capHeight, capWidth), dtype=np.uint8)  # cv2.CV_8U
    maskAroundTrampoline[0:routine.trampoline_top, maskLeftBorder:maskRightBorder] = 255  # [y1:y2, x1:x2]
    maskShowTrampoline = np.zeros(shape=(capHeight, capWidth), dtype=np.uint8)
    maskShowTrampoline[routine.trampoline_top:capHeight, maskLeftBorder:maskRightBorder] = 255  # [y1:y2, x1:x2]

    # Background extractor. Ignore shadow
    pKNN = cv2.createBackgroundSubtractorKNN()
    pKNN.setShadowValue(0)

    # Average background
    framesToAverageStart = (cap.get(cv2.CAP_PROP_FRAME_COUNT) * 0.5) - (framesToAverage / 2)
    framesToAverageEnd = (cap.get(cv2.CAP_PROP_FRAME_COUNT) * 0.5) + (
        framesToAverage / 2)  # Variable only for printing purposes
    print("Averaging {} frames: {:.0f} - {:.0f}, please wait...".format(framesToAverage, framesToAverageStart, framesToAverageEnd))
    cap.set(cv2.CAP_PROP_POS_FRAMES, framesToAverageStart)
    for i in range(framesToAverage):
        _ret, frame = cap.read()
        # maskedFrame = cv2.bitwise_and(frame, frame, mask=maskAroundTrampoline)
        pKNN.apply(frame)  # Train background subtractor

    # Reset video to start
    cap.set(cv2.CAP_PROP_POS_FRAMES, startFrame)

    # print("\nStarting video at frame {}".format(startFrame))
    print("Press v to toggle showing visuals")
    print("Press ENTER to finish, and ESC/'q' to quit")

    lastContours = None  # used to remember last contour if area goes too small
    paused = False
    updateOne = False
    prevErodeDilatedMask = np.zeros(shape=(capHeight, capWidth), dtype=np.uint8)
    comboMask = np.zeros(shape=(capHeight, capWidth), dtype=np.uint8)
    while 1:
        if updateOne or not paused:

            _ret, frame = cap.read()

            # if int(cap.get(cv2.CAP_PROP_POS_FRAMES)) not in range(425, 515):
            #     if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
            #         cap.set(cv2.CAP_PROP_POS_FRAMES, 425)
            #     else:
            #         continue

            # TODO if mask is really noisy (area is large/ high num contours), could increase the learning rate?
            # maskedFrame = cv2.bitwise_and(frame, frame, mask=maskAroundTrampoline)
            fgMaskKNN = pKNN.apply(frame)
            KNNErodeDilated = erode_dilate(fgMaskKNN)
            trampolineForeground = cv2.bitwise_and(KNNErodeDilated, KNNErodeDilated, mask=maskShowTrampoline)
            cv2.imshow("trampolineForeground", cv2.resize(trampolineForeground, (resizeWidth, resizeHeight)))

            KNNErodeDilated = cv2.bitwise_and(KNNErodeDilated, KNNErodeDilated, mask=maskAroundTrampoline)
            comboMask = cv2.bitwise_and(KNNErodeDilated, KNNErodeDilated, mask=prevErodeDilatedMask)

            if visualise:  # show the thing
                KNNImages[0:resizeHeight, 0:resizeWidth] = cv2.resize(pKNN.getBackgroundImage(), (resizeWidth, resizeHeight))
                cv2.putText(KNNImages, 'Current bg model', (10, 20), font, 0.4, (255, 255, 255))

                fgMaskKNNSmall = cv2.resize(fgMaskKNN, (resizeWidth, resizeHeight))
                KNNImages[0:resizeHeight, resizeWidth:resizeWidth * 2] = cv2.cvtColor(fgMaskKNNSmall, cv2.COLOR_GRAY2RGB)
                cv2.putText(KNNImages, 'Subtracted', (10 + resizeWidth, 20), font, 0.4, (255, 255, 255))

                # For report
                # KNNImages[0:resizeHeight, 0:resizeWidth] = cv2.resize(frame, (resizeWidth, resizeHeight))
                # KNNImages[0:resizeHeight, resizeWidth:resizeWidth * 2] = cv2.resize(pKNN.getBackgroundImage(), (resizeWidth, resizeHeight))
                # KNNImages[0:resizeHeight, resizeWidth * 2:resizeWidth * 3] = cv2.cvtColor(fgMaskKNNSmall, cv2.COLOR_GRAY2RGB)
                #
                # Erode dilate for report
                # ErrodeImages[0:resizeHeight, 0:resizeWidth] = cv2.cvtColor(fgMaskKNNSmall, cv2.COLOR_GRAY2RGB)

            #
            # Find contours in masked image
            _im2, contours, _hierarchy = cv2.findContours(np.copy(KNNErodeDilated), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            if len(contours) > 0:

                # Sort DESC, so biggest contour's first
                contours = sorted(contours, key=cv2.contourArea, reverse=True)

                # If contour is less than given area, replace it with previous contour
                area = cv2.contourArea(contours[0])  # print(area)
                if area < consts.minContourArea and lastContours is not None:
                    contours = lastContours
                else:
                    lastContours = contours

                # Find contours in the combo mask and get their centers
                _im2, comboContours, _hierarchy = cv2.findContours(np.copy(comboMask), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                comboContours = sorted(comboContours, key=cv2.contourArea, reverse=True)
                comboContourCenters = [contourCenter(cont) for cont in comboContours if contourCenter(cont) is not None]
                # Show the contours with their numbers
                comboColor = cv2.cvtColor(comboMask, cv2.COLOR_GRAY2RGB)
                for i, cent in enumerate(comboContourCenters):
                    cv2.putText(comboColor, '{}'.format(i), cent, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255))
                # cv2.imshow("combo", cv2.resize(comboColor, (resizeWidth, resizeHeight)))
                # Get contours in this errodedilate mask
                thisContourCenters = [contourCenter(cont) for cont in contours if contourCenter(cont) is not None]

                # Check if they're close to each other
                contourGuessesIndices = []
                for i, comboCenter in enumerate(comboContourCenters):
                    minDist = 99999
                    minDistIndex = 0
                    for ii, thisCenter in enumerate(thisContourCenters):
                        dist = distance.euclidean(thisCenter, comboCenter)
                        if dist < minDist:
                            minDist = dist
                            minDistIndex = ii
                    # The index
                    contourGuessesIndices.append(minDistIndex)

                # Draw the last body detection as a mask
                # cv2.imshow("prevErodeDilatedMask", cv2.resize(prevErodeDilatedMask, (resizeWidth, resizeHeight)))
                prevErodeDilatedMask = np.zeros(shape=(capHeight, capWidth), dtype=np.uint8)
                if False and contourGuessesIndices and 0 in contourGuessesIndices:
                    # check if the biggest and smallest have close edges so that if they're difting apart, the smaller one gets kicked out
                    # if not helper_funcs.find_if_close(contours[0], contours[contourGuessesIndices[-1]]):
                    #     print('throwing away')
                    #     contourGuessesIndices = contourGuessesIndices[:-1]  # throw away the last index

                    foundContours = [contours[i] for i in contourGuessesIndices]
                    personContour = np.concatenate(foundContours)
                    for cont in foundContours:
                        cv2.drawContours(prevErodeDilatedMask, [cont], 0, (255, 255, 255), cv2.FILLED)
                else:
                    personContour = contours[0]
                    cv2.drawContours(prevErodeDilatedMask, contours, 0, (255, 255, 255), cv2.FILLED)

                used2nd = False
                # # Check if the two biggest contours are near each other
                # if False and (len(contours) >= 2 and helper_funcs.find_if_close(contours[0], contours[1])):
                #     personContour = np.concatenate((contours[0], contours[1]))
                #     used2nd = True
                # else:
                #     personContour = contours[0]

                hull = cv2.convexHull(personContour)
                hullMaxXLen = hull[:, 0, 0].max() - hull[:, 0, 0].min()
                hullMaximaY = hull[:, 0, 1].max()
                hullMaxYLen = hullMaximaY - hull[:, 0, 1].min()
                hullMaxLen = max([hullMaxXLen, hullMaxYLen])  # get all y components, get length between them

                # distFromTrampoline = routine.trampoline_top - hullMaximaY
                # print("distFromTrampoline", distFromTrampoline)

                if visualise:
                    # KNNErodeDilated has all the contours of interest
                    biggestContour = cv2.cvtColor(KNNErodeDilated, cv2.COLOR_GRAY2RGB)
                    personMask = np.zeros(shape=(capHeight, capWidth), dtype=np.uint8)
                    cv2.drawContours(personMask, [personContour], 0, 255, cv2.FILLED)
                    # cv2.imshow('personMask', personMask)
                    # Draw the biggest one in red
                    cv2.drawContours(biggestContour, contours, 0, (0, 0, 255), cv2.FILLED)
                    # Draw second biggest in green if it was included in the personContour
                    if len(contours) >= 2 and used2nd:
                        cv2.drawContours(biggestContour, contours, 1, (0, 255, 0), cv2.FILLED)
                    # Draw the outline of the convex hull for the person
                    cv2.drawContours(biggestContour, [hull], 0, (0, 255, 0), 1)

                    for i, cent in enumerate(thisContourCenters):
                        cv2.putText(biggestContour, '{}'.format(i), cent, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0))

                    # Resize and show it
                    biggestContourSmaller = cv2.resize(biggestContour, (resizeWidth, resizeHeight))
                    # cv2.imshow('big', biggestContour)
                    KNNImages[0:resizeHeight, resizeWidth * 2:resizeWidth * 3] = biggestContourSmaller
                    cv2.putText(KNNImages, 'ErodeDilated', (10 + resizeWidth * 2, 20), font, 0.4, (255, 255, 255))
                    cv2.imshow('KNNImages', KNNImages)
                    # cv2.imshow('ErrodeImages', ErrodeImages)

                cx, cy = contourCenter(personContour)
                if cx and cy:
                    # cv2.circle(frame, (cx, cy), 3, (0, 0, 255), -1)
                    centerPoints[int(cap.get(cv2.CAP_PROP_POS_FRAMES))] = [cx, cy]

                    # Fit ellipse
                    frameNoEllipse = np.copy(frame)
                    if len(personContour) > 5:  # ellipse requires contour to have at least 5 points
                        # (x, y), (MA, ma), angle
                        ellipse = cv2.fitEllipse(personContour)
                        # {frame: [(cx, cy), (MA, ma), angle]}
                        ellipses[int(cap.get(cv2.CAP_PROP_POS_FRAMES))] = json.loads(json.dumps(list(ellipse)), parse_float=lambda x: int(float(x)))

                        # Draw it
                        cv2.ellipse(frame, ellipse, color=(0, 255, 0), thickness=2)

                    else:
                        print("Couldn't find enough points for ellipse. Need 5, found {}".format(len(personContour)))

                    # cropLength = np.clip(hullMaxLen+40, 160, 400)
                    # cropLengths[int(cap.get(cv2.CAP_PROP_POS_FRAMES))] = cropLength
                    # print("Hull Max Len:", hullMaxLen, "Crop Height:", cropLength)
                    # cropLength = 256
                    cropLength = routine.crop_length if routine.crop_length else 200

                    x1, x2, y1, y2 = crop_points_constrained(capHeight, capWidth, cx, cy, cropLength)
                    if visualise:
                        finerPersonMask = cv2.bitwise_and(fgMaskKNN, fgMaskKNN, mask=prevErodeDilatedMask)
                        kernel = np.ones((3, 3), np.uint8)
                        finerPersonMask = cv2.dilate(finerPersonMask, kernel, iterations=2)
                        # finerPersonMask = cv2.GaussianBlur(finerPersonMask, (15, 15), 0)
                        # cv2.imshow("finerPersonMask", cv2.resize(finerPersonMask, (resizeWidth, resizeHeight)))

                        darkBg = cv2.addWeighted(frameNoEllipse, 0.4, np.zeros_like(frameNoEllipse), 0.6, 0)
                        darkBg = cv2.GaussianBlur(darkBg, (15, 15), 0)
                        darkBg = cv2.GaussianBlur(darkBg, (15, 15), 0)
                        darkBgHole = cv2.bitwise_and(darkBg, darkBg, mask=255-finerPersonMask)
                        # darkBgHole = alphaMask(darkBg, 255-finerPersonMask)
                        # cv2.imshow('darkBg', cv2.resize(darkBg, (resizeWidth, resizeHeight)))
                        # cv2.imshow('darkBgHole', cv2.resize(darkBgHole, (resizeWidth, resizeHeight)))

                        personMasked = cv2.bitwise_and(frameNoEllipse, frameNoEllipse, mask=finerPersonMask)
                        # personMasked = alphaMask(frameNoEllipse, finerPersonMask)
                        personMasked = cv2.add(darkBgHole, personMasked)
                        trackPerson = personMasked[y1:y2, x1:x2]
                        cv2.imshow('track', trackPerson)
                        #####################################
                        outPath = consts.videosRootPath + routine.path.replace('.mp4', '__dilated_blurred_0.4-0.6/')
                        if not os.path.exists(outPath):
                            print("Creating " + outPath)
                            os.makedirs(outPath)

                        imgName = outPath + "frame_{0:04}.png".format(int(cap.get(cv2.CAP_PROP_POS_FRAMES)))
                        print("Writing frame to {}".format(imgName))
                        ret = cv2.imwrite(imgName, trackPerson)
                        if not ret:
                            print("Couldn't write image {}\nAbort!".format(imgName))
                            exit()
                        #####################################

                        # trackScaled = cv2.resize(trackPerson, (256, 256))
                        # cv2.imshow('track scaled', trackScaled)

                else:
                    print("Skipping center point. No moment")

            #
            # End stuff
            #
            if visualise:
                cv2.putText(frame, '{}'.format(int(cap.get(cv2.CAP_PROP_POS_FRAMES))), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255))
                cv2.line(frame, (0, routine.trampoline_top), (routine.video_width, routine.trampoline_top), (0, 255, 0), 1)
                cv2.imshow('frame ', cv2.resize(frame, (resizeWidth, resizeHeight)))

            if updateOne:
                updateOne = False

        k = cv2.waitKey(waitTime) & 0xff
        if k == ord('v'):
            visualise = not visualise
            # if not visualise:  # destroy any open windows
            #     cv2.destroyAllWindows()
        elif k == ord('k'):  # play pause
            paused = not paused
        elif k == ord('j'):  # prev frame
            updateOne = True
            cap.set(cv2.CAP_PROP_POS_FRAMES, cap.get(cv2.CAP_PROP_POS_FRAMES) - 2)
        elif k == ord('l'):  # next frame
            updateOne = True
        elif k == ord('.'):  # speed up
            waitTime -= 5
            print(waitTime)
        elif k == ord(','):  # slow down
            waitTime += 5
            print(waitTime)
        elif k >= ord('0') and k <= ord('9'):
            num = k - ord('0')
            frameToJumpTo = (cap.get(cv2.CAP_PROP_FRAME_COUNT) / 10) * num
            cap.set(cv2.CAP_PROP_POS_FRAMES, frameToJumpTo)
            updateOne = True
        elif k == ord('\n') or k == ord('\r'):  # return/enter key
            break
        elif k == ord('q') or k == 27:  # q/ESC
            print("Exiting...")
            exit()

        # Finish playing the video when we get to the end.
        if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
            break

    cap.release()
    cv2.destroyAllWindows()

    return
