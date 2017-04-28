import matplotlib.pyplot as plt
import numpy as np

from helpers import consts
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
    if True:
        # peaks = maxima + minima  # concat the two
        peaks = minima  # concat the two
        peaks_x = [pt['x'] for pt in peaks]
        peaks_y = [pt['y'] for pt in peaks]

        fig, ax = plt.subplots(figsize=(8.8, 3))
        # plt.figure("Bounce Peaks")
        # plt.title("Height")
        l2 = plt.scatter(np.array(peaks_x) / 30., np.array(peaks_y), c='C3', marker='o', label="Max Trampoline\nDisplacement")
        l1, = plt.plot(x / 30., y, c='C2', label="Athlete Height")
        l3 = plt.axhline(routine.video_height - routine.trampoline_top, c="C0", label="Trampoline Top")
        plt.ylabel('Height (Pixels)')
        plt.xlabel('Time (s)')
        plt.legend()
        # fig.legend((l2, l1, l3), ("Max Trampoline\nDisplacement", "Athlete Height", "Trampoline Top"))
        fig.tight_layout(pad=0)
        x0, x1, y0, y1 = plt.axis()
        plt.axis((x0,
                  x1 + 1,
                  y0 - 15,
                  y1))
        imgName = consts.thesisImgPath + "segment_bounces.pdf"
        print("Writing image to {}".format(imgName))
        plt.savefig(imgName)
        plt.show(block=False)
        pass

    bounces = []
    i = 0
    for i in range(len(minima) - 1):
        thisBedHit = minima[i]
        nextBedHit = minima[i + 1]
        jumpMaxHeight = maxima[i]

        # routine_id, bounce_index, skill_name, start_frame, apex_frame, end_frame, start_time,
        # apex_time, end_time, start_height, apex_height, end_height)
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
