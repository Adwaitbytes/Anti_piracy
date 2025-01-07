import requests
import json
import time
import cv2
import numpy as np
from PIL import Image

# API configuration
BASE_URL = "http://localhost:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZW1vIiwiZXhwIjoxNzM2MjUzMTM1fQ.sL1o3XwTf9-zqom7F7GF65WoX6tDNVwlGaoXe_mprqc"

def get_headers():
    return {
        "Authorization": f"Bearer {TOKEN}"
    }

def test_register_content():
    """Test content registration endpoint"""
    print("\n1. Testing Content Registration...")
    url = f"{BASE_URL}/api/v1/content/register"
    
    # Prepare registration data
    data = {
        "title": "Test Image",
        "owner": "Demo User",
        "content_type": "image",
        "rights": json.dumps({"license": "CC-BY"})
    }
    
    # Prepare files
    files = {
        'file': ('test_image.png', open('test_image.png', 'rb'), 'image/png')
    }
    
    # Make request
    response = requests.post(url, headers=get_headers(), data=data, files=files)
    print(f"Registration Response: {response.status_code}")
    
    if response.status_code == 200:
        # Save the watermarked image
        with open('watermarked_image.png', 'wb') as f:
            f.write(response.content)
        print("[OK] Watermarked image saved as watermarked_image.png")
        return True
    else:
        print("[ERROR] Registration failed:")
        print(response.content.decode())
    return False

def test_verify_content():
    """Test content verification endpoint"""
    print("\n2. Testing Content Verification...")
    url = f"{BASE_URL}/api/v1/content/verify"
    
    # Prepare files
    files = {
        'file': ('watermarked_image.png', open('watermarked_image.png', 'rb'), 'image/png')
    }
    
    # Make request
    response = requests.post(url, headers=get_headers(), files=files)
    print(f"Verification Response: {response.status_code}")
    result = response.json()
    print(f"Verification Result: {result}")
    return result.get('verified', False)

def test_batch_registration():
    """Test batch content registration"""
    print("\n3. Testing Batch Registration...")
    url = f"{BASE_URL}/api/v1/content/register/batch"
    
    # Create multiple test images
    images = []
    for i in range(3):
        # Create a simple image with text
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        cv2.putText(img, f'Test {i+1}', (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        filename = f'test_batch_{i}.png'
        cv2.imwrite(filename, img)
        images.append(filename)
    
    # Prepare batch registration data
    files = []
    for i, image in enumerate(images):
        files.append(
            ('files', (f'image_{i}.png', open(image, 'rb'), 'image/png'))
        )
        
    data = {
        'registrations': json.dumps([
            {
                "title": f"Batch Image {i}",
                "owner": "Demo User",
                "content_type": "image",
                "rights": {"license": "CC-BY"}
            }
            for i in range(len(images))
        ])
    }
    
    # Make request
    response = requests.post(url, headers=get_headers(), data=data, files=files)
    print(f"Batch Registration Response: {response.status_code}")
    if response.status_code == 200:
        print("[OK] Batch registration successful")
        return True
    else:
        print("[ERROR] Batch registration failed:")
        print(response.content.decode())
    return False

def test_piracy_detection():
    """Test piracy detection endpoint"""
    print("\n4. Testing Piracy Detection...")
    url = f"{BASE_URL}/api/v1/content/detect"
    
    # Load and modify the watermarked image
    img = cv2.imread('watermarked_image.png')
    
    # Apply some modifications
    modified = cv2.GaussianBlur(img, (5, 5), 0)  # Blur
    modified = cv2.resize(modified, (img.shape[1] // 2, img.shape[0] // 2))  # Resize
    modified = cv2.resize(modified, (img.shape[1], img.shape[0]))  # Resize back
    
    # Save modified image
    cv2.imwrite('modified_image.png', modified)
    
    # Prepare files
    files = {
        'file': ('modified_image.png', open('modified_image.png', 'rb'), 'image/png')
    }
    
    # Make request
    response = requests.post(url, headers=get_headers(), files=files)
    print(f"Piracy Detection Response: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Detection Result: {result}")
        return True
    else:
        print("[ERROR] Piracy detection failed:")
        print(response.content.decode())
    return False

def run_all_tests():
    """Run all API tests"""
    print("Starting SecureStream API Tests...")
    
    # Test 1: Content Registration
    if not test_register_content():
        print("[ERROR] Content registration failed, stopping tests")
        return
    
    # Test 2: Content Verification
    if not test_verify_content():
        print("[ERROR] Content verification failed")
    
    # Test 3: Batch Registration
    if not test_batch_registration():
        print("[ERROR] Batch registration failed")
    
    # Test 4: Piracy Detection
    if not test_piracy_detection():
        print("[ERROR] Piracy detection failed")
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    run_all_tests()
