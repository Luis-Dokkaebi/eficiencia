import sys
import os
import multiprocessing
import unittest

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.processing.camera_process import CameraGroupProcess
from src.processing.db_writer import DBWriterProcess

class TestMultiprocessingSetup(unittest.TestCase):
    def test_imports_and_init(self):
        queue = multiprocessing.Queue()

        # Test DBWriter init
        db_writer = DBWriterProcess(queue)
        self.assertIsInstance(db_writer, multiprocessing.Process)

        # Test CameraGroupProcess init
        # Use dummy camera config
        cameras = [(0, 0), (1, 'rtsp://fake')]
        camera_process = CameraGroupProcess(cameras, queue)
        self.assertIsInstance(camera_process, multiprocessing.Process)
        self.assertEqual(len(camera_process.camera_configs), 2)

if __name__ == '__main__':
    unittest.main()
