# src/acquisition/video_stream.py

import cv2
import time
from threading import Thread, Lock

class VideoStreamService:
    def __init__(self, source, name="Camera", reconnect_interval=5):
        """
        Initializes the VideoStreamService.

        Args:
            source: Video source (int for local camera index, str for video file/URL).
            name: Name of the camera (for logging).
            reconnect_interval: Time (in seconds) to wait before retrying connection.
        """
        self.source = source
        self.name = name
        self.reconnect_interval = reconnect_interval

        self.stream = None
        self.stopped = False
        self.frame = None
        self.lock = Lock()
        self.connected = False

    def start(self):
        """Starts the video reading thread."""
        if self.stopped:
            return self

        t = Thread(target=self.update, args=(), daemon=True)
        t.start()
        return self

    def _connect(self):
        """Attempts to connect to the video source."""
        if self.stream:
            self.stream.release()

        print(f"[{self.name}] Connecting to video source...")
        try:
            self.stream = cv2.VideoCapture(self.source)
            if self.stream.isOpened():
                print(f"[{self.name}] Connected successfully.")
                self.connected = True
                return True
            else:
                print(f"[{self.name}] Connection failed.")
                self.connected = False
                return False
        except Exception as e:
            print(f"[{self.name}] Error connecting: {e}")
            self.connected = False
            return False

    def update(self):
        """Thread function to continuously read frames."""
        # Initial connection attempt
        if not self.connected:
             if not self._connect():
                 # Should we wait here or just let the loop handle it?
                 # Let the loop handle retries
                 pass

        while not self.stopped:
            if not self.connected:
                print(f"[{self.name}] Attempting to reconnect in {self.reconnect_interval} seconds...")
                time.sleep(self.reconnect_interval)
                self._connect()
                continue

            try:
                ret, frame = self.stream.read()
                if not ret:
                    print(f"[{self.name}] Failed to read frame. Lost connection.")
                    self.connected = False
                    with self.lock:
                        self.frame = None
                    continue

                with self.lock:
                    self.frame = frame
            except Exception as e:
                print(f"[{self.name}] Error reading frame: {e}")
                self.connected = False
                with self.lock:
                    self.frame = None

    def read(self):
        """Returns the most recent frame."""
        with self.lock:
            return self.frame

    def stop(self):
        """Stops the video stream."""
        self.stopped = True
        if self.stream:
            self.stream.release()
