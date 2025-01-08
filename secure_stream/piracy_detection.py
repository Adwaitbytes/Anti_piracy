import cv2
import numpy as np
import tensorflow as tf
from typing import Dict, List, Optional, Tuple

class PiracyDetector:
    def __init__(self):
        """Initialize the piracy detector with pre-trained model."""
        # Load pre-trained ResNet50 model
        self.model = tf.keras.applications.ResNet50(
            include_top=False,
            weights='imagenet',
            pooling='avg'
        )
        
        # Initialize feature database (in memory for demo)
        self.feature_database = {}
        
    def extract_features(self, image: np.ndarray) -> np.ndarray:
        """Extract features from an image using ResNet50."""
        # Preprocess image
        img = cv2.resize(image, (224, 224))
        img = tf.keras.applications.resnet50.preprocess_input(img)
        img = np.expand_dims(img, axis=0)
        
        # Extract features
        features = self.model.predict(img)
        return features[0]
        
    def compute_similarity(self, features1: np.ndarray, features2: np.ndarray) -> float:
        """Compute cosine similarity between feature vectors."""
        return np.dot(features1, features2) / (np.linalg.norm(features1) * np.linalg.norm(features2))
        
    def detect_similarities(self, image: np.ndarray) -> Dict:
        """
        Detect similarities between input image and database.
        Returns similarity scores and matches.
        """
        # Extract features from input image
        input_features = self.extract_features(image)
        
        # Compare with database
        matches = []
        max_similarity = 0.0
        
        for content_id, stored_features in self.feature_database.items():
            similarity = self.compute_similarity(input_features, stored_features)
            if similarity > 0.85:  # Threshold for similarity
                matches.append({
                    "content_id": content_id,
                    "similarity": float(similarity)
                })
            max_similarity = max(max_similarity, similarity)
        
        return {
            "similarity_score": float(max_similarity),
            "matches": sorted(matches, key=lambda x: x["similarity"], reverse=True)
        }
        
    def register_content(self, content_id: str, image: np.ndarray):
        """Register content in the feature database."""
        features = self.extract_features(image)
        self.feature_database[content_id] = features
        
        # ORB feature matching
        orb_sim = 0.0
        if (len(extra_feat1['descriptors']) > 0 and 
            len(extra_feat2['descriptors']) > 0):
            # Use BFMatcher for ORB descriptors
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bf.match(
                extra_feat1['descriptors'],
                extra_feat2['descriptors']
            )
            
            # Sort matches by distance
            matches = sorted(matches, key=lambda x: x.distance)
            
            # Use top matches with more lenient distance threshold
            good_matches = [m for m in matches[:100] if m.distance < 50]
            orb_sim = len(good_matches) / min(
                len(extra_feat1['keypoints']),
                len(extra_feat2['keypoints'])
            )
        
        # Weighted combination of similarities
        # Increase weight of block similarity for better cropping detection
        weights = {
            'cnn': 0.3,
            'hash': 0.2,
            'block': 0.3,
            'orb': 0.2
        }
        
        overall_sim = (
            weights['cnn'] * cnn_sim +
            weights['hash'] * hash_sim +
            weights['block'] * block_sim +
            weights['orb'] * orb_sim
        )
        
        return float(overall_sim)
        
    def detect_similarities(self, image: np.ndarray) -> Dict:
        """
        Detect similarities between input image and database.
        Returns similarity scores and matches.
        """
        # Extract features from input image
        input_features = self.extract_features(image)
        
        # Compare with database
        matches = []
        max_similarity = 0.0
        
        for content_id, stored_features in self.feature_database.items():
            similarity = self.compute_similarity(input_features, stored_features)
            # Lower threshold and include partial matches
            if similarity > 0.3:  # More permissive threshold for edited images
                matches.append({
                    "content_id": content_id,
                    "similarity": float(similarity)
                })
            max_similarity = max(max_similarity, similarity)
        
        return {
            "similarity_score": float(max_similarity),
            "matches": sorted(matches, key=lambda x: x["similarity"], reverse=True)
        }
        
    def register_content(self, content_id: str, image: np.ndarray):
        """Register content in the feature database."""
        features = self.extract_features(image)
        self.feature_database[content_id] = features
