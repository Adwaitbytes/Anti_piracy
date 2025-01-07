from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import hashlib
import json
from web3 import Web3
from dotenv import load_dotenv
import numpy as np
from PIL import Image
import io
import tensorflow as tf
from secure_stream.watermarking.watermarker import embed_watermark, extract_watermark
from datetime import datetime
import uuid

# Load environment variables
load_dotenv()

app = FastAPI(title="SecureStream API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Web3 and contract
w3 = Web3(Web3.HTTPProvider(os.getenv('WEB3_PROVIDER_URL')))
with open("secure_stream/blockchain/contracts/ContentRegistry.abi", 'r') as f:
    contract_abi = json.load(f)
contract = w3.eth.contract(address=os.getenv('CONTRACT_ADDRESS'), abi=contract_abi)

# Initialize AI model for content detection
model = tf.keras.applications.ResNet50(weights='imagenet', include_top=False)

# Create directories if they don't exist
os.makedirs("uploads", exist_ok=True)
os.makedirs("fingerprints", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

def generate_fingerprint(image):
    """Generate a fingerprint from an image using ResNet50"""
    img = tf.image.resize(image, (224, 224))
    img = tf.keras.applications.resnet50.preprocess_input(img)
    features = model.predict(tf.expand_dims(img, axis=0))
    return features.flatten()

def calculate_similarity(fp1, fp2):
    """Calculate cosine similarity between two fingerprints"""
    return np.dot(fp1, fp2) / (np.linalg.norm(fp1) * np.linalg.norm(fp2))

@app.post("/api/register")
async def register_content(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(...)
):
    try:
        # Read and process the image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Generate content ID and save original
        content_id = str(uuid.uuid4())
        file_path = f"uploads/{content_id}{os.path.splitext(file.filename)[1]}"
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Generate watermark and embed it
        watermark = f"SecureStream_{content_id[:8]}"
        watermarked_image = embed_watermark(image, watermark)
        watermarked_path = f"uploads/watermarked_{content_id}{os.path.splitext(file.filename)[1]}"
        watermarked_image.save(watermarked_path)
        
        # Generate fingerprint
        fingerprint = generate_fingerprint(np.array(image))
        np.save(f"fingerprints/{content_id}.npy", fingerprint)
        
        # Calculate content hash
        content_hash = hashlib.sha256(contents).hexdigest()
        
        # Register on blockchain
        account = w3.eth.account.from_key(os.getenv('PRIVATE_KEY'))
        nonce = w3.eth.get_transaction_count(account.address)
        
        # Estimate gas
        gas_estimate = contract.functions.registerContent(
            content_id,
            content_hash,
            watermark
        ).estimate_gas({'from': account.address})
        
        transaction = contract.functions.registerContent(
            content_id,
            content_hash,
            watermark
        ).build_transaction({
            'chainId': int(os.getenv('NETWORK_ID')),
            'gas': int(gas_estimate * 1.1),
            'maxFeePerGas': w3.eth.gas_price,
            'maxPriorityFeePerGas': w3.eth.gas_price,
            'nonce': nonce,
        })
        
        signed_txn = w3.eth.account.sign_transaction(transaction, os.getenv('PRIVATE_KEY'))
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return JSONResponse({
            "status": "success",
            "content_id": content_id,
            "transaction_hash": tx_receipt['transactionHash'].hex(),
            "watermarked_url": f"/static/watermarked_{content_id}{os.path.splitext(file.filename)[1]}"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/verify")
async def verify_content(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Extract watermark
        extracted_watermark = extract_watermark(image)
        if not extracted_watermark.startswith("SecureStream_"):
            return JSONResponse({
                "status": "unregistered",
                "message": "No valid watermark found"
            })
        
        # Get content ID from watermark
        content_id = extracted_watermark.split("_")[1]
        
        # Verify on blockchain
        content = contract.functions.getContent(content_id).call()
        
        return JSONResponse({
            "status": "verified",
            "owner": content[0],
            "timestamp": content[3],
            "is_valid": content[4]
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/detect")
async def detect_piracy(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Generate fingerprint for uploaded image
        test_fingerprint = generate_fingerprint(np.array(image))
        
        # Compare with stored fingerprints
        matches = []
        for fp_file in os.listdir("fingerprints"):
            stored_fingerprint = np.load(f"fingerprints/{fp_file}")
            similarity = calculate_similarity(test_fingerprint, stored_fingerprint)
            
            if similarity > 0.95:  # High similarity threshold
                content_id = fp_file.split('.')[0]
                content = contract.functions.getContent(content_id).call()
                matches.append({
                    "content_id": content_id,
                    "owner": content[0],
                    "similarity": float(similarity),
                    "is_valid": content[4]
                })
        
        return JSONResponse({
            "status": "success",
            "matches": matches
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/content/{content_id}")
async def get_content_info(content_id: str):
    try:
        content = contract.functions.getContent(content_id).call()
        return JSONResponse({
            "owner": content[0],
            "content_hash": content[1],
            "watermark": content[2],
            "timestamp": content[3],
            "is_valid": content[4]
        })
    except Exception as e:
        raise HTTPException(status_code=404, detail="Content not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
