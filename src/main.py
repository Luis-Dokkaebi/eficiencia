import multiprocessing
import os
import sys
import time

# Set env var to avoid OMP error on some systems
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from config import config
except ImportError:
    # Fallback
    sys.path.append(os.getcwd())
    from config import config

from src.processing.camera_process import CameraGroupProcess
from src.processing.db_writer import DBWriterProcess
from src.storage.database_manager import DatabaseManager

def main():
    print("🚀 System Starting (Multiprocessing Mode)...")
    
    # 1. Setup Multiprocessing
    # 'spawn' is safer for CUDA/PyTorch
    try:
        multiprocessing.set_start_method('spawn', force=True)
    except RuntimeError:
        pass

    if not config.CAMERAS:
        print("❌ No cameras configured.")
        return

    # 2. Initialize Shared Resources (DB Tables)
    print("🔧 Initializing Database Schema...")
    try:
        # Just init to ensure tables exist before processes start
        DatabaseManager()
    except Exception as e:
        print(f"❌ Error initializing DB: {e}")
        return

    # 3. Create Communication Queue
    results_queue = multiprocessing.Queue()

    # 4. Start DB Writer
    db_writer = DBWriterProcess(results_queue)
    db_writer.start()

    # 5. Group Cameras & Start Processes
    camera_processes = []
    chunk_size = 4

    # config.CAMERAS is a list of sources
    cameras_with_ids = list(enumerate(config.CAMERAS))

    # Chunk list
    chunks = [cameras_with_ids[i:i + chunk_size] for i in range(0, len(cameras_with_ids), chunk_size)]

    print(f"📷 Configuring {len(config.CAMERAS)} cameras in {len(chunks)} groups...")

    for i, chunk in enumerate(chunks):
        print(f"  - Starting Process {i+1} with {len(chunk)} cameras...")
        cp = CameraGroupProcess(chunk, results_queue)
        cp.start()
        camera_processes.append(cp)

    print(f"✅ System running with {len(camera_processes)} camera processes + 1 DB writer.")
    print("Press Ctrl+C to exit.")

    try:
        while True:
            time.sleep(1)

            # Basic Health Check
            if not db_writer.is_alive():
                 print("⚠️ DB Writer process died! Exiting...")
                 break

            # Check camera processes
            for i, cp in enumerate(camera_processes):
                if not cp.is_alive():
                    print(f"⚠️ Camera Process {i+1} died!")
                    # In a real production system, we might restart it here.

    except KeyboardInterrupt:
        print("\nCreating shutdown...")
    finally:
        print("🛑 Stopping all processes...")

        # Stop signals
        for cp in camera_processes:
            cp.stop()
        db_writer.stop()

        # Wait a bit
        time.sleep(1)

        # Force terminate if needed
        for cp in camera_processes:
            if cp.is_alive():
                cp.terminate()
            cp.join()

        if db_writer.is_alive():
            db_writer.terminate()
        db_writer.join()

        print("✅ System shutdown complete.")

if __name__ == "__main__":
    main()
