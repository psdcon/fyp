# Constants

videosRootPath = 'C:\\Users\\psdco\\Videos\\'
# databasePath = 'C:/Users/psdco/Documents/ProjectCode/Web/includes/db.sqlite3'
# databasePath = 'C:/Users/psdco/Documents/ProjectCode/Python/db.sqlite3'
lastSelectionFilePath = 'pyqt_gui/lastSaved.txt'
thumbDir = 'C:\\Users\\psdco\\Documents\\ProjectCode\\Python\\web_gui\\static\\images\\thumbs'

contourDistance = 25
minContourArea = 800

comps = [
    'Trainings',
    'Inhouse'
]

levelsDict = {
    'Novice': 0,
    'Intermediate': 1,
    'Intervanced': 2,
    'Advanced': 3,
    'Elite': 4,
    'Elite Pro': 5,
}
levels = [
    'Novice',
    'Intermediate',
    'Intervanced',
    'Advanced',
    'Elite',
    'Elite Pro',
]

# Right and leftFrom the perspective of the person
poseAliai = {
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


def getAngleIndices(poseMethodKey):
    # poseJointLabels
    pjls = poseAliai[poseMethodKey]
    return {
        # Angles order as A, B, C, where C is the one you want to find.
        "Right elbow": [pjls.index('rshoulder'), pjls.index('rhand'), pjls.index('relbow')],
        "Left elbow": [pjls.index('lshoulder'), pjls.index('lhand'), pjls.index('lelbow')],
        "Right shoulder": [pjls.index('relbow'), pjls.index('rhip'), pjls.index('rshoulder')],
        "Left shoulder": [pjls.index('lelbow'), pjls.index('lhip'), pjls.index('lshoulder')],
        "Right hip": [pjls.index('rshoulder'), pjls.index('rknee'), pjls.index('rhip')],
        "Left hip": [pjls.index('lshoulder'), pjls.index('lknee'), pjls.index('lhip')],
        "Right knee": [pjls.index('rhip'), pjls.index('rfoot'), pjls.index('rknee')],
        "Left knee": [pjls.index('lhip'), pjls.index('lfoot'), pjls.index('lknee')],
        "Head": [pjls.index('chest'), pjls.index('head'), pjls.index('neck')],
    }


def getSpecialAngleIndices(poseMethodKey):
    # poseJointLabels
    pjls = poseAliai[poseMethodKey]
    return {
        # Angles order as A, B, C, where C is the one you want to find.
        # And A is the one to be tampered with
        "Right leg with horz": [pjls.index('rhip'), pjls.index('rknee'), pjls.index('rhip')],
        "Left leg with horz": [pjls.index('lhip'), pjls.index('lknee'), pjls.index('lhip')],
        "Torso with horz": [pjls.index('centerhip'), pjls.index('chest'), pjls.index('centerhip')],
    }


specialOffsets = {
    # x, y offsets
    "Right leg with horz": [10, 0],
    "Left leg with horz": [10, 0],
    "Torso with horz": [0, 10],
}

# Maintains order
angleIndexKeys = [
    "Right elbow",
    "Left elbow",
    "Right shoulder",
    "Left shoulder",
    "Right knee",
    "Left knee",
    "Right hip",
    "Left hip",
    "Head"
]
extendedAngleIndexKeys = angleIndexKeys + [
    "Right leg with horz",
    "Left leg with horz",
    "Torso with horz",
]
angleAverageKeys = [
    'Knee',
    'Hip',
    'Shoulder',
    'Elbow',
]

# part_name: [color_name, bgr]. for pyplot, and opencv
poseColors = {
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
