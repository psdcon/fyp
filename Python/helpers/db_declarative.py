import os

from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, scoped_session, sessionmaker

from helpers import consts

Base = declarative_base()

engine = create_engine('sqlite:////Users/psdco/Documents/ProjectCode/Python/db.sqlite3')
Base.metadata.bind = engine
DBSession = scoped_session(sessionmaker(bind=engine))
db = DBSession()

class Routine(Base):
    __tablename__ = 'routines'

    id = Column(INTEGER, primary_key=True)
    path = Column(TEXT, nullable=False, unique=True)
    use = Column(INTEGER)
    crop_length = Column(INTEGER)  # padding (in pixels) from the center point
    note = Column(TEXT)
    # performer_id = Column(INTEGER)
    competition = Column(TEXT)
    level = Column(TEXT)
    video_height = Column(INTEGER)
    video_width = Column(INTEGER)
    video_fps = Column(REAL)
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

    def framesAsDict(self):
        # Dictionary Comprehension
        return {frame.frame_num: frame for frame in self.frames}

    def framesCount(self, db):
        return db.execute(
            select([func.count('*')])
                .select_from(Frame)
                .where(Frame.routine_id == self.id)
        ).fetchone()[0]

    # def createJudgements(self, db):
    #     bounceDeductions = []
    #     for bounce in self.bounces:
    #         if bounce.deductions != []:
    #             bounceDeductions.append(bounce.deductions)
    #
    #     # Transpose all deduction objects using zip. http://stackoverflow.com/questions/6473679/transpose-list-of-lists
    #     routineDeductions = zip(*bounceDeductions) # This assumes same number of deductions for all judgements.
    #
    #     for judgement in routineDeductions:
    #         deduction = judgement[0]
    #         j = Judgement(deduction.bounce.routine_id, deduction.contributor.id)
    #         db.add(j)
    #         db.flush()
    #         for d in judgement:
    #             d.judgement_id = j.id
    #     db.commit()
    #     return

    def getScore(self, contributor):
        for j in self.judgements:
            if j.contributor_id == contributor.id:
                return j.getScore()
        return 'N/A'

    def getAvgScore(self):
        if not self.judgements:
            return 'N/A'
        import numpy as np
        scores = [j.getScore() for j in self.judgements]
        return float("{0:.1f}".format(np.average(scores)))

    def isTracked(self, db):
        return self.framesCount(db) > 0

    def isPosed(self, db):
        # SELECT count(1) FROM frame_data WHERE routine_id=1 AND pose!=''
        # s = select([func.count('*')])\
        #     .select_from(Frame)\
        #     .where(
        #         and_(Frame.pose != '', Frame.routine_id == self.id)
        #     )
        # count = db.execute(s).fetchone()[0]
        # return count > 0
        return os.path.exists(self.getAsDirPath()+'preds_2d.mat')


    def isLabelled(self):
        if not self.bounces:
            return False
        # Otherwise, check that they're all labelled
        labelledCount = 0
        for b in self.bounces:
            if b.skill_name:
                labelledCount += 1
        return labelledCount == len(self.bounces)

    def isJudged(self, contributor=None):
        if contributor:
            for j in self.judgements:
                if j.contributor_id == contributor.id:
                    return True
            return False
        else:
            if self.judgements:
                return True
            return False

    def getAsDirPath(self, suffix=None):
        if suffix:
            path = consts.videosRootPath + self.path.replace('.mp4', os.sep+suffix)
        else:
            path = consts.videosRootPath + self.path.replace('.mp4', os.sep)
        if not os.path.exists(path):
            print("Creating " + path)
            os.makedirs(path)
        return path

    def hasFramesSaved(self, suffix=None):
        import glob
        nFiles = len(glob.glob(self.getAsDirPath(suffix) + 'frame_*'))
        return nFiles > 0

    def prettyName(self):
        return os.path.basename(self.path[:-4])


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
        return self.skill_name != "In/Out Bounce" #and self.skill_name != "Broken"

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
        deductionValues = [d.deduction for d in self.deductions]
        # Only take the first 10
        score = 10 - sum(deductionValues[:10])
        return score


class Deduction(Base):
    __tablename__ = 'bounce_deductions'

    id = Column(INTEGER, primary_key=True)
    judgement_id = Column(INTEGER, ForeignKey('judgements.id'))
    bounce_id = Column(INTEGER, ForeignKey('bounces.id'))
    contributor_id = Column(INTEGER, ForeignKey('contributors.id'))
    deduction = Column(REAL)

    bounce = relationship("Bounce", back_populates='deductions')
    judgement = relationship("Judgement", back_populates='deductions')
    contributor = relationship("Contributor", back_populates='deductions')

    def __repr__(self):
        return "Deduction(deduction=%r, who=%r)" % (self.deduction, self.contributor)


class Contributor(Base):
    __tablename__ = 'contributors'

    id = Column(INTEGER, primary_key=True)
    uid = Column(TEXT, unique=True)
    name = Column(TEXT)

    deductions = relationship("Deduction", back_populates='contributor')
    judgements = relationship("Judgement", back_populates='contributor')

    def __repr__(self):
        return "Contributor(id=%r, name=%s)" % (self.id, self.name)
