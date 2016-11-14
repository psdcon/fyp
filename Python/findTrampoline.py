import cv2
import numpy as np

path = "C:/Users/psdco/Videos/Msc Media/bg_empty 640x360.jpg"
img = cv2.imread(path)
# cv2.imshow('image', image)

kernalHeight = 10
cv2.imshow('blue channel', img[:,:,0])
# for row in range(0, image.shape[0]-kernalHeight):
    # image[0][row:kernalHeight, 0:image.shape[1]]

# hsvImage = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
# cv2.imshow('hsvImage', hsvImage)

# create NumPy arrays for bgr
# lower = np.array([100,90,45], dtype="uint8")
# upper = np.array([200,110,95], dtype="uint8")
#
# # find the colors within the specified boundaries and apply
# # the mask
# mask = cv2.inRange(image, lower, upper)
# output = cv2.bitwise_and(image, image, mask=mask)
# cv2.imshow("output", output)
#
cv2.waitKey(0)
