# Constants
import os

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
levels = [
    'Novice',
    'Intermediate',
    'Intervanced',
    'Advanced',
    'Elite',
    'idk',
    "All"
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


def getAngleIndices(poseMethod):
    # poseJointLabels
    pjl = poseAliai[poseMethod]
    return {
        "Right hip": [pjl.index('rshoulder'), pjl.index('rknee'), pjl.index('rhip')],
        "Left hip": [pjl.index('lshoulder'), pjl.index('lknee'), pjl.index('lhip')],
        "Right knee": [pjl.index('rhip'), pjl.index('rfoot'), pjl.index('rknee')],
        "Left knee": [pjl.index('lhip'), pjl.index('lfoot'), pjl.index('lknee')],
        "Right shoulder": [pjl.index('relbow'), pjl.index('rhip'), pjl.index('rshoulder')],
        "Left shoulder": [pjl.index('lelbow'), pjl.index('lhip'), pjl.index('lshoulder')],
        "Right elbow": [pjl.index('rshoulder'), pjl.index('rhand'), pjl.index('relbow')],
        "Left elbow": [pjl.index('lshoulder'), pjl.index('lhand'), pjl.index('lelbow')],
    }


angleIndexKeys = [
    "Right knee",
    "Left knee",
    "Right hip",
    "Left hip",
    "Right shoulder",
    "Left shoulder",
    "Right elbow",
    "Left elbow",
]
angleAverageKeys = [
    'Knee',
    'Hip',
    'Shoulder',
    'Elbow',
]

# part_name: [name, bgr]. for plot and opencv
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
