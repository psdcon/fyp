"""
SELECT column_name(s)
FROM table_name
WHERE condition
GROUP BY column_name(s)
HAVING condition
ORDER BY column_name(s);
"""

# num_use_bounces = """
# SELECT sum(num_use_bounces_per_routine) AS num_use_bounces FROM (
#     SELECT count(bounces.routine_id) AS num_use_bounces_per_routine
#     FROM routines
#     LEFT JOIN bounces
#     ON (bounces.routine_id = routines.id)
#     WHERE routines.use == 1
#     GROUP BY
#         routines.id
# )
# """

#
# Routines
num_use_pose_routines = """
SELECT count(num_routines_posed_bounces) FROM (
        SELECT count(bounces_posed.routine_id) AS num_routines_posed_bounces
        FROM routines
        LEFT JOIN (SELECT * FROM bounces WHERE bounces.angles NOTNULL) bounces_posed
            ON (routines.id = bounces_posed.routine_id)
        WHERE routines.use == 1
        GROUP BY routines.id
        HAVING num_routines_posed_bounces > 0
)
"""

#
#
# Bounces

judgeable = "bounces.skill_name != 'Straight Bounce' and bounces.skill_name != 'Broken' and bounces.skill_name != 'Landing'"

num_judgeable_bounces = "SELECT count(*) FROM bounces WHERE " + judgeable

num_judgeable_use_bounces = """
SELECT count(*) FROM (
    SELECT routines.use, bounces.routine_id FROM bounces
    LEFT JOIN routines
        ON (bounces.routine_id = routines.id)
    WHERE routines.use == 1 AND {}
)
""".format(judgeable)

num_judgeable_use_pose_bounces = """
SELECT count(*) FROM (
    SELECT routines.use, bounces.routine_id FROM bounces
    LEFT JOIN routines
        ON (bounces.routine_id = routines.id)
    WHERE routines.use == 1 AND bounces.angles NOTNULL AND {}
)
""".format(judgeable)

#
#
# Deductions
num_judged_use_deductions_old = """
SELECT count(*) FROM (
    SELECT count(bounce_deductions.id) AS num_deductions,  routines.use, bounces.skill_name, bounces.angles, bounces.routine_id, bounce_deductions.* FROM bounce_deductions 
    LEFT JOIN bounces
        ON (bounces.id = bounce_deductions.bounce_id)
    LEFT JOIN routines
        ON (routines.id = bounces.routine_id)
    WHERE deduction_json ISNULL AND routines.use==1
    GROUP BY bounce_deductions.bounce_id
)
"""

num_judged_use_pose_deductions_old = """
SELECT count(*) FROM (
    SELECT count(bounce_deductions.id) AS num_deductions,  routines.use, bounces.skill_name, bounces.angles, bounces.routine_id, bounce_deductions.* FROM bounce_deductions 
    LEFT JOIN bounces
        ON (bounces.id = bounce_deductions.bounce_id)
    LEFT JOIN routines
        ON (routines.id = bounces.routine_id)
    WHERE deduction_json ISNULL AND routines.use==1 AND bounces.angles NOTNULL
    GROUP BY bounce_deductions.bounce_id
)
"""

num_judged_use_pose_routines_old = """
SELECT count(*) FROM (
    SELECT routines.use, bounces.skill_name, bounces.angles, bounces.routine_id, bounce_deductions.* FROM bounce_deductions 
    LEFT JOIN bounces
        ON (bounces.id = bounce_deductions.bounce_id)
    LEFT JOIN routines
        ON (routines.id = bounces.routine_id)
    WHERE bounce_deductions.deduction_json ISNULL AND routines.use==1 AND bounces.angles NOTNULL
    GROUP BY bounces.routine_id
)
"""

#
#
# MISC
"""
update judgements set judge_style = CASE 
WHEN (select bounce_deductions.deduction_json from bounce_deductions where bounce_deductions.judgement_id = judgements.id) NOTNULL 
THEN 'new' ELSE 'old' END
"""
