import sys
import os
import cv2
import numpy as np

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from tracking.appearance_extractor import AppearanceFeatureExtractor

def test_reid_extractor():
    print("Testing AppearanceFeatureExtractor...")
    extractor = AppearanceFeatureExtractor(verbose=True)

    # Create a dummy image (256x128x3)
    dummy_img = np.random.randint(0, 255, (256, 128, 3), dtype=np.uint8)

    feature = extractor.extract(dummy_img)

    if feature is None:
        print("❌ FAILED: Feature is None")
        sys.exit(1)

    print(f"Feature shape: {feature.shape}")

    # Check if feature is normalized
    norm = np.linalg.norm(feature)
    print(f"Feature norm: {norm}")

    if not np.isclose(norm, 1.0, atol=1e-5):
        print("❌ FAILED: Feature is not normalized")
        sys.exit(1)

    if feature.shape[0] != 512:
        print(f"❌ FAILED: Feature dimension is {feature.shape[0]}, expected 512")
        sys.exit(1)

    print("✅ AppearanceFeatureExtractor Test Passed!")

if __name__ == "__main__":
    test_reid_extractor()
