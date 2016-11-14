from __future__ import print_function
import numpy as np
import cv2
import matplotlib.pyplot as plt

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

# want to add coverted videos to the dictionary
# want to have a option to add tacking vids, priority of ones that havent got it yet.



def main():
    trampolineTop = 320  # take2 720x480 = 310, day2take3 720x480 = 295, colm 350
    vidPath = "C:/Users/psdco/Videos/Inhouse/480p/VID_20161106_112413_720x480.mp4"
    cap = cv2.VideoCapture(vidPath)
    if not cap.isOpened():
        print("Unable to open video file: %s", vidPath)

    capWidth = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    capHeight = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    resizeWidth = int(capWidth * scalingFactor)
    resizeHeight = int(capHeight * scalingFactor)

    # Create windows
    KNNImages = np.zeros(shape=(resizeHeight * 3, resizeWidth, 3), dtype=np.uint8)  # (h * 3, w, CV_8UC3);

    # Create mask around trampoline
    maskAroundTrampoline = np.zeros(shape=(capHeight, capWidth), dtype=np.uint8)  # cv2.CV_8U
    maskAroundTrampoline[0:trampolineTop, int(capWidth * 0.3):int(capWidth * 0.7)] = 255  # [y1:y2, x1:x2]

    pKNN = cv2.createBackgroundSubtractorKNN()
    pKNN.setShadowValue(0)

    # Center point stuff
    centroids = []
    elipseoids = []
    # plt.ion()
    # plt.axhline(y=capHeight-trampolineTop, xmin=0, xmax=1000, hold=None)

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


# Save a video http://docs.opencv.org/3.1.0/dd/d43/tutorial_py_video_display.html
