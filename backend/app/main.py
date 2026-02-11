from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from prometheus_fastapi_instrumentator import Instrumentator
from app.config import settings
from app.api import stores, health, auth, observability
from app.utils.limiter import limiter
import structlog

# Setup Logger
structlog.configure(
    processors=[
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

# Limiter is imported from app.utils.limiter

app = FastAPI(
    title="Urumi Store Platform API",
    description="Multi-tenant WooCommerce provisioning on Kubernetes",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Observability
Instrumentator().instrument(app).expose(app)

# Routes
app.include_router(health.router, tags=["Health"])
app.include_router(observability.router, prefix="/api/v1/observability", tags=["Observability"])
app.include_router(stores.router, prefix="/api/v1/stores", tags=["Stores"])
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"]) # Optional

@app.on_event("startup")
async def startup_event():
    logger.info("application_startup", environment=settings.ENVIRONMENT)
    # Auto-create tables for local dev
    from app.database import engine, Base
    from app.models import Store, AuditLog # Import models to register them
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_tables_created")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("application_shutdown")
