import os
import json
import logging
from typing import List, Dict, Any, Optional
from PIL import Image

# For local YOLOv8 support, install ultralytics with: pip install ultralytics
from ultralytics import YOLO  
import numpy as np

class LandingAIClient:
    """Client for object detection using either a local YOLOv8 model or LandingAI's API"""

    def __init__(self, api_key: Optional[str] = None, use_local_model: bool = True):
        """
        Args:
            api_key: API key for LandingAI (required if use_local_model is False)
            use_local_model: Flag to determine if the local YOLOv8 model should be used
        """
        self.use_local_model = use_local_model
        self.logger = logging.getLogger(__name__)
        
        if self.use_local_model:
            self.local_model_path = "yolov8_medical_box_best.pt"
            self.logger.info(f"Loading local YOLOv8 model from {self.local_model_path}")
            self.model = YOLO(self.local_model_path)
        else:
            if not api_key or not isinstance(api_key, str):
                raise ValueError("Invalid API key provided")
            self.api_key = api_key
            self.endpoint_id = "eddcb78c-1f45-4350-aac5-7e9897208ae2"
            self.base_url = f"https://predict.app.landing.ai/inference/v1/predict?endpoint_id={self.endpoint_id}"
    
    def detect_objects(self, image: Image.Image, prompt: str = "medibox in the picture") -> List[Dict[str, Any]]:
        """
        Detect objects in an image using either the local YOLOv8 model or LandingAI's API.
        
        Args:
            image: PIL Image object
            prompt: Detection prompt (not used in local model inference)
            
        Returns:
            List of detection results with bounding boxes and scores
        """
        if self.use_local_model:
            # Convert PIL image to numpy array
            image_np = np.array(image)
            results = self.model(image_np)  # Inference with the local YOLOv8 model
            detections = []
            # Process each result returned by the model
            for result in results:
                for box in result.boxes:  # each box corresponds to a detection
                    # box.xyxy, box.conf, and box.cls are tensors
                    xmin, ymin, xmax, ymax = box.xyxy[0].tolist()
                    score = float(box.conf[0])
                    # Map box.cls to a specific label if needed; here we default to 'medibox'
                    detection = {
                        'label': 'medibox',
                        'score': score,
                        'bounding_box': [int(xmin), int(ymin), int(xmax), int(ymax)]
                    }
                    detections.append(detection)
            self.logger.info(f"Local model returned {len(detections)} detections")
            return detections
        else:
            try:
                # Create temporary file for the image
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    image.save(tmp_file.name, 'JPEG', quality=95)
                    tmp_path = tmp_file.name

                try:
                    import requests
                    with open(tmp_path, 'rb') as img_file:
                        files = {"file": img_file}
                        headers = {"apikey": self.api_key}
                        self.logger.info("Sending request to LandingAI API")
                        response = requests.post(
                            self.base_url, files=files, headers=headers, timeout=60
                        )
                        if response.status_code != 200:
                            error_msg = f"API request failed with status {response.status_code}: {response.text}"
                            self.logger.error(error_msg)
                            raise Exception(error_msg)

                        result = response.json()
                        detections = []
                        self.logger.info(f"Raw API response: {result}")
                        if isinstance(result, dict) and 'backbonepredictions' in result:
                            backbone_predictions = result['backbonepredictions']
                            for detection_id, pred_data in backbone_predictions.items():
                                if isinstance(pred_data, dict):
                                    coords = pred_data.get('coordinates', {})
                                    detection = {
                                        'label': pred_data.get('labelName', 'medibox'),
                                        'score': float(pred_data.get('score', 1.0)),
                                        'bounding_box': [
                                            int(coords.get('xmin', 0)),
                                            int(coords.get('ymin', 0)),
                                            int(coords.get('xmax', 0)),
                                            int(coords.get('ymax', 0))
                                        ] if coords else []
                                    }
                                    detections.append(detection)
                        self.logger.info(f"API returned {len(detections)} detections")
                        return detections

                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                        
            except Exception as e:
                self.logger.error(f"Error during API request: {str(e)}")
                raise Exception(f"Detection failed: {str(e)}")
    
    def validate_api_key(self) -> bool:
        """
        Validate the API key by making a test request
        
        Returns:
            True if API key is valid, False otherwise
        """
        try:
            # Create a small test image
            test_image = Image.new('RGB', (100, 100), color='white')
            
            # Try to make a detection request
            self.detect_objects(test_image)
            return True
            
        except Exception as e:
            self.logger.warning(f"API key validation failed: {str(e)}")
            return False
    
    def get_api_status(self) -> Dict[str, Any]:
        """
        Get API status information
        
        Returns:
            Dictionary with API status details
        """
        try:
            # Try a simple prediction to check API availability
            test_image = Image.new('RGB', (100, 100), color='white')
            self.detect_objects(test_image)
            
            return {
                'status': 'available',
                'endpoint_id': self.endpoint_id
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
