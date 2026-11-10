from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.exceptions import (
    KrishiRAGException,
    app_exception_handler,
    generic_exception_handler
)
from backend.app.database.session import init_db
from backend.app.api.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} backend...")
    init_db()
    logger.info("Application startup sequence completed.")
    yield
    # Shutdown actions
    logger.info("Shutting down KrishiRAG backend...")

app = FastAPI(
    title="KrishiRAG API",
    description="Authentic, Evidence-Grounded Agricultural Advisory RAG System strictly backed by ICAR and Government Agricultural Publications.",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    lifespan=lifespan
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Exception Handlers
app.add_exception_handler(KrishiRAGException, app_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include Main API Router
app.include_router(api_router, prefix=settings.API_PREFIX)

@app.get("/", include_in_schema=False)
def root_redirect():
    """Redirect root path to interactive Swagger documentation."""
    return RedirectResponse(url="/docs")
