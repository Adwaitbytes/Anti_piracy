import pytest
import numpy as np
import cv2
from secure_stream.watermarking import WatermarkEngine, WatermarkValidator
from datetime import datetime

@pytest.fixture
def watermark_engine():
    """Create a watermark engine instance for testing."""
    return WatermarkEngine()

@pytest.fixture
def test_frame():
    """Create a test frame for watermarking tests."""
    return np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)

@pytest.fixture
def watermark_data():
    """Create test watermark data."""
    return {
        "content_id": "test_123",
        "timestamp": datetime.utcnow().isoformat(),
        "owner": "test_owner"
    }

class TestWatermarkEngine:
    def test_watermark_embedding(self, watermark_engine, test_frame, watermark_data):
        """Test watermark embedding and extraction."""
        # Embed watermark
        watermarked_frame = watermark_engine.embed_watermark(
            test_frame,
            str(watermark_data)
        )
        
        # Verify frame dimensions unchanged
        assert watermarked_frame.shape == test_frame.shape
        
        # Extract watermark
        extracted_data = watermark_engine.extract_watermark(
            watermarked_frame,
            1024
        )
        
        # Verify extracted data
        assert "test_123" in extracted_data
        assert "test_owner" in extracted_data

    def test_watermark_robustness(self, watermark_engine, test_frame, watermark_data):
        """Test watermark robustness against common manipulations."""
        # Embed watermark
        watermarked_frame = watermark_engine.embed_watermark(
            test_frame,
            str(watermark_data)
        )
        
        # Test compression resistance
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 70]
        _, compressed = cv2.imencode('.jpg', watermarked_frame, encode_param)
        compressed_frame = cv2.imdecode(compressed, cv2.IMREAD_COLOR)
        
        extracted_data = watermark_engine.extract_watermark(
            compressed_frame,
            1024
        )
        assert "test_123" in extracted_data
        
        # Test scaling resistance
        scaled_frame = cv2.resize(watermarked_frame, (640, 360))
        scaled_frame = cv2.resize(scaled_frame, (1280, 720))
        
        extracted_data = watermark_engine.extract_watermark(
            scaled_frame,
            1024
        )
        assert "test_123" in extracted_data

    def test_watermark_security(self, watermark_engine, test_frame, watermark_data):
        """Test watermark security features."""
        # Test with different encryption keys
        engine1 = WatermarkEngine()
        engine2 = WatermarkEngine()
        
        # Embed with first key
        watermarked_frame = engine1.embed_watermark(
            test_frame,
            str(watermark_data)
        )
        
        # Try to extract with different key
        extracted_data = engine2.extract_watermark(
            watermarked_frame,
            1024
        )
        
        # Should fail to decrypt
        assert "Failed to extract watermark" in extracted_data

class TestWatermarkValidator:
    def test_watermark_validation(self, watermark_engine, test_frame):
        """Test watermark validation functionality."""
        validator = WatermarkValidator()
        
        # Create watermarked frame
        watermarked_frame = watermark_engine.add_robust_watermark(
            test_frame,
            "test_watermark"
        )
        
        # Validate watermark
        similarity = validator.verify_watermark(test_frame, watermarked_frame)
        assert 0 <= similarity <= 1
        
        # Test with tampered frame
        tampered_frame = watermarked_frame.copy()
        tampered_frame[100:200, 100:200] = 0
        
        tampered_similarity = validator.verify_watermark(
            test_frame,
            tampered_frame
        )
        assert tampered_similarity < similarity

@pytest.mark.parametrize("frame_size", [
    (640, 480),
    (1280, 720),
    (1920, 1080)
])
def test_different_resolutions(watermark_engine, frame_size, watermark_data):
    """Test watermarking with different frame resolutions."""
    test_frame = np.random.randint(
        0, 255,
        (frame_size[1], frame_size[0], 3),
        dtype=np.uint8
    )
    
    watermarked_frame = watermark_engine.embed_watermark(
        test_frame,
        str(watermark_data)
    )
    
    assert watermarked_frame.shape == test_frame.shape
    
    extracted_data = watermark_engine.extract_watermark(
        watermarked_frame,
        1024
    )
    assert "test_123" in extracted_data
