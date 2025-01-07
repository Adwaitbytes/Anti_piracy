import tensorflow as tf
from tensorflow.keras.applications import EfficientNetB0, ResNet50V2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Concatenate, Input
from tensorflow.keras.models import Model
import numpy as np
from typing import List, Tuple, Dict
import cv2
from PIL import Image
import io

class EnhancedPiracyDetector:
    def __init__(self):
        """Initialize the enhanced piracy detector with multiple models."""
        self.image_size = (224, 224)
        self.models = self._build_models()
        self.feature_extractors = {
            'efficientnet': self.models['feature_extractor_efficientnet'],
            'resnet': self.models['feature_extractor_resnet']
        }
        
    def _build_models(self) -> Dict[str, Model]:
        """Build and return the model architecture."""
        # EfficientNet feature extractor
        efficientnet_base = EfficientNetB0(
            weights='imagenet',
            include_top=False,
            input_shape=(*self.image_size, 3)
        )
        
        # ResNet feature extractor
        resnet_base = ResNet50V2(
            weights='imagenet',
            include_top=False,
            input_shape=(*self.image_size, 3)
        )
        
        # Create feature extractors
        efficientnet_features = GlobalAveragePooling2D()(efficientnet_base.output)
        resnet_features = GlobalAveragePooling2D()(resnet_base.output)
        
        # Create individual feature extractors
        feature_extractor_efficientnet = Model(
            inputs=efficientnet_base.input,
            outputs=efficientnet_features,
            name='feature_extractor_efficientnet'
        )
        
        feature_extractor_resnet = Model(
            inputs=resnet_base.input,
            outputs=resnet_features,
            name='feature_extractor_resnet'
        )
        
        # Combined similarity model
        input_1 = Input(shape=(*self.image_size, 3))
        input_2 = Input(shape=(*self.image_size, 3))
        
        # Extract features using both models
        features_1_efficientnet = feature_extractor_efficientnet(input_1)
        features_2_efficientnet = feature_extractor_efficientnet(input_2)
        
        features_1_resnet = feature_extractor_resnet(input_1)
        features_2_resnet = feature_extractor_resnet(input_2)
        
        # Concatenate features
        combined_features = Concatenate()(
            [features_1_efficientnet, features_1_resnet,
             features_2_efficientnet, features_2_resnet]
        )
        
        # Similarity prediction
        similarity = Dense(1, activation='sigmoid')(combined_features)
        
        similarity_model = Model(
            inputs=[input_1, input_2],
            outputs=similarity,
            name='similarity_model'
        )
        
        return {
            'feature_extractor_efficientnet': feature_extractor_efficientnet,
            'feature_extractor_resnet': feature_extractor_resnet,
            'similarity_model': similarity_model
        }
        
    def preprocess_image(self, image_data: bytes) -> np.ndarray:
        """Preprocess image for model input."""
        # Convert bytes to image
        image = Image.open(io.BytesIO(image_data))
        image = image.convert('RGB')
        
        # Resize
        image = image.resize(self.image_size)
        
        # Convert to array and preprocess
        image_array = np.array(image)
        image_array = image_array.astype(np.float32)
        
        # Normalize
        image_array = image_array / 255.0
        
        return image_array
        
    def extract_features(self, image_data: bytes) -> Dict[str, np.ndarray]:
        """Extract features using multiple models."""
        # Preprocess image
        processed_image = self.preprocess_image(image_data)
        processed_image = np.expand_dims(processed_image, axis=0)
        
        # Extract features using both models
        features = {}
        for name, model in self.feature_extractors.items():
            features[name] = model.predict(processed_image)
            
        return features
        
    def compute_similarity(
        self,
        features1: Dict[str, np.ndarray],
        features2: Dict[str, np.ndarray]
    ) -> float:
        """Compute similarity between two sets of features."""
        similarities = []
        
        # Compute cosine similarity for each feature set
        for name in self.feature_extractors.keys():
            similarity = np.dot(
                features1[name].flatten(),
                features2[name].flatten()
            ) / (
                np.linalg.norm(features1[name]) *
                np.linalg.norm(features2[name])
            )
            similarities.append(similarity)
            
        # Return weighted average of similarities
        return np.mean(similarities)
        
    def detect_modifications(
        self,
        original_image: bytes,
        query_image: bytes
    ) -> Dict:
        """Detect if an image has been modified from the original."""
        # Extract features
        original_features = self.extract_features(original_image)
        query_features = self.extract_features(query_image)
        
        # Compute similarity
        similarity = self.compute_similarity(original_features, query_features)
        
        # Analyze modifications
        modifications = []
        if similarity < 0.95:  # Threshold for modification detection
            # Check for specific modifications
            orig_img = cv2.imdecode(
                np.frombuffer(original_image, np.uint8),
                cv2.IMREAD_COLOR
            )
            query_img = cv2.imdecode(
                np.frombuffer(query_image, np.uint8),
                cv2.IMREAD_COLOR
            )
            
            # Check resolution changes
            if orig_img.shape != query_img.shape:
                modifications.append("Resolution modified")
                
            # Check color changes
            orig_hist = cv2.calcHist([orig_img], [0,1,2], None, [8,8,8], [0,256]*3)
            query_hist = cv2.calcHist([query_img], [0,1,2], None, [8,8,8], [0,256]*3)
            if cv2.compareHist(orig_hist, query_hist, cv2.HISTCMP_CORREL) < 0.95:
                modifications.append("Color modified")
                
            # Check blur
            orig_laplacian = cv2.Laplacian(orig_img, cv2.CV_64F).var()
            query_laplacian = cv2.Laplacian(query_img, cv2.CV_64F).var()
            if abs(orig_laplacian - query_laplacian) > 100:
                modifications.append("Blur detected")
        
        return {
            'similarity_score': float(similarity),
            'is_modified': similarity < 0.95,
            'modifications': modifications,
            'confidence': float(min(1.0, max(0.0, 1.0 - (0.95 - similarity) * 2)))
        }
