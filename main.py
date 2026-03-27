"""
Compliance Autopilot - Main FastAPI Application
"""
import os
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.models.database import Base, engine
from app.api.routes import dashboard, reports
from app.services.notification_service import NotificationService
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Compliance Autopilot API",
    description="RBI Circular tracking and compliance action automation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
Base.metadata.create_all(bind=engine)
logger.info("Database initialized")

# Initialize notification service
notification_service = NotificationService(
    smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
    smtp_port=int(os.getenv("SMTP_PORT", "587")),
    sender_email=os.getenv("SENDER_EMAIL"),
    sender_password=os.getenv("SENDER_PASSWORD"),
)
logger.info("Notification service initialized")

# Include routers
app.include_router(dashboard.router)
app.include_router(reports.router)


@app.get("/", response_class=HTMLResponse)
def read_root():
    """Render main dashboard page"""
    try:
        with open("app/templates/dashboard.html", "r") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        return "<h1>Compliance Autopilot</h1><p>Dashboard loading...</p>"


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Compliance Autopilot",
        "version": "1.0.0"
    }


@app.get("/api/config")
def get_config():
    """Get application configuration"""
    return {
        "app_name": "Compliance Autopilot",
        "app_version": "1.0.0",
        "dashboard_url": os.getenv("DASHBOARD_URL", "http://localhost:8000"),
        "notification_enabled": bool(os.getenv("SENDER_EMAIL")),
    }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors"""
    return {
        "error": "Not Found",
        "message": "The requested resource was not found",
        "status_code": 404
    }


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(exc)}")
    return {
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
        "status_code": 500
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENVIRONMENT") == "development"
    )
