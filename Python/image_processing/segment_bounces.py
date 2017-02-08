import numpy as np

from helpers.db_declarative import Bounce
from libs.peakdetect import peakdetect
import matplotlib.pyplot as plt


def segment_bounces_and_save(db, routine):

    bounces = calculate_bounces(routine)
    # No bounces have been saved before
    if len(routine.bounces) is 0:
        db.add_all(bounces)
        db.commit()
        print("Bounces updated")
    # Bounces were found but there's a mismatch. (The tracking was messed up before)
    elif len(routine.bounces) is not len(bounces):
        print("Error with bounce count. Db has {}, found {}".format(len(routine.bounces), len(bounces)))
    else:
        print("Bounces found in db. No update.")



def calculate_bounces(routine):
    x = np.array([frame.frame_num for frame in routine.frames])
    y = np.array([routine.video_height - frame.center_pt_y for frame in routine.frames])
    maxima, minima = peakdetect(y, x, lookahead=8, delta=20)

    # Plot bounce heights
    # peaks = maxima + minima  # concat the two
    # peaks_x = [pt['x'] for pt in peaks]
    # peaks_y = [pt['y'] for pt in peaks]
    #
    # plt.title("Height")
    # plt.plot(x, y, color="g")
    # plt.plot(peaks_x, peaks_y, 'r+')
    # plt.ylabel('Height (Pixels)')
    # plt.show()

    bounces = []
    for i in range(len(minima)-1):
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
