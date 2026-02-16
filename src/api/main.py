import sys
import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Query, HTTPException
from datetime import datetime, timedelta
from pydantic import BaseModel

# Add project root to path to ensure imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from config import config
except ImportError:
    # Fallback or error handling
    print("Warning: Could not import config")
    config = None

from src.storage.database_manager import DatabaseManager

app = FastAPI(title="Tracking System API", version="1.0.0")

# Initialize DatabaseManager
# In a real production app, we might use dependency injection with a generator
db_manager = DatabaseManager()

class CameraStatus(BaseModel):
    id: str
    source: str
    status: str
    last_seen: Optional[datetime] = None

class TrackingEventResponse(BaseModel):
    id: int
    camera_id: str
    track_id: int
    timestamp: datetime
    x: float
    y: float
    zone: str
    inside_zone: int

@app.get("/cameras", response_model=List[CameraStatus])
def get_cameras():
    """
    List of active cameras and their status (Online/Offline).
    """
    cameras = []
    last_activity = db_manager.get_latest_camera_activity()

    if not config or not hasattr(config, 'CAMERAS') or not config.CAMERAS:
        return []

    for i, source in enumerate(config.CAMERAS):
        cam_id = f"Camera_{i+1}"

        # Determine status
        last_seen = last_activity.get(cam_id)
        status = "Offline"

        if last_seen:
            # Check if active in the last 30 seconds
            if (datetime.now() - last_seen).total_seconds() < 30:
                status = "Online"

        cameras.append(CameraStatus(
            id=cam_id,
            source=str(source), # source might be int or str
            status=status,
            last_seen=last_seen
        ))

    return cameras

@app.get("/events", response_model=List[TrackingEventResponse])
def get_events(
    camera_id: Optional[str] = Query(None, description="Filter by Camera ID"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    Get tracking events with optional filtering.
    """
    events = db_manager.get_filtered_events(camera_id=camera_id, limit=limit, offset=offset)
    return events

@app.get("/stats/efficiency")
def get_efficiency_stats():
    """
    Report aggregated by zone or camera.
    Returns the count of frames/events where people were inside zones.
    """
    stats = db_manager.get_zone_stats()
    return stats

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
