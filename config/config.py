import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_env(key, default, cast=None):
    value = os.getenv(key)
    if value is None:
        return default
    if cast:
        try:
            return cast(value)
        except (ValueError, TypeError):
            return default
    return value

MODE = get_env('MODE', 'local')  # Change to 'remote' when necessary

# Video
# Special handling for LOCAL_CAMERA_INDEX: it can be int (index) or str (path)
_local_cam = os.getenv('LOCAL_CAMERA_INDEX')
if _local_cam is not None:
    if _local_cam.isdigit():
        LOCAL_CAMERA_INDEX = int(_local_cam)
    else:
        LOCAL_CAMERA_INDEX = _local_cam
else:
    LOCAL_CAMERA_INDEX = 1

REMOTE_CAMERA_URL = get_env('REMOTE_CAMERA_URL', "rtsp://usuario:contraseña@IP:PUERTO/cam/path")

# Multi-camera support
CAMERAS_JSON = get_env('CAMERAS_JSON', None)
CAMERAS = []
if CAMERAS_JSON:
    try:
        # We need to handle single quotes if they were used in the env var string by mistake,
        # though valid JSON uses double quotes.
        # However, standard dotenv usually handles strings well.
        CAMERAS = json.loads(CAMERAS_JSON)
    except json.JSONDecodeError:
        print("⚠️ Error parsing CAMERAS_JSON, falling back to legacy config")

if not CAMERAS:
    # Legacy fallback
    if MODE == 'local':
        CAMERAS = [LOCAL_CAMERA_INDEX]
    else:
        CAMERAS = [REMOTE_CAMERA_URL]

# Database
POSTGRES_USER = get_env('POSTGRES_USER', 'admin')
POSTGRES_PASSWORD = get_env('POSTGRES_PASSWORD', 'admin')
POSTGRES_HOST = get_env('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = get_env('POSTGRES_PORT', '5432')
POSTGRES_DB = get_env('POSTGRES_DB', 'tracking_db')

# Construct DATABASE_URL if not provided explicitly
_default_db_url = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
DATABASE_URL = get_env('DATABASE_URL', _default_db_url)

# Snapshots
SNAPSHOTS_DIR = get_env('SNAPSHOTS_DIR', 'data/snapshots')

# General parameters
FRAME_SKIP = get_env('FRAME_SKIP', 1, int)  # Capture every frame, adjust for testing
CONFIDENCE_THRESHOLD = get_env('CONFIDENCE_THRESHOLD', 0.4, float)
HEADLESS = get_env('HEADLESS', 'False').lower() == 'true'

# Face Recognition
FACE_RECOGNITION_TOLERANCE = get_env('FACE_RECOGNITION_TOLERANCE', 0.5, float)  # Lower is stricter (0.6 default, 0.5 recommended)
FACE_RECOGNITION_MIN_MATCHES = get_env('FACE_RECOGNITION_MIN_MATCHES', 3, int)  # Consecutive recognitions to confirm identity
VERIFICATION_INTERVAL = get_env('VERIFICATION_INTERVAL', 30, int)  # Frame interval to re-verify identity

# Security
SECRET_KEY = get_env('SECRET_KEY', '09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7')
ALGORITHM = get_env('ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = get_env('ACCESS_TOKEN_EXPIRE_MINUTES', 30, int)
