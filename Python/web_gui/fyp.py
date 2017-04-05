# -*- coding: utf-8 -*-
from __future__ import print_function

import json
import os
import uuid
from operator import itemgetter

from flask import Flask, request, g, render_template
from flask import after_this_request
from flask import get_template_attribute
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, func, distinct

import judging_rows_html
from helpers import consts
from helpers import helper_funcs
from helpers import sql_queries
from helpers.db_declarative import Routine, Contributor, Judgement, Bounce, Deduction

app = Flask(__name__)

# Load default config and override config from an environment variable
# app.config.update(dict(
#     DEBUG=True,
#     SECRET_KEY='development key',
#     USERNAME='admin',
#     PASSWORD='defaultpassword'
# ))

# Open db in a way that takes care of threading issue on the server
if os.path.abspath('.') == 'C:\\Users\\psdco\\Documents\\ProjectCode\\Python\\web_gui':
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/psdco/Documents/ProjectCode/Python/db.sqlite3'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////var/www/html/fyp/db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app).session


# Set a cookie # http://flask.pocoo.org/docs/0.12/patterns/deferredcallbacks/#deferred-callbacks
@app.before_request
def create_user_id_cookie():
    userId = request.cookies.get('userId')
    if not userId:
        userId = str(uuid.uuid4())
        g.userId = userId

        @after_this_request
        def remember_users(response):
            print("Creating userId=%s" % (userId))
            response.set_cookie('userId', userId)
            return response

    # print("Got userId=%s" % (userId))
    g.userId = userId


#
# Pages in Navbar
#
@app.route('/')
def index():
    counts = {}
    counts['routines'] = db.query(func.count(Routine.id)).scalar()
    counts['routinesUse'] = db.query(func.count(Routine.id)).filter(Routine.use == 1).scalar()
    counts['routinesUsePose'] = db.execute(sql_queries.num_use_pose_routines).scalar()
    counts['routinesUsePoseJudgedOld'] = db.execute(sql_queries.num_judged_use_pose_routines_old).scalar()

    # Bounce total in db
    counts['bounces'] = db.query(func.count(Bounce.id)).scalar()
    counts['bouncesJudgeable'] = db.execute(sql_queries.num_judgeable_bounces).scalar()

    # Bounces to be used, total
    counts['bouncesJudgeableUse'] = db.execute(sql_queries.num_judgeable_use_bounces).scalar()
    counts['bouncesJudgeableUsePose'] = db.execute(sql_queries.num_judgeable_use_pose_bounces).scalar()

    #
    # Deductions
    counts['bouncesJudgedNew'] = db.query(func.count(distinct(Deduction.bounce_id))).filter(Deduction.deduction_json != None).scalar()
    counts['bouncesJudgedOld'] = db.query(func.count(distinct(Deduction.bounce_id))).filter(Deduction.deduction_json == None).scalar()
    # Bounces to be used, done so far
    counts['bouncesUsePoseJudgedOld'] = db.execute(sql_queries.num_judged_use_pose_deductions_old).scalar()
    counts['bouncesUseJudgedOld'] = db.execute(sql_queries.num_judged_use_deductions_old).scalar()

    percentCompletes = {}
    percentCompletes['routinePose'] = int((counts['routinesUsePose'] / float(counts['routinesUse'])) * 100)
    percentCompletes['routinesJudged'] = int((counts['routinesUsePoseJudgedOld'] / float(counts['routinesUsePose'])) * 100)
    percentCompletes['bouncePose'] = int((counts['bouncesJudgeableUsePose'] / float(counts['bouncesJudgeableUse'])) * 100)
    percentCompletes['bouncesJudged'] = int((counts['bouncesUsePoseJudgedOld'] / float(counts['bouncesJudgeableUsePose'])) * 100)

    return render_template('home.html', title='FYP', counts=counts, percentCompletes=percentCompletes)


@app.route('/gui')
def gui():
    # routines = db.query(Routine).filter(or_(Routine.use == 1, Routine.use == None)).order_by(Routine.level).all()
    routines = db.query(Routine).filter(Routine.use == 1).order_by(Routine.level).all()
    for i, routine in enumerate(routines):
        routine.index = i + 1
        routine.name = routine.prettyName()
        routine.level_name = consts.levels[routine.level] if routine.level is not None else 'None'
        routine.tracked = routine.isTracked(db)
        routine.posed = routine.isPoseImported(db)
        # routine.labelled = routine.isLabelled()
        # routine.judged = routine.isJudged(contrib)
        routine.thumbPath = 'images/thumbs/{}.jpg'.format(routine.id)
        routine.poseStatuses = helper_funcs.getPoseStatuses(routine.getPoseDirPaths(), routine.name)
        routine.numBounces = len(routine.bounces)

    return render_template('gui.html', title='List of Routines', routines=routines)


@app.route('/bounces_gui')
def bounces_gui():
    # Get all skill names
    # skills = db.execute(text("SELECT count(*), skill_name FROM bounces GROUP BY skill_name ")).fetchall()
    skills = db.execute(text("SELECT skill_name, (SELECT id FROM skills WHERE skills.name=bounces.skill_name) AS sort_order, count(*) AS c FROM bounces  WHERE sort_order NOTNULL GROUP BY skill_name ORDER BY sort_order")).fetchall()
    # Get all bounce with that name sorted from best to worst (deduction = 0.0 to 0.5)
    sortedBounceClasses = []
    for skill in skills:  # ignore Blank and Broken
        skillName = skill[0]
        skillBounces = db.query(Bounce).filter(Bounce.skill_name == skillName, Bounce.angles != None).all()
        bouncesWithDeductions = []
        for bounce in skillBounces:
            deductions = bounce.deductions
            if not deductions:
                averageDeduction = 99.
            else:
                averageDeduction = deductions[0].deduction_value
            bouncesWithDeductions.append([bounce, averageDeduction])
        # Sort bounces by best to worst
        sortedBounces = sorted(bouncesWithDeductions, key=itemgetter(1))
        sortedBounceClasses.append([skillName, sortedBounces])

    # routines = db.query(Routine).filter(or_(Routine.use == 1, Routine.use == None)).order_by(Routine.level).all()
    # routines = db.query(Routine).filter(Routine.use == 1, Routine.id == 127).order_by(Routine.level).all()
    # for i, routine in enumerate(routines):
    #     routine.index = i + 1
    #     routine.name = routine.prettyName()
    #     routine.level_name = consts.levels[routine.level] if routine.level is not None else 'None'
    #     routine.tracked = routine.isTracked()
    #     routine.posed = routine.isPoseImported(db)
    #     # routine.labelled = routine.isLabelled()
    #     # routine.judged = routine.isJudged(contrib)
    #     routine.thumbPath = 'images/thumbs/{}.jpg'.format(routine.id)
    #     routine.poseStatuses = helper_funcs.getPoseStatuses(routine.getPoseDirPaths(), routine.name)
    #     routine.numBounces = len(routine.bounces)

    return render_template('bounces_gui.html', title='Bounces', bounceClassesAndBounces=sortedBounceClasses)


@app.route('/list')
def list_routines():
    # contrib = db.query(Contributor).filter(Contributor.uid == g.userId).first()
    routines = db.query(Routine).filter(Routine.use == 1).order_by(Routine.level).all()
    for i, routine in enumerate(routines):
        routine.index = i + 1
        routine.name = routine.prettyName()
        routine.level_name = consts.levels[routine.level] if routine.level is not None else 'None'
        routine.tracked = routine.isTracked(db)
        # routine.framesSaved = routine.hasFramesSaved()
        routine.posed = routine.isPoseImported(db)
        routine.labelled = routine.isLabelled(db)
        routine.judged = routine.isOldJudged(db)
        # routine.judged = routine.isJudged(contributor=False)
        # routine.judged = routine.isJudged(contrib)
        # routine.your_score = routine.getScore(contrib)
        # routine.avg_score = routine.getAvgScore()
        routine.thumbPath = 'images/thumbs/{}.jpg'.format(routine.id)
        routine.broken = routine.isBroken(db)

    return render_template('list_routines.html', title='List of Routines', routines=routines)


#
# Sub-pages
#
@app.route('/label/<int:routine_id>', methods=['GET'])
def label_routine(routine_id):
    routine = db.query(Routine).filter(Routine.id == routine_id).one()
    routine.name = routine.prettyName()

    vidPath = os.path.join('videos/', routine.path).replace('\\', '/')
    nextRoutine = getNextUnlabelledRoutine(routine.id)

    # For js
    bounceIds = [bounce.id for bounce in routine.bounces]
    bounceIndexes = [bounce.bounce_index + 1 for bounce in routine.bounces]
    bounceNames = [bounce.skill_name for bounce in routine.bounces]
    startEndTimes = json.dumps([{"start": bounce.start_time, 'end': bounce.end_time} for bounce in routine.bounces])

    return render_template('label_routine.html',
                           title='Label Routine', vidPath=vidPath, routineId=routine.id, bounceIds=bounceIds,
                           bounceIndexes=bounceIndexes, bounceNames=json.dumps(bounceNames), startEndTimes=startEndTimes,
                           nextRoutine=nextRoutine)


@app.route('/judge/<int:routine_id>', methods=['GET'])
def judge_routine(routine_id):
    contrib = db.query(Contributor).filter(Contributor.uid == g.userId).first()
    routine = db.query(Routine).filter(Routine.id == routine_id).one()
    routine.name = routine.prettyName()
    routine.labelled = routine.isLabelled(db)

    vidPath = os.path.join('videos/', routine.path).replace('\\', '/')
    # contrib_id
    nextRoutine = None  # getNextUnjudgedRoutine(routine.id, contrib.id)
    userName = contrib.name if contrib else ""

    # Prepare skills for rendering
    skills = []
    skillIndexCounter = 1
    lookForOutBounce = False
    landingIndexes = []
    for skill in routine.bounces:
        if skill.skill_name == 'Broken':
            continue
        if skill.skill_name == 'Straight Bounce' and not lookForOutBounce:
            continue
        else:
            lookForOutBounce = True
        # Found an out-bounce
        if skill.skill_name == 'Straight Bounce' or skill.skill_name == 'Landing':
            skill.idx = '&nbsp;&nbsp;'
            lookForOutBounce = False  # stop looking once we've found one. Any following this considered landing phase
        else:
            skill.idx = skillIndexCounter

        if skill.skill_name == 'Landing':
            landingIndexes.append(skillIndexCounter - 1)

        # Give all the skills an attribute containing their judging categories' html
        skill.deduction_cats_html = render_deduction_cats_html(skillIndexCounter, skill.skill_name)

        skills.append(skill)
        skillIndexCounter += 1

    # Merge Landings
    if len(landingIndexes) > 1:
        firstLanding = skills[landingIndexes[0]]
        lastLanding = skills[landingIndexes[-1]]
        firstLanding.end_time = lastLanding.end_time
        skills2Delete = [skill for i, skill in enumerate(skills) if i in landingIndexes[1:]]
        for skill in skills2Delete:
            skills.remove(skill)

    skillIds = [skill.id for skill in skills]
    startEndTimes = json.dumps([{"start": skill.start_time, 'end': skill.end_time} for skill in skills])

    return render_template('judge_routine.html',
                           title='Judge Routine', vidPath=vidPath, routine=routine,
                           startEndTimes=startEndTimes, skills=skills, skillIds=skillIds,
                           userName=userName, nextRoutine=nextRoutine)


@app.route('/old_judge/<int:routine_id>', methods=['GET'])
def old_judge_routine(routine_id):
    contrib = db.query(Contributor).filter(Contributor.uid == g.userId).first()
    routine = db.query(Routine).filter(Routine.id == routine_id).one()
    routine.name = routine.prettyName()
    routine.labelled = routine.isLabelled(db)

    vidPath = os.path.join('videos/', routine.path).replace('\\', '/')
    # contrib_id
    nextRoutine = None  # getNextUnjudgedRoutine(routine.id, contrib.id)
    userName = contrib.name if contrib else ""

    # Prepare skills for rendering
    skills = []
    skillIndexCounter = 1
    lookForOutBounce = False
    for skill in routine.bounces:
        # if skill.skill_name == 'Broken':
        #     continue
        if skill.skill_name == 'Landing':
            continue
        if skill.skill_name == 'Straight Bounce' and not lookForOutBounce:
            continue
        else:
            lookForOutBounce = True
        # Found an out-bounce
        if skill.skill_name == 'Straight Bounce' or skill.skill_name == 'Landing':
            skill.idx = '&nbsp;&nbsp;'
            lookForOutBounce = False  # stop looking once we've found one. Any following this considered landing phase
        else:
            skill.idx = skillIndexCounter

        skills.append(skill)
        skillIndexCounter += 1

    skillIds = [skill.id for skill in skills]
    startEndTimes = json.dumps([{"start": skill.start_time, 'end': skill.end_time} for skill in skills])

    return render_template('old_judge_routine.html',
                           title='Judge Routine', vidPath=vidPath, routine=routine,
                           startEndTimes=startEndTimes, skills=skills, skillIds=skillIds,
                           userName=userName, nextRoutine=nextRoutine)


#
# Ajax Endpoints
#
@app.route('/label', methods=['POST'])
def label_routine_db():
    # http://stackoverflow.com/questions/10434599/how-to-get-data-recieved-in-flask-request
    # print(request.values)
    bounceNames = json.loads(request.values.get('bounceNames'))
    bounceIds = json.loads(request.values.get('bounceIds'))

    bounces = db.query(Bounce).filter(Bounce.id.in_(bounceIds)).all()
    for bounce, new_name in zip(bounces, bounceNames):
        bounce.skill_name = new_name
    db.commit()

    return ''


@app.route('/judge', methods=['POST'])
def judge_routine_db():
    # http://stackoverflow.com/questions/10434599/how-to-get-data-recieved-in-flask-request
    routineId = int(request.values['routine_id'])
    username = request.values['username']
    judgeStyle = request.values['judge_style']
    skillIds = json.loads(request.values['skill_ids'])
    routineDeductionValues = json.loads(request.values['routine_deduction_values'])
    routineDeductionsJSON = json.loads(request.values['routine_deductions_json'])

    # Create contributor if there's none in the db already
    contrib = db.query(Contributor).filter(Contributor.uid == g.userId).first()
    if not contrib:
        contrib = Contributor(g.userId, username)
        db.add(contrib)
        db.flush()

    # Create a judgements obj
    judgement = Judgement(routineId, contrib.id, judgeStyle)
    db.add(judgement)
    db.flush()  # interact with db without committing the changes so if there's a crash, nothing is updated

    # Create bounce deductions
    bounce_deductions = []
    for bounceId, deductionValue, deductionsJSON in zip(skillIds, routineDeductionValues, routineDeductionsJSON):
        deductionsJSON = None if deductionsJSON is None else json.dumps(deductionsJSON)
        bounce_deductions.append(Deduction(judgement.id, contrib.id, bounceId, deductionValue, deductionsJSON))

    db.add_all(bounce_deductions)
    db.commit()

    return '', 201  # CREATED


@app.route('/set_level', methods=['POST'])
def setLevel():
    print(request.values)

    routine_id = int(request.values.get('routine_id'))
    routine = db.query(Routine).filter(Routine.id == routine_id).one()

    level = request.values.get('level')
    if level == 'None':
        routine.level = None
    else:
        routine.level = consts.levels.index(level)
    db.commit()

    return ''


@app.route('/play_bounce', methods=['POST'])
def playBounce():
    from image_processing import visualise
    print(request.values)
    bounce_id = int(request.values.get('bounce_id'))
    visualise.play_bounce(db, bounce_id, show_pose=True)


@app.route('/gui_action', methods=['POST'])
def handleAction():
    from image_processing import import_output
    from image_processing import segment_bounces
    from image_processing import track
    from image_processing import trampoline
    from image_processing import visualise

    print(request.values)
    action = request.values.get('action')
    routine_id = int(request.values.get('routine_id'))
    routine = db.query(Routine).filter(Routine.id == routine_id).one()

    # If this routine is selected, automatically prompt to locate trampoline.
    if not routine.trampoline_top or not routine.trampoline_center or not routine.trampoline_width:
        # Detect Trampoline
        trampoline.detect_trampoline(db, routine)

    # Do the action
    if action == 'track':
        track.track_and_save(db, routine)

    elif action == 'segment_bounces':
        segment_bounces.segment_bounces_and_save(db, routine)
        # visualise.plot_data(routine)

    elif action == 'save_frames':
        import_output.save_cropped_frames(db, routine, routine.frames, '_blur_dark_0.6')

    elif action == 'play_monocap':
        # threading.Thread(target=visualise.compare_pose_tracking_techniques, args=(routine,)).start()
        visualise.compare_pose_tracking_techniques(routine)

    elif action == 'play_pose':
        visualise.play_frames(db, routine, show_pose=True)

    elif action == 'import_pose':
        import_output.import_monocap_preds_2d(db, routine)

    elif action == 'delete_pose':
        for frame in routine.frames:
            frame.pose = None
            frame.angles = None

        for bounce in routine.bounces:
            bounce.angles = None
            bounce.angles_count = None
        db.commit()
        print('Delete saved')
    else:
        return 'Action "{}" not found'.format(action)

    return ''


#
# Helper functions
#
def getNextUnjudgedRoutine(routine_id, contributor_id):
    # Gets next routine that hasn't been judged by this contributor
    nextRoutine = db.query(Routine).filter(
        Routine.id > routine_id,
        Routine.use == 1,
        text("routines.id NOT IN (SELECT judgements.routine_id FROM judgements WHERE judgements.contributor_id='{}')".format(contributor_id))
    ).first()
    if nextRoutine:
        nextRoutine.name = nextRoutine.prettyName()
    return nextRoutine


def getNextUnlabelledRoutine(routine_id):
    # Gets next routine that hasn't been judged by this contributor
    nextRoutine = db.query(Routine).filter(
        Routine.id > routine_id,
        Routine.use == 1,
        text("routines.id IN (SELECT bounces.routine_id FROM bounces WHERE bounces.skill_name = '')")
    ).first()
    if nextRoutine:
        nextRoutine.name = nextRoutine.prettyName()
    return nextRoutine


def render_deduction_cats_html(rowi, skill_name):
    deduction_category_html = get_template_attribute('macros.html', 'deduction_category_html')

    for skill_key, deduction_categories in judging_rows_html.deduction_categories_per_skill.items():
        # If this skill's name is in the key, then render the skill's deductions_html
        deduction_categories_html = ''  # holds the html for all deduction categories in the skill row
        if skill_name.lower() in skill_key.lower():
            for category in deduction_categories:
                deduction_categories_html += deduction_category_html(rowi, category, None)
            return deduction_categories_html

    return "Skill not found in judging_rows_html keys"


if __name__ == '__main__':
    # http: // stackoverflow.com / questions / 40247025 / flask - socket - error - errno - 10053 - an - established - connection - was - aborted - by - the
    app.run(debug=True, threaded=True)
