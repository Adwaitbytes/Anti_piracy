# SecureStream - Advanced Content Protection Platform

SecureStream is a cutting-edge content protection platform that combines blockchain technology, digital watermarking, and AI-powered piracy detection to protect digital content.

## Features

- **Blockchain Integration**: Content ownership is registered and verified on the EDU Chain Testnet
- **Digital Watermarking**: Invisible watermarks embedded in content using LSB steganography
- **AI-Powered Detection**: Advanced content matching using ResNet50 neural network
- **User-Friendly Interface**: Modern UI built with FastAPI and Tailwind CSS

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env`:
```ini
CONTRACT_ADDRESS=0x4b86e7fab7E5FF8A44fea97d2a830875272e1Ca9
PRIVATE_KEY=your_private_key_here
WEB3_PROVIDER_URL=https://rpc.open-campus-codex.gelato.digital
NETWORK_ID=656476
```

3. Run the application:
```bash
python -m uvicorn index:app --reload
```

4. Open http://localhost:8000 in your browser

## Usage

### Protecting Content
1. Click "Upload" in the navigation
2. Fill in the content details
3. Select your file
4. Click "Protect Content"

### Verifying Ownership
1. Click "Verify" in the navigation
2. Upload the content you want to verify
3. The system will extract the watermark and check the blockchain

### Detecting Piracy
1. Click "Detect" in the navigation
2. Upload the suspicious content
3. The AI system will compare it with protected content

## Technical Details

### Smart Contract
- Deployed on EDU Chain Testnet
- Handles content registration and verification
- Stores ownership information and content status

### Watermarking
- Uses LSB (Least Significant Bit) steganography
- Embeds unique identifiers in content
- Resistant to basic modifications

### AI Detection
- Uses ResNet50 for feature extraction
- Generates unique fingerprints for content
- High accuracy in detecting modified versions

## Security

- Private keys are stored securely in environment variables
- All blockchain transactions are signed locally
- Content fingerprints are stored separately from content

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
