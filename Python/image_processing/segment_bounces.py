import numpy as np

from helpers.db_declarative import Bounce
from libs.peakdetect import peakdetect


def segment_bounces_and_save(db, routine):
    bounces = calculate_bounces(routine)
    db.add_all(bounces)
    db.commit()


def calculate_bounces(routine):
    x = np.array([frame.center_pt_x for frame in routine.frames])
    y = np.array([frame.center_pt_y for frame in routine.frames])
    maxima, minima = peakdetect(y, x, lookahead=8, delta=20)

    bounces = []
    for i in range(len(minima)):
        thisBedHit = minima[i]
        nextBedHit = minima[i + 1]
        jumpMaxHeight = maxima[i]

        # routine_id, bounce_index, skill_name, start_frame, max_height_frame, end_frame, start_time,
        # max_height_time, end_time, start_height, max_height, end_height)
        bounces.append(Bounce(
            routine.id,
            i,
            "",

            thisBedHit['x'],
            jumpMaxHeight['x'],
            nextBedHit['x'],

            round(float(thisBedHit['x'] / routine.video_fps), 2),
            round(float(jumpMaxHeight['x'] / routine.video_fps), 2),
            round(float(nextBedHit['x'] / routine.video_fps), 2),

            thisBedHit['y'],
            jumpMaxHeight['y'],
            nextBedHit['y']
        ))

    return bounces
