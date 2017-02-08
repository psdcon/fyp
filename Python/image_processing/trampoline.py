import cv2
import numpy as np


def detect_trampoline(db, cap, routine):
    trampoline = find_trampoline(cap, routine)

    routine.trampoline_top = trampoline['top']
    routine.trampoline_center = trampoline['center']
    db.commit()

    print("Trampoline has been set to " + repr(trampoline))


def find_trampoline(cap, routine):
    maskLeftBorder = int(routine.video_width * 0.3)
    maskRightBorder = int(routine.video_width * 0.7)

    # print("Trampoline Top has not yet been set!")
    print("Use the arrow keys to adjust the cross hairs.")
    print("Press ENTER to save, 'c' to continue without save, and ESC/'q' to quit")

    _ret, frame = cap.read()

    # Take a best guess at where it might be
    trampoline = {
        'top': _trampoline_top_best_guess(frame),
        'center': routine.video_width / 2  # TODO this is a poor default
    }

    while 1:  # video will loop back to the start
        _ret, frame = cap.read()

        maskAroundTrampoline = np.zeros(shape=(routine.video_height, routine.video_width), dtype=np.uint8)
        maskAroundTrampoline[0:trampoline['top'], maskLeftBorder:maskRightBorder] = 255  # [y1:y2, x1:x2]
        frameCropped = cv2.bitwise_and(frame, frame, mask=maskAroundTrampoline)

        cv2.line(frame, (0, trampoline['top']), (routine.video_width, trampoline['top']), (0, 255, 0), 1)
        cv2.line(frame, (trampoline['center'], 0), (trampoline['center'], routine.video_height), (0, 255, 0), 1)

        cv2.imshow('Frame', frame)
        cv2.imshow('Frame Cropped', frameCropped)

        k = cv2.waitKey(100)
        res = k
        # TODO this is broken... DONE: Fixed it with asdw
        # print 'You pressed %d (0x%x), LSB: %d (%s)' % (res, res, res % 256,
        #                                                repr(chr(res % 256)) if res % 256 < 128 else '?')
        if k == ord('w'):  #2490368:  # up
            trampoline['top'] -= 1
        elif k == ord('s'):  #2621440:  # down
            trampoline['top'] += 1
        elif k == ord('a'):  #2424832:  # left
            trampoline['center'] -= 1
        elif k == ord('d'):  #2555904:  # right
            trampoline['center'] += 1
        elif k == ord('\n') or k == ord('\r'):  # return/enter key
            break
        elif k == ord('q') or k == 27:  # q/ESC
            print("Exiting...")
            exit()

        # Loop until return or exit pressed
        if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    cv2.destroyAllWindows()
    return trampoline


def _trampoline_top_best_guess(img):
    coloursToShow = [np.array([152, 82, 83], dtype=np.uint8), np.array([94, 55, 47], dtype=np.uint8),
                     np.array([60, 46, 40], dtype=np.uint8), np.array([132, 86, 18], dtype=np.uint8),
                     np.array([131, 79, 43], dtype=np.uint8), np.array([117, 62, 31], dtype=np.uint8),
                     np.array([109, 64, 31], dtype=np.uint8), np.array([106, 62, 33], dtype=np.uint8),
                     np.array([140, 79, 45], dtype=np.uint8), np.array([93, 57, 33], dtype=np.uint8),
                     np.array([103, 60, 41], dtype=np.uint8), np.array([98, 61, 39], dtype=np.uint8),
                     np.array([116, 67, 45], dtype=np.uint8), np.array([130, 73, 47], dtype=np.uint8),
                     np.array([90, 58, 52], dtype=np.uint8), np.array([136, 74, 50], dtype=np.uint8),
                     np.array([109, 62, 31], dtype=np.uint8), np.array([109, 62, 31], dtype=np.uint8),
                     np.array([181, 92, 42], dtype=np.uint8), np.array([144, 53, 22], dtype=np.uint8),
                     np.array([166, 68, 34], dtype=np.uint8), np.array([211, 102, 46], dtype=np.uint8),
                     np.array([119, 49, 26], dtype=np.uint8),
                     np.array([210, 99, 51], dtype=np.uint8), np.array([213, 106, 55], dtype=np.uint8),
                     np.array([195, 97, 57], dtype=np.uint8), np.array([193, 101, 54], dtype=np.uint8),
                     np.array([166, 68, 38], dtype=np.uint8), np.array([144, 60, 34], dtype=np.uint8),
                     np.array([78, 25, 15], dtype=np.uint8), np.array([132, 61, 28], dtype=np.uint8),
                     np.array([52, 23, 16], dtype=np.uint8), np.array([191, 124, 121], dtype=np.uint8),
                     np.array([123, 64, 55], dtype=np.uint8), np.array([189, 118, 128], dtype=np.uint8),
                     np.array([152, 82, 83], dtype=np.uint8), np.array([180, 112, 119], dtype=np.uint8),
                     np.array([120, 57, 67], dtype=np.uint8), np.array([127, 64, 74], dtype=np.uint8),
                     np.array([146, 92, 21], dtype=np.uint8), np.array([143, 90, 21], dtype=np.uint8),
                     np.array([130, 82, 19], dtype=np.uint8), np.array([83, 26, 0], dtype=np.uint8),
                     np.array([231, 174, 141], dtype=np.uint8), np.array([197, 162, 143], dtype=np.uint8),
                     np.array([214, 182, 168], dtype=np.uint8),
                     np.array([202, 160, 127], dtype=np.uint8), np.array([183, 131, 74], dtype=np.uint8),
                     np.array([214, 156, 76], dtype=np.uint8), np.array([230, 172, 89], dtype=np.uint8),
                     np.array([169, 109, 0], dtype=np.uint8), np.array([172, 110, 3], dtype=np.uint8),
                     np.array([177, 110, 5], dtype=np.uint8), np.array([173, 106, 3], dtype=np.uint8),
                     np.array([169, 107, 3], dtype=np.uint8), np.array([176, 110, 9], dtype=np.uint8),
                     np.array([184, 118, 15], dtype=np.uint8), np.array([181, 117, 3], dtype=np.uint8),
                     np.array([163, 98, 0], dtype=np.uint8), np.array([192, 116, 72], dtype=np.uint8),
                     np.array([216, 135, 89], dtype=np.uint8), np.array([116, 71, 15], dtype=np.uint8),
                     np.array([168, 116, 33], dtype=np.uint8), np.array([97, 33, 0], dtype=np.uint8),
                     np.array([96, 32, 0], dtype=np.uint8), np.array([98, 33, 0], dtype=np.uint8),
                     np.array([93, 27, 0], dtype=np.uint8), np.array([101, 34, 0], dtype=np.uint8),
                     np.array([98, 35, 0], dtype=np.uint8),
                     np.array([216, 157, 107], dtype=np.uint8), np.array([214, 164, 119], dtype=np.uint8),
                     np.array([194, 136, 87], dtype=np.uint8), np.array([212, 149, 95], dtype=np.uint8),
                     np.array([194, 125, 66], dtype=np.uint8), np.array([160, 86, 32], dtype=np.uint8),
                     np.array([173, 109, 6], dtype=np.uint8)]

    mask = np.zeros((img.shape[0], img.shape[1]), np.uint8)
    for c in coloursToShow:
        lower = c - 20
        lower.clip(0)  # lower[lower<0] = 0
        upper = c + 20
        upper.clip(max=255)  # upper[upper>255] = 255
        thisMask = cv2.inRange(img, lower, upper)
        mask = mask | thisMask

    imgMasked = cv2.bitwise_and(img, img, mask=mask)

    return _find_blue(imgMasked, mask)


def _find_blue(img, mask):
    binaryMask = mask / 255  #
    # binary mask
    rowSums = np.sum(binaryMask, 1)  # sum across axis 1 = row
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
        colSums = np.sum(binaryMask[y1:y2], 0)  # sum axis 0, columns
        # print colSums
        insideClump = -1
        for k in range(0, colSums.size):
            colVal = colSums[k]
            if insideClump == -1 and colVal > 2:
                insideClump = k
            elif insideClump > -1 and (colVal < 2 or k == colSums.size - 1):
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
