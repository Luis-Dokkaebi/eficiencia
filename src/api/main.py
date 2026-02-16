import sys
import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Query, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from pydantic import BaseModel
import json

# Add project root to path to ensure imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from config import config
except ImportError:
    # Fallback or error handling
    print("Warning: Could not import config")
    config = None

from src.storage.database_manager import DatabaseManager
from src.auth.security import verify_password, create_access_token, verify_token

app = FastAPI(title="Tracking System API", version="1.0.0")

# Initialize DatabaseManager
# In a real production app, we might use dependency injection with a generator
db_manager = DatabaseManager()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str
    role: str
    permissions: Optional[str] = "[]"

class UserCreate(BaseModel):
    username: str
    password: str
    role: Optional[str] = "user"
    permissions: Optional[str] = "[]"

async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db_manager.get_user_by_username(username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    return current_user

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = db_manager.get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user['hashed_password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user['username']}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users", response_model=User)
async def create_user(user: UserCreate, current_user: dict = Depends(get_current_active_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized")

    db_user = db_manager.get_user_by_username(user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    new_user = db_manager.create_user(
        username=user.username,
        password=user.password,
        role=user.role,
        permissions=user.permissions
    )
    return new_user

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: dict = Depends(get_current_active_user)):
    return current_user

def get_user_allowed_cameras(user: dict) -> List[str]:
    permissions = user.get('permissions', "[]")
    if permissions is None:
        permissions = "[]"

    # Handle "all" as a raw string special case
    if permissions == "all":
        return "all"

    try:
        allowed_cameras = json.loads(permissions)
    except json.JSONDecodeError:
        return []

    if allowed_cameras == "all":
        return "all"
    if isinstance(allowed_cameras, list):
        if "all" in allowed_cameras:
            return "all"
        return allowed_cameras
    return []

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
def get_cameras(current_user: dict = Depends(get_current_active_user)):
    """
    List of active cameras and their status (Online/Offline).
    """
    allowed_cameras = get_user_allowed_cameras(current_user)

    cameras = []
    last_activity = db_manager.get_latest_camera_activity()

    if not config or not hasattr(config, 'CAMERAS') or not config.CAMERAS:
        return []

    for i, source in enumerate(config.CAMERAS):
        cam_id = f"Camera_{i+1}"

        # Check permission
        if allowed_cameras != "all" and cam_id not in allowed_cameras:
            continue

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
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get tracking events with optional filtering.
    """
    allowed_cameras = get_user_allowed_cameras(current_user)

    # If a specific camera is requested, check if it's allowed
    if camera_id:
        if allowed_cameras != "all" and camera_id not in allowed_cameras:
             raise HTTPException(status_code=403, detail="Not authorized to access this camera")

    events = db_manager.get_filtered_events(camera_id=camera_id, limit=limit, offset=offset, allowed_cameras=allowed_cameras)
    return events

@app.get("/stats/efficiency")
def get_efficiency_stats(current_user: dict = Depends(get_current_active_user)):
    """
    Report aggregated by zone or camera.
    Returns the count of frames/events where people were inside zones.
    """
    allowed_cameras = get_user_allowed_cameras(current_user)
    stats = db_manager.get_zone_stats()

    if allowed_cameras == "all":
        return stats

    # Filter stats
    filtered_stats = {k: v for k, v in stats.items() if k in allowed_cameras}
    return filtered_stats

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
