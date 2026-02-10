# src/tracking/person_tracker.py

import supervision as sv
import numpy as np
import sys
import os

# Ensure we can import from the same directory
sys.path.append(os.path.dirname(__file__))

from appearance_extractor import AppearanceFeatureExtractor

class PersonTracker:
    def __init__(self):
        self.tracker = sv.ByteTrack()
        print("Inicializando AppearanceFeatureExtractor...")
        self.extractor = AppearanceFeatureExtractor(verbose=True)

    def update(self, detections, frame):
        """
        Updates the tracker and extracts appearance features.

        Args:
            detections (sv.Detections): Detections from the detector.
            frame (numpy.ndarray): Current video frame.

        Returns:
            tracked_detections (sv.Detections): Detections with assigned tracker_ids.
            embeddings (dict): Dictionary mapping {track_id: feature_vector}.
        """
        # ByteTrack update
        tracked_detections = self.tracker.update_with_detections(detections)

        embeddings = {}

        if frame is None:
            return tracked_detections, embeddings

        # Iterate through tracked detections to extract features
        for xyxy, track_id in zip(tracked_detections.xyxy, tracked_detections.tracker_id):
            # tracker_id can be int or str depending on supervision version, casting to int just in case
            track_id = int(track_id)

            x1, y1, x2, y2 = map(int, xyxy)

            # Ensure coordinates are within frame bounds
            h, w, _ = frame.shape
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(w, x2)
            y2 = min(h, y2)

            if x2 > x1 and y2 > y1:
                person_crop = frame[y1:y2, x1:x2]
                feature = self.extractor.extract(person_crop)
                if feature is not None:
                    embeddings[track_id] = feature

        return tracked_detections, embeddings
