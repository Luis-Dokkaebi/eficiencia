# src/tracking/appearance_extractor.py

import torch
import torchreid
import numpy as np
import cv2
import os

class AppearanceFeatureExtractor:
    def __init__(self, model_name='osnet_x1_0', use_gpu=True, verbose=False):
        """
        Initializes the AppearanceFeatureExtractor with a pre-trained ReID model.
        Args:
            model_name (str): Name of the model (e.g., 'osnet_x1_0').
            use_gpu (bool): Whether to use GPU if available.
            verbose (bool): Whether to print model loading info.
        """
        self.device = torch.device('cuda' if use_gpu and torch.cuda.is_available() else 'cpu')

        # Suppress prints if not verbose
        if not verbose:
            import logging
            logging.getLogger("torchreid").setLevel(logging.WARNING)

        # Build model
        # Using ImageNet weights as a good initialization if Market-1501 specific weights aren't provided
        # OSNet is designed for ReID so even ImageNet weights are decent for general feature extraction
        try:
            self.model = torchreid.models.build_model(
                name=model_name,
                num_classes=1000, # Standard ImageNet classes
                pretrained=True
            )
        except Exception as e:
            print(f"Error building model {model_name}: {e}")
            raise e

        self.model.to(self.device)
        self.model.eval()

        # Input dimensions for OSNet
        self.height = 256
        self.width = 128

        # Normalization parameters (ImageNet stats)
        self.mean = np.array([0.485, 0.456, 0.406]).astype(np.float32)
        self.std = np.array([0.229, 0.224, 0.225]).astype(np.float32)

    def preprocess(self, image):
        """
        Preprocesses the image for the model.
        Args:
            image (numpy.ndarray): BGR image crop.
        Returns:
            torch.Tensor: Preprocessed image tensor (1, C, H, W).
        """
        # Resize
        image = cv2.resize(image, (self.width, self.height))

        # BGR to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Normalize to [0, 1]
        image = image.astype(np.float32) / 255.0

        # Normalize with mean and std
        image = (image - self.mean) / self.std

        # HWC to CHW
        image = image.transpose(2, 0, 1)

        # Add batch dimension
        image_tensor = torch.from_numpy(image).unsqueeze(0).float()

        return image_tensor.to(self.device)

    def extract(self, image_crop):
        """
        Extracts the appearance embedding for a given image crop.
        Args:
            image_crop (numpy.ndarray): BGR image of the person.
        Returns:
            numpy.ndarray: Normalized feature vector (dimension depends on model, e.g., 512 for osnet_x1_0).
                           Returns None if crop is invalid.
        """
        if image_crop is None or image_crop.size == 0:
            return None

        try:
            input_tensor = self.preprocess(image_crop)

            with torch.no_grad():
                features = self.model(input_tensor)
                # Normalize features to unit length (important for cosine similarity)
                features = torch.nn.functional.normalize(features, p=2, dim=1)

            return features.cpu().numpy().flatten()
        except Exception as e:
            print(f"Error extracting features: {e}")
            return None
