from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Union
import numpy as np
import cv2
import json
import uuid
from datetime import datetime, timedelta
import asyncio
import jwt
from pathlib import Path
import tempfile
import os
from .watermarking import WatermarkEngine
from .blockchain import ContentRegistry
from .piracy_detection import PiracyDetector

# Configuration
SECRET_KEY = "your-secret-key-here"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(
    title="SecureStream API",
    version="1.0.0",
    description="Advanced content protection and anti-piracy solution"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = {}
    
    async def check_rate_limit(self, client_id: str) -> bool:
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old requests
        self.requests = {
            k: v for k, v in self.requests.items()
            if v[-1] > minute_ago
        }
        
        # Check current client
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        client_requests = self.requests[client_id]
        client_requests = [t for t in client_requests if t > minute_ago]
        
        if len(client_requests) >= self.requests_per_minute:
            return False
        
        client_requests.append(now)
        self.requests[client_id] = client_requests
        return True

# Initialize components
watermark_engine = WatermarkEngine()
# Mock content registry for testing
class MockContentRegistry:
    def register_content(self, content_id, content_hash, metadata):
        return True
    
    def verify_content(self, content_id, content_hash):
        return {"verified": True}
    
    def get_content_history(self, content_id):
        return []
    
    def get_content_status(self, content_id):
        return {"status": "completed"}

content_registry = MockContentRegistry()
piracy_detector = PiracyDetector()
rate_limiter = RateLimiter()

# Models
class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class ContentRegistration(BaseModel):
    title: str
    owner: str
    description: Optional[str] = None
    content_type: str = Field(..., regex="^(image|video)$")
    rights: Dict[str, str]
    watermark_strength: Optional[float] = Field(default=80.0, ge=0.0, le=100.0)

class BatchRegistration(BaseModel):
    registrations: List[ContentRegistration]

class DetectionRequest(BaseModel):
    content_url: str
    detection_type: str = Field(default="full", regex="^(full|quick|watermark-only)$")
    sensitivity: float = Field(default=0.8, ge=0.0, le=1.0)

class DetectionResponse(BaseModel):
    is_pirated: bool
    confidence: float
    details: Dict
    timestamp: str
    processing_time: float

class ContentStatus(BaseModel):
    content_id: str
    status: str
    progress: Optional[float]
    details: Optional[Dict]

# Authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception
    
    # In production, get user from database
    user = User(username=username)
    if user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_id = request.client.host
    if not await rate_limiter.check_rate_limit(client_id):
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later."
        )
    return await call_next(request)

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # In production, validate against database
    if form_data.username != "demo" or form_data.password != "demo":
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt.encode(
        {"sub": form_data.username, "exp": datetime.utcnow() + access_token_expires},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    return {"access_token": access_token, "token_type": "bearer"}

async def process_content_file(
    file: UploadFile,
    registration: ContentRegistration
) -> tuple:
    """Process a single content file."""
    content_id = str(uuid.uuid4())
    
    # Create temp file for video processing
    temp_file = None
    if registration.content_type == "video":
        # Save uploaded file to temp
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        temp_file.write(await file.read())
        temp_file.close()
        
        # Open video
        cap = cv2.VideoCapture(temp_file.name)
        if not cap.isOpened():
            raise HTTPException(
                status_code=400,
                detail="Could not open video file"
            )
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Create output video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out_path = temp_file.name.replace(".mp4", "_watermarked.mp4")
        out = cv2.VideoWriter(
            out_path,
            fourcc,
            fps,
            (int(cap.get(3)), int(cap.get(4)))
        )
        
        # Process each frame
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Add watermark to frame
            watermark_data = json.dumps({
                "content_id": content_id,
                "owner": registration.owner,
                "timestamp": datetime.utcnow().isoformat(),
                "frame": frame_idx
            })
            watermarked_frame = watermark_engine.embed_watermark(
                frame,
                watermark_data,
                strength=registration.watermark_strength
            )
            
            out.write(watermarked_frame)
            frame_idx += 1
        
        cap.release()
        out.release()
        
        # Read output video for hash
        with open(out_path, 'rb') as f:
            content = f.read()
            content_hash = str(hash(content))
        
        return content_id, content_hash, out_path
    
    else:  # Image processing
        content = await file.read()
        nparr = np.frombuffer(content, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        watermark_data = json.dumps({
            "content_id": content_id,
            "owner": registration.owner,
            "timestamp": datetime.utcnow().isoformat()
        })
        watermarked_frame = watermark_engine.embed_watermark(
            frame,
            watermark_data,
            strength=registration.watermark_strength
        )
        
        content_hash = str(hash(watermarked_frame.tobytes()))
        return content_id, content_hash, watermarked_frame

@app.post("/api/v1/content/register")
async def register_content(
    file: UploadFile = File(...),
    title: str = Form(...),
    owner: str = Form(...),
    content_type: str = Form(...),
    rights: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """Register new content with watermark and blockchain."""
    try:
        start_time = datetime.utcnow()
        
        # Create registration object
        registration = ContentRegistration(
            title=title,
            owner=owner,
            content_type=content_type,
            rights=json.loads(rights)
        )
        
        # Process content
        content_id, content_hash, processed_content = await process_content_file(
            file,
            registration
        )
        
        # Register on blockchain
        metadata = {
            "title": registration.title,
            "owner": registration.owner,
            "description": registration.description,
            "content_type": registration.content_type,
            "rights": registration.rights,
            "registration_date": datetime.utcnow().isoformat(),
            "registered_by": current_user.username
        }
        
        success = content_registry.register_content(
            content_id=content_id,
            content_hash=content_hash,
            metadata=metadata
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to register content on blockchain"
            )
        
        # Prepare response
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        if registration.content_type == "video":
            # Stream the processed video
            def iterfile():
                with open(processed_content, mode="rb") as file_like:
                    yield from file_like
            
            # Clean up temp files in background
            async def cleanup():
                await asyncio.sleep(1)  # Wait for streaming to start
                if os.path.exists(processed_content):
                    os.unlink(processed_content)
            
            asyncio.create_task(cleanup())
            
            return StreamingResponse(
                iterfile(),
                media_type="video/mp4",
                headers={
                    "Content-Disposition": f"attachment; filename={content_id}.mp4",
                    "X-Content-ID": content_id,
                    "X-Processing-Time": str(processing_time)
                }
            )
        else:
            # Return the watermarked image
            _, img_encoded = cv2.imencode('.png', processed_content)
            return StreamingResponse(
                iter([img_encoded.tobytes()]),
                media_type="image/png",
                headers={
                    "Content-Disposition": f"attachment; filename={content_id}.png",
                    "X-Content-ID": content_id,
                    "X-Processing-Time": str(processing_time)
                }
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing content: {str(e)}"
        )

@app.post("/api/v1/content/register/batch")
async def register_content_batch(
    files: List[UploadFile] = File(...),
    registrations: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """Register multiple content items with watermarks."""
    try:
        # Parse registrations JSON
        registrations_data = json.loads(registrations)
        if len(files) != len(registrations_data):
            raise HTTPException(
                status_code=400,
                detail="Number of files must match number of registrations"
            )
        
        results = []
        for file, reg_data in zip(files, registrations_data):
            # Create registration object
            registration = ContentRegistration(
                title=reg_data["title"],
                owner=reg_data["owner"],
                content_type=reg_data["content_type"],
                rights=reg_data["rights"]
            )
            
            # Process content
            content_id, content_hash, _ = await process_content_file(
                file,
                registration
            )
            
            # Register on blockchain
            metadata = {
                "title": registration.title,
                "owner": registration.owner,
                "content_type": registration.content_type,
                "rights": registration.rights,
                "registration_date": datetime.utcnow().isoformat(),
                "registered_by": current_user.username
            }
            
            success = content_registry.register_content(
                content_id=content_id,
                content_hash=content_hash,
                metadata=metadata
            )
            
            results.append({
                "content_id": content_id,
                "success": success,
                "title": registration.title
            })
        
        return {"results": results}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing batch: {str(e)}"
        )

@app.post("/api/v1/content/verify")
async def verify_content(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Verify content authenticity using watermark and blockchain."""
    try:
        start_time = datetime.utcnow()
        
        # Read content
        content = await file.read()
        nparr = np.frombuffer(content, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Extract watermark
        extracted_data = watermark_engine.extract_watermark(frame, 1024)
        if not extracted_data.startswith("{"):
            return {
                "verified": False,
                "error": "No valid watermark found",
                "processing_time": (datetime.utcnow() - start_time).total_seconds()
            }
        
        watermark_data = json.loads(extracted_data)
        content_id = watermark_data["content_id"]
        
        # Verify on blockchain
        verification = content_registry.verify_content(
            content_id=content_id,
            content_hash=str(hash(frame.tobytes()))
        )
        
        return {
            "verified": verification["verified"],
            "content_id": content_id,
            "owner": watermark_data["owner"],
            "timestamp": watermark_data["timestamp"],
            "blockchain_verification": verification,
            "processing_time": (datetime.utcnow() - start_time).total_seconds()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error verifying content: {str(e)}"
        )

@app.post("/api/v1/content/detect")
async def detect_piracy(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Detect potential piracy in content."""
    try:
        # Read and process the file
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )
        
        # Extract features and detect similarities
        start_time = datetime.utcnow()
        results = piracy_detector.detect_similarities(img)
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Check for watermark
        watermark = watermark_engine.extract_watermark(img, 128)  # Assume max 128 bytes
        
        response = {
            "processing_time": processing_time,
            "similarity_score": results.get("similarity_score", 0),
            "matches": results.get("matches", []),
            "watermark_found": watermark is not None,
            "watermark_data": watermark if watermark else None
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error detecting piracy: {str(e)}"
        )

@app.get("/api/v1/content/{content_id}/history")
async def get_content_history(
    content_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get content registration and usage history."""
    try:
        history = content_registry.get_content_history(content_id)
        return {
            "content_id": content_id,
            "history": history,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving content history: {str(e)}"
        )

@app.get("/api/v1/content/{content_id}/status")
async def get_content_status(
    content_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get current status of content processing."""
    try:
        # Get status from registry
        status = content_registry.get_content_status(content_id)
        return ContentStatus(
            content_id=content_id,
            status=status["status"],
            progress=status.get("progress"),
            details=status.get("details")
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving content status: {str(e)}"
        )
