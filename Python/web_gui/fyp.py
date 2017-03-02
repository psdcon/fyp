# -*- coding: utf-8 -*-
from __future__ import print_function

import json
import os
import uuid

from flask import Flask, request, g, render_template
from flask import after_this_request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

from helpers.db_declarative import Routine, Contributor, Judgement
from judging_rows_html import *

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
    routines = db.query(Routine).filter(Routine.use == 1).all()
    for i, routine in enumerate(routines):
        routine.index = i + 1
        routine.name = routine.prettyName()
        routine.tracked = routine.isTracked(db)
        routine.framesSaved = routine.hasFramesSaved()
        routine.posed = routine.isPosed(db)
        routine.labelled = routine.isLabelled()
        routine.judged = routine.isJudged(contrib)
        routine.your_score = routine.getScore(contrib)
        routine.avg_score = routine.getAvgScore()
        routine.thumbPath = 'images/thumbs/' + os.path.basename(routine.path).replace('.mp4', '.jpg')

    return render_template('list_routines.html', title='List of Routines', routines=routines)


def getNextRoutine(routine_id, contributor_id):
    # Gets next routine that hasn't been judged by this contributor
    nextRoutine = db.query(Routine).filter(
        Routine.id > routine_id,
        text("routines.id NOT IN (SELECT judgements.routine_id FROM judgements WHERE judgements.contributor_id='{}')".format(contributor_id))
    ).first()
    if nextRoutine:
        nextRoutine.name = nextRoutine.prettyName()
    return nextRoutine


@app.route('/judge/<int:routine_id>', methods=['GET'])
def judge_routine(routine_id):
    contrib = db.query(Contributor).filter(Contributor.uid == g.userId).first()
    routine = db.query(Routine).filter(Routine.id == routine_id).one()
    routine.labelled = routine.isLabelled()

    vidPath = os.path.join('videos/', routine.path).replace('\\', '/')
    # contrib_id
    nextRoutine = None  # getNextRoutine(routine.id, contrib.id)
    userName = contrib.name if contrib else ""

    skills = [sk for sk in routine.bounces if sk.isJudgeable()]
    skillIds = [sk.id for sk in routine.bounces]
    for i, sk in enumerate(skills):
        sk.idx = i + 1
    startEndTimes = json.dumps([{"start": sk.start_time, 'end': sk.end_time} for sk in skills])

    for i, sk in enumerate(skills):
        for skill_key in skill_deductions:
            if sk.skill_name.lower() in skill_key.lower():
                sk.judging_rows = get_judging_rows(i, skill_deductions[skill_key])

    return render_template('judge_routine.html',
                           title='Judge Routine', vidPath=vidPath, routine=routine,
                           startEndTimes=startEndTimes, skills=skills, skillIds=skillIds,
                           userName=userName, nextRoutine=nextRoutine)


def get_judging_rows(rowi, rows):
    row_html = ''
    for row_key in rows:
        row_html += judging_rows_html[row_key].replace('{index}', '{}'.format(rowi))
    return row_html


@app.route('/judge', methods=['POST'])
def judge_routine_db():
    # http://stackoverflow.com/questions/10434599/how-to-get-data-recieved-in-flask-request
    print(request.values)
    return ''
    # # Create contributor if there's none in the db already
    # contrib = db.query(Contributor).filter(Contributor.uid == g.userId).first()
    # if not contrib:
    #     contrib = Contributor(request.args.get('user_name'), g.userId)
    #     db.add(contrib)
    #     db.flush()
    #
    # # Create a judgements obj
    # judgement = Judgement(request.args.get('routine_id'), contrib.id)
    # db.add(judgement)
    # db.flush()  # interact with db without commiting the changes so if there's a crash nothing is updated
    #
    # # Create bounce deductions
    # bounce_deductions = []
    # # for deduction in request.args.get('deductions'):
    # #     bounce_deductions.append([
    # #
    # #     ])
    #
    # db.add_all(bounce_deductions)
    # db.commit()
    #
    # return '', 201  # CREATED


if __name__ == '__main__':
    app.run(debug=True)
