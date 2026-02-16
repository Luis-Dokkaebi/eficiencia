import sys
import os
from sqlalchemy import create_engine, func
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

    def get_filtered_events(self, camera_id=None, limit=100, offset=0):
        session = self.Session()
        try:
            query = session.query(TrackingEvent)
            if camera_id:
                query = query.filter(TrackingEvent.camera_id == camera_id)

            # Order by timestamp desc to get latest events
            query = query.order_by(TrackingEvent.timestamp.desc())

            records = query.limit(limit).offset(offset).all()
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

    def get_latest_camera_activity(self):
        session = self.Session()
        try:
            # Query max timestamp per camera
            results = session.query(
                TrackingEvent.camera_id,
                func.max(TrackingEvent.timestamp)
            ).group_by(TrackingEvent.camera_id).all()
            return {r[0]: r[1] for r in results}
        finally:
            session.close()

    def get_zone_stats(self):
        session = self.Session()
        try:
            # Count records where inside_zone=1, grouped by camera and zone
            results = session.query(
                TrackingEvent.camera_id,
                TrackingEvent.zone,
                func.count(TrackingEvent.id).label('count')
            ).filter(TrackingEvent.inside_zone == 1)\
             .group_by(TrackingEvent.camera_id, TrackingEvent.zone).all()

            stats = {}
            for cam_id, zone, count in results:
                if cam_id not in stats:
                    stats[cam_id] = {}
                stats[cam_id][zone] = count
            return stats
        finally:
            session.close()
