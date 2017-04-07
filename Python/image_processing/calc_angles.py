import json
from math import acos, degrees

import numpy as np
from scipy.spatial import distance

from helpers import helper_funcs

num_angles = 13

# Right and leftFrom the perspective of the person
pose_aliai = {
    'deepcut': [
        'rfoot',  #: 0,
        'rknee',  #: 1,
        'rhip',  #: 2,
        'lhip',  #: 3,
        'lknee',  #: 4,
        'lfoot',  #: 5,
        'rhand',  #: 6,
        'relbow',  #: 7,
        'rshoulder',  #: 8,
        'lshoulder',  #: 9,
        'lelbow',  #: 10,
        'lhand',  #: 11,
        'neck',  #: 12,
        'head',  #: 13
    ],
    'hourglass': [
        'rfoot',  #: 0,
        'rknee',  #: 1,
        'rhip',  #: 2,
        'lhip',  #: 3,
        'lknee',  #: 4,
        'lfoot',  #: 5,
        'centerhip',  #: 6,
        'chest',  #: 7,
        'neck',  #: 8,
        'head',  #: 9,
        'rhand',  #: 10,
        'relbow',  #: 11,
        'rshoulder',  #: 12,
        'lshoulder',  #: 13,
        'lelbow',  #: 14,
        'lhand',  #: 15
    ]
}

# Angle names
angle_r_elbow = "Right Elbow"
angle_l_elbow = "Left Elbow"
angle_r_shoulder = "Right Shoulder"
angle_l_shoulder = "Left Shoulder"
angle_r_knee = "Right Knee"
angle_l_knee = "Left Knee"
angle_r_hip = "Right Hip"
angle_l_hip = "Left Hip"
angle_head = "Head"
angle_r_leg_with_vertical = "Right Leg with Vertical"
angle_l_leg_with_vertical = "Left Leg with Vertical"
angle_torso_with_vertical = "Torso with Vertical"
angle_twist_angle = "Twist Angle"

labels = [
    'Elbow',
    'Shoulder',
    'Hip',
    'Knee',
    'Leg with Vertical',
    'Torso & Twist'
]


def get_angle_indices(pose_method_key):
    # poseJointLabels
    pjls = pose_aliai[pose_method_key]
    return [
        # Angles order as A, B, C, where C is the one you want to find.
        [pjls.index('rshoulder'), pjls.index('rhand'), pjls.index('relbow')],  # angle_r_elbow = "Right Elbow"
        [pjls.index('lshoulder'), pjls.index('lhand'), pjls.index('lelbow')],  # angle_l_elbow = "Left Elbow"
        [pjls.index('relbow'), pjls.index('rhip'), pjls.index('rshoulder')],  # angle_r_shoulder = "Right Shoulder"
        [pjls.index('lelbow'), pjls.index('lhip'), pjls.index('lshoulder')],  # angle_l_shoulder = "Left Shoulder"
        [pjls.index('rshoulder'), pjls.index('rknee'), pjls.index('rhip')],  # angle_r_knee = "Right Knee"
        [pjls.index('lshoulder'), pjls.index('lknee'), pjls.index('lhip')],  # angle_l_knee = "Left Knee"
        [pjls.index('rhip'), pjls.index('rfoot'), pjls.index('rknee')],  # angle_r_hip = "Right Hip"
        [pjls.index('lhip'), pjls.index('lfoot'), pjls.index('lknee')],  # angle_l_hip = "Left Hip"
        [pjls.index('chest'), pjls.index('head'), pjls.index('neck')],  # angle_head = "Head"
    ]


def get_special_angle_indices(pose_method_key):
    # poseJointLabels
    pjls = pose_aliai[pose_method_key]
    return {
        # Angles order as A, B, C, where C is the one you want to find.
        # And A is the one to be tampered with
        [pjls.index('rhip'), pjls.index('rknee'), pjls.index('rhip')],  # angle_r_leg_with_vertical = "Right Leg with Vertical"
        [pjls.index('lhip'), pjls.index('lknee'), pjls.index('lhip')],  # angle_l_leg_with_vertical = "Left Leg with Vertical"
        [pjls.index('centerhip'), pjls.index('chest'), pjls.index('centerhip')],  # angle_torso_with_vertical = "Torso with Vertical"
    }


special_offsets = [
    # x, y offsets
    (0, -10),
    (0, -10),
    (0, -10),
]

# Maintains order
angle_keys = [
    angle_r_elbow,
    angle_l_elbow,
    angle_r_shoulder,
    angle_l_shoulder,
    angle_r_knee,
    angle_l_knee,
    angle_r_hip,
    angle_l_hip,
    angle_head
]

extended_angle_keys = angle_keys + [
    angle_r_leg_with_vertical,
    angle_l_leg_with_vertical,
    angle_torso_with_vertical,
    angle_twist_angle,
]


# Take a single pose isntance and generate all angles (except twist) from it
# Return angles as a named dict
def pose_2_ordered_angles(pose):
    angles = angles_from_poses([pose])
    orderedAngles = []
    for key in extended_angle_keys[:1]:  # Don't include twist
        angle = angles[key][0]  # returns a list of a single angle
        orderedAngles.append(angle)
    return orderedAngles


def rel_pose_to_abs_pose(pose, cx, cy, padding=100):
    # pose points are relative to the top left (cx cy = ix iy; 0 0 = ix-100 iy-100) of the 200x200 cropped frame
    # pose given by (0 + posex, 0 + posey) => cx-100+posex, cy-100+posey
    for p_idx in range(14):
        pose[0, p_idx] = int((cx - padding) + pose[0, p_idx])
        pose[1, p_idx] = int((cy - padding) + pose[1, p_idx])
    return pose


def pose_2_pt(pose, p_idx):
    pt = np.array([pose[0, p_idx], pose[1, p_idx]])
    return pt


def calc_angle(A, B, C):
    a = distance.euclidean(C, B)
    b = distance.euclidean(A, C)
    c = distance.euclidean(A, B)
    num = a ** 2 + b ** 2 - c ** 2
    denom = (2.0 * a * b)
    if denom == 0.0:
        ratio = 0
    else:
        ratio = num / denom

    if ratio <= -1.0 or ratio >= 1.0:
        return acos(int(ratio))
    ang = acos(ratio)
    return degrees(ang)


def angles_from_poses(poses, max_shoulder_width, average=False):
    # Make a list for each of the joints to be plotted
    jointsIndexes = get_angle_indices('hourglass')  # 10 * 3
    specialJointsIndexes = get_special_angle_indices('hourglass')  # 3 * 3
    jointsAngles = [[] for _ in (extended_angle_keys)]  # <type 'list'>: [[], [], [], [], [], [], [], [], [], [], [], [], []]

    for pose in poses:
        # Get the 3 pose points that make up this joint
        for i, jointIndexes in enumerate(jointsIndexes):
            # Calculate the angle between them
            angle = calc_angle(pose_2_pt(pose, jointIndexes[0]), pose_2_pt(pose, jointIndexes[1]), pose_2_pt(pose, jointIndexes[2]))
            # Append it to the appropriate list
            jointsAngles[i].append(angle)
            # Special angles

        # Do Special angles
        for i, jointIndexes in enumerate(specialJointsIndexes):
            specialsOffset = np.array(special_offsets[i])
            # Calculate the angle between them
            angle = calc_angle(pose_2_pt(pose, jointIndexes[0]) + specialsOffset, pose_2_pt(pose, jointIndexes[1]), pose_2_pt(pose, jointIndexes[2]))
            # Append it to the appropriate dict
            ii = i + len(jointsIndexes)
            jointsAngles[ii].append(angle)

        # Twist angle
        pjls = pose_aliai['hourglass']
        lspt = pose_2_pt(pose, pjls.index('lshoulder'))
        rspt = pose_2_pt(pose, pjls.index('rshoulder'))
        shoulderWidth = np.linalg.norm(lspt - rspt)
        twistAngle = (shoulderWidth / max_shoulder_width) * 180
        jointsAngles[extended_angle_keys.index(angle_twist_angle)].append(twistAngle)

    if not average:
        return jointsAngles
    else:
        print("This code is nonsense! Stop what you're doing and try again.")
        averagedJointAngles = {}
        for i in range(0, len(angle_keys), 2):  # step from 0 to 8 in increments of 2
            rightKey = angle_keys[i]
            leftKey = angle_keys[i + 1]
            jointName = rightKey.split(' ')[1].title()  # take the last word and set it to title case
            averagedJointAngles[jointName] = np.average([jointsAngles[rightKey], jointsAngles[leftKey]], axis=0)
        return averagedJointAngles


def shoulder_width_to_angle(db, routine):
    # Check that this routine doesn't already have the new angle
    for bounce in routine.bounces:
        if bounce.angles:
            angles = json.loads(bounce.angles)
            if len(angles) == 13:
                print("Already has new angle: ", routine)
                return

    # poseJointLabels
    pjls = pose_aliai['hourglass']
    lsi = pjls.index('lshoulder')
    rsi = pjls.index('rshoulder')

    # Get the routines poses
    poses = []
    for frame in routine.frames:
        if frame.pose:
            poses.append(np.array(json.loads(frame.pose)))
        else:
            poses.append(None)

    # Get the distances between the shoulders
    shoulderWidths = []
    for pose in poses:
        if pose is not None:
            lspt = np.array((pose[0, lsi], pose[1, lsi]))
            rspt = np.array((pose[0, rsi], pose[1, rsi]))
            shoulderWidth = np.linalg.norm(lspt - rspt)
            shoulderWidths.append(shoulderWidth)
        else:
            shoulderWidths.append(None)

    # Normalise and scale the distances in to an angle
    maxShoulderWidth = max(shoulderWidths)
    twistAngles = []
    for sw in shoulderWidths:
        if sw is not None:
            twistAngle = (sw / maxShoulderWidth) * 180
            twistAngles.append(twistAngle)
        else:
            twistAngles.append(None)

    # Plot x,y and shoulder angle and print bounces
    # f, axarr = plt.subplots(1, sharex=True)
    #
    # # Plot bounce heights
    # x_frames = [frame.frame_num / routine.video_fps for frame in routine.frames]
    # y_height = [routine.video_height - frame.center_pt_y for frame in routine.frames]
    #
    # # List inside list gets flattened
    # peaks_x = list(chain.from_iterable((bounce.start_time, bounce.max_height_frame / routine.video_fps) for bounce in routine.bounces))
    # peaks_x.append(routine.bounces[-1].end_time)
    # peaks_y = list(chain.from_iterable((bounce.start_height, bounce.max_height) for bounce in routine.bounces))
    # peaks_y.append(routine.bounces[-1].end_height)
    #
    # axarr.set_title("Height")
    # axarr.plot(x_frames, y_height, color="g")
    # # axarr.plot(peaks_x, peaks_y, 'r+')
    # axarr.set_ylabel('Height (Pixels)')
    #
    # axarr.set_title("Twist Angle")
    # axarr.plot(x_frames, twistAngles, color="g")
    # axarr.set_ylabel('Angle (deg)')
    #
    # labels = [bounce.skill_name for bounce in routine.bounces[:-1]]
    # labels_x = [bounce.start_time for bounce in routine.bounces[:-1]]
    # plt.xticks(labels_x, labels, rotation='vertical')
    # for x in labels_x:
    #     plt.axvline(x)
    # # Pad margins so that markers don't get clipped by the axes
    # plt.margins(0.2)
    # # Tweak spacing to prevent clipping of tick-labels
    # plt.subplots_adjust(bottom=0.15)
    #
    # print(routine.bounces)
    # plt.show()

    # Append the new angle to the existing angles
    for twistAngle, frame in zip(twistAngles, routine.frames):
        if frame.angles:
            angles = json.loads(frame.angles)
            angles.append(twistAngle)
            newangles = helper_funcs.round_list_floats_into_str(angles, 1)
            frame.angles = newangles

    db.flush()

    # Update the bounces entry of angles
    for bounce in routine.bounces:
        anglesInEachFrame = [json.loads(frame.angles) for frame in bounce.frames if frame.angles is not None]
        if not anglesInEachFrame:
            continue
        framesInEachAngle = zip(*anglesInEachFrame)  # * = transpose

        # TODO Make sure this doesn't add quotes to the db entry
        bounce.angles = json.dumps(framesInEachAngle)
        bounce.angles_count = len(framesInEachAngle[0])

    db.commit()

    return
