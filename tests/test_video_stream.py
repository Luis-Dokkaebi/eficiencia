import unittest
from unittest.mock import MagicMock, patch
import time
import sys
import os

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from acquisition.video_stream import VideoStreamService

class TestVideoStreamService(unittest.TestCase):
    @patch('cv2.VideoCapture')
    def test_connection_lifecycle(self, mock_capture):
        # Setup mock
        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = True
        mock_cap_instance.read.return_value = (True, "frame") # Mock read to return valid tuple
        mock_capture.return_value = mock_cap_instance

        service = VideoStreamService(0)

        # Verify initially disconnected (non-blocking init)
        self.assertFalse(service.connected)

        service.start()
        time.sleep(0.1) # Wait for thread to connect

        # Verify connected
        self.assertTrue(service.connected)
        mock_capture.assert_called_with(0)
        mock_cap_instance.isOpened.assert_called()

        service.stop()

    @patch('cv2.VideoCapture')
    def test_connection_failure(self, mock_capture):
        # Setup mock
        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = False
        mock_capture.return_value = mock_cap_instance

        service = VideoStreamService(0)
        service.start()
        time.sleep(0.1)

        # Verify connection failure
        self.assertFalse(service.connected)
        service.stop()

    @patch('cv2.VideoCapture')
    def test_read_frame(self, mock_capture):
        # Setup mock
        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = True
        mock_frame = "dummy_frame"
        mock_cap_instance.read.return_value = (True, mock_frame)
        mock_capture.return_value = mock_cap_instance

        service = VideoStreamService(0)
        service.start()

        # Give some time for thread to run
        time.sleep(0.1)

        frame = service.read()
        self.assertEqual(frame, mock_frame)

        service.stop()

    @patch('cv2.VideoCapture')
    def test_reconnection_logic(self, mock_capture):
        # Mock instances
        mock_fail = MagicMock()
        mock_fail.isOpened.return_value = False

        mock_success = MagicMock()
        mock_success.isOpened.return_value = True
        mock_success.read.return_value = (True, "frame")

        # side_effect for the constructor
        mock_capture.side_effect = [mock_fail, mock_success, mock_success]

        service = VideoStreamService(0, reconnect_interval=0.1)
        service.start()

        # Wait for first attempt (fail)
        time.sleep(0.05)
        self.assertFalse(service.connected)

        # Wait for reconnection attempt (0.1s interval + margin)
        time.sleep(0.2)

        # Should have called constructor again -> mock_success
        self.assertTrue(service.connected)

        service.stop()

if __name__ == '__main__':
    unittest.main()
