import sys
import os

def get_base_path():
    """
    Returns the base directory for user data and configuration.
    - Frozen (Exe): The directory containing the executable.
    - Script: The project root directory.
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    # Assuming this file is at src/paths.py, so project root is one level up
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def get_bundled_resource_path(relative_path):
    """
    Returns path to a bundled resource (read-only).
    - Frozen (Exe): The temporary _MEIPASS directory.
    - Script: The project root directory.
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller stores bundled files in sys._MEIPASS
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(base_path, relative_path)

def get_user_data_path(relative_path):
    """
    Returns path to user data (read/write).
    - Frozen (Exe): Relative to the executable.
    - Script: Relative to the project root.
    """
    return os.path.join(get_base_path(), relative_path)
