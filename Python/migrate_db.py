import json
import sqlite3

import cv2

from helpers import consts as com

db = sqlite3.connect(com.dbPath)
db.row_factory = sqlite3.Row

# INSERT INTO _routines (path, level) SELECT name, level FROM routines

# routines = db.execute("SELECT * FROM routines")
db.execute("INSERT INTO _routines (path, level) SELECT name, level FROM routines")
routines = db.execute("SELECT _routines.id as new_id, routines.* FROM routines INNER JOIN _routines on routines.name = _routines.path")
# routines = res.fetchall()
for routine in routines:
    trampoline = json.loads(routine['trampoline'])
    center_points = json.loads(routine['center_points'])
    ellipses = json.loads(routine['ellipses'])
    bounces = json.loads(routine['bounces'])
    competition = routine['name'][:routine['name'].index("/")]

    cap = com.open_video(routine['name'])
    fps = cap.get(cv2.CAP_PROP_FPS)
    capWidth = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    capHeight = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if not trampoline:
        db.execute(
            "UPDATE _routines SET competition=?, note=?, video_height=?, video_width=?, video_fps=? WHERE id=?",
            (competition, routine['notes'], capHeight, capWidth, fps,
             routine['new_id'],))
        continue

    db.execute("UPDATE _routines SET competition=?, note=?, video_height=?, video_width=?, video_fps=?, trampoline_top=?, trampoline_center=? WHERE id=?",
               (competition, routine['notes'], capHeight, capWidth, fps, trampoline['top'], trampoline['center'], routine['new_id'],))

    for cpt, ell in zip(center_points, ellipses):
        frameNum = cpt[0]
        db.execute("INSERT INTO _tracking_data (routine_id, frame_num, center_pt_x, center_pt_y, ellipse_len_major, ellipse_len_minor, ellipse_angle) "
                   "VALUES (?, ?, ?, ?, ?, ?, ?)", (routine['new_id'], frameNum, cpt[1], cpt[2], ell[2][0], ell[2][1], ell[3],))

    judgements = db.execute("SELECT * FROM judgements WHERE routine_id=?", (routine['id'],))
    for judgement in judgements:
        res = db.execute("SELECT id FROM _contributors WHERE m5d_id=?", (judgement['user_id'],)).fetchone()
        if res:
            contributorId = res['id']
        else:
            cur = db.execute("INSERT INTO _contributors (name, m5d_id) VALUES (?, ?)", (judgement['user_name'], judgement['user_id'],))
            contributorId = cur.lastrowid

        # Loop through bounces and deductions simultaneously
        # Need bounce id before can add deduction
        deductions = json.loads(judgement['deductions'])
        for bounce, deduction in zip(bounces, deductions):
            cur = db.execute(
                "INSERT INTO _bounces (routine_id, skill_name, start_frame, end_frame, start_time, end_time, max_height_frame, start_height, end_height, max_height) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (routine['new_id'], bounce['name'], bounce['startFrame'], bounce['endFrame'], bounce['startTime'], bounce['endTime'], bounce['maxHeightFrame'],
                 bounce['startHeightInPixels'], bounce['endHeightInPixels'], bounce['maxHeightInPixels'],))
            bounceId = cur.lastrowid
            if deduction:  # make sure not null, i.e. not judging an in/out bounce
                db.execute("INSERT INTO _bounce_deductions (bounce_id, deduction, contributor_id) VALUES (?, ?, ?)", (bounceId, deduction, contributorId,))

    # done
db.commit()
db.close()
