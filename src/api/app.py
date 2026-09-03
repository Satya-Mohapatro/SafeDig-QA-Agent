import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.api.middleware import CorrelationIdMiddleware
from src.api.routes import jobs, qa, evidence, batch, eval, health, metrics
from src.config.settings import settings
from src.config.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle for the FastAPI application."""
    # Startup: initialize database tables
    from src.db.engine import init_db
    await init_db()
    logger.info("Database initialized on startup.")
    yield
    # Shutdown: nothing to clean up for now
    logger.info("Application shutting down.")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description="Production AI Map QA & Validation Agent REST API with Human-in-the-loop Disposition",
        version=settings.engine_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Mount API routes
    app.include_router(health.router)
    app.include_router(metrics.router)
    app.include_router(jobs.router, prefix="/api/v1")
    app.include_router(qa.router, prefix="/api/v1")
    app.include_router(evidence.router, prefix="/api/v1")
    app.include_router(batch.router, prefix="/api/v1")
    app.include_router(eval.router, prefix="/api/v1")

    
    @app.get("/api/v1/health", tags=["Health"])
    def health_check():
        return {
            "status": "HEALTHY",
            "app_name": settings.app_name,
            "engine_version": settings.engine_version,
            "policy_version": settings.policy_version,
            "warning_catalogue_version": settings.warning_catalogue_version,
            "legend_version": settings.legend_version,
            "safe_mode": settings.safe_mode
        }
        
    # Mount Static Frontend
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static_assets")
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend_ui")
        
    return app

app = create_app()
