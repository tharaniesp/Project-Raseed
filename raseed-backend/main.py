# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import initialize_firebase
from app.api.routes import receipt_router, health_router
from app.core.logging import setup_logging

# Setup logging
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    initialize_firebase()
    yield
    # Shutdown
    pass

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(receipt_router, prefix="/api", tags=["Receipts"])

# Add a root-level health check for compatibility
@app.get("/health")
async def root_health_check():
    """Root-level health check endpoint"""
    from app.core.database import is_firebase_initialized
    return {
        "status": "healthy",
        "firebase_initialized": is_firebase_initialized(),
        "timestamp": "2025-07-18T10:30:00Z"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"{settings.PROJECT_NAME} API is running!",
        "version": settings.VERSION,
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )