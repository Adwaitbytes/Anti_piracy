import numpy as np
import cv2
from typing import Tuple, List, Dict, Any
from datetime import datetime, timedelta
import json
import os

def create_test_frame(
    size: Tuple[int, int] = (1280, 720),
    pattern: str = 'random'
) -> np.ndarray:
    """
    Create a test frame for testing.
    
    Args:
        size: Frame size (width, height)
        pattern: Pattern type ('random', 'gradient', 'checkerboard')
        
    Returns:
        Test frame as numpy array
    """
    if pattern == 'random':
        return np.random.randint(0, 255, (size[1], size[0], 3), dtype=np.uint8)
    elif pattern == 'gradient':
        x = np.linspace(0, 255, size[0])
        y = np.linspace(0, 255, size[1])
        xx, yy = np.meshgrid(x, y)
        frame = np.zeros((size[1], size[0], 3), dtype=np.uint8)
        frame[:,:,0] = xx
        frame[:,:,1] = yy
        frame[:,:,2] = (xx + yy) / 2
        return frame
    elif pattern == 'checkerboard':
        frame = np.zeros((size[1], size[0], 3), dtype=np.uint8)
        square_size = 50
        for i in range(0, size[1], square_size):
            for j in range(0, size[0], square_size):
                if (i + j) // square_size % 2:
                    frame[i:i+square_size, j:j+square_size] = 255
        return frame
    else:
        raise ValueError(f"Unknown pattern type: {pattern}")

def apply_manipulation(
    frame: np.ndarray,
    manipulation_type: str,
    params: Dict[str, Any] = None
) -> np.ndarray:
    """
    Apply various manipulations to a frame.
    
    Args:
        frame: Input frame
        manipulation_type: Type of manipulation
        params: Manipulation parameters
        
    Returns:
        Manipulated frame
    """
    if params is None:
        params = {}
        
    if manipulation_type == 'compression':
        quality = params.get('quality', 50)
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        _, compressed = cv2.imencode('.jpg', frame, encode_param)
        return cv2.imdecode(compressed, cv2.IMREAD_COLOR)
        
    elif manipulation_type == 'noise':
        noise_level = params.get('level', 25)
        noisy = frame + np.random.normal(0, noise_level, frame.shape)
        return np.clip(noisy, 0, 255).astype(np.uint8)
        
    elif manipulation_type == 'blur':
        kernel_size = params.get('kernel_size', 5)
        return cv2.GaussianBlur(frame, (kernel_size, kernel_size), 0)
        
    elif manipulation_type == 'crop':
        margin = params.get('margin', 100)
        h, w = frame.shape[:2]
        return frame[margin:h-margin, margin:w-margin]
        
    else:
        raise ValueError(f"Unknown manipulation type: {manipulation_type}")

def create_test_blockchain_data(num_records: int = 10) -> List[Dict[str, Any]]:
    """
    Create test blockchain transaction data.
    
    Args:
        num_records: Number of records to create
        
    Returns:
        List of test blockchain records
    """
    base_time = datetime.utcnow()
    records = []
    
    for i in range(num_records):
        timestamp = base_time - timedelta(hours=i)
        record = {
            'content_id': f'test_content_{i}',
            'content_hash': f'0x{os.urandom(32).hex()}',
            'metadata': {
                'title': f'Test Content {i}',
                'owner': f'Test Owner {i}',
                'type': 'video' if i % 2 == 0 else 'image',
                'timestamp': timestamp.isoformat()
            },
            'transaction_hash': f'0x{os.urandom(32).hex()}',
            'block_number': 1000000 + i,
            'timestamp': int(timestamp.timestamp())
        }
        records.append(record)
    
    return records

def create_test_detection_data(
    num_frames: int = 10,
    violation_probability: float = 0.3
) -> List[Dict[str, Any]]:
    """
    Create test detection results data.
    
    Args:
        num_frames: Number of frames
        violation_probability: Probability of violation per frame
        
    Returns:
        List of detection results
    """
    base_time = datetime.utcnow()
    results = []
    
    for i in range(num_frames):
        timestamp = base_time - timedelta(seconds=i)
        is_violation = np.random.random() < violation_probability
        
        result = {
            'frame_id': i,
            'timestamp': timestamp.isoformat(),
            'is_violation': is_violation,
            'confidence': np.random.uniform(0.7, 0.99) if is_violation else np.random.uniform(0.1, 0.3),
            'analysis': {
                'noise_level': np.random.uniform(0.1, 0.5),
                'compression_artifacts': np.random.uniform(0.1, 0.5),
                'manipulation_type': np.random.choice(['compression', 'noise', 'blur']) if is_violation else None
            }
        }
        results.append(result)
    
    return results

def compare_frames(
    frame1: np.ndarray,
    frame2: np.ndarray,
    method: str = 'mse'
) -> float:
    """
    Compare two frames using various metrics.
    
    Args:
        frame1: First frame
        frame2: Second frame
        method: Comparison method ('mse', 'psnr', 'ssim')
        
    Returns:
        Similarity score
    """
    if method == 'mse':
        return np.mean((frame1 - frame2) ** 2)
        
    elif method == 'psnr':
        mse = np.mean((frame1 - frame2) ** 2)
        if mse == 0:
            return float('inf')
        max_pixel = 255.0
        return 20 * np.log10(max_pixel / np.sqrt(mse))
        
    elif method == 'ssim':
        # Simplified SSIM implementation
        c1 = (0.01 * 255) ** 2
        c2 = (0.03 * 255) ** 2
        
        frame1 = frame1.astype(np.float64)
        frame2 = frame2.astype(np.float64)
        
        kernel = cv2.getGaussianKernel(11, 1.5)
        window = np.outer(kernel, kernel.transpose())
        
        mu1 = cv2.filter2D(frame1, -1, window)[5:-5, 5:-5]
        mu2 = cv2.filter2D(frame2, -1, window)[5:-5, 5:-5]
        mu1_sq = mu1 ** 2
        mu2_sq = mu2 ** 2
        mu1_mu2 = mu1 * mu2
        
        sigma1_sq = cv2.filter2D(frame1 ** 2, -1, window)[5:-5, 5:-5] - mu1_sq
        sigma2_sq = cv2.filter2D(frame2 ** 2, -1, window)[5:-5, 5:-5] - mu2_sq
        sigma12 = cv2.filter2D(frame1 * frame2, -1, window)[5:-5, 5:-5] - mu1_mu2
        
        ssim_map = ((2 * mu1_mu2 + c1) * (2 * sigma12 + c2)) / \
                   ((mu1_sq + mu2_sq + c1) * (sigma1_sq + sigma2_sq + c2))
        return ssim_map.mean()
        
    else:
        raise ValueError(f"Unknown comparison method: {method}")

def create_test_report_data() -> Dict[str, Any]:
    """
    Create test data for report generation.
    
    Returns:
        Dictionary containing test report data
    """
    return {
        'content_info': {
            'id': 'test_content_123',
            'title': 'Test Content',
            'owner': 'Test Owner',
            'registration_date': datetime.utcnow().isoformat(),
            'content_type': 'video',
            'status': 'protected'
        },
        'protection_history': [
            {
                'event_type': 'registration',
                'timestamp': (datetime.utcnow() - timedelta(days=7)).isoformat(),
                'details': 'Content registered with blockchain'
            },
            {
                'event_type': 'scan',
                'timestamp': (datetime.utcnow() - timedelta(days=5)).isoformat(),
                'details': 'Regular protection scan completed'
            },
            {
                'event_type': 'violation',
                'timestamp': (datetime.utcnow() - timedelta(days=2)).isoformat(),
                'details': 'Violation detected on Platform X',
                'platform': 'Platform X',
                'confidence': 0.85
            }
        ],
        'analytics': {
            'protection_effectiveness': {
                'detection_rate': 95.5,
                'false_positive_rate': 2.1,
                'avg_response_time': 15
            },
            'platform_distribution': [
                {'platform': 'Platform X', 'value': 45},
                {'platform': 'Platform Y', 'value': 30},
                {'platform': 'Platform Z', 'value': 25}
            ]
        }
    }
