# -*- coding: utf-8 -*-
from __future__ import print_function

import json
import os
import uuid

from flask import Flask, request, g, render_template
from flask import after_this_request
from flask import get_template_attribute
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import case
from sqlalchemy import text

import judging_rows_html
from helpers.db_declarative import Routine, Contributor, Judgement, Bounce, Deduction

# create our little application :)
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='defaultpassword'
))

# Open db in a way that takes care of threding issue on the server
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


@app.route('/')
def index():
    routines = []  # db.query(Routine).all()
    return render_template('home.html', title='FYP', routines=routines)


@app.route('/list')
def list_routines():
    contrib = db.query(Contributor).filter(Contributor.uid == g.userId).first()
    routines = db.query(Routine).filter(Routine.use == 1).order_by(
        case(((Routine.level == 'Novice', 0),
              (Routine.level == 'Intermediate', 1),
              (Routine.level == 'Intervanced', 2),
              (Routine.level == 'Advanced', 3),
              (Routine.level == 'Elite', 4)))
    ).all()
    for i, routine in enumerate(routines):
        routine.index = i + 1
        routine.name = routine.prettyName()
        routine.tracked = routine.isTracked(db)
        routine.framesSaved = routine.hasFramesSaved()
        routine.posed = routine.isPoseImported(db)
        routine.labelled = routine.isLabelled()
        routine.judged = routine.isJudged(contrib)
        routine.your_score = routine.getScore(contrib)
        routine.avg_score = routine.getAvgScore()
        routine.thumbPath = 'images/thumbs/' + os.path.basename(routine.path).replace('.mp4', '.jpg')
        routine.broken = routine.isBroken()

    return render_template('list_routines.html', title='List of Routines', routines=routines)


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


@app.route('/judge/<int:routine_id>', methods=['GET'])
def judge_routine(routine_id):
    contrib = db.query(Contributor).filter(Contributor.uid == g.userId).first()
    routine = db.query(Routine).filter(Routine.id == routine_id).one()
    routine.name = routine.prettyName()
    routine.labelled = routine.isLabelled()

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
        if skill.skill_name == 'In/Out Bounce' and not lookForOutBounce:
            continue
        else:
            lookForOutBounce = True
        # Found an out-bounce
        if skill.skill_name == 'In/Out Bounce' or skill.skill_name == 'Landing':
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


@app.route('/judge', methods=['POST'])
def judge_routine_db():
    # http://stackoverflow.com/questions/10434599/how-to-get-data-recieved-in-flask-request
    routineId = int(request.values['routine_id'])
    username = request.values['username']
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
    judgement = Judgement(routineId, contrib.id)
    db.add(judgement)
    db.flush()  # interact with db without committing the changes so if there's a crash nothing is updated

    # Create bounce deductions
    bounce_deductions = []
    for bounceId, deductionValue, deductionsJSON in zip(skillIds, routineDeductionValues, routineDeductionsJSON):
        bounce_deductions.append(Deduction(judgement.id, contrib.id, bounceId, deductionValue, json.dumps(deductionsJSON)))

    db.add_all(bounce_deductions)
    db.commit()

    return '', 201  # CREATED


if __name__ == '__main__':
    # http: // stackoverflow.com / questions / 40247025 / flask - socket - error - errno - 10053 - an - established - connection - was - aborted - by - the
    app.run(debug=True, threaded=True)
