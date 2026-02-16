import sys
import os
import argparse

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.storage.database_manager import DatabaseManager

def create_admin(username, password):
    db_manager = DatabaseManager()

    # Check if user exists
    existing = db_manager.get_user_by_username(username)
    if existing:
        print(f"User '{username}' already exists.")
        return

    user = db_manager.create_user(
        username=username,
        password=password,
        role="admin",
        permissions="all"
    )
    if user:
        print(f"Admin user '{username}' created successfully.")
    else:
        print("Failed to create user.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create an admin user.")
    parser.add_argument("username", help="Username")
    parser.add_argument("password", help="Password")
    args = parser.parse_args()

    create_admin(args.username, args.password)
