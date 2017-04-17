import glob
import json
import os

from numpy import array
from sqlalchemy import Column, ForeignKey, INTEGER, REAL, TEXT
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from helpers import consts

Base = declarative_base()


def getDb():
    if 'C:\\Users\\psdco\\Documents\\ProjectCode\\Python' in os.path.abspath('.'):
        engine = create_engine('sqlite:////Users/psdco/Documents/ProjectCode/Python/db.sqlite3')
    else:
        engine = create_engine('sqlite:////var/www/html/fyp/db.sqlite3')
    Base.metadata.bind = engine
    Session = sessionmaker(bind=engine)
    return Session()


class Routine(Base):
    __tablename__ = 'routines'

    id = Column(INTEGER, primary_key=True)
    path = Column(TEXT, nullable=False, unique=True)
    use = Column(INTEGER)
    crop_length = Column(INTEGER)  # padding (in pixels) from the center point
    note = Column(TEXT)
    competition = Column(TEXT)
    level = Column(INTEGER)
    video_height = Column(INTEGER)
    video_width = Column(INTEGER)
    video_fps = Column(REAL)
    frame_count = Column(INTEGER)
    trampoline_top = Column(INTEGER)
    trampoline_center = Column(INTEGER)
    trampoline_width = Column(INTEGER)
    original_path = Column(TEXT, unique=True)
    has_pose = Column(INTEGER)

    frames = relationship("Frame", back_populates='routine')
    bounces = relationship("Bounce", back_populates='routine')
    judgements = relationship("Judgement", back_populates='routine')

    def __init__(self, path, original_path, competition, video_height, video_width, video_fps, frame_count):
        self.path = path
        self.original_path = original_path
        self.competition = competition
        self.video_height = video_height
        self.video_width = video_width
        self.video_fps = video_fps
        self.frame_count = frame_count

    def __repr__(self):
        return "Routine(id=%r, path=%r, level=%r)" % (self.id, self.path, self.level)

    # Path related getters
    def getAsDirPath(self, suffix=None, create=False):
        if suffix:
            path = consts.videosRootPath + self.path.replace('.mp4', suffix + os.sep)
        else:
            path = consts.videosRootPath + self.path.replace('.mp4', os.sep)
        if create and not os.path.exists(path):
            print("Creating " + path)
            os.makedirs(path)
        return path

    def prettyName(self):
        return os.path.splitext(os.path.basename(self.path))[0]

    def getPoseDirPaths(self):
        return [poseDir for poseDir in glob.glob(os.path.dirname(self.getAsDirPath()) + '*') if os.path.isdir(poseDir)]

    # File related attributes
    def hasFramesSaved(self, suffix=None):
        nFiles = len(glob.glob(self.getAsDirPath(suffix) + 'frame_*'))
        return nFiles > 0

    def hasMonocapImgs(self, suffix=None):
        nFiles = len(glob.glob(self.getAsDirPath(suffix) + 'smoothed_*'))
        return nFiles > 0

    def personMasksPath(self):
        return os.path.dirname(self.getAsDirPath()) + '_person_masks.gzip'

    # Db related values
    def getTrampolineTouches(self):
        from helpers import helper_funcs
        trampolineTouches = array([frame.trampoline_touch for frame in self.frames])
        trampolineTouches = helper_funcs.trim_touches(trampolineTouches)
        return trampolineTouches

    def getScore(self, contributor):
        if not contributor:
            return 'N/A'
        for j in self.judgements:
            if j.contributor_id == contributor.id:
                return '{0:.1f}'.format(j.getScore())
        return 'N/A'

    def getAvgScore(self):
        if not self.judgements:
            return 'N/A'
        scores = [j.getScore() for j in self.judgements]
        return '{0:.1f}'.format(sum(scores) / len(scores))

    # Db related attributes
    def isTracked(self, db):
        # return len(self.frames) > 0
        count = db.execute("select count(*) from frame_data where frame_data.routine_id == {}".format(self.id)).scalar()
        return count > 0

    # def isPoseImported(self, db):
    #     # SELECT count(1) FROM frame_data WHERE routine_id=1 AND pose!=''
    #     # count = db.query(Frame.id).filter(Frame.pose != '', Frame.routine_id == self.id).count()
    #     count = db.execute("select count(*) from frame_data where frame_data.pose notnull and frame_data.routine_id == {}".format(self.id)).scalar()
    #     return count > 0

    def isLabelled(self, db):
        count = db.execute("select count(*) from bounces where skill_name NOTNULL and routine_id == {}".format(self.id)).scalar()
        # count = db.execute("SELECT count(*) FROM bounces WHERE skill_name = 'Broken' AND routine_id = {}".format(self.id)).scalar()
        return count > 0
        # if not self.bounces:
        #     return False
        # # Otherwise, check that they're all labelled
        # for b in self.bounces:
        #     if b.skill_name == '':
        #         return False
        # return True

    def isBroken(self, db):
        count = db.execute("SELECT count(*) FROM bounces WHERE skill_name = 'Broken' AND routine_id = {}".format(self.id)).scalar()
        return count > 0
        # if not self.bounces:
        #     return False
        # # Otherwise, check that they're all labelled
        # for b in self.bounces:
        #     if b.skill_name == 'Broken':
        #         return True
        # return False

    def isOldJudged(self, db):
        count = db.execute("SELECT * FROM judgements WHERE has_categories = 'old' AND routine_id = {}".format(self.id)).scalar()
        return count > 0

    def isNewJudged(self, db):
        count = db.execute("SELECT * FROM judgements WHERE has_categories = 'new' AND routine_id = {}".format(self.id)).scalar()
        return count > 0

    def isJudged(self, contributor=False):
        if contributor:  # has a value, the database Contributor obj
            for j in self.judgements:
                if j.contributor_id == contributor.id:
                    return True
            return False
        elif not contributor or contributor is None:  # contributor is false or non existent so tell me the general case
            if self.judgements:
                return True
            return False


class Frame(Base):
    __tablename__ = 'frame_data'

    id = Column(INTEGER, primary_key=True)
    routine_id = Column(INTEGER, ForeignKey('routines.id'))
    bounce_id = Column(INTEGER, ForeignKey('bounces.id'))
    frame_num = Column(INTEGER)
    center_pt_x = Column(INTEGER)
    center_pt_y = Column(INTEGER)
    hull_max_length = Column(INTEGER)
    trampoline_touch = Column(INTEGER)
    pose = Column(TEXT)
    angles = Column(TEXT)

    routine = relationship("Routine", back_populates='frames')
    bounce = relationship("Bounce", back_populates='frames')

    def __init__(self, routine_id, frame_num, center_pt_x, center_pt_y, hull_max_length, trampoline_touch):
        self.routine_id = routine_id
        self.frame_num = frame_num
        self.center_pt_x = center_pt_x
        self.center_pt_y = center_pt_y
        self.hull_max_length = hull_max_length
        self.trampoline_touch = trampoline_touch

    def __repr__(self):
        return "Frame(id=%r, r_id=%r, b_id=%r, f_num=%r)" % (self.id, self.routine_id, self.bounce_id, self.frame_num)


class Bounce(Base):
    __tablename__ = 'bounces'

    id = Column(INTEGER, primary_key=True)
    routine_id = Column(INTEGER, ForeignKey('routines.id'))
    bounce_index = Column(INTEGER)
    skill_name = Column(TEXT)
    code_name = Column(TEXT)
    shape = Column(TEXT)

    start_frame = Column(INTEGER)
    apex_frame = Column(INTEGER)
    end_frame = Column(INTEGER)

    start_time = Column(REAL)
    apex_time = Column(REAL)
    end_time = Column(REAL)

    start_height = Column(INTEGER)
    apex_height = Column(INTEGER)
    end_height = Column(INTEGER)

    angles = Column(TEXT)
    angles_count = Column(INTEGER)
    match_count = Column(INTEGER)
    ref_or_test = Column(TEXT)

    routine = relationship("Routine", back_populates='bounces')
    deductions = relationship("Deduction", back_populates='bounce')
    frames = relationship("Frame", back_populates='bounce')
    tariff_match = relationship("TariffMatches", back_populates='bounce', foreign_keys='TariffMatches.bounce_id')

    # bounces_i_match = relationship("TariffMatches", back_populates='matched_bounce')

    def __init__(self, routine_id, bounce_index, skill_name, start_frame, apex_frame, end_frame, start_time,
                 apex_time, end_time, start_height, apex_height, end_height):
        self.routine_id = routine_id
        self.bounce_index = bounce_index
        self.skill_name = skill_name

        self.start_frame = start_frame
        self.apex_frame = apex_frame
        self.end_frame = end_frame

        self.start_time = start_time
        self.apex_time = apex_time
        self.end_time = end_time

        self.start_height = start_height
        self.apex_height = apex_height
        self.end_height = end_height

    def __repr__(self):
        if self.shape:
            return "Bounce(id=%r, r_id=%r, skill_name=%r, shape=%r)" % (self.id, self.routine_id, self.skill_name, self.shape)
        else:
            return "Bounce(id=%r, r_id=%r, skill_name=%r)" % (self.id, self.routine_id, self.skill_name)

    def isJudgeable(self):
        return self.skill_name != "Straight Bounce"  # and self.skill_name != "Broken"

    # Used in segment bounces to set up the frame to bounce relationship
    def getFrames(self, db):
        return db.query(Frame).filter(
            Frame.routine_id == self.routine_id,
            Frame.frame_num >= self.start_frame,
            Frame.frame_num < self.end_frame
        ).all()

    def getAngles(self):
        # import numpy as np
        angles = []
        for frame in self.frames:
            if frame.angles:
                angles.append(array(json.loads(frame.angles)))
        return angles

    def getTariff(self, db):
        # Get tariff for this bounce i.e. 0.x
        skill = db.query(Skill).filter(Skill.name == self.skill_name).one()
        tariff = skill.tariff
        if self.shape and self.shape != 'Tuck':
            tariff += skill.shape_bonus

        return tariff

    def getAnyDeduction(self):
        deductions = self.deductions
        if not deductions:
            return None
        else:
            averageDeduction = deductions[0].deduction_value
            return averageDeduction

    def getNewDeduction(self):
        deductions = self.deductions
        if not deductions:
            return None, None
        for deduction in reversed(deductions):
            if deduction.deduction_cats is not None:
                return deduction.deduction_value, json.loads(deduction.deduction_cats)
        return None, None


class Judgement(Base):
    __tablename__ = 'judgements'

    id = Column(INTEGER, primary_key=True)
    routine_id = Column(INTEGER, ForeignKey('routines.id'))
    contributor_id = Column(INTEGER, ForeignKey('contributors.id'))
    score = Column(REAL)
    has_categories = Column(TEXT)

    routine = relationship("Routine", back_populates='judgements')
    contributor = relationship("Contributor", back_populates='judgements')
    deductions = relationship("Deduction", back_populates='judgement')

    def __init__(self, routine_id, contributor_id, has_categories):
        self.routine_id = routine_id
        self.contributor_id = contributor_id
        self.has_categories = has_categories

    def __repr__(self):
        return "Judgement(routine=%r, deductions=%r, who=%r)" % (self.routine, self.deductions, self.contributor)

    def getScore(self):
        deductionValues = [d.deduction_value for d in self.deductions]
        # Only take the first 10
        score = 10 - sum(deductionValues[:10])
        return score


class Deduction(Base):
    __tablename__ = 'bounce_deductions'

    id = Column(INTEGER, primary_key=True)
    judgement_id = Column(INTEGER, ForeignKey('judgements.id'))
    bounce_id = Column(INTEGER, ForeignKey('bounces.id'))
    contributor_id = Column(INTEGER, ForeignKey('contributors.id'))
    deduction_value = Column(REAL)
    deduction_cats = Column(TEXT)

    bounce = relationship("Bounce", back_populates='deductions')
    judgement = relationship("Judgement", back_populates='deductions')
    contributor = relationship("Contributor", back_populates='deductions')

    def __init__(self, judgement_id, contributor_id, bounce_id, deduction_value, deduction_cats):
        self.judgement_id = judgement_id
        self.contributor_id = contributor_id
        self.bounce_id = bounce_id
        self.deduction_value = deduction_value
        self.deduction_cats = deduction_cats

    def __repr__(self):
        return "Deduction(deduction=%r, who=%r)" % (self.deduction_value, self.contributor)


class Contributor(Base):
    __tablename__ = 'contributors'

    id = Column(INTEGER, primary_key=True)
    uid = Column(TEXT, unique=True)
    name = Column(TEXT)

    deductions = relationship("Deduction", back_populates='contributor')
    judgements = relationship("Judgement", back_populates='contributor')

    def __init__(self, uid, name):
        self.uid = uid
        self.name = name

    def __repr__(self):
        return "Contributor(id=%r, name=%s)" % (self.id, self.name)


class Skill(Base):
    __tablename__ = 'skills'

    id = Column(INTEGER, primary_key=True)
    name = Column(TEXT)
    code = Column(TEXT)
    fig_notation = Column(TEXT)
    tariff = Column(REAL)
    shape_bonus = Column(REAL)
    start_position = Column(TEXT)
    end_position = Column(TEXT)


class TariffMatches(Base):
    __tablename__ = 'tariff_matches'

    id = Column(INTEGER, primary_key=True)
    bounce_id = Column(INTEGER, ForeignKey('bounces.id'))
    matched_bounce_id = Column(INTEGER, ForeignKey('bounces.id'))
    matched_bounces_ids = Column(TEXT)
    matched_bounces_distances = Column(TEXT)
    time_taken = Column(REAL)

    bounce = relationship("Bounce", back_populates='tariff_match', foreign_keys=[bounce_id])
    # matched_bounce = relationship("Bounce", back_populates='bounces_i_match', foreign_keys=[matched_bounce_id])
    matched_bounce = relationship("Bounce", foreign_keys=[matched_bounce_id])

    def __init__(self, bounce_id, matched_bounce_id, matched_bounces_ids, matched_bounces_distances, time_taken):
        self.bounce_id = bounce_id
        self.matched_bounce_id = matched_bounce_id
        self.matched_bounces_ids = matched_bounces_ids
        self.matched_bounces_distances = matched_bounces_distances
        self.time_taken = time_taken

    def __repr__(self):
        return "TariffMatch(id={}, b_id={}, ids={!r}, dists={!r}, time={})" \
            .format(self.id, self.bounce_id, self.matched_bounces_ids, self.matched_bounces_distances, self.time_taken)


class Reference(Base):
    __tablename__ = 'references'

    id = Column(INTEGER, primary_key=True)
    bounce_id = Column(INTEGER, ForeignKey('bounces.id'))
    # skill_id = Column(INTEGER, ForeignKey('skill.id'))
    name = Column(TEXT)

    bounce = relationship("Bounce")
