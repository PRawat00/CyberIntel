"""
FastAPI main application.
Provides REST API endpoints for dependency scanning.
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env files
# Load project root .env first
load_dotenv(project_root / ".env")
# Then load API-specific .env (overrides project settings)
api_env_path = Path(__file__).parent / ".env"
if api_env_path.exists():
    load_dotenv(api_env_path, override=True)

from api.routes import auth, auth_debug, chat, rag, scans  # noqa: E402

# Initialize FastAPI app
app = FastAPI(
    title="SecureChat API",
    description="AI-Powered Dependency Security Scanner API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS Configuration
# Allow Next.js dev server and production domains
allowed_origins = [
    "http://localhost:3000",  # Next.js dev
    "http://localhost:3001",
    "http://127.0.0.1:3000",
]

# Add production frontend URL from environment
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)
    # Also allow without trailing slash
    if frontend_url.endswith("/"):
        allowed_origins.append(frontend_url.rstrip("/"))
    else:
        allowed_origins.append(frontend_url + "/")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware for debugging authentication
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and their headers for debugging."""
    # Log request details
    logger.info(f"{'='*60}")
    logger.info(f"Request: {request.method} {request.url.path}")

    # Log headers (excluding sensitive data)
    headers = dict(request.headers)
    auth_header = headers.get("authorization", "Not present")
    if auth_header != "Not present" and auth_header.startswith("Bearer "):
        # Mask the token for security but show it exists
        auth_header = f"Bearer {auth_header[7:20]}..." if len(auth_header) > 27 else auth_header

    logger.info(f"Authorization header: {auth_header}")
    logger.info(f"Content-Type: {headers.get('content-type', 'Not set')}")
    logger.info(f"Origin: {headers.get('origin', 'Not set')}")

    # Special logging for file uploads
    if request.method == "POST" and request.url.path == "/api/scans":
        logger.info("FILE UPLOAD DETECTED - POST /api/scans")
        logger.info(f"All headers: {list(headers.keys())}")

    # Process the request
    response = await call_next(request)

    # Log response with more detail for errors
    logger.info(f"Response status: {response.status_code}")
    if response.status_code >= 400:
        logger.warning(
            f"ERROR Response: {response.status_code} for {request.method} {request.url.path}"
        )
    logger.info(f"{'='*60}")

    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions gracefully."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if os.getenv("DEBUG") else "An unexpected error occurred",
        },
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "SecureChat API",
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "SecureChat API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "endpoints": {
            "scans": "/api/scans",
            "rag": "/api/rag",
            "chat": "/api/chat",
            "health": "/health",
        },
    }


# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(scans.router, prefix="/api", tags=["scans"])
app.include_router(rag.router)
app.include_router(chat.router)
app.include_router(auth_debug.router)  # Debug endpoints for testing auth


# Startup event
@app.on_event("startup")
async def startup_event():
    """Log startup with smart context features enabled."""
    print("=" * 80)
    print("SecureChat API Starting - PHASE 6: SMART CONTEXT INJECTION")
    print("=" * 80)
    print("Features enabled:")
    print("  - Intent-based dependency context injection")
    print("  - Direct CVE retrieval (bypassing vector search)")
    print("  - Hash-based state change detection")
    print("  - Eager loading with selectinload(Dependency.cves)")
    print("=" * 80)

    # Verify intent detector module is importable
    try:
        from llm_engine.intent_detector import DependencyIntentDetector  # noqa: F401

        print("✓ Intent detector module loaded successfully")
    except ImportError as e:
        print(f"✗ FAILED to load intent detector: {e}")

    print("API ready at http://localhost:8000")
    print("=" * 80)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",  # noqa: S104
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info",
    )
