# Import statements
import json
import os

import cv2
import numpy as np
from sqlalchemy import or_
from sqlalchemy.orm.exc import NoResultFound

from helpers import consts
from helpers import helper_funcs
from helpers.db_declarative import getDb, Routine, Frame
from image_processing import track
from image_processing.visualise import _draw_pose_on_frame


def save_cropped_frames(db, routine, frames, suffix=None):
    routineDirPath = routine.getAsDirPath(suffix, create=True)

    # plt.figure()
    position = np.array([routine.video_height - frame_data.center_pt_y for frame_data in frames])
    scaleWithPerson = False
    # scaleWithPerson = frames[0].hull_max_length is not None
    cropLengths = []
    cropLength = 0
    if scaleWithPerson:  # hull length
        # Compensate... something
        cropLengths = np.array([frame_data.hull_max_length for frame_data in frames])

        cropLengths[np.nonzero(position < np.median(position))] = int(np.average(cropLengths) * 1.1)
        # plt.plot(cropLengths, label="Hull Length", color="blue")
        # # plt.axhline(np.average(cropLengths), label="Average Length", color="blue")
        # # plt.axhline(np.median(cropLengths), label="Med Length", color="purple")
    else:  # Ellipse lengths
        hullLengths = [frame_data.hull_max_length for frame_data in frames]
        # plt.plot(hullLengths, label="Hull Length", color="blue")

        cropLength = helper_funcs.get_crop_length(hullLengths) + 10
        routine.crop_length = cropLength
        db.commit()

        # # plt.axhline(np.average(hullLengths), label="Average Length", color="blue")
        # plt.axhline(cropLength, label="Percentile", color="blue")
        # plt.axhline(routine.crop_length, label="routine.crop_length", color="orange")

    # plt.plot(position, label="Position", color="green")
    # plt.xlabel("Time (s)")
    # plt.legend(loc="best")
    # plt.show(block=False)

    trampolineTouches = np.array([frame.trampoline_touch for frame in routine.frames])
    trampolineTouches = helper_funcs.trim_touches(trampolineTouches)

    personMasks = helper_funcs.load_zipped_pickle(routine.personMasksPath())

    cap = helper_funcs.open_video(routine.path)
    frame = []
    for i, frame_data in enumerate(frames):
        # ignore frames where trampoline is touched
        if trampolineTouches[i] == 1:
            continue
        # ignore any frame that aren't tracked
        while frame_data.frame_num != cap.get(cv2.CAP_PROP_POS_FRAMES):
            ret, frame = cap.read()
            if not ret:
                print('Something went wrong')
                return

        cx = frame_data.center_pt_x
        cy = frame_data.center_pt_y
        # Use original background or darken
        if True:
            frameCropped = track.highlightPerson(frame, np.array(json.loads(personMasks[frame_data.frame_num]), dtype=np.uint8), cx, cy, cropLength)
        else:
            x1, x2, y1, y2 = helper_funcs.crop_points_constrained(routine.video_height, routine.video_width, cx, cy, cropLength)
            frameCropped = frame[y1:y2, x1:x2]
        frameCropped = cv2.resize(frameCropped, (256, 256))

        # cv2.imshow('Track ', frameCropped)
        # k = cv2.waitKey(50) & 0xff

        imgName = routineDirPath + "frame_{0:04}.png".format(frame_data.frame_num)
        # print("Writing frame to {}".format(imgName))
        cv2.imwrite(imgName, frameCropped)

    # Done
    cap.release()
    db.commit()
    print("Done saving frames")


#
# Making images for web interface
#
def bounce_to_gif(db, bounce):
    from helpers.consts import bouncesRootPath
    gifFilepath = bouncesRootPath + '{}.gif'.format(bounce.id)
    if os.path.exists(gifFilepath):
        print("Image exists: {}".format(gifFilepath))
        return

    import imageio
    routine = bounce.routine

    cap = helper_funcs.open_video(routine.path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, bounce.start_frame)
    peak = bounce.max_height_frame
    peaksIndex = 0

    images = []
    while 1:
        _ret, frame = cap.read()

        if int(cap.get(cv2.CAP_PROP_POS_FRAMES)) >= bounce.end_frame:
            break

        if peak == int(cap.get(cv2.CAP_PROP_POS_FRAMES)):
            peaksIndex = len(images)

        try:
            frame_data = db.query(Frame).filter_by(routine_id=routine.id, frame_num=cap.get(cv2.CAP_PROP_POS_FRAMES)).one()
        except NoResultFound:
            continue

        cx = frame_data.center_pt_x
        cy = frame_data.center_pt_y

        x1, x2, y1, y2 = helper_funcs.crop_points_constrained(routine.video_height, routine.video_width, cx, cy, routine.crop_length)
        if not frame_data.pose:
            continue
        pose = np.array(json.loads(frame_data.pose))

        frameCropped = frame[y1:y2, x1:x2]
        frameCropped = cv2.resize(frameCropped, (256, 256))
        # cv2.putText(frameCropped, '{}'.format(prevBounceName), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255))
        cv2.putText(frameCropped, '{}'.format(frame_data.frame_num), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255))
        frameCropped = _draw_pose_on_frame(pose, frameCropped)

        images.append(cv2.cvtColor(frameCropped, cv2.COLOR_BGR2RGB))

    print("Writing to: {}".format(gifFilepath))
    imageio.mimwrite(gifFilepath, images[::2])

    if peaksIndex == 0:
        peaksIndex = int(len(images) / 2)
    jpgFilepath = bouncesRootPath + '{}.jpg'.format(bounce.id)
    imageio.imwrite(jpgFilepath, images[peaksIndex])


def generate_many_thumbnails():
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
