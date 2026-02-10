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

# Reconocimiento Facial
FACE_RECOGNITION_TOLERANCE = 0.5  # Menor es más estricto (0.6 es defecto, 0.5 recomendado para evitar falsos positivos)
FACE_RECOGNITION_MIN_MATCHES = 3  # Número de veces consecutivas que debe reconocerse para confirmar identidad
VERIFICATION_INTERVAL = 30  # Intervalo de frames para re-verificar identidad de personas ya identificadas

# Re-Identificación (ReID)
REID_SIMILARITY_THRESHOLD = 0.6  # Umbral de similitud coseno (0-1). Más alto = más estricto.
REID_HISTORY_ALPHA = 0.9  # Factor de actualización para el embedding histórico (Media Móvil Exponencial)
