import cv2
import numpy as np

def nothing(_unused):
    pass

colorMode = 0  # 0 = RBG, 1 = HSV

paths = ["C:/Users/psdco/Videos/Msc Media/vlcsnap-2016-11-03-12h30m47s590.png", "C:/Users/psdco/Videos/Msc Media/bg_empty 640x360.jpg"]
imgs = [cv2.imread(path) for path in paths]

if colorMode == 1:
    imgs = [cv2.cvtColor(img, cv2.COLOR_HSV2BGR) for img in imgs]

for i, img in enumerate(imgs):
    cv2.imshow("img"+i, img)

cv2.namedWindow('trackbars', cv2.WINDOW_AUTOSIZE)
# cv2.setMouseCallback('trackbars', onMouse)

trackBarMax = 255
if colorMode == 0:
    trackBarValues = [0, 110, 30, 150, 110, 250]
    trackBarNames = ['R_min','R_max','G_min','G_max','B_min','B_max']
else:
    trackBarValues = [0, 255, 0, 255, 0, 255]
    trackBarNames = ['H_min','H_max','S_min','S_max','V_min','V_max']

for i in range(6):
    cv2.createTrackbar(trackBarNames[i], 'trackbars', trackBarValues[i], trackBarMax, nothing)

while (1):
    # get current positions of four trackbars
    rmin = cv2.getTrackbarPos('h_min', 'trackbars')
    rmax = cv2.getTrackbarPos('h_max', 'trackbars')
    gmin = cv2.getTrackbarPos('s_min', 'trackbars')
    gmax = cv2.getTrackbarPos('s_max', 'trackbars')
    bmin = cv2.getTrackbarPos('v_min', 'trackbars')
    bmax = cv2.getTrackbarPos('v_max', 'trackbars')

    lower = np.array([bmin, gmin, rmin], dtype="uint8")
    upper = np.array([bmax, gmax, rmax], dtype="uint8")

    # find the colors within the specified boundaries and apply
    # the mask
    mask1 = cv2.inRange(img1, lower, upper)
    mask2 = cv2.inRange(img2, lower, upper)
    cv2.imshow('mask1', mask1)
    cv2.imshow('mask2', mask2)
    output1 = cv2.bitwise_and(img1, img1, mask=mask1)
    output2 = cv2.bitwise_and(img2, img2, mask=mask2)
    cv2.imshow("img1", output1)
    cv2.imshow("img2", output2)


    # binmask = mask/255  # binary mask
    # rowSums = np.sum(binmask, 1)  # sum each row
    # blueRows = []
    # i = 0
    # start = -1
    # while i < rowSums.size:
    #     if start == -1 and rowSums[i] > 30:
    #         start = i
    #     elif start > -1 and rowSums[i] < 30:
    #         blueRows.append([start, i])
    #         start = -1
    #     i += 1
    # print blueRows
    # # for i in range(len(blueRows)):
    # #     y1 = blueRows[i][0]
    # #     y2 = blueRows[i][1]
    # #     cv2.rectangle(img, (0, y1), (img.shape[1], y2), (0, 0, 255), 1)
    #
    # colSums = None
    # blueAreas = []
    # for i in range(len(blueRows)):
    #     y1 = blueRows[i][0]
    #     y2 = blueRows[i][1]
    #     colSums = np.sum(binmask[y1:y2], 0)
    #     print colSums
    #     start = -1
    #     k = 0
    #     while k < colSums.size:
    #         colVal = colSums[k]
    #         if start == -1 and colVal > 2:
    #             start = k
    #         elif start > -1 and (colVal < 2 or k == colSums.size-1):
    #             # y1 y2 x1 x2
    #             if k - start > 10:  # obj more than 10 pixels wide
    #                 blueAreas.append([y1, y2, start, k])
    #             start = -1
    #         k += 1
    # print blueAreas
    #
    # for i in range(len(blueAreas)):
    #     y1 = blueAreas[i][0]
    #     y2 = blueAreas[i][1]
    #     x1 = blueAreas[i][2]
    #     x2 = blueAreas[i][3]
    #     cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 1)
    #
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

    k = cv2.waitKey(1) & 0xFF
    if k == 27 or k == 'q':
        break


cv2.destroyAllWindows()
