import cv2
import numpy as np
from PIL import Image
import io
from typing import Tuple, Optional
import random
import string

class DigitalWatermarker:
    def __init__(self):
        self.watermark_size = 32
        
    def _generate_watermark(self, content_id: str) -> str:
        """Generate a unique watermark string based on content ID."""
        return f"SecureStream_{content_id}"[:self.watermark_size].ljust(self.watermark_size, '0')
    
    def embed_watermark(self, image: Image.Image, watermark: str) -> Image.Image:
        """
        Embed a text watermark into an image using simple LSB steganography
        """
        try:
            print(f"Starting watermark embedding process for watermark: {watermark}")
            
            # Convert image to RGB
            if image.mode != 'RGB':
                image = image.convert('RGB')
                print(f"Converted image to RGB mode: {image.mode}")
            
            # Get image data
            width, height = image.size
            pixels = list(image.getdata())
            print(f"Image size: {width}x{height}, Total pixels: {len(pixels)}")
            
            # Convert watermark to binary
            watermark_bytes = watermark.encode('utf-8')
            watermark_length = len(watermark_bytes)
            print(f"Watermark length: {watermark_length} bytes")
            
            # First embed the length (4 bytes)
            length_bytes = watermark_length.to_bytes(4, byteorder='big')
            print(f"Length bytes: {[hex(b) for b in length_bytes]}")
            
            # Create new pixel data
            new_pixels = []
            pixel_index = 0
            
            # Embed length
            for length_byte in length_bytes:
                for bit_index in range(8):
                    bit = (length_byte >> (7 - bit_index)) & 1
                    r, g, b = pixels[pixel_index]
                    # Modify least significant bit of red channel
                    r = (r & 0xFE) | bit
                    new_pixels.append((r, g, b))
                    pixel_index += 1
            print(f"Embedded length in first {pixel_index} pixels")
            
            # Embed watermark
            for byte in watermark_bytes:
                for bit_index in range(8):
                    bit = (byte >> (7 - bit_index)) & 1
                    r, g, b = pixels[pixel_index]
                    # Modify least significant bit of red channel
                    r = (r & 0xFE) | bit
                    new_pixels.append((r, g, b))
                    pixel_index += 1
            print(f"Embedded watermark using {pixel_index} pixels total")
            
            # Add remaining pixels unchanged
            new_pixels.extend(pixels[pixel_index:])
            
            # Create new image
            new_image = Image.new('RGB', (width, height))
            new_image.putdata(new_pixels)
            
            print(f"Watermark embedded successfully: {watermark}")
            return new_image
            
        except Exception as e:
            print(f"Error embedding watermark: {str(e)}")
            raise

    def extract_watermark(self, image: Image.Image) -> str:
        """
        Extract the watermark from an image
        """
        try:
            print("Starting watermark extraction process")
            
            # Convert image to RGB
            if image.mode != 'RGB':
                image = image.convert('RGB')
                print(f"Converted image to RGB mode: {image.mode}")
            
            width, height = image.size
            pixels = list(image.getdata())
            print(f"Image size: {width}x{height}, Total pixels: {len(pixels)}")
            
            # First extract the length (4 bytes = 32 bits)
            length_bits = []
            for i in range(32):
                r, _, _ = pixels[i]
                length_bits.append(r & 1)
            
            # Convert bits to length
            length_bytes = bytearray()
            for i in range(0, 32, 8):
                byte = 0
                for j in range(8):
                    byte = (byte << 1) | length_bits[i + j]
                length_bytes.append(byte)
            
            length = int.from_bytes(length_bytes, byteorder='big')
            print(f"Extracted length bytes: {[hex(b) for b in length_bytes]}")
            print(f"Decoded length: {length} bytes")
            
            if length <= 0 or length > 1000:  # Sanity check
                print(f"Invalid length: {length}")
                return ""
            
            # Extract watermark bits
            watermark_bits = []
            for i in range(length * 8):
                r, _, _ = pixels[32 + i]
                watermark_bits.append(r & 1)
            
            # Convert bits to bytes
            watermark_bytes = bytearray()
            for i in range(0, len(watermark_bits), 8):
                byte = 0
                for j in range(8):
                    if i + j < len(watermark_bits):
                        byte = (byte << 1) | watermark_bits[i + j]
                watermark_bytes.append(byte)
            
            try:
                # Convert bytes to string
                watermark = watermark_bytes.decode('utf-8')
                print(f"Successfully extracted watermark: '{watermark}'")
                return watermark
            except UnicodeDecodeError as e:
                print(f"Error decoding watermark bytes: {watermark_bytes}")
                return ""
            
        except Exception as e:
            print(f"Error extracting watermark: {str(e)}")
            return ""

    def add_watermark(self, image_data: bytes, content_id: str) -> Tuple[bytes, str]:
        """Add a watermark to an image"""
        try:
            # Open the image
            image = Image.open(io.BytesIO(image_data))
            
            # Generate watermark string
            watermark = self._generate_watermark(content_id)
            print(f"Generated watermark: {watermark}")
            
            # Embed watermark
            watermarked_image = self.embed_watermark(image, watermark)
            
            # Save to bytes
            output = io.BytesIO()
            watermarked_image.save(output, format='PNG')
            return output.getvalue(), watermark
            
        except Exception as e:
            print(f"Error in add_watermark: {str(e)}")
            raise

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
