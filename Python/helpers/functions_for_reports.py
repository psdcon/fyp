from operator import itemgetter

import cv2
import numpy as np
from sqlalchemy import text

from helpers import helper_funcs, consts
from helpers.db_declarative import Bounce


def plot_skil_bar_charts(db):
    from collections import Counter
    import matplotlib.pyplot as plt
    # Counter({u'Straight Bounce': 286, u'Back S/S': 76, u'Tuck Jump': 58, u'Barani': 52, u'Straddle Jump': 42, u'Pike Jump': 40, u'Seat Half Twist To Seat': 24, u'Half Twist to Feet from Seat': 24, u'Landing': 22, u'Full Twist Jump': 19, u'Half Twist Jump': 18, u'Crash Dive': 18, u'Seat Drop': 13, u'Half Twist to Feet from Back': 12, u'To Feet from Seat': 11, u'Front S/S': 11, u'Back S/S to Seat': 10, u'Half Twist to Seat Drop': 10, u'Back Drop': 10, u'To Feet from Back': 8, u'Barani Ball Out': 7, u'To Feet from Front': 5, u'Front Drop': 4, u'Rudolph / Rudi': 3, u'Lazy Back': 3, u'Cody': 3, u'Full Back': 2, u'Back Half': 1, u'Full Front': 1})

    bounceNames = [bounce.code_name for bounce in db.query(Bounce).filter(Bounce.angles != None, Bounce.id != 127, Bounce.skill_name != 'Straight Bounce').all()]
    countedBounces = Counter(bounceNames)
    sortedContedBounces = sorted(countedBounces.items(), key=itemgetter(1), reverse=True)
    codes = zip(*sortedContedBounces)[0]
    counts = zip(*sortedContedBounces)[1]

    fig, ax = plt.subplots()
    rects1 = plt.barh(range(len(countedBounces)), counts, align='center', color='#5a9bd4')
    plt.yticks(range(len(countedBounces)), codes)
    plt.xlabel('Number Recorded')
    plt.ylabel('Skill Class')

    # plt.subplots_adjust(bottom=0.5)
    # Create a 5% (0.05) and 10% (0.1) padding in the
    # x and y directions respectively.
    plt.margins(y=0.05)
    fig.tight_layout(pad=0)
    imgName = consts.confImgPath + "all_skills_bar.pdf"
    print("Writing image to {}".format(imgName))
    plt.savefig(imgName)
    plt.show()

    fig, ax = plt.subplots(figsize=(8, 3))

    # Count shapes
    skills = {}
    for bounce in db.query(Bounce).filter(Bounce.angles != None, Bounce.shape != None, Bounce.id != 127).all():
        if bounce.shape:
            if bounce.code_name not in skills.keys():
                skills[bounce.code_name] = {'Tuck': 0, 'Pike': 0, 'Straight': 0}

            skills[bounce.code_name][bounce.shape] += 1

    # bss tuck pike straight
    # fss tuck pike straight
    tucks = [skills[skillKey]['Tuck'] for skillKey in skills]
    pikes = [skills[skillKey]['Pike'] for skillKey in skills]
    straights = [skills[skillKey]['Straight'] for skillKey in skills]

    tuckRects = plt.barh(range(len(skills)), tucks, align='center', color='#f15a60')
    pikeRects = plt.barh(range(len(skills)), pikes, align='center', color='#7ac36a', left=tucks)
    tuckPikes = [sum(x) for x in zip(tucks, pikes)]
    straightRects = plt.barh(range(len(skills)), straights, align='center', color='#5a9bd4', left=tuckPikes)

    plt.yticks(range(len(skills)), skills.keys())
    plt.xlabel('Number Recorded')
    plt.ylabel('Skill Class')
    plt.legend((tuckRects, pikeRects, straightRects), ('Tuck', 'Pike', 'Straight'), loc=4)

    fig.tight_layout(pad=0)
    imgName = consts.confImgPath + "shaped_skills_bar.pdf"
    print("Writing image to {}".format(imgName))
    plt.savefig(imgName)
    plt.show()

    return


def print_list_of_skills(db):
    sql = text("""
      SELECT
          skill_name,
          count(1) AS cnt,
          (SELECT code FROM skills WHERE skills.name = bounces.skill_name) AS code,
          (SELECT tariff FROM skills WHERE skills.name = bounces.skill_name) AS tariff,
          (SELECT id FROM skills WHERE skills.name = bounces.skill_name) AS sort_id
      FROM bounces WHERE skill_name NOTNULL AND angles NOTNULL GROUP BY skill_name ORDER BY sort_id
      """)
    results = db.execute(sql)
    results = list(results)
    for res in results:
        # name count code_name tariff
        print("{name} & {code} & {tariff} & {count}\\\\".format(name=res[0], count=res[1], code=res[2].upper(), tariff=res[3]))


def skill_into_filmstrip(bounce):
    cap = helper_funcs.open_video(bounce.routine.path)

    capWidth = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    capHeight = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    frameClipping = 6
    numFrames = 5

    start = bounce.start_frame + frameClipping
    end = bounce.end_frame - frameClipping
    step = (end - start) / numFrames
    step = int(round(step, 0))
    framesToSave = range(start, end, step)

    whitespace = 4
    width = 255

    leftCrop = int((capWidth * 0.5) - width / 2)
    rightCrop = int(leftCrop + width)
    filmStrip = np.ones(shape=(capHeight * 0.8, (width * len(framesToSave)) + (whitespace * len(framesToSave) - 1), 3),
                        dtype=np.uint8)
    filmStrip[:] = 250

    for i, frameNum in enumerate(framesToSave):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frameNum)
        _ret, frame = cap.read()

        # possible improvement
        trackPerson = frame[0:int(capHeight * 0.8), leftCrop:rightCrop]
        start = ((whitespace + width) * i)
        filmStrip[0:int(capHeight * 0.8), start:start + width] = trackPerson

    cv2.imshow('Filmstrip', filmStrip)
    cv2.waitKey(50)

    # imgName = "C:/Users/psdco/Videos/{}/{}.png".format(bounce.routine.getAsDirPath(), bounce.skill_name)
    imgName = consts.confImgPath + "{}.png".format(bounce.skill_name)
    print("Writing frame to {}".format(imgName))
    ret = cv2.imwrite(imgName, filmStrip)
    if not ret:
        print("Couldn't write image {}\nAbort!".format(imgName))
