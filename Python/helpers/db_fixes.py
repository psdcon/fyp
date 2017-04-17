import json

import numpy as np

from helpers import helper_funcs
from helpers.db_declarative import Bounce, Routine, Skill
from image_processing import visualise, calc_angles, output_images


#
# Quick database fixes that may end up being useful in the future
#

def fix_angles(db, routine):
    frames = []
    poses = []
    maxShoulderWidth = 0
    pjls = calc_angles.pose_aliai['hourglass']  # poseJointLabels
    for frame in routine.frames:
        if not frame.pose:
            continue
        pose = np.array(json.loads(frame.pose))
        poses.append(pose)
        frames.append(frame)

        # Get the distances between the shoulders
        lspt = calc_angles.pose_2_pt(pose, pjls.index('lshoulder'))
        rspt = calc_angles.pose_2_pt(pose, pjls.index('rshoulder'))
        shoulderWidth = np.linalg.norm(lspt - rspt)
        if shoulderWidth > maxShoulderWidth:
            maxShoulderWidth = shoulderWidth

    # Calculate all the angles
    jointsAngles = calc_angles.angles_from_poses(poses, maxShoulderWidth, False)
    framesAngles = zip(*jointsAngles)
    # Add the angles to db
    for frame, angles in zip(frames, framesAngles):
        frame.angles = helper_funcs.round_list_floats_into_str(angles, 1)
    db.flush()

    # Update bounces with their angles
    for bounce in routine.bounces:
        anglesInEachFrame = [json.loads(frame.angles) for frame in bounce.frames if frame.angles is not None]
        if not anglesInEachFrame:
            continue
        framesInEachAngle = zip(*anglesInEachFrame)  # * = transpose

        bounce.angles = json.dumps(framesInEachAngle)
        bounce.angles_count = len(framesInEachAngle[0])

    routine.has_pose = 1

    db.commit()


def make_images(db):
    # Remake all the saved plots and gifs
    # for bounce in db.query(Bounce).filter(Bounce.angles != None).all():
    for bounce in db.query(Bounce).filter(Bounce.angles != None, Bounce.skill_name == 'Tuck Jump').all():
        if bounce.getAnyDeduction() is None:
            output_images.bounce_to_gif(db, bounce)
            visualise.plot_angles_1x6_save_image(bounce)


def assign_shape(db):
    # Back S/S to Seat, Cody, Barani Ball Out , Rudolph / Rudi.
    # TODO this hasnt been tested in awhile
    # TODO it should check skills.shape_bonus
    bouncesNeedingShape = db.query(Bounce).filter(Bounce.shape == None, Bounce.angles != None).all()
    for i, somi in enumerate(bouncesNeedingShape, start=1):
        # skills
        visualise.play_bounce(db, somi.id, True)
        print("{} of {}".format(i, len(bouncesNeedingShape)))

    exit()


def shoulders_to_twist_angle(db):
    routines = db.query(Routine).filter(Routine.use == 1).order_by(Routine.level).all()
    for routine in routines:
        if not routine.isPoseImported(db):
            continue
        calc_angles.shoulder_width_to_angle(db, routine)


def assign_code_name_to_bounce(db):
    for bounce in db.query(Bounce).filter(Bounce.skill_name != None, Bounce.angles != None):
        bounceCode = db.query(Skill).filter(Skill.name == bounce.skill_name).one().code
        bounce.code_name = bounceCode.upper()
    db.commit()
