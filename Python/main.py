from __future__ import print_function

import cv2

from helpers.db_declarative import Routine, getDb
from image_processing import import_pose
# https://github.com/opencv/opencv/issues/6055
from image_processing.track import track_gymnast

cv2.ocl.setUseOpenCL(False)


def main():
    db = getDb()
    # for routine in db.query(Routine).filter(Routine.has_pose == 1).all():
    #     fix_angles(db, routine)

    # bounce = db.query(Bounce).filter(Bounce.id == 65).one()
    # bounce.getNewDeduction()
    # bounce.deductions

    # make_images(db)

    # judge_skill(db)

    # Tariff
    # routines = db.query(Routine).filter(Routine.use == 1)
    # tariff_many_routines(db, routines)
    # tariff_bounces_test_set(db)
    routine = db.query(Routine).filter(Routine.id == 82).one()
    # detect_trampoline(db, routine)
    track_gymnast(db, routine)

    exit()

    # Execute
    routines = db.query(Routine).filter(Routine.use == 1, Routine.id >= 89).order_by(Routine.level).all()
    for routine in routines:
        print(routine)

        # for i, routine in enumerate(routines):
        #     print()
        #     print(routine.id, routine.path)
        #     print("Note:", routine.note)
        #     # print("Level:", consts.levels[routine.level])
        #     # trampolineObj = {'top': routine.trampoline_top, 'center': routine.trampoline_center, 'width': routine.trampoline_width, }
        #     # print("Trampoline:", trampolineObj)
        #     print("Tracked:", routine.isTracked(db))
        #     # print("Bounces:", prettyPrintRoutine(routine.bounces))
        #     # print("Bounces:", len(routine.bounces))
        #     # print("Frames Saved:", routine.hasFramesSaved())
        #     print("Pose Imported:", routine.isPoseImported(db))
        #     print("Use:", routine.use)
        #
        #     helper_funcs.print_pose_status(routine.getPoseDirPaths())
        #
        #     print()

        # import_output.import_monocap_preds_2d(db, routine)
        # if routine.isPoseImported(db):
        #     # Play the MATLAB images back as a video
        #     # visualise.compare_pose_tracking_techniques(routine)
        #     pass
        # else:
        #     continue

        # If this routine is selected, automatically prompt to locate trampoline.
        # if not routine.trampoline_top or not routine.trampoline_center or not routine.trampoline_width:
        #     # Detect Trampoline
        #     trampoline.detect_trampoline(db, routine)
        #
        # if not routine.isTracked():
        #     print("Auto tracking frames")
        #     # Track gymnast and save
        #     track.track_and_save(db, routine)
        #     # Find bounces and save
        #     segment_bounces.segment_bounces_and_save(db, routine)
        #     # Plot
        #     visualise.plot_data(routine)

        if not routine.hasFramesSaved('_blur_dark_0.6'):
            import_pose.save_cropped_frames(db, routine, routine.frames, '_blur_dark_0.6')
        # else:
        # image_processing.visualise.compare_pose_tracking_techniques(routine)

        # if True:
        #     continue
        # else:
        #     # Options as [Title, function name, [function args]]
        #     options = [
        #         ["Detect Trampoline", trampoline.detect_trampoline, [db, routine]],
        #         ["Track and Save", track.track_and_save, [db, routine]],
        #         ["Track without Save", track.track_gymnast, [routine]],
        #         ["Segment Bounces", segment_bounces.segment_bounces_and_save, [db, routine]],
        #         ["Save Cropped Frames", import_output.save_cropped_frames, [db, routine]],
        #         ["Plot", visualise.plot_data, [routine]],
        #         ["Import Pose", import_output.import_pose_hg_smooth, [db, routine, routine.frames]],
        #         ["Play Video", visualise.play_frames, [db, routine]],
        #         # ["Plot Routine Angles", visualise.plot_frame_angles, [db, routine]],
        #         ["Exit", None, [None]],
        #     ]
        #     print("This routine has already been tracked.")
        #     while True:
        #         print("What would you like to do?")
        #         choiceIndex = helper_funcs.selectListOption([op[0] for op in options])
        #         if choiceIndex == len(options) - 1:  # Last option is to Exit
        #             break
        #         else:
        #             # Load function name and covert iterable to positional args.    http://stackoverflow.com/questions/3941517/converting-list-to-args-in-python
        #             options[choiceIndex][1](*options[choiceIndex][2])

        print("Finished routine {} of {}".format(i + 1, len(routines)))

    db.close()
    print("Done")


if __name__ == '__main__':
    main()
