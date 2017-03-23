from __future__ import division
from __future__ import print_function

import json

import cv2

import image_processing.tariff
from helpers import consts
from helpers import helper_funcs
from helpers.db_declarative import Routine, getDb, TariffMatches
from image_processing import judge
from image_processing import trampoline, visualise, track, segment_bounces, import_output

# https://github.com/opencv/opencv/issues/6055
cv2.ocl.setUseOpenCL(False)


def main():
    db = getDb()
    # judge.judge(db)
    # exit()

    # Back S/S to Seat, Cody, Barani Ball Out , Rudolph / Rudi.
    # somis = db.query(Bounce).filter(Bounce.skill_name == 'Back S/S to Seat', Bounce.shape == None, Bounce.angles != None).all()
    # for i, somi in enumerate(somis, start=1):
    #     visualise.play_skill(db, somi.id, True)
    #     print("{} of {}".format(i, len(somis)))
    #
    # exit()

    routines = db.query(Routine).filter(Routine.use == 1).order_by(Routine.level).all()
    routinesToTariff = []
    for routine in routines:
        if routine.isPoseImported(db):  # and not os.path.exists(routine.tariffPath()):
            routinesToTariff.append(routine)
    image_processing.tariff.tariff_many(db, routinesToTariff)
    image_processing.tariff.accuracy_of_many(db, routinesToTariff)

    # routine = db.query(Routine).filter(Routine.id == 14).first()

    exit()

    # Execute
    for i, routine in enumerate(routines):
        print()
        print(routine.id, routine.path)
        print("Note:", routine.note)
        print("Level:", consts.levels[routine.level])
        # trampolineObj = {'top': routine.trampoline_top, 'center': routine.trampoline_center, 'width': routine.trampoline_width, }
        # print("Trampoline:", trampolineObj)
        print("Tracked:", routine.isTracked())
        # print("Bounces:", prettyPrintRoutine(routine.bounces))
        # print("Bounces:", len(routine.bounces))
        # print("Frames Saved:", routine.hasFramesSaved())
        print("Pose Imported:", routine.isPoseImported(db))
        print("Use:", routine.use)

        helper_funcs.printPoseStatus(routine.getPoseDirPaths())

        print()

        # import_output.import_monocap_preds_2d(db, routine)
        if routine.isPoseImported(db):
            # Play the MATLAB images back as a video
            # visualise.compare_pose_tracking_techniques(routine)
            pass
        else:
            continue

        # If this routine is selected, automatically prompt to locate trampoline.
        if not routine.trampoline_top or not routine.trampoline_center or not routine.trampoline_width:
            # Detect Trampoline
            trampoline.detect_trampoline(db, routine)

        if not routine.isTracked():
            print("Auto tracking frames")
            # Track gymnast and save
            track.track_and_save(db, routine)
            # Find bounces and save
            segment_bounces.segment_bounces_and_save(db, routine)
            # Plot
            visualise.plot_data(routine)

        # if not routine.hasFramesSaved('_blur_dark_0.6'):
        #     import_output.save_cropped_frames(db, routine, routine.frames, '_blur_dark_0.6')
        # else:
        # image_processing.visualise.compare_pose_tracking_techniques(routine)

        if True:
            continue
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
                choiceIndex = helper_funcs.selectListOption([op[0] for op in options])
                if choiceIndex == len(options) - 1:  # Last option is to Exit
                    break
                else:
                    # Load function name and covert iterable to positional args.    http://stackoverflow.com/questions/3941517/converting-list-to-args-in-python
                    options[choiceIndex][1](*options[choiceIndex][2])

        print("Finished routine {} of {}".format(i + 1, len(routines)))

    db.close()
    print("Done")


if __name__ == '__main__':
    main()
