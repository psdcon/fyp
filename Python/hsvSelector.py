import cv2
import numpy as np

def nothing(_unused):
    pass

def findBlue(img, mask):
    binmask = mask/255  # binary mask
    rowSums = np.sum(binmask, 1)  # sum across axis 1 = row
    # Get the start and end index of a clump or rows that have more than 30 unmasked (blue) pixels in them.
    blueRows = []
    i = 0
    start = -1
    while i < rowSums.size:
        if start == -1 and rowSums[i] > 30:
            start = i
        elif start > -1 and rowSums[i] < 30:
            blueRows.append([start, i])
            start = -1
        i += 1
    # print blueRows
    # for i in range(len(blueRows)):
    #     y1 = blueRows[i][0]
    #     y2 = blueRows[i][1]
    #     cv2.rectangle(img, (0, y1), (img.shape[1], y2), (0, 0, 255), 1)

    colSums = None
    blueAreas = []
    for i in range(len(blueRows)):
        y1 = blueRows[i][0]
        y2 = blueRows[i][1]
        colSums = np.sum(binmask[y1:y2], 0)
        # print colSums
        start = -1
        k = 0
        while k < colSums.size:
            colVal = colSums[k]
            if start == -1 and colVal > 2:
                start = k
            elif start > -1 and (colVal < 2 or k == colSums.size-1):
                # y1 y2 x1 x2
                if k - start > 10:  # obj more than 10 pixels wide
                    blueAreas.append([y1, y2, start, k])
                start = -1
            k += 1
    # print blueAreas

    for i in range(len(blueAreas)):
        y1 = blueAreas[i][0]
        y2 = blueAreas[i][1]
        x1 = blueAreas[i][2]
        x2 = blueAreas[i][3]
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 1)

    # cv2.imshow("imgDrawnOn", img)
    # k = cv2.waitKey(0)
    # exit()

    # _im2, contours, _hierarchy = cv2.findContours(mask.copy(), 1, 2)
    # cv2.drawContours(image, contours, -1, (0, 255, 0), 1)
    # cv2.imshow('image1', image)
    # cnt = contours[0]
    # x, y, w, h = cv2.boundingRect(cnt)
    # cv2.rectangle(output, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # show the images
    # cv2.imshow('output', output)


def main():
    colorMode = 0  # 0 = RBG, 1 = HSV

    paths = [
        # "C:/Users/psdco/Videos/Msc Media/vlcsnap-2016-11-03-12h30m47s590.png",
        "C:/Users/psdco/Videos/Msc Media/bg_empty 640x360.jpg",
        "C:/Users/psdco/Videos/Msc Media/vlcsnap-2016-11-14-19h02m40s002.png",
        # "C:/Users/psdco/Videos/Inhouse/IMG_20161106_110810.jpg"
    ]
    imgs = [cv2.imread(path) for path in paths]

    if colorMode == 1:
        imgs = [cv2.cvtColor(img, cv2.COLOR_HSV2BGR) for img in imgs]

    for i, img in enumerate(imgs):
        cv2.imshow("img{}".format(i), img)

    cv2.namedWindow('trackbars', cv2.WINDOW_AUTOSIZE)
    # cv2.setMouseCallback('trackbars', onMouse)

    trackBarMax = 255
    if colorMode == 0:
        trackBarInitalValues = [0, 125, 40, 130, 130, 255]
        trackBarNames = ['B_min','B_max','G_min','G_max','R_min','R_max']
    else:
        # trackBarInitalValues = [0, 255, 0, 255, 0, 255]
        trackBarInitalValues = [50, 95, 0, 50, 0, 60]
        trackBarNames = ['H_min','H_max','S_min','S_max','V_min','V_max']

    for i in range(len(trackBarInitalValues)):
        cv2.createTrackbar(trackBarNames[i], 'trackbars', trackBarInitalValues[i], trackBarMax, nothing)

    while (1):
        # get current positions of four trackbars
        minvals = [cv2.getTrackbarPos(tbn, 'trackbars') for tbn in trackBarNames if "_min" in tbn]
        maxvals = [cv2.getTrackbarPos(tbn, 'trackbars') for tbn in trackBarNames if "_max" in tbn]

        lower = np.array(minvals, dtype="uint8")
        upper = np.array(maxvals, dtype="uint8")

        # find the colours within the specified boundaries and apply the mask
        masks = [cv2.inRange(img, lower, upper) for img in imgs]
        outputs = [cv2.bitwise_and(img, img, mask=mask) for img, mask in zip(imgs, masks)]

        for i, img in enumerate(outputs):
            findBlue(img, masks[i])
            # cv2.imshow("mask{}".format(i), masks[i])
            cv2.imshow("img{}".format(i), img)

        k = cv2.waitKey(1) & 0xFF
        if k == 27 or k == ord('q'):
            break


    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
