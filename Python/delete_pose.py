import glob
import os
from helpers.db_declarative import getDb, Routine

db = getDb()

routines = db.query(Routine).filter(Routine.use == 1).all()

for routine in routines:
    if routine.id < 57:
        continue

    dirPath = routine.getAsDirPath('_blur_dark_0.6')
    framesToKeep = glob.glob(dirPath + 'frame_*')
    allFiles = glob.glob(dirPath + '*')

    # Delete files
    for frame in framesToKeep:
        allFiles.remove(frame)

    filesToRemove = allFiles

    for f in filesToRemove:
        os.remove(f)
