import cv2
import numpy as np
from PIL import Image
import io
from typing import Tuple, Optional
import random
import string

class DigitalWatermarker:
    def __init__(self):
        self.watermark_size = 32  # Size of the watermark bit string
        
    def _generate_watermark(self, content_id: str) -> str:
        """Generate a unique watermark string based on content ID."""
        # Use content ID and add some random chars to make it harder to remove
        random_chars = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        base = content_id[:24] + random_chars  # Ensure total length is 32
        return base.ljust(self.watermark_size, '0')
    
    def embed_watermark(self, image: Image.Image, watermark: str) -> Image.Image:
        """
        Embed a text watermark into an image using LSB steganography
        """
        # Convert image to numpy array
        img_array = np.array(image)
        
        # Convert watermark to binary
        watermark_binary = ''.join(format(ord(c), '08b') for c in watermark)
        watermark_length = len(watermark_binary)
        
        # Embed watermark length first (32 bits)
        length_binary = format(watermark_length, '032b')
        
        # Flatten the image array
        flat_img = img_array.flatten()
        
        # Embed length
        for i in range(32):
            flat_img[i] = (flat_img[i] & 0xFE) | int(length_binary[i])
        
        # Embed watermark
        for i in range(watermark_length):
            flat_img[i + 32] = (flat_img[i + 32] & 0xFE) | int(watermark_binary[i])
        
        # Reshape back to original dimensions
        watermarked = flat_img.reshape(img_array.shape)
        
        return Image.fromarray(watermarked)

    def extract_watermark(self, image: Image.Image) -> str:
        """
        Extract the watermark from an image
        """
        # Convert to numpy array
        img_array = np.array(image)
        flat_img = img_array.flatten()
        
        # Extract length first
        length_binary = ''.join(str(pixel & 1) for pixel in flat_img[:32])
        length = int(length_binary, 2)
        
        # Extract watermark
        watermark_binary = ''.join(str(pixel & 1) for pixel in flat_img[32:32 + length])
        
        # Convert binary to text
        watermark = ''
        for i in range(0, len(watermark_binary), 8):
            byte = watermark_binary[i:i+8]
            if len(byte) == 8:  # Ensure we have a complete byte
                watermark += chr(int(byte, 2))
        
        return watermark

    def add_watermark(self, image_data: bytes, content_id: str) -> Tuple[bytes, str]:
        """Add a digital watermark to an image."""
        # Convert bytes to image
        image = Image.open(io.BytesIO(image_data))
        image = image.convert('RGB')
        
        # Generate watermark
        watermark = self._generate_watermark(content_id)
        
        # Embed watermark
        watermarked_image = self.embed_watermark(image, watermark)
        
        # Convert back to bytes
        img_byte_arr = io.BytesIO()
        watermarked_image.save(img_byte_arr, format=image.format or 'PNG')
        
        return img_byte_arr.getvalue(), watermark
    
    def remove_watermark(self, image_data: bytes) -> Optional[str]:
        """Extract watermark from an image."""
        try:
            # Convert bytes to image
            image = Image.open(io.BytesIO(image_data))
            image = image.convert('RGB')
            
            # Extract watermark
            watermark = self.extract_watermark(image)
            
            return watermark
        except Exception:
            return None
