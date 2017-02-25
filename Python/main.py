from __future__ import division
from __future__ import print_function

from collections import OrderedDict

import cv2

from pyqt_gui.showRoutineSelectDialog import show_selection_menu
from helpers import helper_funcs
from helpers.db_declarative import db, Routine
from helpers.helper_funcs import prettyPrintRoutine
from image_processing import trampoline
from image_processing import visualise, track, segment_bounces, import_output

# https://github.com/opencv/opencv/issues/6055
cv2.ocl.setUseOpenCL(False)


def main():
    # judge.judge(db)
    # exit()

    ask = False
    # Ask the user to select routine from database
    # routines = db.query(Routine).filter(Routine.use == 1).all()
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
        selectedRoutineIndices = [1]  # select by id
    selectedRoutines = [routines[i - 1] for i in selectedRoutineIndices]
    selectedRoutines = routines

    # Execute
    for i, routine in enumerate(selectedRoutines):
        print("\n" + routine.path)
        print("Note:", repr(routine.note))
        print("Level:", routine.level)
        trampolineObj = {'top': routine.trampoline_top, 'center': routine.trampoline_center, 'width': routine.trampoline_width, }
        print("Trampoline:", trampolineObj)
        print("Tracked:", routine.isTracked(db))
        # print("Bounces:", prettyPrintRoutine(routine.bounces))
        print("Bounces:", len(routine.bounces))
        print("Cropped:", routine.hasFramesSaved())
        print("Posed:", routine.isPosed(db))
        print()

        # judge.compare_pose_tracking(routine)
        # exit()

        # if framesCount > 0:
        #     print("Has {} frames. Continuing to next..".format(framesCount))
        #     continue

        # If this routine is selected, automatically prompt to locate trampoline.
        if not routine.trampoline_top or not routine.trampoline_center or not routine.trampoline_width:
            # Detect Trampoline
            trampoline.detect_trampoline(db, routine)

        if not routine.isTracked(db):
            print("Auto tracking frames")
            # Track gymnast and save
            track.track_and_save(db, routine)
            continue
            # Find bounces and save
            # segment_bounces.segment_bounces_and_save(db, routine)
            # Plot
            # visualise.plot_data(routine)

        if True:  # False:
            import_output.save_cropped_frames(db, routine, routine.frames)

        else:
            # Options as [Title, function name, [function args]]
            options = [
                ["Detect Trampoline", trampoline.detect_trampoline, [db, routine]],
                ["Track and Save", track.track_and_save, [db, routine]],
                ["Track without Save", track.track_gymnast, [routine]],
                ["Segment Bounces", segment_bounces.segment_bounces_and_save, [db, routine]],
                ["Save Cropped Frames", import_output.save_cropped_frames, [db, routine]],
                ["Plot", visualise.plot_data, [routine]],
                ["Import Pose", import_output.import_pose_hg_smooth, [db, routine, routine.frames]],
                ["Play Video", visualise.play_frames, [db, routine]],
                # ["Plot Routine Angles", visualise.plot_frame_angles, [db, routine]],
                ["Exit", None, [None]],
            ]
            print("This routine has already been tracked.")
            while True:
                print("What would you like to do?")
                for ii, op in enumerate(options):
                    print('%d) %s' % (ii + 1, op[0]))
                choiceInt = helper_funcs.read_num(len(options)) - 1
                if choiceInt == len(options) - 1:  # Last option is to Exit
                    break
                else:
                    # Load function name and covert iterable to positional args
                    # http://stackoverflow.com/questions/3941517/converting-list-to-args-in-python
                    options[choiceInt][1](*options[choiceInt][2])

        print("Finished routine {} of {}".format(i + 1, len(selectedRoutines)))

    db.close()
    print("Done")


if __name__ == '__main__':
    main()
