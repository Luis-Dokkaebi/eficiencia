# src/detection/person_detector.py

from ultralytics import YOLO
import numpy as np
import supervision as sv

class PersonDetector:
    def __init__(self, model_path="models/yolov8/yolov8n.pt", confidence_threshold=0.4):
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
