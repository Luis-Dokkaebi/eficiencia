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

