import cv2
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import sys
import time
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
from acquisition.video_stream import VideoStreamService

def get_bbox_center(xyxy):
    x1, y1, x2, y2 = xyxy
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    return center_x, center_y

def main():
    print("🚀 System Starting...")
    
    if not config.CAMERAS:
        print("❌ No cameras configured in config.CAMERAS.")
        return

    # Initialize shared resources
    print("🔧 Initializing shared resources (Detector, DB, FaceRec)...")
    try:
        detector = PersonDetector(confidence_threshold=config.CONFIDENCE_THRESHOLD)
        db_manager = DatabaseManager()
        face_recognizer = FaceRecognizer(tolerance=getattr(config, 'FACE_RECOGNITION_TOLERANCE', 0.6))
    except Exception as e:
        print(f"❌ Error initializing shared resources: {e}")
        return

    # Ensure snapshots dir exists
    snapshots_dir = getattr(config, 'SNAPSHOTS_DIR', 'data/snapshots')
    os.makedirs(snapshots_dir, exist_ok=True)

    # Initialize camera systems
    camera_systems = []

    print(f"📷 Configuring {len(config.CAMERAS)} cameras...")
    for i, source in enumerate(config.CAMERAS):
        cam_name = f"Camera_{i+1}" # Underscore for filename safety
        print(f"  - Setting up {cam_name}...")

        try:
            # Per-camera components
            tracker = PersonTracker()
            # Load zones
            zone_checker = ZoneChecker(zones_path="data/zonas/zonas.json")
            
            # Video Service
            service = VideoStreamService(source, name=cam_name)

            # State tracking
            system = {
                'id': i,
                'name': cam_name,
                'service': service,
                'tracker': tracker,
                'zone_checker': zone_checker,
                'zone_state': {},          # {track_id: {zone_name: was_inside}}
                'track_id_to_name': {},    # {track_id: name}
                'track_id_votes': {},      # {track_id: {'name': name, 'count': count}}
                'frame_count': 0
            }
            camera_systems.append(system)
        except Exception as e:
             print(f"❌ Error setting up {cam_name}: {e}")

    # Start all streams
    print("▶️ Starting video streams...")
    for system in camera_systems:
        system['service'].start()

    print(f"✅ System running with {len(camera_systems)} cameras. Press 'q' to exit.")

    try:
        while True:
            # Loop over cameras
            for system in camera_systems:
                # 1. Get Frame
                frame = system['service'].read()
                
                if frame is None:
                    # Show reconnecting status
                    blank = np.zeros((480, 640, 3), dtype=np.uint8)
                    msg = "Reconnecting..."
                    cv2.putText(blank, msg, (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    cv2.imshow(system['name'], blank)
                    continue

                system['frame_count'] += 1

                # 2. Detect & Track
                detections = detector.detect(frame)
                tracked_detections = system['tracker'].update(detections)

                # 3. Process each tracked person
                for xyxy, local_track_id in zip(tracked_detections.xyxy, tracked_detections.tracker_id):
                    local_track_id = int(local_track_id)

                    # Offset ID to ensure uniqueness across cameras
                    # e.g., Cam 0: 0-99999, Cam 1: 100000-199999
                    global_track_id = local_track_id + (system['id'] * 100000)

                    x1, y1, x2, y2 = map(int, xyxy)
                    cx, cy = get_bbox_center(xyxy)

                    # --- IDENTITY RECOGNITION LOGIC ---
                    current_name = system['track_id_to_name'].get(global_track_id, "Unknown")

                    should_verify = False
                    if current_name == "Unknown":
                        should_verify = True
                    else:
                        verification_interval = getattr(config, 'VERIFICATION_INTERVAL', 30)
                        if (system['frame_count'] + local_track_id) % verification_interval == 0:
                            should_verify = True

                    if should_verify:
                        recognized_name = face_recognizer.recognize_face(frame, bbox=(x1, y1, x2, y2))

                        if recognized_name != "Unknown":
                            votes = system['track_id_votes'].get(global_track_id)

                            # Initialize vote entry if needed
                            if not votes:
                                votes = {'name': recognized_name, 'count': 0}
                                system['track_id_votes'][global_track_id] = votes

                            if votes['name'] == recognized_name:
                                votes['count'] += 1
                            else:
                                # Reset votes if name changes
                                system['track_id_votes'][global_track_id] = {'name': recognized_name, 'count': 1}

                            min_matches = getattr(config, 'FACE_RECOGNITION_MIN_MATCHES', 3)
                            if system['track_id_votes'][global_track_id]['count'] >= min_matches:
                                if current_name != "Unknown" and current_name != recognized_name:
                                    print(f"[{system['name']}] 🔄 Identity Change! ID: {global_track_id} {current_name} -> {recognized_name}")

                                system['track_id_to_name'][global_track_id] = recognized_name

                                if current_name == "Unknown":
                                    print(f"[{system['name']}] ✅ ID: {global_track_id} identified as {recognized_name}")

                    display_name = system['track_id_to_name'].get(global_track_id, "Unknown")

                    # --- ZONE LOGIC ---
                    results = system['zone_checker'].check(cx, cy)

                    if global_track_id not in system['zone_state']:
                        system['zone_state'][global_track_id] = {}

                    for zone_name, inside in results.items():
                        inside_zone = int(inside)
                        was_inside = system['zone_state'][global_track_id].get(zone_name, False)

                        if inside_zone and not was_inside:
                            # EVENT: Entered Zone
                            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                            filename = f"{system['name']}_{global_track_id}_{display_name}_{zone_name}_{timestamp_str}.jpg"
                            filename = filename.replace(" ", "_")
                            filepath = os.path.join(snapshots_dir, filename)

                            try:
                                cv2.imwrite(filepath, frame)
                                db_manager.insert_snapshot(system['name'], global_track_id, zone_name, filepath, employee_name=display_name)
                                print(f"[{system['name']}] 📸 Snapshot: {display_name} entered {zone_name}")
                            except Exception as e:
                                print(f"Error saving snapshot: {e}")

                        # Update state
                        system['zone_state'][global_track_id][zone_name] = bool(inside_zone)

                        # Record position
                        db_manager.insert_record(
                            camera_id=system['name'],
                            track_id=global_track_id,
                            x=cx,
                            y=cy,
                            zone=zone_name,
                            inside_zone=inside_zone
                        )

                    # Draw
                    color = (0, 255, 0) if any(system['zone_state'][global_track_id].values()) else (0, 0, 255)
                    label = f"ID:{global_track_id} {display_name}"
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                # Show frame
                cv2.imshow(system['name'], frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("\nCreating shutdown...")
    except Exception as e:
        print(f"❌ Unexpected error in main loop: {e}")
    finally:
        print("🛑 Stopping all services...")
        for system in camera_systems:
            system['service'].stop()
        cv2.destroyAllWindows()
        print("✅ System shutdown complete.")

if __name__ == "__main__":
    main()
