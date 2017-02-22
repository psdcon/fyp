import os

from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from helpers import consts

Base = declarative_base()


class Routine(Base):
    __tablename__ = 'routines'

    id = Column(INTEGER, primary_key=True)
    path = Column(TEXT, nullable=False, unique=True)
    note = Column(TEXT)
    use = Column(INTEGER)
    # performer_id = Column(INTEGER)
    competition = Column(TEXT)
    level = Column(TEXT)
    video_height = Column(INTEGER)
    video_width = Column(INTEGER)
    video_fps = Column(REAL)
    trampoline_top = Column(INTEGER)
    trampoline_center = Column(INTEGER)
    trampoline_width = Column(INTEGER)
    crop_length = Column(INTEGER)  # padding (in pixels) from the center point

    frames = relationship("Frame", back_populates='routine')
    bounces = relationship("Bounce", back_populates='routine')

    def __init__(self, path=None):
        self.path = path

    def __repr__(self):
        return "Routine(path=%r, bounces=%r)" % (self.path, self.bounces)

    def framesAsDict(self):
        # Dictionary Comprehension
        return {frame.frame_num: frame for frame in self.frames}

    def framesCount(self, db):
        return db.execute(
            select([func.count('*')])
                .select_from(Frame)
                .where(Frame.routine_id == self.id)
        ).fetchone()[0]

    def getScores(self):
        bounceDeductions = []
        for bounce in self.bounces:
            if bounce.deductions != []:
                bounceDeductions.append(bounce.deductions)
        # Transpose all deduction objects using * operator with zip. http://stackoverflow.com/questions/6473679/transpose-list-of-lists
        routineDeductions = zip(*bounceDeductions)  # returns a tuple. * operator causes transpose
        # This assumes same number of deductions for all judgements.
        # TODO because of incorrect number of bounces on some routines, all previous judgements of a routine should be updated or for new judgements including that deduction will never be counted
        scores = []
        for deductions in routineDeductions:
            deductionValues = [deduction.deduction for deduction in deductions]
            # Only take the first 10
            scores.append(10 - sum(deductionValues[:10]))
        return scores

    def getScore(self):
        import numpy as np
        return float("{0:.1f}".format(np.average(self.getScores())))

    def isTracked(self, db):
        return self.framesCount(db) > 0

    def isPosed(self, db):
        # SELECT count(1) FROM frame_data WHERE routine_id=1 AND pose!=NULL
        s = select([func.count('*')])\
            .select_from(Frame)\
            .where(
                and_(Frame.pose != '', Frame.routine_id == self.id)
            )
        poseCount = db.execute(s).fetchone()[0]
        return poseCount > 0

    def getAsDirPath(self):
        return consts.videosRootPath + self.path.replace('.mp4', os.sep)

    def hasFramesSaved(self):
        import glob
        nFiles = len(glob.glob(self.getAsDirPath() + 'frame_*'))
        return nFiles > 0


class Frame(Base):
    __tablename__ = 'frame_data'

    id = Column(INTEGER, primary_key=True)
    routine_id = Column(INTEGER, ForeignKey('routines.id'))
    frame_num = Column(INTEGER)
    center_pt_x = Column(INTEGER)
    center_pt_y = Column(INTEGER)
    hull_max_length = Column(INTEGER)
    trampoline_area = Column(INTEGER)
    trampoline_touch = Column(INTEGER)
    person_mask = Column(TEXT)
    pose = Column(TEXT)

    routine = relationship("Routine", back_populates='frames')

    def __init__(self, routine_id, frame_num, center_pt_x, center_pt_y, hull_length, trampoline_area, trampoline_touch, person_mask):
        self.routine_id = routine_id
        self.frame_num = frame_num
        self.center_pt_x = center_pt_x
        self.center_pt_y = center_pt_y
        self.hull_max_length = hull_length
        self.trampoline_area = trampoline_area
        self.trampoline_touch = trampoline_touch
        self.person_mask = person_mask
        self.pose = ""

    def get_scale_factor(self):
        return 256.0 / float(self.hull_max_length)


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
        return self.skill_name != "In/Out Bounce" and self.skill_name != "Broken"

    def getFrames(self, db):
        return db.query(Frame).filter(Frame.routine_id == self.routine_id, Frame.frame_num >= self.start_frame, Frame.frame_num <= self.end_frame).all()


class Deduction(Base):
    __tablename__ = 'bounce_deductions'

    id = Column(INTEGER, primary_key=True)
    bounce_id = Column(INTEGER, ForeignKey('bounces.id'))
    deduction = Column(REAL)
    contributor_id = Column(INTEGER, ForeignKey('contributors.id'))

    bounce = relationship("Bounce", back_populates='deductions')
    contributor = relationship("Contributor", back_populates='deductions')

    def __repr__(self):
        return "Deduction(deduction=%r, who=%r)" % (self.deduction, self.contributor)


class Contributor(Base):
    __tablename__ = 'contributors'

    id = Column(INTEGER, primary_key=True)
    m5d_id = Column(TEXT, unique=True)
    name = Column(TEXT)

    deductions = relationship("Deduction", back_populates='contributor')

    def __repr__(self):
        return "Contributor(id=%r, name=%s)" % (self.id, self.name)

# Create an engine that stores data in the local directory's
# sqlalchemy_example.db file.
# engine = create_engine('sqlite:///sqlalchemy_example.db')

# Create all tables in the engine. This is equivalent to "Create Table"
# statements in raw SQL.
# Base.metadata.create_all(engine)
