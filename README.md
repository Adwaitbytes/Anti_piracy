# SecureStream: Advanced Content Protection System

SecureStream is an innovative content protection system that combines blockchain technology, advanced watermarking, and AI-powered detection to protect digital content from unauthorized use and distribution.

## Features

### 1. Digital Watermarking
- DCT-based invisible watermarking
- Error correction and validation
- Resistant to common manipulations
- Adjustable watermark strength

### 2. AI-Powered Piracy Detection
- ResNet50-based feature extraction
- Similarity detection
- Quick content comparison
- Manipulation detection

### 3. Secure API
- JWT authentication
- Rate limiting
- Input validation
- Comprehensive error handling

### 4. Content Management
- Single and batch content registration
- Content verification
- Piracy detection
- Content status tracking

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/SecureStream.git
cd SecureStream
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the server:
```bash
uvicorn secure_stream.api:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

### Authentication
```bash
POST /token
Content-Type: application/x-www-form-urlencoded
username=demo&password=demo
```

### Content Registration
```bash
POST /api/v1/content/register
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <file>
title: "Content Title"
owner: "Owner Name"
content_type: "image"
rights: {"license": "CC-BY"}
```

### Batch Registration
```bash
POST /api/v1/content/register/batch
Authorization: Bearer <token>
Content-Type: multipart/form-data

files: [<file1>, <file2>]
registrations: [
    {
        "title": "Content 1",
        "owner": "Owner",
        "content_type": "image",
        "rights": {"license": "CC-BY"}
    },
    ...
]
```

### Content Verification
```bash
POST /api/v1/content/verify
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <file>
```

### Piracy Detection
```bash
POST /api/v1/content/detect
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <file>
```

## Testing

Run the test suite:
```bash
cd tests
python test_all_endpoints.py
```

## Technology Stack

- **Backend**: FastAPI
- **Authentication**: JWT
- **Image Processing**: OpenCV
- **AI/ML**: TensorFlow, ResNet50
- **Testing**: Python unittest

## Future Enhancements

1. **Blockchain Integration**
   - Replace mock blockchain with actual implementation
   - Smart contracts for content registration

2. **Advanced Detection**
   - Train custom AI models
   - Add more detection methods

3. **Scalability**
   - Distributed processing
   - Cloud storage integration

4. **User Interface**
   - Web dashboard
   - Analytics and reporting

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
