import os

import cv2
import numpy as np

from helpers import consts
from helpers import helper_funcs
from helpers.db_declarative import getDb, Routine

db = getDb()

# Add frame count to database table
routines = db.query(Routine).all()
for routine in routines:
    pathToVideo = os.path.join(consts.videosRootPath, routine.path)
    cap = cv2.VideoCapture(pathToVideo)
    routine.frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
db.commit()
exit()

routines = db.query(Routine).filter(Routine.use == 1).all()
# routines = db.query(Routine).filter(Routine.id == 35).all()
# if False:
# Delete frames coming from some other routine... :/
for routine in routines:
    cap = helper_funcs.open_video(routine.path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if routine.frames[-1].frame_num > frame_count:
        for frame in routine.frames:
            if frame.frame_num > frame_count:
                db.delete(frame)
db.commit()

# else:
# Delete duplicate entries for routine in frame_data (Won't catch back to back)
for routine in routines:
    frameDataIds = [frame.id for frame in routine.frames]
    diff = np.diff(frameDataIds)
    boundaryIndex = np.nonzero(diff > 1)[0]
    if boundaryIndex:
        frames2Delete = routine.frames[:boundaryIndex + 1]
        for frame in frames2Delete:
            db.delete(frame)
db.commit()
