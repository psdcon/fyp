# -*- coding: utf-8 -*-
from __future__ import print_function

import json
import os
import uuid

from flask import Flask, request, g, render_template
from flask import after_this_request

from helpers.db_declarative import db, Routine, text, Contributor

# create our little application :)
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='defaultpassword'
))
# app.config.from_envvar('FLASKR_SETTINGS', silent=True)


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
    routines = db.query(Routine).all()
    # print routines
    return render_template('home.html', title='FYP', routines=routines)


@app.route('/list')
def list_routines():
    contrib = db.query(Contributor).filter(Contributor.uid == g.userId).one()
    routines = db.query(Routine).all()
    for r in routines:
        r.name = r.prettyName()
        r.tracked = r.isTracked(db)
        r.labelled = r.isLabelled()
        r.judged = r.isJudged(contrib)
        r.score = '{}'.format(r.getAvgScore()) if r.isJudged else 'N/A'
    # print routines
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

@app.route('/judge/<int:routine_id>')
def judge_routine(routine_id):
    contrib = db.query(Contributor).filter(Contributor.uid == g.userId).one()
    routine = db.query(Routine).filter(Routine.id == routine_id).one()
    routine.labelled = routine.isLabelled()

    vidPath = os.path.join('videos/', routine.path).replace('\\', '/')
    nextRoutine = getNextRoutine(routine.id, contrib.id)
    userName = contrib.name if contrib else ""

    bounces = [b for b in routine.bounces if b.isJudgeable()]
    for i, b in enumerate(bounces):
        b.idx = i + 1
    startEndTimes = json.dumps([{"start": b.start_time, 'end': b.end_time} for b in bounces])

    arms = """<div class="clearfix">
    Arms
    <span class="pull-right">
        <label><input type="checkbox" name="" id=""> 0.1 Bent elbows</label>
    </span>
</div>"""
    legs = """<div class="clearfix" title="Bent knees, toes not pointed, legs note">
    Legs
    <span class="pull-right">
        <label><input type="checkbox" name="" id=""> 0.1 Knees</label>
        <label><input type="checkbox" name="" id=""> 0.1 Toes</label>
        <label><input type="checkbox" name="" id=""> 0.1 Apart</label>
    </span>
</div>"""
    # <!-- tighness of shape/dished/angle of hips(pikey) -->
    body = """<div class="clearfix">
    Body
    <span class="pull-right">
        <label><input type="radio" name="body" id=""> 0.1 Loose</label>
        <label><input type="radio" name="body" id=""> 0.2 Very loose</label>
    </span>
</div>"""
    angle_with_horizontal = """<div class="clearfix">
    Angle of legs with Horizontal <br>
    <label><input type="radio" name="horz" id=""> >65&deg; <90&deg; 0.1</label>
    <label><input type="radio" name="horz" id=""> >45&deg; <65&deg; 0.2</label>
</div>"""
    opening_shape_jumps = """<div class="clearfix">
    Opening (shape jumps) TODO fix<br>
    <label><input type="radio" name="horz" id=""> >65&deg; <90&deg; 0.1</label>
    <label><input type="radio" name="horz" id=""> >45&deg; <65&deg; 0.2</label>
</div>"""
    opening_timing_somi = """<div class="clearfix">
    Opening timing (somi) for feet/front landing (cody)/back landing <br>
    <label><input type="radio" name="horz" id=""> bet 1 & 2 o'clock 0.1</label>
    <label><input type="radio" name="horz" id=""> bet 2 & 3 o'clock 0.2</label>
    <label><input type="radio" name="horz" id=""> after 3/no opening 0.3</label>
</div>"""
    opening_holding_shape_feet_front = """<div class="clearfix">
    Opening holding shape for feet or front. (later is better) <br>
    Person
    <label><input type="radio" name="" id=""> piked down</label>
    <label><input type="radio" name="" id=""> tucked down</label>

    <label><input type="radio" name="horz" id=""> bet 12 & 2 o'clock 0.2</label>
    <label><input type="radio" name="horz" id=""> bet 2 & 3 o'clock 0.1</label>
</div>"""
    opening_holding_shape_back = """<div class="clearfix">
    Opening holding shape for back. (later is better) <br>
    <label><input type="radio" name="" id=""> piked down</label>
    <label><input type="radio" name="" id=""> tucked down (adds 0.1 to deduction)</label>

    <label><input type="radio" name="horz" id=""> bet 12 & 3 o'clock 0.2</label>
    <label><input type="radio" name="horz" id=""> bet 3 & 4:30 o'clock 0.1</label>
</div>"""
    twist_timing = """<div class="clearfix">
    End of twist <br>
    <label><input type="checkbox" name="" id=""> not finished twist at 3 o'clock 0.1</label>
</div>"""
    twist_arms_half_full = """<div class="clearfix">
    Arms to stop twist (baraini/full/half outs) <br>
    <label><input type="checkbox" name="" id=""> arms >45&deg; 0.1</label>
</div>"""
    twist_arms_over_full = """<div class="clearfix">
    Arms to stop twist (>full twist)
    <label><input type="checkbox" name="" id=""> arms >90&deg; 0.1</label>
</div>"""

    skill_deductions = {
        'tuck jump, pike jump, straddle jump,': [arms, legs, body, angle_with_horizontal, opening_shape_jumps],
        'seat drop': [arms, legs, body],
        'Swivel Hips/Seat Half Twist to Seat Drop': [arms, legs, body, twist_timing],
        'Half Twist to Feet (from seat)': [arms, legs, body, twist_timing],
        'front drop, back drop': [arms, legs, body], #"windmilling"
        'to feet (from front), to feet (from back)': [arms, legs, body],
        'half twist jump, full twist jump': [arms, legs, body, twist_timing],
        'front/back somi': [arms, legs, body, opening_timing_somi, opening_holding_shape_feet_front],
    }
    for b in bounces:
        for skill_key in skill_deductions:
            if b.skill_name.lower() in skill_key.lower():
                deduction_things = ""
                for thing in skill_deductions[skill_key]:
                    deduction_things += thing
                b.deductions_things = deduction_things


    return render_template('judge_routine.html',
                           title='Judge Routine', vidPath=vidPath, routine=routine,
                           startEndTimes=startEndTimes, bounces=bounces, userName=userName,
                           nextRoutine=nextRoutine)


# http://flask.pocoo.org/docs/0.12/patterns/sqlalchemy/
# @app.teardown_appcontext
# def shutdown_session(exception=None):
#     db.remove()
"""
judgements
    id
    routine_id
    contributer_id

    bounce_deductions

"""

if __name__ == '__main__':
    app.run(debug=True)
