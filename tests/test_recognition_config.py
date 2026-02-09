
import unittest
import sys
import os
from unittest.mock import MagicMock

# Mock dependencies
sys.modules['cv2'] = MagicMock()
sys.modules['face_recognition'] = MagicMock()
sys.modules['numpy'] = MagicMock()

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from recognition.face_recognizer import FaceRecognizer

class TestFaceRecognizerConfig(unittest.TestCase):
    def test_tolerance_init(self):
        # Default
        fr_default = FaceRecognizer()
        print(f"Default tolerance: {fr_default.tolerance}")
        self.assertEqual(fr_default.tolerance, 0.6, "Default tolerance should be 0.6")

        # Custom
        fr_custom = FaceRecognizer(tolerance=0.5)
        print(f"Custom tolerance: {fr_custom.tolerance}")
        self.assertEqual(fr_custom.tolerance, 0.5, "Custom tolerance should be 0.5")

if __name__ == '__main__':
    unittest.main()
