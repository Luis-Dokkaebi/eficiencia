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
LOCAL_DB_PATH = get_env('LOCAL_DB_PATH', 'data/db/local_tracking.db')
REMOTE_DB_URL = get_env('REMOTE_DB_URL', 'mysql://usuario:contraseña@servidor_ip/dbname')

# Snapshots
SNAPSHOTS_DIR = get_env('SNAPSHOTS_DIR', 'data/snapshots')

# General parameters
FRAME_SKIP = get_env('FRAME_SKIP', 1, int)  # Capture every frame, adjust for testing
CONFIDENCE_THRESHOLD = get_env('CONFIDENCE_THRESHOLD', 0.4, float)

# Face Recognition
FACE_RECOGNITION_TOLERANCE = get_env('FACE_RECOGNITION_TOLERANCE', 0.5, float)  # Lower is stricter (0.6 default, 0.5 recommended)
FACE_RECOGNITION_MIN_MATCHES = get_env('FACE_RECOGNITION_MIN_MATCHES', 3, int)  # Consecutive recognitions to confirm identity
VERIFICATION_INTERVAL = get_env('VERIFICATION_INTERVAL', 30, int)  # Frame interval to re-verify identity
