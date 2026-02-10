# src/main.py

import cv2
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import sys
import numpy as np
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
    face_recognizer = FaceRecognizer(tolerance=getattr(config, 'FACE_RECOGNITION_TOLERANCE', 0.6))

    # Track state: {track_id: {zone_name: was_inside}}
    zone_state = {}
    
    # Track names: {track_id: name}
    track_id_to_name = {}

    # Track votes for recognition verification: {track_id: {'name': name, 'count': count}}
    track_id_votes = {}

    # Registro de Identidades (Nombre -> Embedding Vector Promedio)
    identity_registry = {}

    # Ensure snapshots dir exists
    snapshots_dir = getattr(config, 'SNAPSHOTS_DIR', 'data/snapshots')
    os.makedirs(snapshots_dir, exist_ok=True)

    print("✅ Sistema iniciado. Presiona 'q' para salir.")

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1

        # Detección y tracking
        detections = detector.detect(frame)
        tracked_detections, current_embeddings = tracker.update(detections, frame)

        # Procesamos cada persona detectada
        for xyxy, track_id in zip(tracked_detections.xyxy, tracked_detections.tracker_id):
            track_id = int(track_id)
            x1, y1, x2, y2 = map(int, xyxy)
            cx, cy = get_bbox_center(xyxy)

            # --- LÓGICA DE IDENTIDAD HÍBRIDA (CARA + APARIENCIA) ---

            current_name = track_id_to_name.get(track_id, "Unknown")
            current_embedding = current_embeddings.get(track_id)
            
            # --- 1. RECONOCIMIENTO FACIAL ---
            face_recognized = False
            embedding_updated = False
            recognized_name_face = "Unknown"

            should_verify_face = False
            if current_name == "Unknown":
                should_verify_face = True
            else:
                # Verificamos periódicamente
                verification_interval = getattr(config, 'VERIFICATION_INTERVAL', 30)
                if (frame_count + track_id) % verification_interval == 0:
                    should_verify_face = True

            if should_verify_face:
                recognized_name_face = face_recognizer.recognize_face(frame, bbox=(x1, y1, x2, y2))
                
                if recognized_name_face != "Unknown":
                    # Sistema de votación para cara
                    if track_id not in track_id_votes:
                        track_id_votes[track_id] = {'name': recognized_name_face, 'count': 1}
                    else:
                        if track_id_votes[track_id]['name'] == recognized_name_face:
                            track_id_votes[track_id]['count'] += 1
                        else:
                            track_id_votes[track_id] = {'name': recognized_name_face, 'count': 1}

                    min_matches = getattr(config, 'FACE_RECOGNITION_MIN_MATCHES', 3)
                    if track_id_votes[track_id]['count'] >= min_matches:
                        face_recognized = True
                        final_name = recognized_name_face

                        if current_name != "Unknown" and current_name != final_name:
                            print(f"🔄 Cambio de identidad (CARA)! ID: {track_id} era {current_name}, ahora es {final_name}")
                        elif current_name == "Unknown":
                            print(f"✅ ¡Identificado (CARA)! ID: {track_id} es {final_name}")

                        track_id_to_name[track_id] = final_name
                        current_name = final_name

                        # Actualizar Embedding de Identidad (si tenemos embedding visual)
                        if current_embedding is not None:
                            embedding_updated = True
                            if final_name not in identity_registry:
                                identity_registry[final_name] = current_embedding
                            else:
                                # Media Móvil Exponencial
                                alpha = getattr(config, 'REID_HISTORY_ALPHA', 0.9)
                                identity_registry[final_name] = alpha * identity_registry[final_name] + (1 - alpha) * current_embedding
                                # Renormalizar
                                identity_registry[final_name] /= (np.linalg.norm(identity_registry[final_name]) + 1e-6)

            # --- 2. RE-IDENTIFICACIÓN POR APARIENCIA (Si cara falló y nombre desconocido) ---
            if not face_recognized and current_name == "Unknown" and current_embedding is not None:
                best_match_name = None
                max_similarity = -1.0

                for name, saved_embedding in identity_registry.items():
                    similarity = np.dot(current_embedding, saved_embedding)
                    if similarity > max_similarity:
                        max_similarity = similarity
                        best_match_name = name

                threshold = getattr(config, 'REID_SIMILARITY_THRESHOLD', 0.6)
                if best_match_name and max_similarity > threshold:
                    print(f"🔍 Re-Identificado (APARIENCIA)! ID: {track_id} parece ser {best_match_name} (Sim: {max_similarity:.2f})")
                    track_id_to_name[track_id] = best_match_name
                    current_name = best_match_name

                    # Actualización suave del registro de identidad
                    embedding_updated = True
                    alpha_reid = 0.95
                    identity_registry[best_match_name] = alpha_reid * identity_registry[best_match_name] + (1 - alpha_reid) * current_embedding
                    identity_registry[best_match_name] /= (np.linalg.norm(identity_registry[best_match_name]) + 1e-6)

            # --- 3. MANTENIMIENTO DEL MODELO VISUAL ---
            # Si ya conocemos el nombre, seguimos actualizando suavemente el embedding
            if not embedding_updated and current_name != "Unknown" and current_embedding is not None:
                 if current_name in identity_registry:
                    alpha_update = 0.98
                    identity_registry[current_name] = alpha_update * identity_registry[current_name] + (1 - alpha_update) * current_embedding
                    identity_registry[current_name] /= (np.linalg.norm(identity_registry[current_name]) + 1e-6)

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