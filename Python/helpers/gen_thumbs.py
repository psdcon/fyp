import os

import cv2

from helpers import consts
from helpers import helper_funcs
from helpers.db_declarative import db, Routine

routines = db.query(Routine).all()
for r in routines:
    thumbFilePath = os.path.join(consts.thumbDir, os.path.basename(r.path).replace('.mp4', '.jpg'))
    # if os.path.exists(thumbFilePath):
    #     continue
    cap = helper_funcs.open_video(r.path)
    _ret, frame = cap.read()

    # Calculate dimens
    percToKeep = 0.4
    percFromCenter = percToKeep / 2
    height, width = frame.shape[:2]
    cropTop = height * percFromCenter
    cropBottom = height * (1 - percFromCenter)
    cropLeft = width * percFromCenter
    cropRight = width * (1 - percFromCenter)

    # Crop
    frame = frame[cropTop:cropBottom, cropLeft:cropRight]
    # Shrink
    frame = cv2.resize(frame, (frame.shape[1] / 4, frame.shape[0] / 4))
    cv2.imwrite(thumbFilePath, frame)
