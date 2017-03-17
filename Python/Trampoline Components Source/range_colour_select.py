import cv2
import numpy as np

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
    # print blueRows
    # for i in range(len(blueRows)):
    #     y1 = blueRows[i][0]
    #     y2 = blueRows[i][1]
    #     cv2.rectangle(img, (0, y1), (img.shape[1], y2), (0, 0, 255), 1)

    blueAreas = []
    for i in range(0, len(blueRows)):
        y1 = blueRows[i][0]
        y2 = blueRows[i][1]
        colSums = np.sum(binmask[y1:y2], 0)
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
    # print blueAreas

    for i in range(0, len(blueAreas)):
        y1 = blueAreas[i][0]
        y2 = blueAreas[i][1]
        x1 = blueAreas[i][2]
        x2 = blueAreas[i][3]
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 1)

    biggestArea = 0
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
            trampolineTop = min(y1, y2)

    return trampolineTop


global coloursToShow
coloursToShow = []


def modColourRange(event, x, y, flags, img):
    if event == cv2.EVENT_LBUTTONDOWN:
        px = img[y, x]
        coloursToShow.append(px)
        print coloursToShow
    elif event == cv2.EVENT_RBUTTONDOWN:
        px = img[y, x]
        coloursToShow.remove(px)  # this doesnt work
        print coloursToShow


imgPaths = [
    "C:/Users/psdco/Videos/Msc Media/bg_empty 640x360.jpg",
    "C:/Users/psdco/Videos/Msc Media/vlcsnap-2016-11-03-12h30m47s590.png",
    "C:/Users/psdco/Videos/Msc Media/vlcsnap-2016-11-14-19h02m40s002.png",
    # "C:/Users/psdco/Videos/Inhouse/IMG_20161106_110810.jpg"
]
def main():
    imgs = [cv2.imread(path) for path in imgPaths]

    # Preselected these numbers while testing
    coloursToShow = [np.array([152,  82,  83], dtype=np.uint8), np.array([94, 55, 47], dtype=np.uint8), np.array([60, 46, 40], dtype=np.uint8), np.array([132,  86,  18], dtype=np.uint8), np.array([131,  79,  43], dtype=np.uint8), np.array([117,  62,  31], dtype=np.uint8), np.array([109,  64,  31], dtype=np.uint8), np.array([106,  62,  33], dtype=np.uint8), np.array([140,  79,  45], dtype=np.uint8), np.array([93, 57, 33], dtype=np.uint8), np.array([103,  60,  41], dtype=np.uint8), np.array([98, 61, 39], dtype=np.uint8), np.array([116,  67,  45], dtype=np.uint8), np.array([130,  73,  47], dtype=np.uint8), np.array([90, 58, 52], dtype=np.uint8), np.array([136,  74,  50], dtype=np.uint8), np.array([109,  62,  31], dtype=np.uint8), np.array([109,  62,  31], dtype=np.uint8), np.array([181,  92,  42], dtype=np.uint8), np.array([144,  53,  22], dtype=np.uint8), np.array([166,  68,  34], dtype=np.uint8), np.array([211, 102,  46], dtype=np.uint8), np.array([119,  49,  26], dtype=np.uint8), np.array([210,  99,  51], dtype=np.uint8), np.array([213, 106,  55], dtype=np.uint8), np.array([195,  97,  57], dtype=np.uint8), np.array([193, 101,  54], dtype=np.uint8), np.array([166,  68,  38], dtype=np.uint8), np.array([144,  60,  34], dtype=np.uint8), np.array([78, 25, 15], dtype=np.uint8), np.array([132,  61,  28], dtype=np.uint8), np.array([52, 23, 16], dtype=np.uint8), np.array([191, 124, 121], dtype=np.uint8), np.array([123,  64,  55], dtype=np.uint8), np.array([189, 118, 128], dtype=np.uint8), np.array([152,  82,  83], dtype=np.uint8), np.array([180, 112, 119], dtype=np.uint8), np.array([120,  57,  67], dtype=np.uint8), np.array([127,  64,  74], dtype=np.uint8), np.array([146,  92,  21], dtype=np.uint8), np.array([143,  90,  21], dtype=np.uint8), np.array([130,  82,  19], dtype=np.uint8), np.array([83, 26,  0], dtype=np.uint8), np.array([231, 174, 141], dtype=np.uint8), np.array([197, 162, 143], dtype=np.uint8), np.array([214, 182, 168], dtype=np.uint8), np.array([202, 160, 127], dtype=np.uint8), np.array([183, 131,  74], dtype=np.uint8), np.array([214, 156,  76], dtype=np.uint8), np.array([230, 172,  89], dtype=np.uint8), np.array([169, 109,   0], dtype=np.uint8), np.array([172, 110,   3], dtype=np.uint8), np.array([177, 110,   5], dtype=np.uint8), np.array([173, 106,   3], dtype=np.uint8), np.array([169, 107,   3], dtype=np.uint8), np.array([176, 110,   9], dtype=np.uint8), np.array([184, 118,  15], dtype=np.uint8), np.array([181, 117,   3], dtype=np.uint8), np.array([163,  98,   0], dtype=np.uint8), np.array([192, 116,  72], dtype=np.uint8), np.array([216, 135,  89], dtype=np.uint8), np.array([116,  71,  15], dtype=np.uint8), np.array([168, 116,  33], dtype=np.uint8), np.array([97, 33,  0], dtype=np.uint8), np.array([96, 32,  0], dtype=np.uint8), np.array([98, 33,  0], dtype=np.uint8), np.array([93, 27,  0], dtype=np.uint8), np.array([101,  34,   0], dtype=np.uint8), np.array([98, 35,  0], dtype=np.uint8), np.array([216, 157, 107], dtype=np.uint8), np.array([214, 164, 119], dtype=np.uint8), np.array([194, 136,  87], dtype=np.uint8), np.array([212, 149,  95], dtype=np.uint8), np.array([194, 125,  66], dtype=np.uint8), np.array([160,  86,  32], dtype=np.uint8), np.array([173, 109,   6], dtype=np.uint8)]

    for i, img in enumerate(imgs):
        # cv2.imshow("img{}".format(i), img)
        cv2.setMouseCallback("img{}".format(i), modColourRange, img)

    while 1:
        masks = [np.zeros((img.shape[0], img.shape[1]), np.uint8) for img in imgs]
        for c in coloursToShow:
            lower = c-20
            lower.clip(0)  # lower[lower<0] = 0
            upper = c+20
            upper.clip(max=255)  # upper[upper>255] = 255
            imageMasks = [cv2.inRange(img, lower, upper) for img in imgs]
            masks = [cm | im for cm, im in zip(masks, imageMasks)] # or the two masks together

        # find the colours within the specified boundaries and apply the mask
        imgMasked = [cv2.bitwise_and(img, img, mask=mask) for img, mask in zip(imgs, masks)]

        for i, img in enumerate(imgs):
            findBlue(imgMasked[i], masks[i])
            # cv2.imshow("mask{}".format(i), masks[i])
            # cv2.imshow("img{}".format(i), img)
            cv2.imshow("masked op{} ".format(i), imgMasked[i])

        k = cv2.waitKey(1) & 0xFF
        if k == ord('z'):  # undo
            coloursToShow = coloursToShow[:-1]
        elif k == 27 or k == ord('q'):
            break

    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
