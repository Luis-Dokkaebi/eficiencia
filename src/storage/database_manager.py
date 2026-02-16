import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

try:
    from config import config
except ImportError:
    import config

from src.storage.models import Base, TrackingEvent, Snapshot

class DatabaseManager:
    def __init__(self, db_url=None):
        if db_url is None:
            if hasattr(config, 'DATABASE_URL'):
                db_url = config.DATABASE_URL
            else:
                db_url = 'sqlite:///data/db/local_tracking.db'

        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def insert_record(self, camera_id, track_id, x, y, zone, inside_zone):
        session = self.Session()
        try:
            event = TrackingEvent(
                camera_id=str(camera_id),
                track_id=track_id,
                timestamp=datetime.now(),
                x=x,
                y=y,
                zone=zone,
                inside_zone=inside_zone
            )
            session.add(event)
            session.commit()
        except Exception as e:
            print(f"Error inserting record: {e}")
            session.rollback()
        finally:
            session.close()

    def insert_snapshot(self, camera_id, track_id, zone, snapshot_path, employee_name=None):
        session = self.Session()
        try:
            snapshot = Snapshot(
                camera_id=str(camera_id),
                track_id=track_id,
                timestamp=datetime.now(),
                zone=zone,
                snapshot_path=snapshot_path,
                employee_name=employee_name
            )
            session.add(snapshot)
            session.commit()
        except Exception as e:
            print(f"Error inserting snapshot: {e}")
            session.rollback()
        finally:
            session.close()

    def get_all_records(self):
        session = self.Session()
        try:
            records = session.query(TrackingEvent).all()
            return [
                {
                    'id': r.id,
                    'camera_id': r.camera_id,
                    'track_id': r.track_id,
                    'timestamp': r.timestamp,
                    'x': r.x,
                    'y': r.y,
                    'zone': r.zone,
                    'inside_zone': r.inside_zone
                } for r in records
            ]
        finally:
            session.close()
