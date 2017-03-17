import glob
import os

from sqlalchemy import Column, ForeignKey, INTEGER, REAL, TEXT
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from helpers import consts
from helpers import helper_funcs

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
    level = Column(TEXT)
    video_height = Column(INTEGER)
    video_width = Column(INTEGER)
    video_fps = Column(REAL)
    frame_count = Column(INTEGER)
    trampoline_top = Column(INTEGER)
    trampoline_center = Column(INTEGER)
    trampoline_width = Column(INTEGER)

    frames = relationship("Frame", back_populates='routine')
    bounces = relationship("Bounce", back_populates='routine')
    judgements = relationship("Judgement", back_populates='routine')

    def __init__(self, path=None):
        self.path = path

    def __repr__(self):
        return "Routine(path=%r, bounces=%r)" % (self.path, self.bounces)

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
        from numpy import array
        trampolineTouches = array([frame.trampoline_touch for frame in self.frames])
        trampolineTouches = helper_funcs.trimTouches(trampolineTouches)
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
        import numpy as np
        scores = [j.getScore() for j in self.judgements]
        return '{0:.1f}'.format(np.average(scores))

    # Db related attributes
    def isTracked(self):
        return len(self.frames) > 0

    def isPoseImported(self, db):
        # SELECT count(1) FROM frame_data WHERE routine_id=1 AND pose!=''
        count = db.query(Frame).filter(Frame.pose != '', Frame.routine_id == self.id).count()
        return count > 0

    def isLabelled(self):
        if not self.bounces:
            return False
        # Otherwise, check that they're all labelled
        for b in self.bounces:
            if b.skill_name == '':
                return False
        return True

    def isBroken(self):
        if not self.bounces:
            return False
        # Otherwise, check that they're all labelled
        for b in self.bounces:
            if b.skill_name == 'Broken':
                return True
        return False

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
    frame_num = Column(INTEGER)
    center_pt_x = Column(INTEGER)
    center_pt_y = Column(INTEGER)
    hull_max_length = Column(INTEGER)
    trampoline_touch = Column(INTEGER)
    pose = Column(TEXT)

    routine = relationship("Routine", back_populates='frames')

    def __init__(self, routine_id, frame_num, center_pt_x, center_pt_y, hull_max_length, trampoline_touch):
        self.routine_id = routine_id
        self.frame_num = frame_num
        self.center_pt_x = center_pt_x
        self.center_pt_y = center_pt_y
        self.hull_max_length = hull_max_length
        self.trampoline_touch = trampoline_touch
        self.pose = ""


class Bounce(Base):
    __tablename__ = 'bounces'

    id = Column(INTEGER, primary_key=True)
    routine_id = Column(INTEGER, ForeignKey('routines.id'))
    bounce_index = Column(INTEGER)
    skill_name = Column(TEXT)

    start_frame = Column(INTEGER)
    max_height_frame = Column(INTEGER)
    end_frame = Column(INTEGER)

    start_time = Column(REAL)
    max_height_time = Column(REAL)
    end_time = Column(REAL)

    start_height = Column(INTEGER)
    max_height = Column(INTEGER)
    end_height = Column(INTEGER)

    routine = relationship("Routine", back_populates='bounces')
    deductions = relationship("Deduction", back_populates='bounce')

    def __init__(self, routine_id, bounce_index, skill_name, start_frame, max_height_frame, end_frame, start_time,
                 max_height_time, end_time, start_height, max_height, end_height):
        self.routine_id = routine_id
        self.bounce_index = bounce_index
        self.skill_name = skill_name

        self.start_frame = start_frame
        self.max_height_frame = max_height_frame
        self.end_frame = end_frame

        self.start_time = start_time
        self.max_height_time = max_height_time
        self.end_time = end_time

        self.start_height = start_height
        self.max_height = max_height
        self.end_height = end_height

    def __repr__(self):
        return "Bounce(skill_name=%r)" % (self.skill_name)
        # return "Bounce(name=%r, routine=%r)" % (self.name, self.routine)

    def isJudgeable(self):
        return self.skill_name != "In/Out Bounce"  # and self.skill_name != "Broken"

    def getFrames(self, db):
        return db.query(Frame).filter(Frame.routine_id == self.routine_id, Frame.frame_num >= self.start_frame, Frame.frame_num <= self.end_frame).all()


class Judgement(Base):
    __tablename__ = 'judgements'

    id = Column(INTEGER, primary_key=True)
    routine_id = Column(INTEGER, ForeignKey('routines.id'))
    contributor_id = Column(INTEGER, ForeignKey('contributors.id'))
    # score = Column(REAL)

    routine = relationship("Routine", back_populates='judgements')
    contributor = relationship("Contributor", back_populates='judgements')
    deductions = relationship("Deduction", back_populates='judgement')

    def __init__(self, routine_id, contributor_id):
        self.routine_id = routine_id
        self.contributor_id = contributor_id

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
    deduction_json = Column(TEXT)

    bounce = relationship("Bounce", back_populates='deductions')
    judgement = relationship("Judgement", back_populates='deductions')
    contributor = relationship("Contributor", back_populates='deductions')

    def __init__(self, judgement_id, contributor_id, bounce_id, deduction_value, deduction_json):
        self.judgement_id = judgement_id
        self.contributor_id = contributor_id
        self.bounce_id = bounce_id
        self.deduction_value = deduction_value
        self.deduction_json = deduction_json

    def __repr__(self):
        return "Deduction(deduction=%r, who=%r)" % (self.deduction, self.contributor)


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
