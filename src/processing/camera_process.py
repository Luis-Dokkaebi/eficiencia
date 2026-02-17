import multiprocessing
import cv2
import time
import os
import sys
import numpy as np
from datetime import datetime

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from config import config
except ImportError:
    # Fallback
    import config

from src.detection.person_detector import PersonDetector
from src.tracking.person_tracker import PersonTracker
from src.zones.zone_checker import ZoneChecker
from src.recognition.face_recognizer import FaceRecognizer
from src.acquisition.video_stream import VideoStreamService
from src.paths import get_user_data_path

def get_bbox_center(xyxy):
    x1, y1, x2, y2 = xyxy
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    return center_x, center_y

class CameraGroupProcess(multiprocessing.Process):
    def __init__(self, camera_configs, results_queue):
        """
        camera_configs: list of tuples (global_index, source)
        """
        super().__init__()
        self.camera_configs = camera_configs
        self.results_queue = results_queue
        self.running = multiprocessing.Event()
        self.running.set()

    def run(self):
        print(f"🔄 Camera Group Process Started for {len(self.camera_configs)} cameras")

        # --- Initialize Shared Resources (within process) ---
        try:
            detector = PersonDetector(confidence_threshold=config.CONFIDENCE_THRESHOLD)
            face_recognizer = FaceRecognizer(tolerance=getattr(config, 'FACE_RECOGNITION_TOLERANCE', 0.6))
        except Exception as e:
            print(f"❌ Error initializing shared resources in process: {e}")
            return

        snapshots_dir = getattr(config, 'SNAPSHOTS_DIR', 'data/snapshots')
        os.makedirs(snapshots_dir, exist_ok=True)

        # --- Initialize Camera Systems ---
        systems = []
        for cam_data in self.camera_configs:
            # Handle different config formats
            if len(cam_data) == 2:
                idx, source = cam_data
                name = f"Camera_{idx+1}"
            else:
                idx, source, name = cam_data

            print(f"  - Setting up {name} in process...")
            try:
                tracker = PersonTracker()
                zone_checker = ZoneChecker(zones_path=get_user_data_path("data/zonas/zonas.json"))
                service = VideoStreamService(source, name=name)
                service.start() # Start the thread inside this process

                systems.append({
                    'id': idx,
                    'name': name,
                    'service': service,
                    'tracker': tracker,
                    'zone_checker': zone_checker,
                    'zone_state': {},          # {global_track_id: {zone_name: was_inside}}
                    'track_id_to_name': {},    # {global_track_id: name}
                    'track_id_votes': {},      # {global_track_id: {'name': name, 'count': count}}
                    'frame_count': 0
                })
            except Exception as e:
                print(f"❌ Error setting up {name}: {e}")

        # --- Main Loop ---
        try:
            while self.running.is_set():

                # 1. Collect Frames for Batch Inference
                frames = []
                valid_systems = [] # Systems that provided a frame this iteration

                for sys_obj in systems:
                    frame = sys_obj['service'].read()
                    if frame is not None:
                        frames.append(frame)
                        valid_systems.append(sys_obj)
                    else:
                        # Optional: Add small sleep if all cameras are down?
                        pass

                if not frames:
                    time.sleep(0.01) # Avoid busy loop if no frames
                    continue

                # 2. Batch Detect
                # detector.detect_batch returns list of detections corresponding to frames
                batch_detections = detector.detect_batch(frames)

                # 3. Process Results per Camera
                for i, sys_obj in enumerate(valid_systems):
                    frame = frames[i]
                    detections = batch_detections[i]
                    sys_obj['frame_count'] += 1

                    # Update Tracker
                    tracked_detections = sys_obj['tracker'].update(detections)

                    # Process tracks
                    for xyxy, local_track_id in zip(tracked_detections.xyxy, tracked_detections.tracker_id):
                        local_track_id = int(local_track_id)
                        # Global ID calculation
                        global_track_id = local_track_id + (sys_obj['id'] * 100000)

                        x1, y1, x2, y2 = map(int, xyxy)
                        cx, cy = get_bbox_center(xyxy)

                        # --- IDENTITY RECOGNITION ---
                        current_name = sys_obj['track_id_to_name'].get(global_track_id, "Unknown")
                        should_verify = False

                        if current_name == "Unknown":
                            should_verify = True
                        else:
                            ver_interval = getattr(config, 'VERIFICATION_INTERVAL', 30)
                            if (sys_obj['frame_count'] + local_track_id) % ver_interval == 0:
                                should_verify = True

                        if should_verify:
                            # Face Rec is single image, no batching implemented in FaceRecognizer usually
                            recognized_name = face_recognizer.recognize_face(frame, bbox=(x1, y1, x2, y2))

                            if recognized_name != "Unknown":
                                votes = sys_obj['track_id_votes'].get(global_track_id)
                                if not votes:
                                    votes = {'name': recognized_name, 'count': 0}
                                    sys_obj['track_id_votes'][global_track_id] = votes

                                if votes['name'] == recognized_name:
                                    votes['count'] += 1
                                else:
                                    sys_obj['track_id_votes'][global_track_id] = {'name': recognized_name, 'count': 1}

                                min_matches = getattr(config, 'FACE_RECOGNITION_MIN_MATCHES', 3)
                                if sys_obj['track_id_votes'][global_track_id]['count'] >= min_matches:
                                    if current_name != recognized_name and current_name != "Unknown":
                                        print(f"[{sys_obj['name']}] 🔄 Identity Change! {global_track_id}: {current_name} -> {recognized_name}")

                                    sys_obj['track_id_to_name'][global_track_id] = recognized_name

                        display_name = sys_obj['track_id_to_name'].get(global_track_id, "Unknown")

                        # --- ZONE LOGIC ---
                        results = sys_obj['zone_checker'].check(cx, cy)
                        if global_track_id not in sys_obj['zone_state']:
                            sys_obj['zone_state'][global_track_id] = {}

                        for zone_name, inside in results.items():
                            inside_zone = int(inside)
                            was_inside = sys_obj['zone_state'][global_track_id].get(zone_name, False)

                            if inside_zone and not was_inside:
                                # Snapshot Event
                                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                                filename = f"{sys_obj['name']}_{global_track_id}_{display_name}_{zone_name}_{timestamp_str}.jpg".replace(" ", "_")
                                filepath = os.path.join(snapshots_dir, filename)

                                # Write file locally in this process
                                cv2.imwrite(filepath, frame)

                                # Send metadata to DB Writer
                                self.results_queue.put({
                                    'type': 'snapshot',
                                    'data': {
                                        'camera_id': sys_obj['name'],
                                        'track_id': global_track_id,
                                        'zone': zone_name,
                                        'snapshot_path': filepath,
                                        'employee_name': display_name
                                    }
                                })
                                print(f"[{sys_obj['name']}] 📸 Snapshot: {display_name} entered {zone_name}")

                            sys_obj['zone_state'][global_track_id][zone_name] = bool(inside_zone)

                            # Send Tracking Record to DB Writer
                            self.results_queue.put({
                                'type': 'record',
                                'data': {
                                    'camera_id': sys_obj['name'],
                                    'track_id': global_track_id,
                                    'x': cx,
                                    'y': cy,
                                    'zone': zone_name,
                                    'inside_zone': inside_zone
                                }
                            })

        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"❌ Error in CameraProcess loop: {e}")
        finally:
            print("🛑 Stopping CameraProcess services...")
            for s in systems:
                s['service'].stop()
            print("✅ CameraProcess shutdown.")

    def stop(self):
        self.running.clear()
