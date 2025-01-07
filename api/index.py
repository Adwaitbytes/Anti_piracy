from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from pathlib import Path

# Import your SecureStream modules
from secure_stream.api import app as secure_stream_app

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the SecureStream API
app.mount("/api/v1", secure_stream_app)

# Setup templates
templates = Jinja2Templates(directory="dashboard/templates")

# Serve static files
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Handle 404 errors
@app.exception_handler(404)
async def custom_404_handler(request, exc):
    return templates.TemplateResponse(
        "index.html",
        {"request": request},
        status_code=200
    )
