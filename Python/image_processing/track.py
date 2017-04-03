import json

import cv2
import numpy as np

from helpers import consts
from helpers import helper_funcs
from helpers.db_declarative import Frame
from image_processing import trampoline


# Global Vars that get updated in the track loop with frame numbers
# Used when saving data back to db

def track_and_save(db, routine):
    centerPoints, hullLengths, trampolineTouches, personMasks = track_gymnast(db, routine)

    if routine.use == 0:
        print("use is", routine.use, ". Frame data is not being saved.")
        return

    print("Saving points...")

    if routine.frames:
        print("Existing frames. What do?")

    helper_funcs.save_zipped_pickle(personMasks, routine.personMasksPath())

    # Add data for routine to db frame-by-frame
    frames = []
    for frameNum in centerPoints.keys():
        cpt = centerPoints[frameNum]  # [cx, cy]
        center_pt_x = cpt[0]
        center_pt_y = cpt[1]
        hull_length = hullLengths[frameNum]
        trampoline_touch = 1 if trampolineTouches[frameNum] else 0

        frame = Frame(routine.id, frameNum, center_pt_x, center_pt_y, hull_length, trampoline_touch)
        frames.append(frame)

    db.add_all(frames)
    db.commit()
    print("Frames Saved")


def prepareBgSubt(pKNN, cap, framesToAverage):
    framesToAverageStart = (cap.get(cv2.CAP_PROP_FRAME_COUNT) * 0.5) - (framesToAverage / 2)
    framesToAverageEnd = (cap.get(cv2.CAP_PROP_FRAME_COUNT) * 0.5) + (framesToAverage / 2)  # Variable only for printing purposes
    print("Averaging {} frames: {:.0f} - {:.0f}, please wait...".format(framesToAverage, framesToAverageStart, framesToAverageEnd))
    cap.set(cv2.CAP_PROP_POS_FRAMES, framesToAverageStart)
    for i in range(framesToAverage):
        _ret, frame = cap.read()
        # maskedFrame = cv2.bitwise_and(frame, frame, mask=maskAboveTrmpl)
        pKNN.apply(frame)  # Train background subtractor

    # Reset video to start
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)


def getPersonContour(fgMaskPrevPersonOverlap, contours):
    # Find contours in the combo mask and get their centers
    # _im2, overlapContours, _hierarchy = cv2.findContours(np.copy(fgMaskPrevPersonOverlap), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Sort the contours and find their centers
    # overlapContours = sorted(overlapContours, key=cv2.contourArea, reverse=True)
    # overlapContourCenters = [helper_funcs.calcContourCenter(contour) for contour in overlapContours if helper_funcs.calcContourCenter(contour) is not None]

    # Show the contours with their numbers
    # overlapColor = cv2.cvtColor(fgMaskPrevPersonOverlap, cv2.COLOR_GRAY2RGB)
    # for i, cpt in enumerate(overlapContourCenters):
    #     cv2.putText(overlapColor, '{}'.format(i), cpt, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255))
    # cv2.imshow("overlap", cv2.resize(overlapColor, (resizeWidth, resizeHeight)))

    # Get contours in this errodedilate mask
    # thisFrameContourCenters = [helper_funcs.calcContourCenter(contour) for contour in contours if helper_funcs.calcContourCenter(contour) is not None]

    # Match the contours in both frames based on min distance to their center points
    # contourGuessesIndices = []  # list where the index refers to the overlaContour and the value is the index of the closest thisContour
    # for i, overlapCenter in enumerate(overlapContourCenters):
    #     minDist = 99999
    #     minDistIndex = 0
    #     for ii, thisCenter in enumerate(thisFrameContourCenters):
    #         dist = distance.euclidean(thisCenter, overlapCenter)
    #         if dist < minDist:
    #             minDist = dist
    #             minDistIndex = ii
    #     contourGuessesIndices.append(minDistIndex)

    # Draw the last body detection as a mask
    # cv2.imshow("prevPersonFgMask", cv2.resize(prevPersonFgMask, (resizeWidth, resizeHeight)))

    # Create a mask to draw the selected regions of the person onto
    prevPersonFgMask = np.zeros_like(fgMaskPrevPersonOverlap)

    # Decide which regions to select.
    # 1 Use previous frame masked with this frame to find regions that overlap.
    # 2 Use any contour that are close to the biggest
    # 3 Use the biggest contour
    if False:  # and contourGuessesIndices and 0 in contourGuessesIndices:
        pass
        # check if the biggest and smallest have close edges so that if they're difting apart, the smaller one gets kicked out
        # if not helper_funcs.find_if_close(contours[0], contours[contourGuessesIndices[-1]]):
        #     print('throwing away')
        #     contourGuessesIndices = contourGuessesIndices[:-1]  # throw away the last index

        # foundContours = [contours[i] for i in contourGuessesIndices]
        # personContourConcat = np.concatenate(foundContours)
        # for contour in foundContours:
        #     cv2.drawContours(prevPersonFgMask, [contour], 0, (255, 255, 255), cv2.FILLED)
    elif False:
        # Concat contours if they're "near"
        personContours = [contours[0]]
        personContourConcat = contours[0]
        for contour in contours[1:]:
            helper_funcs.find_if_close(personContourConcat, contour)
            personContours.append(contour)
            personContourConcat = np.concatenate([personContourConcat, contour])

        for contour in personContours:
            cv2.drawContours(prevPersonFgMask, [contour], 0, (255, 255, 255), cv2.FILLED)
    else:
        personContours = [contours[0]]
        personContourConcat = contours[0]
        cv2.drawContours(prevPersonFgMask, contours, 0, (255, 255, 255), cv2.FILLED)

    return personContourConcat, personContours, prevPersonFgMask


def highlightPerson(frame, personMask, cx, cy, cropLength):
    # Get boundary
    x1, x2, y1, y2 = helper_funcs.crop_points_constrained(frame.shape[0], frame.shape[1], cx, cy, cropLength)

    # Dilate the mask
    kernel = np.ones((3, 3), np.uint8)
    personMask = cv2.dilate(personMask, kernel, iterations=3)
    # personMask = cv2.GaussianBlur(personMask, (15, 15), 0)
    # cv2.imshow("personMask", cv2.resize(personMask, (resizeWidth, resizeHeight)))

    # Darken the background and blur it
    percDarker = 0.6  # 60% darker
    darkBg = cv2.addWeighted(frame, 1-percDarker, np.zeros_like(frame), percDarker, 0)
    darkBg = cv2.GaussianBlur(darkBg, (15, 15), 0)
    darkBg = cv2.GaussianBlur(darkBg, (15, 15), 0)
    # Make a person shaped hole in the bg
    darkBgHole = cv2.bitwise_and(darkBg, darkBg, mask=255 - personMask)

    # darkBgHole = alphaMask(darkBg, 255-personMask)
    # cv2.imshow('darkBg', cv2.resize(darkBg, (resizeWidth, resizeHeight)))
    # cv2.imshow('darkBgHole', cv2.resize(darkBgHole, (resizeWidth, resizeHeight)))

    # Fill person shaped hole
    personRevealed = cv2.bitwise_and(frame, frame, mask=personMask)
    # personRevealed = alphaMask(frameNoEllipse, personMask)

    # Add the two together
    personRevealed = cv2.add(darkBgHole, personRevealed)

    return personRevealed[y1:y2, x1:x2]


def getMaxHullLength(hull):
    hullMaxXLen = hull[:, 0, 0].max() - hull[:, 0, 0].min()
    hullMaxYLen = hull[:, 0, 1].max() - hull[:, 0, 1].min()
    return max([hullMaxXLen, hullMaxYLen])  # get all y components, get length between them


def sq_area(ys, xs):
    # Calculate the area between two points assuming they're not on a horizontal or vertical line
    h = ys[0] - ys[1]
    w = xs[0] - xs[1]
    return abs(w * h)


# Blends a greyscale mask into the src
def alphaMask(src, mask):
    scalar = mask / 255.0
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
    opening = cv2.dilate(opening, kernel, iterations=10)
    return opening


def isTouchingTrmpl(trmpl_top, hull):
    # Bottom of person
    personMinPt = hull[:, 0, 1].max()  # y coordinate frame direction, duh
    distFromTrmpl = trmpl_top - personMinPt

    if distFromTrmpl == 1:
        return True
        # if len(hull) == 1:
        #     return True
        # # Sort the points of the hull by max(y) to find the length of the line touching the trampoline
        # hullSorted = sorted(hull[:, 0], key=lambda h: h[1], reverse=True)
        # lenTrmplTouch = np.linalg.norm(hullSorted[0] - hullSorted[1])
        # if lenTrmplTouch > 5:
        #     return True
    return False


def track_gymnast(db, routine):
    centerPoints = {}
    hullLengths = {}
    trampolineTouches = {}
    personMasks = {}

    print("Starting to track gymnast")
    cap = helper_funcs.open_video(routine.path)

    font = cv2.FONT_HERSHEY_SIMPLEX
    framesToAverage = 300

    # Keyboard stuff
    visualise = True  # show windows rendering video
    waitTime = 15  # delay for keyboard input
    paused = False
    goOneFrame = False

    # Window vars
    scalingFactor = 0.4
    capWidth = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    capHeight = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    resizeWidth = int(capWidth * scalingFactor)
    resizeHeight = int(capHeight * scalingFactor)

    # For masking to the right and left of the trampoline
    maskLeftBorder = int(routine.trampoline_center - (trampoline.calcTrampolineEnds(routine.trampoline_width) / 2))
    maskRightBorder = int(routine.trampoline_center + (trampoline.calcTrampolineEnds(routine.trampoline_width) / 2))

    # Create array for tiled window
    processVisImgs = np.zeros(shape=(resizeHeight * 2, resizeWidth * 2, 3), dtype=np.uint8)  # (h * 3, w, CV_8UC3);
    prevPersonFgMask = np.zeros(shape=(capHeight, capWidth), dtype=np.uint8)

    # Create mask around trampoline
    maskAboveTrmpl = np.zeros(shape=(capHeight, capWidth), dtype=np.uint8)  # cv2.CV_8U
    maskAboveTrmpl[0:routine.trampoline_top, maskLeftBorder:maskRightBorder] = 255  # [y1:y2, x1:x2]
    maskBelowTrmpl = np.zeros(shape=(capHeight, capWidth), dtype=np.uint8)
    maskBelowTrmpl[routine.trampoline_top:capHeight, maskLeftBorder:maskRightBorder] = 255  # [y1:y2, x1:x2]
    trampolineAreaPx = sq_area((routine.trampoline_top, capHeight), (maskLeftBorder, maskRightBorder))

    # Pick a default crop len if none saved
    # cropLength = routine.crop_length if routine.crop_length else 200

    # Background extractor. Ignore shadow
    pKNN = cv2.createBackgroundSubtractorKNN()
    pKNN.setShadowValue(0)
    # Prepare background by pre-training the bg sub
    prepareBgSubt(pKNN, cap, framesToAverage)

    print("Press v to toggle showing visuals")
    print("Press ENTER to finish, and ESC/'q' to quit")

    lastContours = None  # used to remember last contour if area goes too small
    while 1:
        if goOneFrame or not paused:

            _ret, frame = cap.read()

            # TODO if mask is really noisy (area is large/ high num contours), could increase the learning rate?
            frameFgMask = pKNN.apply(frame)
            frameFgMaskMorphed = erode_dilate(frameFgMask)

            # Crop fg mask detail to be ROI (region of interest) above the trampoline
            frameFgMaskMorphed = cv2.bitwise_and(frameFgMaskMorphed, frameFgMaskMorphed, mask=maskAboveTrmpl)

            # Create mask of the common regions in this and in the prevPersonFgMask
            fgMaskPrevPersonOverlap = cv2.bitwise_and(frameFgMaskMorphed, frameFgMaskMorphed, mask=prevPersonFgMask)

            if visualise:
                # Show current background model
                processVisImgs[0:resizeHeight, 0:resizeWidth] = cv2.resize(pKNN.getBackgroundImage(), (resizeWidth, resizeHeight))
                cv2.putText(processVisImgs, 'Background Model', (10, 20), font, 0.4, (255, 255, 255))
                # Show fg mask
                frameFgMask4Vis = cv2.cvtColor(cv2.resize(frameFgMask, (resizeWidth, resizeHeight)), cv2.COLOR_GRAY2RGB)
                cv2.line(frameFgMask4Vis, (0, int(routine.trampoline_top*scalingFactor)), (resizeWidth, int(routine.trampoline_top*scalingFactor)), (0, 255, 0), 1)
                cv2.putText(frameFgMask4Vis, 'Foreground Mask', (10, 20), font, 0.4, (255, 255, 255))
                processVisImgs[resizeHeight * 1:resizeHeight * 2, resizeWidth * 0:resizeWidth * 1] = frameFgMask4Vis
                # Trampoline area
                # cv2.putText(fgMaskBelowTrmpl, '{}%'.format(trampolineArea), (10, 20), font, 1, (255, 255, 255))
                # cv2.imshow("fgMaskBelowTrmpl", cv2.resize(fgMaskBelowTrmpl, (resizeWidth, resizeHeight)))

            # Find contours in masked image
            _img, contours, _hierarchy = cv2.findContours(np.copy(frameFgMaskMorphed), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            if len(contours) > 0:
                # Sort DESC, so biggest contour is first
                contours = sorted(contours, key=cv2.contourArea, reverse=True)
                # If contour is less than min area, replace it with previous contour
                if cv2.contourArea(contours[0]) < consts.minContourArea and lastContours is not None:
                    contours = lastContours
                else:
                    lastContours = contours

                personContourConcat, personContours, prevPersonFgMask = getPersonContour(fgMaskPrevPersonOverlap, contours)
                blobHull = cv2.convexHull(personContourConcat)

                if visualise:
                    # Convert the foreground mask to color so the biggest can be coloured in
                    biggestContour = cv2.cvtColor(frameFgMaskMorphed, cv2.COLOR_GRAY2RGB)
                    # Draw the biggest one in red
                    for contour in personContours:
                        cv2.drawContours(biggestContour, [contour], 0, (0, 0, 255), cv2.FILLED)
                    # Draw the outline of the convex blobHull for the person
                    cv2.drawContours(biggestContour, [blobHull], 0, (0, 255, 0), 2)
                    # Resize and show it
                    biggestContour = cv2.resize(biggestContour, (resizeWidth, resizeHeight))
                    cv2.putText(biggestContour, 'Blob Detection', (10, 20), font, 0.4, (255, 255, 255))
                    processVisImgs[resizeHeight * 1:resizeHeight * 2, resizeWidth * 1:resizeWidth * 2] = biggestContour
                    # cv2.imshow('personMask', personMask)

                cx, cy = helper_funcs.calcContourCenter(personContourConcat)
                if cx and cy:
                    centerPoints[int(cap.get(cv2.CAP_PROP_POS_FRAMES))] = [cx, cy]

                    # Save person mask so it can be used when outputting frames
                    # prevPersonFgMask is, at the moment, the current person fg mask. It's already been updated.
                    finerPersonMask = cv2.bitwise_and(frameFgMask, frameFgMask, mask=prevPersonFgMask)
                    personMasks[int(cap.get(cv2.CAP_PROP_POS_FRAMES))] = json.dumps(finerPersonMask.tolist())

                    # Get max dimension of person
                    _img, finerContours, _h = cv2.findContours(np.copy(finerPersonMask), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                    if len(finerContours) > 0:
                        finerContours = sorted(finerContours, key=cv2.contourArea, reverse=True)
                        finerHull = cv2.convexHull(finerContours[0])
                    # Use finer hull because blob morph opperations will change height
                    hullMaxLen = getMaxHullLength(finerHull)
                    hullLengths[int(cap.get(cv2.CAP_PROP_POS_FRAMES))] = hullMaxLen

                    touchingTrmpl = isTouchingTrmpl(routine.trampoline_top, finerHull)
                    trampolineTouches[int(cap.get(cv2.CAP_PROP_POS_FRAMES))] = touchingTrmpl

                    if visualise:
                        # Show trampoline touch detection
                        finerPersonMask4Vis = cv2.cvtColor(finerPersonMask, cv2.COLOR_GRAY2RGB)
                        cv2.drawContours(finerPersonMask4Vis, [finerHull], 0, (0, 255, 0), 2)
                        if touchingTrmpl:
                            cv2.line(finerPersonMask4Vis, (0, routine.trampoline_top), (routine.video_width, routine.trampoline_top), (0, 255, 0), 5)
                        else:
                            cv2.line(finerPersonMask4Vis, (0, routine.trampoline_top), (routine.video_width, routine.trampoline_top), (0, 0, 255), 5)
                        finerPersonMask4Vis = cv2.resize(finerPersonMask4Vis, (resizeWidth, resizeHeight))
                        cv2.imshow('finerPersonMask4Vis', finerPersonMask4Vis)

                        # Show person drawing the center of mass
                        cv2.circle(frame, (cx, cy), 3, (0, 0, 255), -1)
                        # cropLength = helper_funcs.getCropLength(hullLengths.values())
                        trackedPerson = highlightPerson(frame, finerPersonMask, cx, cy, 250)
                        trackedPerson = cv2.resize(trackedPerson, (256, 256))
                        cv2.imshow("Track", trackedPerson)
                else:
                    print("Skipping center point. Couldn't find moment")
            else:
                print("Skipping everything. Couldn't find contours")

            # End stuff
            if visualise:
                cv2.line(frame, (0, routine.trampoline_top), (routine.video_width, routine.trampoline_top), (0, 255, 0), 1)
                frameSm = cv2.resize(frame, (resizeWidth, resizeHeight))
                cv2.putText(frameSm, 'Frame {}'.format(int(cap.get(cv2.CAP_PROP_POS_FRAMES))), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255))
                processVisImgs[resizeHeight * 0:resizeHeight * 1, resizeWidth * 1:resizeWidth * 2] = frameSm
                cv2.imshow('Visualise Processing', processVisImgs)

            # If we went one frame, stop from going another
            if goOneFrame:
                goOneFrame = False

        k = cv2.waitKey(waitTime) & 0xff
        if k == ord('v'):
            visualise = not visualise
        elif k == ord('k'):  # play pause
            paused = not paused
        elif k == ord('j'):  # prev frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, cap.get(cv2.CAP_PROP_POS_FRAMES) - 2)
            goOneFrame = True
        elif k == ord('l'):  # next frame
            goOneFrame = True
        elif k == ord('.'):  # speed up
            waitTime -= 5
            print(waitTime)
        elif k == ord(','):  # slow down
            waitTime += 5
            print(waitTime)
        elif ord('0') <= k <= ord('9'):
            num = k - ord('0')
            frameToJumpTo = (cap.get(cv2.CAP_PROP_FRAME_COUNT) / 10) * num
            cap.set(cv2.CAP_PROP_POS_FRAMES, frameToJumpTo)
            goOneFrame = True
        elif k == ord('u'):
            routine.use = 0 if routine.use else 1
            db.commit()
            print("use updated to", routine.use)
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

    return centerPoints, hullLengths, trampolineTouches, personMasks
