import multiprocessing
import queue
import time
import sys
import os

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.storage.database_manager import DatabaseManager

class DBWriterProcess(multiprocessing.Process):
    def __init__(self, data_queue):
        super().__init__()
        self.data_queue = data_queue
        self.running = multiprocessing.Event()
        self.running.set()

    def run(self):
        print("💾 DB Writer Process Started")

        # Initialize DB Manager within the process
        try:
            db_manager = DatabaseManager()
        except Exception as e:
            print(f"❌ DB Writer failed to initialize DatabaseManager: {e}")
            return

        while self.running.is_set() or not self.data_queue.empty():
            try:
                # Use a timeout to allow checking self.running periodically
                item = self.data_queue.get(timeout=1.0)

                msg_type = item.get('type')
                data = item.get('data')

                if msg_type == 'record':
                    db_manager.insert_record(
                        camera_id=data['camera_id'],
                        track_id=data['track_id'],
                        x=data['x'],
                        y=data['y'],
                        zone=data['zone'],
                        inside_zone=data['inside_zone']
                    )
                elif msg_type == 'snapshot':
                    db_manager.insert_snapshot(
                        camera_id=data['camera_id'],
                        track_id=data['track_id'],
                        zone=data['zone'],
                        snapshot_path=data['snapshot_path'],
                        employee_name=data.get('employee_name')
                    )
                else:
                    print(f"⚠️ Unknown message type in DB queue: {msg_type}")

            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Error in DB Writer: {e}")

        print("💾 DB Writer Process Stopped")

    def stop(self):
        self.running.clear()
