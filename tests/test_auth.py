import os
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set environment variables for testing
os.environ['DATABASE_URL'] = 'sqlite:///./test_auth.db'
os.environ['SECRET_KEY'] = 'testsecret'
os.environ['CAMERAS_JSON'] = '["rtsp://cam1", "rtsp://cam2"]'

# Import app and db_manager after setting env vars
# Note: In a real test suite, we might need to reload modules or use fixture patching
from src.api.main import app, db_manager
from src.storage.models import Base

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_db():
    # Re-create the engine with the test URL if needed, but db_manager should have picked it up
    # if this is the first import.
    # To be safe, let's re-initialize the engine or just use what we have if it points to sqlite

    # Create tables
    Base.metadata.create_all(db_manager.engine)

    yield

    # Cleanup
    Base.metadata.drop_all(db_manager.engine)
    if os.path.exists("./test_auth.db"):
        os.remove("./test_auth.db")

def test_create_admin_user(setup_db):
    # Manually create an admin user
    user = db_manager.create_user("admin", "adminpass", role="admin", permissions="all")
    assert user['username'] == "admin"
    assert user['role'] == "admin"

def test_login(setup_db):
    response = client.post("/token", data={"username": "admin", "password": "adminpass"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    return response.json()["access_token"]

def test_create_restricted_user(setup_db):
    token = test_login(setup_db)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/users",
        json={"username": "viewer", "password": "viewerpass", "role": "user", "permissions": '["Camera_1"]'},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["username"] == "viewer"

def test_login_restricted_user(setup_db):
    response = client.post("/token", data={"username": "viewer", "password": "viewerpass"})
    assert response.status_code == 200
    return response.json()["access_token"]

def test_access_control_cameras(setup_db):
    token = test_login_restricted_user(setup_db)
    headers = {"Authorization": f"Bearer {token}"}

    # Based on CAMERAS_JSON=["rtsp://cam1", "rtsp://cam2"], we have Camera_1 and Camera_2
    response = client.get("/cameras", headers=headers)
    assert response.status_code == 200
    cameras = response.json()

    # Should only contain Camera_1
    camera_ids = [c["id"] for c in cameras]
    assert "Camera_1" in camera_ids
    assert "Camera_2" not in camera_ids

def test_access_denied_for_wrong_camera(setup_db):
    token = test_login_restricted_user(setup_db)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/events?camera_id=Camera_2", headers=headers)
    assert response.status_code == 403

def test_access_allowed_for_correct_camera(setup_db):
    token = test_login_restricted_user(setup_db)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/events?camera_id=Camera_1", headers=headers)
    assert response.status_code == 200

def test_efficiency_stats_filtering(setup_db):
    token = test_login_restricted_user(setup_db)
    headers = {"Authorization": f"Bearer {token}"}

    # Mock some data
    # Insert events for Camera_1 and Camera_2
    db_manager.insert_record("Camera_1", 1, 0, 0, "ZoneA", 1)
    db_manager.insert_record("Camera_2", 2, 0, 0, "ZoneB", 1)

    response = client.get("/stats/efficiency", headers=headers)
    assert response.status_code == 200
    stats = response.json()

    assert "Camera_1" in stats
    assert "Camera_2" not in stats

def test_admin_access_all_cameras(setup_db):
    token = test_login(setup_db)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/cameras", headers=headers)
    assert response.status_code == 200
    cameras = response.json()

    # Should contain all cameras (Camera_1 and Camera_2)
    camera_ids = [c["id"] for c in cameras]
    assert "Camera_1" in camera_ids
    assert "Camera_2" in camera_ids
