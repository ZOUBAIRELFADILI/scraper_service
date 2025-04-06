"""
Main FastAPI application for the enhanced scraper service.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import time
import os
from loguru import logger
import traceback
from dotenv import load_dotenv

from app.routers import scraper
from app.utils.helpers import setup_logger
from app.db.mongodb import MongoDBClient

# Load environment variables
load_dotenv()

# Setup logger
setup_logger()

# Create FastAPI app
app = FastAPI(
    title="AI-Powered Content Intelligence Service",
    description="A microservice for scraping, enriching, and analyzing articles from websites",
    version="2.0.0",
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

# Mount static files directory if it exists
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(static_dir):
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
        logger.error(traceback.format_exc())
        
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
    logger.error(traceback.format_exc())
    
    # Return error response
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Setup MongoDB indexes on startup
@app.on_event("startup")
async def startup_db_client():
    try:
        db_client = MongoDBClient()
        await db_client.setup_indexes()
        logger.info("MongoDB indexes setup completed")
    except Exception as e:
        logger.error(f"Error setting up MongoDB indexes: {str(e)}")

# Serve the frontend at the root endpoint if it exists
@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
async def serve_frontend():
    """
    Serve the frontend web application if available.
    
    Returns:
        HTMLResponse: The HTML content of the frontend or API info
    """
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    else:
        # Return API info if no frontend is available
        return HTMLResponse(content=f"""
        <html>
            <head>
                <title>AI-Powered Content Intelligence Service</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; line-height: 1.6; }}
                    .container {{ max-width: 800px; margin: 0 auto; }}
                    h1 {{ color: #2563eb; }}
                    h2 {{ color: #4b5563; margin-top: 30px; }}
                    a {{ color: #2563eb; text-decoration: none; }}
                    a:hover {{ text-decoration: underline; }}
                    .endpoint {{ background-color: #f3f4f6; padding: 15px; border-radius: 5px; margin-bottom: 10px; }}
                    .method {{ font-weight: bold; color: #059669; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>AI-Powered Content Intelligence Service</h1>
                    <p>A microservice for scraping, enriching, and analyzing articles from websites.</p>
                    
                    <h2>Available Endpoints:</h2>
                    <div class="endpoint">
                        <p><span class="method">POST</span> <a href="/docs#/Scraper/scrape_urls_scrape_post">/scrape</a></p>
                        <p>Scrape and enrich articles from a list of URLs.</p>
                    </div>
                    
                    <div class="endpoint">
                        <p><span class="method">GET</span> <a href="/docs#/Scraper/search_articles_articles_get">/articles</a></p>
                        <p>Search for articles in the database.</p>
                    </div>
                    
                    <div class="endpoint">
                        <p><span class="method">GET</span> <a href="/docs#/Scraper/health_check_health_get">/health</a></p>
                        <p>Health check endpoint.</p>
                    </div>
                    
                    <h2>Documentation:</h2>
                    <p><a href="/docs">Swagger UI</a> - Interactive API documentation</p>
                    <p><a href="/redoc">ReDoc</a> - Alternative API documentation</p>
                </div>
            </body>
        </html>
        """)
