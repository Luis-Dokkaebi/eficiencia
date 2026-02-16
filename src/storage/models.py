from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class TrackingEvent(Base):
    __tablename__ = 'tracking_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    camera_id = Column(String, nullable=False)  # Stores 'Camera_1', 'Camera_2', etc. or ID
    track_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    x = Column(Float)
    y = Column(Float)
    zone = Column(String)
    inside_zone = Column(Integer)  # 0 or 1

    def __repr__(self):
        return f"<TrackingEvent(camera_id='{self.camera_id}', track_id={self.track_id}, zone='{self.zone}')>"

class Snapshot(Base):
    __tablename__ = 'snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True)
    camera_id = Column(String, nullable=False)
    track_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    zone = Column(String)
    snapshot_path = Column(String)
    employee_name = Column(String, nullable=True)

    def __repr__(self):
        return f"<Snapshot(camera_id='{self.camera_id}', track_id={self.track_id}, employee_name='{self.employee_name}')>"
