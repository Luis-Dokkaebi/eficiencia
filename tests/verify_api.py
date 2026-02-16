import sys
import os
import unittest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set DATABASE_URL to sqlite for testing
os.environ['DATABASE_URL'] = 'sqlite:///data/db/test_tracking.db'

try:
    from src.api.main import app, db_manager
except ImportError as e:
    print(f"Error importing app: {e}")
    sys.exit(1)

class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Insert dummy data
        print("Inserting dummy data...")
        # Recent event for Camera_1 (Online)
        db_manager.insert_record(
            camera_id="Camera_1",
            track_id=101,
            x=100.0,
            y=200.0,
            zone="ZoneA",
            inside_zone=1
        )

        # Old event for Camera_2 (Offline)
        # Hack to insert old timestamp: modifying after insertion isn't easy with insert_record as it uses datetime.now()
        # But we can insert another record for Camera_2 now, it will appear as Online if we check now.
        # To simulate Offline, we need an old timestamp.
        # insert_record uses datetime.now().
        # So we can't easily simulate Offline unless we mock datetime or modify the record after insertion.
        # But for filtering test, we can just insert for Camera_2.

        db_manager.insert_record(
            camera_id="Camera_2",
            track_id=202,
            x=150.0,
            y=250.0,
            zone="ZoneB",
            inside_zone=0
        )

    def setUp(self):
        self.client = TestClient(app)

    def test_get_cameras(self):
        print("\nTesting GET /cameras...")
        response = self.client.get("/cameras")
        self.assertEqual(response.status_code, 200)
        cameras = response.json()
        self.assertIsInstance(cameras, list)
        print(f"Found {len(cameras)} cameras.")
        if len(cameras) > 0:
            cam = cameras[0]
            self.assertIn("id", cam)
            self.assertIn("status", cam)
            # Camera_1 should be Online because we just inserted a record
            if cam['id'] == 'Camera_1':
                self.assertEqual(cam['status'], 'Online')
            print(f"Sample Camera: {cam}")

    def test_get_events(self):
        print("\nTesting GET /events...")
        response = self.client.get("/events")
        self.assertEqual(response.status_code, 200)
        events = response.json()
        self.assertIsInstance(events, list)
        print(f"Found {len(events)} events.")

        self.assertGreater(len(events), 0)

        if len(events) > 0:
            # Test filter
            cam_id = "Camera_1"
            print(f"Testing filter for camera_id={cam_id}...")
            response_filtered = self.client.get(f"/events?camera_id={cam_id}")
            self.assertEqual(response_filtered.status_code, 200)
            events_filtered = response_filtered.json()
            self.assertTrue(all(e['camera_id'] == cam_id for e in events_filtered))
            # Should have at least one event for Camera_1
            self.assertGreater(len(events_filtered), 0)
            print(f"Filter returned {len(events_filtered)} events.")

    def test_get_efficiency_stats(self):
        print("\nTesting GET /stats/efficiency...")
        response = self.client.get("/stats/efficiency")
        self.assertEqual(response.status_code, 200)
        stats = response.json()
        self.assertIsInstance(stats, dict)
        print(f"Stats: {stats}")
        # Expect Camera_1 to have ZoneA count >= 1
        if "Camera_1" in stats:
            self.assertIn("ZoneA", stats["Camera_1"])
            self.assertGreaterEqual(stats["Camera_1"]["ZoneA"], 1)

if __name__ == '__main__':
    unittest.main()
