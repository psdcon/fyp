import os

import cv2
from sqlalchemy import or_

from helpers import consts
from helpers import helper_funcs
from helpers.db_declarative import Routine
from helpers.db_declarative import getDb


def generate_many():
    db = getDb()

    routines = db.query(Routine).filter(or_(Routine.use == 1, Routine.use == None)).all()

    for routine in routines:
        generate_thumbnail(routine)


def generate_thumbnail(routine):
    thumbFilePath = os.path.join(consts.thumbDir, '{}.jpg'.format(routine.id))
    # if os.path.exists(thumbFilePath):
    #     print('Found existing thumb')
    #     return

    cap = helper_funcs.open_video(routine.path)
    _ret, frame = cap.read()

    # Calculate dimens
    percentToKeep = 0.35
    percentFromCenter = percentToKeep / 2
    height, width = frame.shape[:2]
    cropTop = int(height * percentFromCenter)
    cropBottom = int(height * (1 - percentFromCenter))
    cropLeft = int(width * percentFromCenter)
    cropRight = int(width * (1 - percentFromCenter))

    # Crop
    frame = frame[cropTop:cropBottom, cropLeft:cropRight]
    # Shrink
    frame = cv2.resize(frame, (frame.shape[1] / 2, frame.shape[0] / 2))
    cv2.imwrite(thumbFilePath, frame)

    print('Thumbnail created: {}'.format(thumbFilePath))


if __name__ == '__main__':
    generate_many()
