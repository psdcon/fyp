from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Routine(Base):
    __tablename__ = 'routines'

    id = Column(INTEGER, primary_key=True)
    path = Column(TEXT, nullable=False, unique=True)
    note = Column(TEXT)
    performer_id = Column(INTEGER)
    competition = Column(TEXT)
    level = Column(TEXT)
    video_height = Column(INTEGER)
    video_width = Column(INTEGER)
    video_fps = Column(REAL)
    trampoline_top = Column(INTEGER)
    trampoline_center = Column(INTEGER)
    trampoline_width = Column(INTEGER)
    # padding = Column(INTEGER)  # padding (in pixels) from the center point

    frames = relationship("Frame", back_populates='routine')
    bounces = relationship("Bounce", back_populates='routine')

    def __init__(self, path=None):
        self.path = path

        # def __repr__(self):
        # return "Routine(path=%r, bounces=%r)" % (self.path, self.bounces)

    def isTracked(self):
        return self.trampoline_top is not None


class Frame(Base):
    __tablename__ = 'frame_data'

    id = Column(INTEGER, primary_key=True)
    routine_id = Column(Integer, ForeignKey('routines.id'))
    frame_num = Column(INTEGER)
    center_pt_x = Column(INTEGER)
    center_pt_y = Column(INTEGER)
    ellipse_len_major = Column(REAL)
    ellipse_len_minor = Column(REAL)
    ellipse_angle = Column(INTEGER)
    pose = Column(TEXT)
    # pose_hg = Column(TEXT)

    routine = relationship("Routine", back_populates='frames')

    def __init__(self, routine_id, frame_num, center_pt_x, center_pt_y, ellipse_len_major, ellipse_len_minor,
                 ellipse_angle):
        self.routine_id = routine_id
        self.frame_num = frame_num
        self.center_pt_x = center_pt_x
        self.center_pt_y = center_pt_y
        self.ellipse_len_major = ellipse_len_major
        self.ellipse_len_minor = ellipse_len_minor
        self.ellipse_angle = ellipse_angle


class Bounce(Base):
    __tablename__ = 'bounces'

    id = Column(Integer, primary_key=True)
    routine_id = Column(Integer, ForeignKey('routines.id'))
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


class Deduction(Base):
    __tablename__ = 'bounce_deductions'

    id = Column(INTEGER, primary_key=True)
    bounce_id = Column(INTEGER, ForeignKey('bounces.id'))
    deduction = Column(REAL)
    contributor_id = Column(INTEGER, ForeignKey('contributors.id'))

    bounce = relationship("Bounce", back_populates='deductions')
    contributor = relationship("Contributor", back_populates='deductions')

    def __repr__(self):
        return "Deduction(deduction=%r)" % (self.deduction)


class Contributor(Base):
    __tablename__ = 'contributors'

    id = Column(INTEGER, primary_key=True)
    m5d_id = Column(TEXT, unique=True)
    name = Column(TEXT)

    deductions = relationship("Deduction", back_populates='contributor')


# Create an engine that stores data in the local directory's
# sqlalchemy_example.db file.
# engine = create_engine('sqlite:///sqlalchemy_example.db')

# Create all tables in the engine. This is equivalent to "Create Table"
# statements in raw SQL.
# Base.metadata.create_all(engine)
