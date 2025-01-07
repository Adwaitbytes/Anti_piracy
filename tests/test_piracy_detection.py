import pytest
import numpy as np
import tensorflow as tf
import cv2
from secure_stream.piracy_detection import PiracyDetector, DetectionResult
from datetime import datetime

@pytest.fixture
def detector():
    """Create a PiracyDetector instance for testing."""
    return PiracyDetector()

@pytest.fixture
def test_frames():
    """Create test frames for detection."""
    return [
        np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
        for _ in range(5)
    ]

class TestPiracyDetector:
    def test_model_initialization(self, detector):
        """Test model initialization and architecture."""
        assert detector.model is not None
        assert isinstance(detector.model, tf.keras.Model)
        
        # Verify model layers
        expected_layers = [
            'input',
            'resnet50',
            'global_average_pooling2d',
            'dense',
            'dropout',
            'dense_1',
            'dense_2'
        ]
        
        model_layers = [layer.name.lower() for layer in detector.model.layers]
        for layer in expected_layers:
            assert any(layer.lower() in name for name in model_layers), f"Layer {layer} not found in model"

    def test_feature_extraction(self, detector, test_frames):
        """Test feature extraction functionality."""
        frame = test_frames[0]
        features = detector.extract_features(frame)
        
        # Verify feature dimensions
        assert features.ndim == 1
        assert features.shape[0] > 0
        
        # Test batch processing
        features_batch = np.array([
            detector.extract_features(frame)
            for frame in test_frames
        ])
        assert features_batch.shape[0] == len(test_frames)

    def test_manipulation_detection(self, detector, test_frames):
        """Test manipulation detection."""
        # Test original frame
        frame = test_frames[0]
        is_manipulated, confidence = detector.detect_manipulation(frame)
        
        assert isinstance(is_manipulated, bool)
        assert 0 <= confidence <= 1
        
        # Test manipulated frame
        manipulated_frame = frame.copy()
        manipulated_frame[100:200, 100:200] = 0
        
        is_manipulated, confidence = detector.detect_manipulation(
            manipulated_frame
        )
        assert isinstance(is_manipulated, bool)
        assert 0 <= confidence <= 1

    def test_video_analysis(self, detector, test_frames):
        """Test video segment analysis."""
        results = detector.analyze_video_segment(test_frames)
        
        assert len(results) == len(test_frames)
        for result in results:
            assert isinstance(result, DetectionResult)
            assert 0 <= result.confidence <= 1
            assert result.match_type in ('manipulated', 'original')
            assert isinstance(result.source_details, dict)
            assert 'noise_level' in result.source_details
            assert 'compression_artifacts' in result.source_details

    def test_noise_analysis(self, detector, test_frames):
        """Test noise pattern analysis."""
        frame = test_frames[0]
        noise_level = detector._analyze_noise_pattern(frame)
        
        assert isinstance(noise_level, float)
        assert noise_level >= 0
        
        # Test with noisy frame
        noisy_frame = frame + np.random.normal(0, 25, frame.shape)
        noisy_frame = np.clip(noisy_frame, 0, 255).astype(np.uint8)
        
        noisy_level = detector._analyze_noise_pattern(noisy_frame)
        assert noisy_level > noise_level

    def test_compression_detection(self, detector, test_frames):
        """Test compression artifact detection."""
        frame = test_frames[0]
        original_score = detector._detect_compression_artifacts(frame)
        
        # Test with compressed frame
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 10]
        _, compressed = cv2.imencode('.jpg', frame, encode_param)
        compressed_frame = cv2.imdecode(compressed, cv2.IMREAD_COLOR)
        
        compressed_score = detector._detect_compression_artifacts(
            compressed_frame
        )
        assert compressed_score != original_score

    def test_model_training(self, detector):
        """Test model training functionality."""
        # Create synthetic training data
        num_samples = 10
        frames = [
            np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
            for _ in range(num_samples)
        ]
        labels = np.random.randint(0, 2, num_samples)
        
        training_data = list(zip(frames, labels))
        
        # Train model
        detector.train(training_data, epochs=1)
        
        # Verify model updates
        assert detector.model is not None
        
        # Test prediction after training
        test_frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
        is_manipulated, confidence = detector.detect_manipulation(test_frame)
        
        assert isinstance(is_manipulated, bool)
        assert 0 <= confidence <= 1

@pytest.mark.parametrize("frame_size", [
    (640, 480),
    (1280, 720),
    (1920, 1080)
])
def test_different_resolutions(detector, frame_size):
    """Test detection with different frame resolutions."""
    frame = np.random.randint(
        0, 255,
        (frame_size[1], frame_size[0], 3),
        dtype=np.uint8
    )
    
    is_manipulated, confidence = detector.detect_manipulation(frame)
    assert isinstance(is_manipulated, bool)
    assert 0 <= confidence <= 1
