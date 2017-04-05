from __future__ import division
from __future__ import print_function

import cv2

from helpers import helper_funcs
from helpers.db_declarative import Routine, getDb, TariffMatches, Judgement, Deduction
from image_processing import trampoline, visualise, track, segment_bounces, import_output

# https://github.com/opencv/opencv/issues/6055
cv2.ocl.setUseOpenCL(False)


def main():
    db = getDb()

    routines = db.query(Routine).filter(Routine.use == 1).all()
    for routine in routines:
        print(routine)
        judgements = db.query(Judgement).filter(Judgement.routine_id == routine.id).all()
        print(judgements)
        for judge in judgements:
            db.query(Deduction).filter(Deduction.judgement_id == judge.id).all()
    exit()

    # functions_for_reports.plot_skil_bar_charts(db)
    # exit()
    #
    # # Plot angles for a bounce
    # bounce = db.query(Bounce).filter(Bounce.id == 1870).first()
    # functions_for_reports.skill_into_filmstrip(bounce)
    # visualise.plot_bounce_angles(bounce)
    # # visualise.play_skill(db, bounce.id)
    # exit()
    #
    # # Tariff bounces
    # consts.referenceCountPerSkill = None
    # for i in [1, 2, 3, 4, 5, 6]:
    #     db.execute("DELETE FROM tariff_matches")
    #     tariff.chose_reference_skills(db, i)
    #     tariff.tariff_bounces_test_set(db)
    # exit()

    #
    # Plot Confusion Matrix!
    tariffMatches = db.query(TariffMatches).all()
    visualise.plot_tariff_confusion_matrix(tariffMatches)
    exit()

    #
    # Play that shhh
    tariffMatches = db.query(TariffMatches).all()
    for thisMatch in tariffMatches:
        thisBounce = thisMatch.bounce
        matchedBounce = thisMatch.matched_bounce
        if thisBounce.skill_name != matchedBounce.skill_name:
            visualise.play_frames_of_2_bounces(db, thisBounce, matchedBounce)
            # visualise.play_frames_of_2(db, thisBounce.routine, matchedBounce.routine, thisBounce.start_frame, thisBounce.end_frame, matchedBounce.start_frame, matchedBounce.end_frame)

    exit()

    # Execute
    routines = db.query(Routine).filter(Routine.use == 1, Routine.id >= 89).order_by(Routine.level).all()
    for routine in routines:
        print(routine)

    for i, routine in enumerate(routines):
        print()
        print(routine.id, routine.path)
        print("Note:", routine.note)
        # print("Level:", consts.levels[routine.level])
        # trampolineObj = {'top': routine.trampoline_top, 'center': routine.trampoline_center, 'width': routine.trampoline_width, }
        # print("Trampoline:", trampolineObj)
        print("Tracked:", routine.isTracked(db))
        # print("Bounces:", prettyPrintRoutine(routine.bounces))
        # print("Bounces:", len(routine.bounces))
        # print("Frames Saved:", routine.hasFramesSaved())
        print("Pose Imported:", routine.isPoseImported(db))
        print("Use:", routine.use)

        helper_funcs.printPoseStatus(routine.getPoseDirPaths())

        print()

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
            import_output.save_cropped_frames(db, routine, routine.frames, '_blur_dark_0.6')
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
