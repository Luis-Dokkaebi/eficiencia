import multiprocessing
import sys
import os
import time

# Ensure root is in path so we can import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import src.main as processing_main
from src.api.main import app

def start_api():
    """Starts the Uvicorn API server."""
    import uvicorn
    print("🚀 Starting API Server on port 8000...")
    # workers=1 ensures we don't spawn more processes implicitly unless configured
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info", workers=1)

def start_processing():
    """Starts the Computer Vision Processing Loop."""
    print("🚀 Starting Computer Vision Processing...")
    try:
        processing_main.main()
    except Exception as e:
        print(f"❌ Processing Loop Crashed: {e}")

if __name__ == "__main__":
    # Crucial for PyInstaller on Windows
    multiprocessing.freeze_support()

    # Set start method to spawn for consistency with PyTorch/CUDA
    try:
        multiprocessing.set_start_method('spawn', force=True)
    except RuntimeError:
        pass

    print("🔹 Launcher Initialized.")

    # Start API Process
    api_process = multiprocessing.Process(target=start_api, name="API_Process")
    api_process.start()

    # Start Processing Process
    # We run the main processing logic in a separate process to keep the launcher responsive
    processing_process = multiprocessing.Process(target=start_processing, name="Processing_Process")
    processing_process.start()

    try:
        while True:
            time.sleep(1)

            if not api_process.is_alive():
                print("⚠️ API Process died! Attempting restart in 5s...")
                api_process.join()
                time.sleep(5)
                api_process = multiprocessing.Process(target=start_api, name="API_Process")
                api_process.start()

            if not processing_process.is_alive():
                print("⚠️ Processing Process died! Attempting restart in 5s...")
                processing_process.join()
                time.sleep(5)
                processing_process = multiprocessing.Process(target=start_processing, name="Processing_Process")
                processing_process.start()

    except KeyboardInterrupt:
        print("\n🛑 Received Shutdown Signal. Terminating processes...")
    finally:
        # Graceful shutdown attempt
        if api_process.is_alive():
            api_process.terminate()
            api_process.join()

        if processing_process.is_alive():
            processing_process.terminate()
            processing_process.join()

        print("👋 System Shutdown Complete.")
