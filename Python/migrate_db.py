import json
import sqlite3

import cv2

from helpers import consts, helper

db = sqlite3.connect(consts.databasePath)
db.row_factory = sqlite3.Row

# Copy data from old table
db.execute("INSERT INTO routines (path, level) SELECT name, level FROM old_routines")
routines = db.execute("SELECT routines.id as new_id, old_routines.* FROM old_routines INNER JOIN routines on old_routines.name = routines.path")
# routines = res.fetchall()
for routine in routines:
    trampoline = json.loads(routine['trampoline'])
    center_points = json.loads(routine['center_points'])
    ellipses = json.loads(routine['ellipses'])
    bounces = json.loads(routine['bounces'])
    competition = routine['name'][:routine['name'].index("/")]

    cap = helper.open_video(routine['name'])
    fps = cap.get(cv2.CAP_PROP_FPS)
    capWidth = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    capHeight = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # If the routine has not yet been tracked, only update it's meta info and move onto the next routine.
    if not trampoline:
        db.execute(
            "UPDATE routines SET competition=?, note=?, video_height=?, video_width=?, video_fps=? WHERE id=?",
            (competition, routine['notes'], capHeight, capWidth, fps,
             routine['new_id'],))
        continue

    # Routine has been tracked, add all meta data
    db.execute("UPDATE routines SET competition=?, note=?, video_height=?, video_width=?, video_fps=?, trampoline_top=?, trampoline_center=? WHERE id=?",
               (competition, routine['notes'], capHeight, capWidth, fps, trampoline['top'], trampoline['center'], routine['new_id'],))

    # Add tacking data
    for cpt, ell in zip(center_points, ellipses):
        frameNum = cpt[0]
        db.execute("INSERT INTO frame_data (routine_id, frame_num, center_pt_x, center_pt_y, ellipse_len_major, ellipse_len_minor, ellipse_angle) "
                   "VALUES (?, ?, ?, ?, ?, ?, ?)", (routine['new_id'], frameNum, cpt[1], cpt[2], ell[2][0], ell[2][1], ell[3],))

    # Add bounces
    for i, bounce in enumerate(bounces):
        cur = db.execute(
            "INSERT INTO bounces (routine_id, bounce_index, skill_name, start_frame, end_frame, max_height_time, start_time, end_time, max_height_frame, start_height, end_height, max_height) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (routine['new_id'], i, bounce['name'], bounce['startFrame'], bounce['endFrame'], format(bounce['maxHeightFrame']/fps, '.2f'),
             bounce['startTime'], bounce['endTime'], bounce['maxHeightFrame'],
             bounce['startHeightInPixels'], bounce['endHeightInPixels'], bounce['maxHeightInPixels'],)
        )

    # Get judgements
    judgements = db.execute("SELECT * FROM old_judgements WHERE routine_id=?", (routine['id'],))
    for judgement in judgements:
        # Get contributor id. First check if contributor exists
        res = db.execute("SELECT id FROM contributors WHERE m5d_id=?", (judgement['user_id'],)).fetchone()
        if res:
            contributorId = res['id']
        else:
            cur = db.execute("INSERT INTO contributors (name, m5d_id) VALUES (?, ?)", (judgement['user_name'], judgement['user_id'],))
            contributorId = cur.lastrowid

        # Loop through bounces and deductions simultaneously
        # Need bounce id before can add deduction
        deductions = json.loads(judgement['deductions'])
        for i, deduction in enumerate(deductions):
            bounce = db.execute("SELECT id FROM bounces WHERE routine_id=? AND bounce_index=?", (routine['new_id'], i,)).fetchone()
            bounceId = bounce['id']
            if deduction:  # make sure not null, i.e. not judging an in/out bounce
                db.execute("INSERT INTO bounce_deductions (bounce_id, deduction, contributor_id) VALUES (?, ?, ?)", (bounceId, deduction, contributorId,))

    # done
db.commit()
db.close()



































