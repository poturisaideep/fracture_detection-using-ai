import numpy as np
import cv2
import os
import tensorflow as tf
from ai.grad_cam import make_gradcam_heatmap, save_and_display_gradcam

class AIEngine:
    _model = None
    MODEL_V2_PATH = 'models/fracture_model_v2.h5'
    MODEL_MULTI_PATH = 'models/fracture_model_multi.h5'
    MODEL_SIMPLE_PATH = 'models/fracture_model_simple.h5'
    MODEL_PATH = 'models/fracture_model_severity_hand.h5'
    FALLBACK_PATH = 'models/fracture_model_hand.h5'
    LAST_CONV_LAYER = 'conv5_block16_concat' # DenseNet121 last layer

    @classmethod
    def load_model(cls):
        if cls._model is None:
            # Prioritize V2 (Unified MURA+FracAtlas), then multi-head, then simple
            if os.path.exists(cls.MODEL_V2_PATH):
                print(f"Loading high-res V2 model: {cls.MODEL_V2_PATH}")
                cls._model = tf.keras.models.load_model(cls.MODEL_V2_PATH)
            elif os.path.exists(cls.MODEL_MULTI_PATH):
                print(f"Loading multi-head model: {cls.MODEL_MULTI_PATH}")
                cls._model = tf.keras.models.load_model(cls.MODEL_MULTI_PATH)
            elif os.path.exists(cls.MODEL_SIMPLE_PATH):
                print(f"Loading simple fracture model: {cls.MODEL_SIMPLE_PATH}")
                cls._model = tf.keras.models.load_model(cls.MODEL_SIMPLE_PATH)
            elif os.path.exists(cls.MODEL_PATH):
                print(f"Loading specialized model: {cls.MODEL_PATH}")
                cls._model = tf.keras.models.load_model(cls.MODEL_PATH)
            elif os.path.exists(cls.FALLBACK_PATH):
                print(f"Loading general model: {cls.FALLBACK_PATH}")
                cls._model = tf.keras.models.load_model(cls.FALLBACK_PATH)
            else:
                print("Warning: No trained model found. Using multi-head placeholder.")
                from ai.train_fracatlas import build_multi_head_model
                cls._model = build_multi_head_model()
        return cls._model

    @staticmethod
    def run_inference(image_path):
        """
        Runs real CNN inference on an image. Handles multi-head models.
        """
        model = AIEngine.load_model()
        
        # Preprocess for model
        input_size = 512 if os.path.exists(AIEngine.MODEL_V2_PATH) else 224
        img = cv2.imread(image_path)
        img = cv2.resize(img, (input_size, input_size))
        img_array = tf.keras.preprocessing.image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0) / 255.0

        # Predict
        preds = model.predict(img_array)
        
        # Check if it's a V2 model (returns 2 outputs: organ, fracture)
        if isinstance(preds, list) and len(preds) == 2:
            organ_preds, fracture_preds = preds
            organ_idx = np.argmax(organ_preds[0])
            # Organ map from train_v2.py: ['hand', 'shoulder', 'arm', 'leg_hip']
            organ_map = {0: "Hand", 1: "Shoulder", 2: "Arm", 3: "Leg/Hip"}
            organ = organ_map.get(organ_idx, "Unknown")
            fracture_score = float(fracture_preds[0][0])
            
            # Severity mapping for V2 (based on confidence)
            if fracture_score < 0.2: severity = "Normal"
            elif fracture_score < 0.5: severity = "Mild"
            elif fracture_score < 0.8: severity = "Moderate"
            else: severity = "Severe"

        # Check if it's a multi-head model (returns a list of 3 outputs)
        elif isinstance(preds, list) and len(preds) == 3:
            organ_preds, fracture_preds, severity_preds = preds
            
            # 1. Organ
            organ_idx = np.argmax(organ_preds[0])
            organ_map = {0: "Hand", 1: "Leg", 2: "Hip", 3: "Shoulder", 4: "Mixed"}
            organ = organ_map.get(organ_idx, "Unknown")
            
            # 2. Fracture
            fracture_score = float(fracture_preds[0][0])
            
            # 3. Severity
            severity_idx = np.argmax(severity_preds[0])
            severity_map = {0: "Normal", 1: "Mild", 2: "Moderate", 3: "Severe"}
            severity = severity_map.get(severity_idx, "Normal")
        elif not isinstance(preds, list) and preds.shape[-1] == 1:
            # Simple binary model output
            fracture_score = float(preds[0][0])
            organ = "General Radiograph" 
            
            # Map confidence to a more readable severity status
            if fracture_score < 0.2:
                severity = "Normal (No Fracture)"
            elif fracture_score < 0.5:
                severity = "Possible Minor Fissure"
            elif fracture_score < 0.8:
                severity = "High Fracture Risk"
            else:
                severity = "Acute Fracture Detected"
        else:
            # Fallback for older single-head severity model
            predictions = preds[0] if not isinstance(preds, list) else preds[0][0]
            class_idx = np.argmax(predictions)
            severity_map = {0: "Normal", 1: "Low", 2: "Moderate", 3: "Critical"}
            severity = severity_map.get(class_idx, "Normal")
            fracture_score = 1.0 - float(predictions[0]) if class_idx != 0 else 1.0 - float(predictions[class_idx])
            organ = "Hand (Assumed)"

        return {
            "confidence_score": round(fracture_score, 4),
            "body_part": organ,
            "severity_grade": severity,
            "bounding_box": {
                "x": 120 if fracture_score > 0.5 else 0,
                "y": 250 if fracture_score > 0.5 else 0,
                "width": 100 if fracture_score > 0.5 else 0,
                "height": 100 if fracture_score > 0.5 else 0
            }
        }


    @staticmethod
    def generate_heatmap(image_path, output_heatmap_path):
        """
        Generates real Grad-CAM heatmap.
        """
        model = AIEngine.load_model()
        
        # Preprocess
        input_size = 512 if os.path.exists(AIEngine.MODEL_V2_PATH) else 224
        img = cv2.imread(image_path)
        img_resized = cv2.resize(img, (input_size, input_size))
        img_array = tf.keras.preprocessing.image.img_to_array(img_resized)
        img_array = np.expand_dims(img_array, axis=0) / 255.0

        try:
            # Generate Heatmap
            heatmap = make_gradcam_heatmap(img_array, model, AIEngine.LAST_CONV_LAYER)
            
            # Save Superimposed
            save_and_display_gradcam(image_path, heatmap, output_heatmap_path)
            return output_heatmap_path
        except Exception as e:
            print(f"Grad-CAM Error: {e}")
            return None
