import matplotlib.pyplot as plt
import numpy as np

from helpers.db_declarative import Bounce
from libs.peakdetect import peakdetect


def segment_bounces_and_save(db, routine):
    # Includes landing bounce (from end of last bounce to end of video)
    bounces = calculate_bounces(routine)

    # Don't update db if something seems weird with the bounces
    if len(routine.bounces) is 0:  # No bounces have been saved before
        db.add_all(bounces)
        db.flush()  # gives bounces ids

        # Associate a bounce with each frame
        for bounce in bounces:
            frames = bounce.getFrames(db)
            for frame in frames:
                frame.bounce_id = bounce.id
        db.commit()

        print("Added {} bounces".format(len(routine.bounces)))

    elif len(routine.bounces) == len(bounces):
        print('Already done, in the hype')
        return

    # Bounces were found but there's a mismatch. (The tracking was messed up before or there's no landing bounce)
    else:  # if len(routine.bounces) != len(bounces):
        print("Error with bounce count. Db has {}, found {}. Fixing...".format(len(routine.bounces), len(bounces)))
        print("Nothing was done")
        return
        # # Update the names and deductions from the old bounces to refer to the new ones.
        # old_bounces = list(routine.bounces)
        # if len(old_bounces) > len(bounces):  # if we've found less than there was previously then chop off the end bounces so the loop doesnt over run
        #     old_bounces = old_bounces[:len(bounces)]
        # for i, old_bounce in enumerate(old_bounces):
        #     # Add name from old bounce to the new one for corresponding bounces
        #     bounces[i].skill_name = old_bounce.skill_name
        #
        # # Delete all the old bounces
        # for old_bounce in routine.bounces:
        #     db.delete(old_bounce)
        #
        # # Mark the routine as having changed
        # routine.dirtyBounces = 1
        #
        # db.add_all(bounces)
        # db.add(landingBounce)
        # db.commit()
        # print("Landing added")


def calculate_bounces(routine):
    print("Segmenting bounces")
    x = np.array([frame.frame_num for frame in routine.frames])
    y = np.array([routine.video_height - frame.center_pt_y for frame in routine.frames])

    pc = np.percentile(y, 5)
    delta = pc - np.min(y)

    maxima, minima = peakdetect(y, x, lookahead=8, delta=delta)
    # maxima, minima = peakdetect(y, x, lookahead=5, delta=10)

    # Plot bounce heights
    if routine.id == 26:
        peaks = maxima + minima  # concat the two
        peaks_x = [pt['x'] for pt in peaks]
        peaks_y = [pt['y'] for pt in peaks]

        plt.figure("Bounce Peaks")
        plt.title("Height")
        plt.plot(x, y, color="g")
        plt.plot(peaks_x, peaks_y, 'r+')
        plt.ylabel('Height (Pixels)')
        plt.show(block=True)

    bounces = []
    i = 0
    for i in range(len(minima) - 1):
        thisBedHit = minima[i]
        nextBedHit = minima[i + 1]
        jumpMaxHeight = maxima[i]

        # routine_id, bounce_index, skill_name, start_frame, max_height_frame, end_frame, start_time,
        # max_height_time, end_time, start_height, max_height, end_height)
        bounces.append(Bounce(
            routine.id,
            i,
            None,
            # Frame Numbers
            thisBedHit['x'],
            jumpMaxHeight['x'],
            nextBedHit['x'],
            # Timestamps in 0.00s
            round(float(thisBedHit['x'] / routine.video_fps), 2),
            round(float(jumpMaxHeight['x'] / routine.video_fps), 2),
            round(float(nextBedHit['x'] / routine.video_fps), 2),
            # Heights (Not yet used)
            thisBedHit['y'],
            jumpMaxHeight['y'],
            nextBedHit['y']
        ))

    # Add landing bounce
    bounces.append(Bounce(
        routine.id,
        i + 1,
        "Landing",
        nextBedHit['x'],  # start of this is the end of the last bounce
        0,  # Not used
        x[-1],  # End of video
        round(float(nextBedHit['x'] / routine.video_fps), 2),
        round(float(0 / routine.video_fps), 2),
        round(float(x[-1] / routine.video_fps), 2),
        # Not used
        0, 0, 0
    ))

    return bounces
