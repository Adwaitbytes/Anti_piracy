import requests
import json

# API configuration
BASE_URL = "http://localhost:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZW1vIiwiZXhwIjoxNzM2MjUzMTM1fQ.sL1o3XwTf9-zqom7F7GF65WoX6tDNVwlGaoXe_mprqc"

def test_register_content():
    """Test content registration endpoint"""
    url = f"{BASE_URL}/api/v1/content/register"
    headers = {
        "Authorization": f"Bearer {TOKEN}"
    }
    
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
    response = requests.post(url, headers=headers, data=data, files=files)
    print(f"Registration Response: {response.status_code}")
    
    if response.status_code == 200:
        # Save the watermarked image
        with open('watermarked_image.png', 'wb') as f:
            f.write(response.content)
        print("Watermarked image saved as watermarked_image.png")
        return True
    else:
        print(response.content.decode())
    return False

def test_verify_content():
    """Test content verification endpoint"""
    url = f"{BASE_URL}/api/v1/content/verify"
    headers = {
        "Authorization": f"Bearer {TOKEN}"
    }
    
    # Prepare files
    files = {
        'file': ('watermarked_image.png', open('watermarked_image.png', 'rb'), 'image/png')
    }
    
    # Make request
    response = requests.post(url, headers=headers, files=files)
    print(f"\nVerification Response: {response.status_code}")
    print(response.json())

if __name__ == "__main__":
    print("Testing SecureStream API...")
    if test_register_content():
        test_verify_content()
