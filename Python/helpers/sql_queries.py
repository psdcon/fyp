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
# Bounces

judgeable = "bounces.skill_name != 'Straight Bounce' and bounces.skill_name != 'Broken'"

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
# Deductions
