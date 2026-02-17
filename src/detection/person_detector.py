# src/detection/person_detector.py

from ultralytics import YOLO
import numpy as np
import supervision as sv
from src.paths import get_bundled_resource_path

class PersonDetector:
    def __init__(self, model_path=None, confidence_threshold=0.4):
        if model_path is None:
            model_path = get_bundled_resource_path("models/yolov8/yolov8n.pt")
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold

    def detect(self, frame):
        results = self.model(frame)[0]
        
        detections = sv.Detections.from_ultralytics(results)
        detections = detections[detections.class_id == 0]  # Solo personas
        detections = detections[detections.confidence > self.confidence_threshold]

        return detections

    def detect_batch(self, frames):
        """
        Runs detection on a list of frames.
        Returns a list of sv.Detections objects, one for each frame.
        """
        if not frames:
            return []

        # Ultralytics supports list of frames
        results_list = self.model(frames, verbose=False)

        batch_detections = []
        for results in results_list:
            detections = sv.Detections.from_ultralytics(results)
            detections = detections[detections.class_id == 0]  # Solo personas
            detections = detections[detections.confidence > self.confidence_threshold]
            batch_detections.append(detections)

        return batch_detections
