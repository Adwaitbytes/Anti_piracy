import cv2
import numpy as np
from typing import Tuple, Optional

class WatermarkEngine:
    """Engine for embedding and extracting watermarks from video frames."""
    
    def __init__(self, block_size: int = 8, strength: float = 80.0):
        """
        Initialize watermark engine.
        
        Args:
            block_size: Size of DCT blocks
            strength: Strength of watermark
        """
        self.block_size = block_size
        self.strength = strength
        # Generate a random key for this instance
        self.key = np.random.randint(0, 2, 128, dtype=np.uint8)

    def _encode_message(self, message: str) -> bytes:
        """
        Encode message with error correction.
        """
        # Convert message to bytes
        message_bytes = message.encode('utf-8')
        
        # Add length prefix (2 bytes)
        length = len(message_bytes)
        length_bytes = length.to_bytes(2, byteorder='big')
        
        # Add simple checksum (1 byte)
        checksum = sum(message_bytes) % 256
        checksum_byte = bytes([checksum])
        
        # Combine all parts
        data = length_bytes + checksum_byte + message_bytes
        
        # Convert to bit array for embedding
        bits = []
        for byte in data:
            for i in range(8):
                bits.append((byte >> (7-i)) & 1)
        
        return bits

    def _decode_message(self, data: list) -> str:
        """
        Decode message with error correction.
        """
        if len(data) < 24:  # Minimum 3 bytes (2 for length, 1 for checksum)
            return None
            
        try:
            # Convert bit array to bytes
            bytes_data = bytearray()
            for i in range(0, len(data), 8):
                byte = 0
                for j in range(8):
                    if i + j < len(data):
                        byte = (byte << 1) | data[i + j]
                bytes_data.append(byte)
            
            # Extract length (first 2 bytes)
            length = int.from_bytes(bytes_data[:2], byteorder='big')
            
            # Extract checksum (next byte)
            stored_checksum = bytes_data[2]
            
            # Extract message
            message_bytes = bytes_data[3:3+length]
            
            # Verify checksum
            calculated_checksum = sum(message_bytes) % 256
            if calculated_checksum != stored_checksum:
                return None
            
            # Decode message
            return message_bytes.decode('utf-8')
            
        except Exception:
            return None

    def _repeat_key(self, key: np.ndarray, length: int) -> np.ndarray:
        """Repeat key to match required length."""
        repeats = (length + len(key) - 1) // len(key)
        return np.tile(key, repeats)[:length]

    def embed_watermark(self, frame: np.ndarray, watermark_data: str, strength: float = None) -> np.ndarray:
        """
        Embed watermark into a frame.
        
        Args:
            frame: Input frame
            watermark_data: Watermark data to embed
            strength: Optional watermark strength override
            
        Returns:
            Watermarked frame
        """
        # Use provided strength or default
        embed_strength = strength if strength is not None else self.strength
        
        # Convert frame to YUV color space
        yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
        
        # Get Y channel
        y = yuv[:, :, 0]
        
        # Encode watermark data
        watermark = self._encode_message(watermark_data)
        
        # Apply DCT to blocks
        height, width = y.shape
        watermarked = y.copy()
        
        block_positions = []
        for i in range(0, height - self.block_size + 1, self.block_size):
            for j in range(0, width - self.block_size + 1, self.block_size):
                block = y[i:i + self.block_size, j:j + self.block_size].astype(float)
                dct_block = cv2.dct(block)
                block_positions.append((i, j))
        
        # Embed watermark bits
        bits_per_block = 3
        for idx, bit in enumerate(watermark):
            if idx * bits_per_block >= len(block_positions):
                break
                
            for offset in range(bits_per_block):
                if idx * bits_per_block + offset >= len(block_positions):
                    break
                    
                i, j = block_positions[idx * bits_per_block + offset]
                block = y[i:i + self.block_size, j:j + self.block_size].astype(float)
                dct_block = cv2.dct(block)
                
                # Modify mid-frequency coefficients
                if bit:
                    dct_block[4, 4] = abs(dct_block[4, 4]) + embed_strength
                    dct_block[4, 5] = abs(dct_block[4, 5]) + embed_strength
                    dct_block[5, 4] = abs(dct_block[5, 4]) + embed_strength
                else:
                    dct_block[4, 4] = -abs(dct_block[4, 4]) - embed_strength
                    dct_block[4, 5] = -abs(dct_block[4, 5]) - embed_strength
                    dct_block[5, 4] = -abs(dct_block[5, 4]) - embed_strength
                
                # Apply inverse DCT
                watermarked[i:i + self.block_size, j:j + self.block_size] = cv2.idct(dct_block)
        
        # Reconstruct image
        yuv[:, :, 0] = watermarked
        watermarked_frame = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
        
        return watermarked_frame

    def extract_watermark(self, frame: np.ndarray, watermark_length: int) -> str:
        """
        Extract watermark from a frame.
        
        Args:
            frame: Input frame
            watermark_length: Expected length of watermark data
            
        Returns:
            Extracted watermark data
        """
        # Convert to YUV color space
        yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
        y = yuv[:, :, 0]
        
        # Get block positions
        height, width = y.shape
        block_positions = []
        for i in range(0, height - self.block_size + 1, self.block_size):
            for j in range(0, width - self.block_size + 1, self.block_size):
                block_positions.append((i, j))
        
        # Extract watermark bits
        bits_per_block = 3
        extracted_bits = []
        required_blocks = (watermark_length * 8 + bits_per_block - 1) // bits_per_block
        
        for idx in range(required_blocks):
            if idx * bits_per_block >= len(block_positions):
                break
                
            block_votes = []
            for offset in range(bits_per_block):
                if idx * bits_per_block + offset >= len(block_positions):
                    break
                    
                i, j = block_positions[idx * bits_per_block + offset]
                block = y[i:i + self.block_size, j:j + self.block_size].astype(float)
                dct_block = cv2.dct(block)
                
                # Check mid-frequency coefficients
                vote = (
                    int(dct_block[4, 4] > 0) +
                    int(dct_block[4, 5] > 0) +
                    int(dct_block[5, 4] > 0)
                )
                block_votes.append(vote > 1)  # Majority vote
            
            # Take majority vote across blocks
            if block_votes:
                bit = sum(block_votes) > len(block_votes) // 2
                extracted_bits.append(bit)
        
        # Convert bits to bytes
        if not extracted_bits:
            return None
            
        # Pad with zeros if needed
        while len(extracted_bits) % 8 != 0:
            extracted_bits.append(False)
        
        # Convert bits to bytes
        extracted_bytes = []
        for i in range(0, len(extracted_bits), 8):
            byte = 0
            for j in range(8):
                if i + j < len(extracted_bits):
                    byte = (byte << 1) | int(extracted_bits[i + j])
            extracted_bytes.append(byte)
        
        try:
            # Decode the message
            decoded = self._decode_message(extracted_bytes)
            return decoded if decoded else None
        except:
            return None

    def add_robust_watermark(self, frame: np.ndarray, text: str) -> np.ndarray:
        """
        Add a more robust watermark using multiple techniques.

        Args:
            frame: Input video frame
            text: Watermark text to embed

        Returns:
            Frame with robust watermark
        """
        # First apply DCT watermark
        frame = self.embed_watermark(frame, text)
        
        # Add spatial domain watermark
        h, w = frame.shape[:2]
        watermark = np.zeros((h, w), dtype=np.float32)
        cv2.putText(watermark, text, (w//4, h//2), 
                   cv2.FONT_HERSHEY_SIMPLEX, 2, 1, 2)
        
        # Expand watermark to match frame channels
        watermark = np.stack([watermark] * 3, axis=2)
        
        # Convert frame to float32 for blending
        frame_float = frame.astype(np.float32)
        
        # Blend watermark with frame
        alpha = 0.1
        blended = cv2.addWeighted(frame_float, 1-alpha, watermark, alpha, 0)
        
        return np.clip(blended, 0, 255).astype(np.uint8)

class WatermarkValidator:
    """Validator for checking watermark integrity."""
    
    def validate_watermark(self, frame: np.ndarray, expected_text: str) -> bool:
        """
        Validate if frame contains expected watermark.
        
        Args:
            frame: Input frame to check
            expected_text: Expected watermark text
            
        Returns:
            True if watermark is valid, False otherwise
        """
        engine = WatermarkEngine()
        extracted = engine.extract_watermark(frame, len(expected_text) * 8)
        return expected_text in extracted

    def verify_watermark(self, original_frame: np.ndarray, watermarked_frame: np.ndarray) -> float:
        """
        Verify watermark by comparing original and watermarked frames.
        
        Args:
            original_frame: Original video frame
            watermarked_frame: Watermarked video frame
            
        Returns:
            Similarity score between frames (0-1)
        """
        # Convert frames to grayscale
        original_gray = cv2.cvtColor(original_frame, cv2.COLOR_BGR2GRAY)
        watermarked_gray = cv2.cvtColor(watermarked_frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate structural similarity index
        score = cv2.matchTemplate(original_gray, watermarked_gray, cv2.TM_CCOEFF_NORMED)[0][0]
        
        return float(score)
