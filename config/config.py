# --- config/config.py ---

MODE = 'local'  # Cambiar a 'remote' cuando sea necesario

# Video
LOCAL_CAMERA_INDEX = 1
REMOTE_CAMERA_URL = "rtsp://usuario:contraseña@IP:PUERTO/cam/path"

# Base de datos
LOCAL_DB_PATH = 'data/db/local_tracking.db'
REMOTE_DB_URL = 'mysql://usuario:contraseña@servidor_ip/dbname'

# Snapshots
SNAPSHOTS_DIR = 'data/snapshots'

# Otros parámetros generales
FRAME_SKIP = 1  # Capturar cada frame, ajustar para pruebas
CONFIDENCE_THRESHOLD = 0.4
