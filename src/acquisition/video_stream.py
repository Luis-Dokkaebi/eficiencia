import cv2
import time
from threading import Thread, Lock

class VideoStreamService:
    def __init__(self, source, name="Camera"):
        self.source = source
        self.name = name
        self.stream = None
        self.stopped = False
        self.frame = None
        self.grabbed = False
        self.lock = Lock()
        self.is_reconnecting = False

    def start(self):
        self.stopped = False
        t = Thread(target=self.update, args=(), daemon=True)
        t.start()
        return self

    def update(self):
        # Initial connection
        self._connect()

        while not self.stopped:
            if self.stream is None or not self.stream.isOpened():
                self._reconnect()
                continue

            grabbed, frame = self.stream.read()

            if not grabbed:
                print(f"[{self.name}] Connection lost/End of stream. Reconnecting...")
                self._reconnect()
                continue

            with self.lock:
                self.grabbed = grabbed
                self.frame = frame

        # Cleanup on stop
        if self.stream:
            self.stream.release()

    def _connect(self):
        """Initial connection attempt."""
        print(f"[{self.name}] Connecting to {self.source}...")
        try:
            self.stream = cv2.VideoCapture(self.source)
            if self.stream.isOpened():
                grabbed, frame = self.stream.read()
                if grabbed:
                    with self.lock:
                        self.grabbed = True
                        self.frame = frame
                    print(f"[{self.name}] Connected.")
                else:
                    print(f"[{self.name}] Connected but no frame.")
                    self.stream.release()
                    self.stream = None
            else:
                 print(f"[{self.name}] Failed to open stream.")
                 self.stream = None
        except Exception as e:
            print(f"[{self.name}] Connection error: {e}")
            self.stream = None

    def _reconnect(self):
        """Reconnection loop."""
        self.is_reconnecting = True
        with self.lock:
             self.grabbed = False

        if self.stream:
            self.stream.release()

        print(f"[{self.name}] Attempting to reconnect...")

        while not self.stopped:
            try:
                self.stream = cv2.VideoCapture(self.source)
                if self.stream.isOpened():
                    grabbed, frame = self.stream.read()
                    if grabbed:
                        with self.lock:
                            self.grabbed = True
                            self.frame = frame
                        print(f"[{self.name}] Reconnected!")
                        self.is_reconnecting = False
                        return
                    else:
                        self.stream.release()
            except Exception as e:
                # print(f"[{self.name}] Reconnection error: {e}")
                pass

            # Wait before next attempt
            time.sleep(2)

    def read(self):
        with self.lock:
            if self.grabbed:
                return self.frame
            return None

    def stop(self):
        self.stopped = True
