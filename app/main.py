from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import time
import os
from loguru import logger

from app.routers import scraper
from app.utils.helpers import setup_logger

# Setup logger
setup_logger()

# Create FastAPI app
app = FastAPI(
    title="Scraper Service",
    description="A microservice for scraping articles from websites",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Mount static files directory
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routers
app.include_router(scraper.router, tags=["Scraper"])

# Add middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Get client IP
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0]
    else:
        client_ip = request.client.host if request.client else "unknown"
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path} from {client_ip}")
    
    # Process request
    try:
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(f"Response: {response.status_code} in {process_time:.3f}s")
        
        return response
    except Exception as e:
        # Log exception
        process_time = time.time() - start_time
        logger.error(f"Error: {str(e)} in {process_time:.3f}s")
        
        # Return error response
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

# Add exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log exception
    logger.error(f"Unhandled exception: {str(exc)}")
    
    # Return error response
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Add health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Status of the service
    """
    return {"status": "ok"}

# Serve the frontend at the root endpoint
@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
async def serve_frontend():
    """
    Serve the frontend web application.
    
    Returns:
        HTMLResponse: The HTML content of the frontend
    """
    with open(os.path.join(static_dir, "index.html"), "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)
