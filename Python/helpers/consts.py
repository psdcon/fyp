# Constants

videosRootPath = 'C:\\Users\\psdco\\Videos\\'
# bouncesRootPath = 'C:\\Users\\psdco\\Videos\\bounces\\'
bouncesRootPath = 'C:\\Users\\psdco\\Documents\\ProjectCode\\Python\\web_gui\\static\\images\\bounces\\'
lastSelectionFilePath = 'pyqt_gui/lastSaved.txt'
thumbDir = 'C:\\Users\\psdco\\Documents\\ProjectCode\\Python\\web_gui\\static\\images\\thumbs'
confImgPath = 'C:\\Users\\psdco\\Dropbox\\My College\\Y5 Project\\4. Conference Paper\\images\\'

contourDistance = 25
minContourArea = 800

referenceCountPerSkill = 2

comps = [
    'Trainings',
    'Inhouse'
]
levels = [
    'Novice',
    'Intermediate',
    'Intervanced',
    'Advanced',
    'Elite',
    'Elite Pro',
]


# part_name: [color_name, bgr]. for pyplot, and opencv
poseColors = {
    # Right side is hotter! (More red)

    # right leg pink
    'rhip': ['red', (129, 64, 255)],
    'rknee': ['green', (87, 0, 245)],
    'rfoot': ['blue', (98, 17, 197)],

    # left leg blue
    'lhip': ['yellow', (255, 196, 64)],
    'lknee': ['purple', (255, 176, 0)],
    'lfoot': ['cyan', (234, 145, 0)],

    # right arm orange
    'rshoulder': ['blue', (64, 110, 255)],
    'relbow': ['green', (0, 61, 255)],
    'rhand': ['red', (0, 44, 221)],

    # left arm green
    'lshoulder': ['cyan', (89, 255, 178)],
    'lelbow': ['purple', (3, 255, 118)],
    'lhand': ['yellow', (23, 221, 100)],

    'head': ['green', (141, 255, 255)],
    'neck': ['red', (0, 255, 255)],
    'chest': ['black', (0, 234, 255)],
    'centerhip': ['black', (0, 214, 255)],
}
original_pose_colors = {
    'rfoot': ['red', (0, 0, 255)],
    'rknee': ['green', (0, 255, 0)],
    'rhip': ['blue', (255, 0, 0)],
    'lhip': ['yellow', (0, 255, 255)],
    'lknee': ['purple', (255, 0, 255)],
    'lfoot': ['cyan', (255, 255, 0)],
    'rhand': ['red', (0, 0, 255)],
    'relbow': ['green', (0, 255, 0)],
    'rshoulder': ['blue', (255, 0, 0)],
    'lshoulder': ['cyan', (255, 255, 0)],
    'lelbow': ['purple', (255, 0, 255)],
    'lhand': ['yellow', (0, 255, 255)],
    'neck': ['red', (0, 0, 255)],
    'head': ['green', (0, 255, 0)],
    'centerhip': ['black', (0, 0, 0)],
    'chest': ['black', (0, 0, 0)]
}

jointAngleColors = [
    'red',
    'green',
    'blue',
    'yellow',
    'purple',
    'cyan',
    'black'
]
