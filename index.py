from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from web3 import Web3
from dotenv import load_dotenv
import os
import json
import uuid
import numpy as np
from PIL import Image
import io
import logging
from secure_stream.watermarking.watermarker import DigitalWatermarker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Web3 setup
WEB3_PROVIDER_URL = os.getenv('WEB3_PROVIDER_URL')
NETWORK_ID = int(os.getenv('NETWORK_ID'))
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS')

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)

# Load contract ABI
with open("secure_stream/blockchain/contracts/ContentRegistry.abi", 'r') as f:
    contract_abi = json.load(f)
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)

# Initialize FastAPI app
app = FastAPI(
    title="SecureStream API",
    description="Content Protection System"
)

# Initialize templates
templates = Jinja2Templates(directory="templates")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create necessary directories
os.makedirs("static", exist_ok=True)
os.makedirs("fingerprints", exist_ok=True)

def generate_fingerprint(image_data: bytes) -> np.ndarray:
    """Generate a fingerprint from image data"""
    try:
        # Convert image data to numpy array
        image = Image.open(io.BytesIO(image_data)).convert('RGB')  # Convert to RGB
        image = image.resize((256, 256))  # Larger size for better detail
        
        # Convert to numpy array and split channels
        img_array = np.array(image)
        r, g, b = img_array[:,:,0], img_array[:,:,1], img_array[:,:,2]
        
        # Calculate average of RGB channels
        avg_channel = (r.astype(float) + g.astype(float) + b.astype(float)) / 3
        
        # Apply basic normalization
        avg_channel = (avg_channel - avg_channel.mean()) / (avg_channel.std() + 1e-8)
        
        print(f"Generated fingerprint shape: {avg_channel.shape}")
        return avg_channel
        
    except Exception as e:
        print(f"Error in generate_fingerprint: {str(e)}")
        raise

def calculate_similarity(fp1: np.ndarray, fp2: np.ndarray) -> float:
    """Calculate similarity between two fingerprints"""
    try:
        # Ensure same shape
        if fp1.shape != fp2.shape:
            print(f"Shape mismatch: fp1={fp1.shape}, fp2={fp2.shape}")
            min_shape = (min(fp1.shape[0], fp2.shape[0]), min(fp1.shape[1], fp2.shape[1]))
            fp1 = fp1[:min_shape[0], :min_shape[1]]
            fp2 = fp2[:min_shape[0], :min_shape[1]]
        
        # Normalize arrays
        fp1_norm = (fp1 - fp1.mean()) / (fp1.std() + 1e-8)
        fp2_norm = (fp2 - fp2.mean()) / (fp2.std() + 1e-8)
        
        # Calculate correlation coefficient
        correlation = np.corrcoef(fp1_norm.flatten(), fp2_norm.flatten())[0, 1]
        correlation_score = (correlation + 1) / 2  # Convert to [0,1] range
        
        # Calculate MSE
        mse = np.mean((fp1_norm - fp2_norm) ** 2)
        mse_score = 1 / (1 + mse)
        
        # Calculate histogram similarity
        hist1, _ = np.histogram(fp1_norm, bins=50)
        hist2, _ = np.histogram(fp2_norm, bins=50)
        hist1 = hist1.astype(float) / hist1.sum()
        hist2 = hist2.astype(float) / hist2.sum()
        hist_sim = 1 - np.mean(np.abs(hist1 - hist2))
        
        # Combine scores with weights
        final_score = (0.5 * correlation_score + 
                      0.3 * mse_score + 
                      0.2 * hist_sim)
        
        print(f"Similarity scores - Correlation: {correlation_score:.3f}, MSE: {mse_score:.3f}, Histogram: {hist_sim:.3f}, Final: {final_score:.3f}")
        return float(final_score)
        
    except Exception as e:
        print(f"Error in calculate_similarity: {str(e)}")
        return 0.0

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/register/")
async def register_content(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(...)
):
    """Register new content"""
    try:
        # Read image data
        image_data = await file.read()
        
        # Generate content ID and fingerprint
        content_id = str(uuid.uuid4())
        fingerprint = generate_fingerprint(image_data)
        np.save(f"fingerprints/{content_id}.npy", fingerprint)
        
        # Add watermark
        watermarker = DigitalWatermarker()
        watermarked_image, watermark = watermarker.add_watermark(image_data, content_id)
        
        # Save watermarked image
        output_path = f"static/{content_id}_watermarked.png"
        with open(output_path, "wb") as f:
            f.write(watermarked_image)
        
        try:
            # Get current nonce
            nonce = w3.eth.get_transaction_count(account.address)
            
            # Get current gas price and increase it by 20%
            gas_price = int(w3.eth.gas_price * 1.2)
            logger.info(f"Using gas price: {gas_price}")
            
            # Create fingerprint hash
            fingerprint_hash = w3.keccak(fingerprint.tobytes()).hex()
            
            # Estimate gas for the transaction
            try:
                estimated_gas = contract.functions.registerContent(
                    content_id,
                    fingerprint_hash,
                    watermark
                ).estimate_gas({
                    'from': account.address,
                    'nonce': nonce
                })
                gas_limit = int(estimated_gas * 1.5)  # Add 50% buffer
                logger.info(f"Estimated gas: {estimated_gas}, Using gas limit: {gas_limit}")
            except Exception as e:
                logger.warning(f"Gas estimation failed: {str(e)}, using default gas limit")
                gas_limit = 8000000  # Higher default gas limit
            
            # Build transaction
            tx = contract.functions.registerContent(
                content_id,
                fingerprint_hash,
                watermark
            ).build_transaction({
                'chainId': NETWORK_ID,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'nonce': nonce,
                'from': account.address
            })
            
            logger.info(f"Transaction built with gas limit: {gas_limit}, gas price: {gas_price}")
            
            # Sign and send transaction
            signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            logger.info(f"Transaction sent with hash: {tx_hash.hex()}")
            
            # Wait for receipt
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            logger.info(f"Transaction receipt received: {receipt}")
            
            if receipt['status'] != 1:
                raise Exception("Transaction failed")
            
            return JSONResponse({
                "success": True,
                "content_id": content_id,
                "transaction_hash": tx_hash.hex(),
                "watermarked_image": f"{content_id}_watermarked.png",
                "watermark": watermark,
                "message": "Content registered successfully"
            })
            
        except Exception as e:
            logger.error(f"Blockchain error: {str(e)}")
            error_msg = str(e).lower()
            if "gas too low" in error_msg or "intrinsic gas too low" in error_msg:
                raise HTTPException(
                    status_code=500,
                    detail="Transaction failed: Gas limit too low. Please try again."
                )
            elif "nonce too low" in error_msg:
                raise HTTPException(
                    status_code=500,
                    detail="Transaction failed: Nonce issue. Please try again."
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Blockchain error: {str(e)}"
                )
            
    except Exception as e:
        logger.error(f"Error registering content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/verify/")
async def verify_content(file: UploadFile = File(...)):
    """Verify if content is registered and authentic"""
    try:
        # Read image data
        image_data = await file.read()
        
        # Extract watermark
        watermarker = DigitalWatermarker()
        watermark = watermarker.remove_watermark(image_data)
        
        if not watermark:
            return JSONResponse({
                "status": "unverified",
                "message": "No watermark found in the image"
            })
        
        # Extract content ID (remove the prefix and any trailing zeros)
        content_id = watermark.replace("SecureStream_", "").rstrip('0')
        logger.info(f"Extracted content ID: {content_id}")
        
        try:
            # Get content details from blockchain
            content = contract.functions.getContent(content_id).call()
            tx_hash = contract.functions.getTransactionHash(content_id).call()
            owner = contract.functions.getContentOwner(content_id).call()
            
            # Calculate fingerprint similarity
            similarity = 1.0
            if os.path.exists(f"fingerprints/{content_id}.npy"):
                stored_fp = np.load(f"fingerprints/{content_id}.npy")
                current_fp = generate_fingerprint(image_data)
                similarity = calculate_similarity(stored_fp, current_fp)
            
            return JSONResponse({
                "status": "verified",
                "content_id": content_id,
                "transaction_hash": tx_hash,
                "owner": owner,
                "watermark": watermark,
                "similarity": similarity,
                "registration_time": content[2],
                "message": "Content verified successfully"
            })
            
        except Exception as e:
            logger.error(f"Blockchain query error: {str(e)}")
            # Even if blockchain query fails, return watermark info
            return JSONResponse({
                "status": "partial",
                "content_id": content_id,
                "watermark": watermark,
                "message": "Content has a valid watermark but blockchain data is unavailable"
            })
            
    except Exception as e:
        logger.error(f"Verification error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/detect/")
async def detect_piracy(file: UploadFile = File(...)):
    """Detect potential piracy in uploaded content"""
    try:
        print("\n=== Starting Piracy Detection ===")
        
        # Read image data
        image_data = await file.read()
        results = []
        
        # Generate fingerprint for uploaded image
        print("Generating fingerprint for uploaded image...")
        current_fp = generate_fingerprint(image_data)
        
        # Try fingerprint-based detection first
        print("\nStarting fingerprint comparison...")
        if os.path.exists("fingerprints"):
            fingerprint_files = [f for f in os.listdir("fingerprints") if f.endswith('.npy')]
            print(f"Found {len(fingerprint_files)} fingerprint files to compare")
            
            for fp_file in fingerprint_files:
                try:
                    fp_path = os.path.join("fingerprints", fp_file)
                    print(f"\nComparing with fingerprint: {fp_file}")
                    
                    # Load stored fingerprint
                    stored_fp = np.load(fp_path)
                    print(f"Loaded fingerprint shape: {stored_fp.shape}")
                    
                    # Calculate similarity
                    similarity = calculate_similarity(stored_fp, current_fp)
                    print(f"Similarity score: {similarity}")
                    
                    # Check if similar enough
                    if similarity >= 0.80:  # High threshold for accuracy
                        print(f"Match found! Similarity: {similarity}")
                        content_id = fp_file.replace(".npy", "")
                        
                        try:
                            # Get blockchain data
                            content = contract.functions.getContent(content_id).call()
                            tx_hash = contract.functions.getTransactionHash(content_id).call()
                            owner = contract.functions.getContentOwner(content_id).call()
                            
                            results.append({
                                "detection_type": "fingerprint",
                                "content_id": content_id,
                                "transaction_hash": tx_hash,
                                "owner": owner,
                                "similarity": similarity,
                                "registration_time": content[2]
                            })
                            print(f"Added match to results: {content_id}")
                        except Exception as e:
                            print(f"Blockchain query error: {str(e)}")
                            results.append({
                                "detection_type": "fingerprint",
                                "content_id": content_id,
                                "similarity": similarity,
                                "message": "Similar content found but blockchain data unavailable"
                            })
                except Exception as e:
                    print(f"Error processing fingerprint {fp_file}: {str(e)}")
                    continue
        
        # Then try watermark-based detection
        print("\nChecking for watermark...")
        watermarker = DigitalWatermarker()
        watermark = watermarker.remove_watermark(image_data)
        
        if watermark:
            print(f"Found watermark: {watermark}")
            content_id = watermark.replace("SecureStream_", "").rstrip('0')
            
            if not any(r.get("content_id") == content_id for r in results):
                try:
                    content = contract.functions.getContent(content_id).call()
                    tx_hash = contract.functions.getTransactionHash(content_id).call()
                    owner = contract.functions.getContentOwner(content_id).call()
                    
                    results.append({
                        "detection_type": "watermark",
                        "content_id": content_id,
                        "transaction_hash": tx_hash,
                        "owner": owner,
                        "watermark": watermark,
                        "similarity": 1.0,
                        "registration_time": content[2]
                    })
                    print("Added watermark match to results")
                except Exception as e:
                    print(f"Blockchain query error for watermark: {str(e)}")
                    results.append({
                        "detection_type": "watermark",
                        "content_id": content_id,
                        "watermark": watermark,
                        "similarity": 1.0,
                        "message": "Watermark detected but blockchain data unavailable"
                    })
        
        if results:
            print(f"\nFound {len(results)} matches!")
            results.sort(key=lambda x: x.get("similarity", 0), reverse=True)
            return JSONResponse({
                "detected": True,
                "matches": results,
                "message": f"Found {len(results)} matching content(s)"
            })
        
        print("\nNo matches found")
        return JSONResponse({
            "detected": False,
            "message": "No protected content detected"
        })
        
    except Exception as e:
        print(f"Detection error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/content/{content_id}")
async def get_content_info(content_id: str):
    """Get information about registered content"""
    try:
        content = contract.functions.getContent(content_id).call()
        if content and content[0]:
            return {
                "content_id": content_id,
                "owner": content[0],
                "registration_time": content[2],
                "is_valid": content[3]
            }
    except Exception as e:
        raise HTTPException(status_code=404, detail="Content not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("index:app", host="127.0.0.1", port=3000, reload=True)
