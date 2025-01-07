# SecureStream Demo Script

## Setup (Before Recording)
1. Start the API server:
   ```bash
   uvicorn secure_stream.api:app --reload --host 0.0.0.0 --port 8000
   ```

2. Open a new terminal for the demo

## Recording Steps

1. **Introduction (30 seconds)**
   - "Welcome to SecureStream, an advanced content protection system"
   - "Today we'll demonstrate its key features:"
     - Digital watermarking
     - Content verification
     - Piracy detection

2. **Run Demo Script (2-3 minutes)**
   ```bash
   cd demo
   python demo_script.py
   ```
   - Explain each step as it happens:
     - Authentication
     - Content registration
     - Watermark embedding
     - Content verification
     - Piracy detection

3. **Show Results (1 minute)**
   - Open the output directory
   - Show original image
   - Show watermarked image
   - Show modified image
   - Explain detection results

4. **API Documentation (30 seconds)**
   - Open browser to http://localhost:8000/docs
   - Show available endpoints
   - Demonstrate interactive documentation

5. **Conclusion (30 seconds)**
   - Recap key features
   - Highlight security aspects
   - Mention scalability and future enhancements

Total video length: ~5 minutes

## Key Points to Emphasize
- Invisible yet robust watermarking
- AI-powered detection system
- Secure API with authentication
- Scalable architecture
- Easy integration

## Technical Requirements
- Screen resolution: 1920x1080 (minimum)
- Clear terminal font
- Browser window ready
- All dependencies installed
