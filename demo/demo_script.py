import requests
import json
import cv2
import numpy as np
import time
import os
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
DEMO_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(DEMO_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_demo_image(text, filename):
    """Create a demo image with text"""
    # Create a new image with a gradient background
    width, height = 800, 400
    image = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Create gradient background
    for y in range(height):
        for x in range(width):
            image[y, x] = [
                int(255 * (x / width)),
                int(255 * (y / height)),
                int(255 * ((x + y) / (width + height)))
            ]
    
    # Add text using OpenCV
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.5
    thickness = 2
    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
    text_x = (width - text_size[0]) // 2
    text_y = (height + text_size[1]) // 2
    
    # Add text shadow
    cv2.putText(image, text, (text_x + 2, text_y + 2), font, font_scale, (0, 0, 0), thickness + 2)
    cv2.putText(image, text, (text_x, text_y), font, font_scale, (255, 255, 255), thickness)
    
    # Add timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(image, timestamp, (10, height - 20), font, 0.5, (255, 255, 255), 1)
    
    # Save image
    cv2.imwrite(os.path.join(OUTPUT_DIR, filename), image)
    return os.path.join(OUTPUT_DIR, filename)

def get_auth_token():
    """Get authentication token"""
    print("\n1. Getting authentication token...")
    url = f"{BASE_URL}/token"
    response = requests.post(
        url,
        data={"username": "demo", "password": "demo"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    token = response.json()["access_token"]
    print("✓ Authentication successful")
    return token

def register_content(token, image_path):
    """Register content with watermark"""
    print("\n2. Registering content...")
    url = f"{BASE_URL}/api/v1/content/register"
    
    # Prepare registration data
    data = {
        "title": "Demo Content",
        "owner": "Demo User",
        "content_type": "image",
        "rights": json.dumps({"license": "CC-BY"})
    }
    
    # Prepare files
    files = {
        'file': ('demo.png', open(image_path, 'rb'), 'image/png')
    }
    
    # Make request
    response = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}"},
        data=data,
        files=files
    )
    
    if response.status_code == 200:
        # Save watermarked image
        watermarked_path = os.path.join(OUTPUT_DIR, "watermarked.png")
        with open(watermarked_path, 'wb') as f:
            f.write(response.content)
        print("✓ Content registered and watermarked")
        return watermarked_path
    else:
        print("✗ Registration failed:", response.content.decode())
        return None

def verify_content(token, image_path):
    """Verify content watermark"""
    print("\n3. Verifying content...")
    url = f"{BASE_URL}/api/v1/content/verify"
    
    files = {
        'file': ('verify.png', open(image_path, 'rb'), 'image/png')
    }
    
    response = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}"},
        files=files
    )
    
    print("Verification result:", response.json())
    return response.status_code == 200

def test_piracy_detection(token, original_path):
    """Test piracy detection"""
    print("\n4. Testing piracy detection...")
    
    # Create a modified version of the image
    img = cv2.imread(original_path)
    
    # Apply some modifications
    modified = cv2.GaussianBlur(img, (5, 5), 0)  # Blur
    modified = cv2.resize(modified, (img.shape[1] // 2, img.shape[0] // 2))  # Resize down
    modified = cv2.resize(modified, (img.shape[1], img.shape[0]))  # Resize up
    
    # Save modified image
    modified_path = os.path.join(OUTPUT_DIR, "modified.png")
    cv2.imwrite(modified_path, modified)
    
    # Test detection
    url = f"{BASE_URL}/api/v1/content/detect"
    files = {
        'file': ('modified.png', open(modified_path, 'rb'), 'image/png')
    }
    
    response = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}"},
        files=files
    )
    
    print("Detection result:", response.json())
    return response.status_code == 200

def run_demo():
    """Run complete demo"""
    print("Starting SecureStream Demo...")
    
    # Create demo image
    original_path = create_demo_image("SecureStream Demo", "original.png")
    print("✓ Created demo image:", original_path)
    
    # Get authentication token
    token = get_auth_token()
    
    # Register content
    watermarked_path = register_content(token, original_path)
    if not watermarked_path:
        return
    
    # Verify content
    verify_content(token, watermarked_path)
    
    # Test piracy detection
    test_piracy_detection(token, watermarked_path)
    
    print("\nDemo completed! Check the output directory for generated images.")

if __name__ == "__main__":
    run_demo()
