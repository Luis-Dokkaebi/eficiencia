import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.storage.database_manager import DatabaseManager
from config import config

def init_db():
    print("Initializing database...")
    print(f"URL: {config.DATABASE_URL}")
    try:
        db_manager = DatabaseManager()
        print("Database initialized successfully.")
        print("Tables created (if not existed): tracking_events, snapshots")
    except Exception as e:
        print(f"Error initializing database: {e}")

if __name__ == "__main__":
    init_db()
