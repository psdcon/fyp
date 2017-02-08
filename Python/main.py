from __future__ import division
from __future__ import print_function

from collections import OrderedDict

import cv2
import matplotlib.pyplot as plt
from scipy import signal
from scipy.spatial.distance import euclidean
from sqlalchemy.orm import sessionmaker

from gui.showRoutineSelectDialog import show_selection_menu
from helpers import helper
from helpers.db_declarative import *
from image_processing import visualise, track, trampoline, segment_bounces, write_reads
from libs.fastdtw import fastdtw

# https://github.com/opencv/opencv/issues/6055
cv2.ocl.setUseOpenCL(False)


def main():
    # engine = create_engine('sqlite:///'+consts.dbPath)
    engine = create_engine('sqlite:///db.sqlite3')
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    db = DBSession()

    ask = False
    # Ask the user to select routine from database
    routines = db.query(Routine).all()
    if ask:
        routinesAsDict = []
        for routine in routines:
            routinesAsDict.append(OrderedDict([
                ('id', str(routine.id)),
                ('path', routine.path),
                ('competition', routine.competition),
                ('level', routine.level),
                ('tracked', 'Yes' if routine.isTracked() else 'No'),
                ('note', routine.note)
            ]))

        selectedRoutineIndices = show_selection_menu(routinesAsDict)
    else:
        selectedRoutineIndices = [0]  # [87]
    selectedRoutines = [routines[i] for i in selectedRoutineIndices]

    # Execute
    for i, routine in enumerate(selectedRoutines):
        # Open the video with some error handling
        cap = helper.open_video(routine.path)

        '''
        If the routine is not tracked:
            detect trampoline
            track
            find bounces
        Else is tracked, present with option to:
            detect trampoline
            track and save
            track without save
            find bounces
            plot
        '''
        if not routine.isTracked():
            # Detect Trampoline
            trampoline.detect_trampoline(db, cap, routine)

            # Track gymnast and save
            track.track_and_save(db, cap, routine)

            write_reads.save_cropped_frames(db, cap, routine)

            # Find bounces and save
            segment_bounces.segment_bounces_and_save(db, routine)

            # Plot
            visualise.plot_data(routine)
        else:
            # Show options loop
            options = [
                ["Detect Trampoline", trampoline.detect_trampoline, [db, cap, routine]],
                ["Track and Save", track.track_and_save, [db, cap, routine]],
                ["Track without Save", track.track_gymnast, [cap, routine]],
                ["Segment Bounces", segment_bounces.segment_bounces_and_save, [db, routine]],
                ["Save Cropped Frames", write_reads.save_cropped_frames, [db, cap, routine]],
                ["Plot", visualise.plot_data, [routine]],
                ["Import Pose", write_reads.import_pose_hg_smooth, [db, routine]],
                ["Play Video", visualise.play_frames, [db, routine]],
                ["Exit", None, [None]],
            ]
            print("This routine has already been tracked.")
            while True:
                print("What would you like to do?")
                for ii, op in enumerate(options):
                    print('%d) %s' % (ii + 1, op[0]))
                choiceInt = helper.read_num(len(options)) - 1
                if choiceInt == len(options)-1:  # Last option is to Exit
                    break
                else:
                    # Load function name and covert iterable to positional args  http://stackoverflow.com/questions/3941517/converting-list-to-args-in-python
                    options[choiceInt][1](*options[choiceInt][2])

        print("Finished routine {} of {}".format(i + 1, len(selectedRoutines)))

    db.close()
    print("Done")


def judge_skill(db):
    # Get all straddle jumps, plot their sequences
    desiredSkill = 'Tuck Jump'
    straddles = db.query(Bounce).filter_by(skill_name=desiredSkill)
    plt.title(desiredSkill)
    skillRatios = []
    for i, skill in enumerate(straddles[0:7]):
        if i == 6:
            visualise.play_skill(db, skill.id)

        skillFrames = db.query(Frame).filter(Frame.routine_id == skill.routine_id, Frame.frame_num > skill.start_frame,
                                             Frame.frame_num < skill.end_frame)
        frame_nums = [f.frame_num for f in skillFrames]
        print("start", skill.start_frame, "end", skill.end_frame, "num frame", skill.end_frame - skill.start_frame,
              len(frame_nums), frame_nums)
        print(skill.deductions)

        ellipseLenRatios = [f.ellipse_len_major / f.ellipse_len_minor for f in skillFrames]
        skillRatios.append(ellipseLenRatios)

    distance, path = fastdtw(skillRatios[0], skillRatios[1], dist=euclidean)
    print(distance, path)
    for sk in skillRatios:
        plt.plot(signal.resample(sk, 43))
    plt.plot()

    plt.ylabel('Height (Pixels)')
    plt.show()


if __name__ == '__main__':
    main()
