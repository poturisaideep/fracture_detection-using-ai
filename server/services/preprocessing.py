import cv2
import numpy as np
from PIL import Image
import os

class PreprocessingPipeline:
    @staticmethod
    def process_image(image_path, output_path):
        """
        Applies medical-grade preprocessing to an image:
        1. Normalization
        2. Contrast Enhancement (CLAHE)
        3. Noise Reduction
        """
        # Load image
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError("Image not found or invalid format")

        # 1. Normalization (Linear scaling)
        normalized_img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)

        # 2. Contrast Enhancement (CLAHE)
        # Contrast Limited Adaptive Histogram Equalization is standard for medical imaging
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        contrast_img = clahe.apply(normalized_img)

        # 3. Noise Reduction (Gaussian Blur)
        denoised_img = cv2.GaussianBlur(contrast_img, (5, 5), 0)

        # Save processed image
        cv2.imwrite(output_path, denoised_img)
        return output_path

    @staticmethod
    def handle_dicom(dicom_path, output_path):
        """
        Placeholder for DICOM conversion. For Phase 1, we simulate this.
        In a full system, pydicom would be used to extract pixel data.
        """
        # Simulate conversion by reading it as a standard image if it exists
        # In reality, pydicom.dcmread() would be here.
        return PreprocessingPipeline.process_image(dicom_path, output_path)
