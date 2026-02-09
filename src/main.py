# src/main.py

import cv2
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import sys
from datetime import datetime

# Add the project root directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from config import config
except ImportError:
    # Fallback if config module is not found directly
    sys.path.append(os.getcwd())
    from config import config

from detection.person_detector import PersonDetector
from tracking.person_tracker import PersonTracker
from zones.zone_checker import ZoneChecker
from storage.database_manager import DatabaseManager
from recognition.face_recognizer import FaceRecognizer

def get_bbox_center(xyxy):
    x1, y1, x2, y2 = xyxy
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    return center_x, center_y

def start_video_stream():
    # Selección de fuente de video
    if config.MODE == 'local':
        video_source = config.LOCAL_CAMERA_INDEX
    else:
        video_source = config.REMOTE_CAMERA_URL

    cap = cv2.VideoCapture(video_source)

    # Inicializamos los módulos
    detector = PersonDetector(confidence_threshold=config.CONFIDENCE_THRESHOLD)
    tracker = PersonTracker()
    zone_checker = ZoneChecker(zones_path="data/zonas/zonas.json")
    db_manager = DatabaseManager(db_path=config.LOCAL_DB_PATH)
    
    # Initialize face recognizer
    face_recognizer = FaceRecognizer()

    # Track state: {track_id: {zone_name: was_inside}}
    zone_state = {}
    
    # Track names: {track_id: name}
    track_id_to_name = {}

    # Ensure snapshots dir exists
    snapshots_dir = getattr(config, 'SNAPSHOTS_DIR', 'data/snapshots')
    os.makedirs(snapshots_dir, exist_ok=True)

    print("✅ Sistema iniciado. Presiona 'q' para salir.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Detección y tracking
        detections = detector.detect(frame)
        tracked_detections = tracker.update(detections)

        # Procesamos cada persona detectada
        for xyxy, track_id in zip(tracked_detections.xyxy, tracked_detections.tracker_id):
            track_id = int(track_id)
            x1, y1, x2, y2 = map(int, xyxy)
            cx, cy = get_bbox_center(xyxy)

            # --- LÓGICA DE RECONOCIMIENTO CONSTANTE ---
            # Si el ID es nuevo o aún es "Unknown", intentamos reconocerlo
            current_name = track_id_to_name.get(track_id, "Unknown")
            
            if current_name == "Unknown":
                # Intentamos reconocer la cara en este frame
                recognized_name = face_recognizer.recognize_face(frame, bbox=(x1, y1, x2, y2))
                
                # Si logramos reconocerlo, actualizamos su nombre para siempre
                if recognized_name != "Unknown":
                    track_id_to_name[track_id] = recognized_name
                    print(f"✅ ¡Identificado! ID: {track_id} es {recognized_name}")
            
            # Recuperamos el nombre actualizado para mostrarlo
            display_name = track_id_to_name.get(track_id, "Unknown")
            # ------------------------------------------

            results = zone_checker.check(cx, cy)

            if track_id not in zone_state:
                zone_state[track_id] = {}

            for zone_name, inside in results.items():
                inside_zone = int(inside)
                
                # Check for entry event (Entrada a zona)
                was_inside = zone_state[track_id].get(zone_name, False)
                
                if inside_zone and not was_inside:
                    # ACABA DE ENTRAR A LA ZONA
                    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    filename = f"{track_id}_{display_name}_{zone_name}_{timestamp_str}.jpg"
                    filepath = os.path.join(snapshots_dir, filename)

                    try:
                        # Guardamos la evidencia
                        cv2.imwrite(filepath, frame)
                        db_manager.insert_snapshot(track_id, zone_name, filepath, employee_name=display_name)
                        print(f"📸 Foto guardada: {display_name} entró a {zone_name}")
                    except Exception as e:
                        print(f"Error saving snapshot: {e}")

                # Update state
                zone_state[track_id][zone_name] = bool(inside_zone)

                # Registramos posición en la base de datos
                db_manager.insert_record(
                    track_id=track_id,
                    x=cx,
                    y=cy,
                    zone=zone_name,
                    inside_zone=inside_zone
                )

                # Dibujamos bounding box y etiquetas
                color = (0, 255, 0) if inside_zone else (0, 0, 255) # Verde si está dentro, Rojo si está fuera
                
                # Etiqueta: ID - Nombre - Zona - Estado
                label = f"ID:{track_id} {display_name} [{zone_name}]"
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        cv2.imshow("Sistema completo en acción", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    start_video_stream()