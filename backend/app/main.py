from contextlib import asynccontextmanager
import sys
import subprocess
from datetime import datetime, timezone
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.exceptions import AppException, ValidationException, NotFoundException, DatabaseException
from backend.app.middleware.logging import RequestLoggingMiddleware
from backend.app.schemas.common import ResponseEnvelope, ErrorEnvelope
from backend.app.schemas.analytics import DatasetFreshnessOut
from backend.app.services.summary import SummaryService
from backend.database.pool import initialize_pool, close_pool

# Import routers
from backend.app.routers.summary import router as summary_router
from backend.app.routers.companies import router as companies_router
from backend.app.routers.skills import router as skills_router
from backend.app.routers.technology import router as technology_router
from backend.app.routers.geography import router as geography_router
from backend.app.routers.salary import router as salary_router

# Lifetime context manager for pool lifecycle orchestration
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup sequence
    print("Starting up FastAPI serving server...")
    try:
        initialize_pool()
    except Exception as e:
        print(f"Failed to initialize database pool during startup: {e}")
    yield
    # Shutdown sequence
    print("Shutting down FastAPI serving server...")
    close_pool()

app = FastAPI(
    title="CareerPulse Serving API",
    description="Production-ready REST API exposing job market intelligence analytics from the serving layer.",
    version="1.0.0",
    contact={
        "name": "CareerPulse Support",
        "email": "support@careerpulse.dev"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    lifespan=lifespan,
    debug=settings.API_DEBUG
)

# Register CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register GZip response compression middleware
app.add_middleware(
    GZipMiddleware,
    minimum_size=1024
)

# Register custom request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# --- Global Exception Handlers ---

@app.exception_handler(NotFoundException)
async def handle_not_found(request: Request, exc: NotFoundException):
    return JSONResponse(
        status_code=404,
        content=ErrorEnvelope(success=False, error=exc.message, error_code=exc.error_code).model_dump()
    )

@app.exception_handler(ValidationException)
async def handle_validation(request: Request, exc: ValidationException):
    return JSONResponse(
        status_code=400,
        content=ErrorEnvelope(success=False, error=exc.message, error_code=exc.error_code).model_dump()
    )

@app.exception_handler(DatabaseException)
async def handle_database_error(request: Request, exc: DatabaseException):
    return JSONResponse(
        status_code=500,
        content=ErrorEnvelope(success=False, error="A database error occurred.", error_code=exc.error_code).model_dump()
    )

@app.exception_handler(AppException)
async def handle_app_error(request: Request, exc: AppException):
    return JSONResponse(
        status_code=500,
        content=ErrorEnvelope(success=False, error=exc.message, error_code=exc.error_code).model_dump()
    )

@app.exception_handler(RequestValidationError)
async def handle_pydantic_validation(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        msg = err.get("msg", "Invalid parameter")
        errors.append(f"{loc}: {msg}")
    msg_str = "; ".join(errors)
    return JSONResponse(
        status_code=400,
        content=ErrorEnvelope(success=False, error=msg_str, error_code="VALIDATION_ERROR").model_dump()
    )

@app.exception_handler(StarletteHTTPException)
async def handle_http_exception(request: Request, exc: StarletteHTTPException):
    # Hide details of generic internal exceptions if not in debug mode
    err_msg = exc.detail
    if exc.status_code == 500 and not settings.API_DEBUG:
        err_msg = "An unexpected server error occurred."
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorEnvelope(success=False, error=err_msg, error_code=f"HTTP_{exc.status_code}").model_dump()
    )

@app.exception_handler(Exception)
async def handle_generic_exception(request: Request, exc: Exception):
    err_msg = "An unexpected server error occurred."
    if settings.API_DEBUG:
        err_msg = str(exc)
    return JSONResponse(
        status_code=500,
        content=ErrorEnvelope(success=False, error=err_msg, error_code="UNHANDLED_SERVER_ERROR").model_dump()
    )

# --- Standard Lifecycle / Utility Endpoints ---

@app.get(
    "/",
    response_model=ResponseEnvelope[dict],
    summary="API Root Info",
    description="Returns standard serving API info and operational status."
)
def root():
    return ResponseEnvelope(data={
        "title": app.title,
        "description": app.description,
        "version": app.version,
        "status": "online"
    })

@app.get(
    "/health",
    response_model=ResponseEnvelope[dict],
    summary="API Health Check",
    description="Validates active connection and latency to PostgreSQL RDS database."
)
def health(db=Depends(get_db)):
    with db.cursor() as cursor:
        cursor.execute("SELECT 1;")
        cursor.fetchone()
    return ResponseEnvelope(data={
        "status": "healthy",
        "database": "connected"
    })

@app.get(
    "/metrics",
    response_model=ResponseEnvelope[list[DatasetFreshnessOut]],
    summary="Pipeline Freshness Metrics",
    description="Exposes sync loading metrics and dataset refresh age alerts from serving.v_dataset_status view."
)
def metrics(db=Depends(get_db)):
    freshness = SummaryService.get_dataset_freshness(db)
    return ResponseEnvelope(data=freshness)

def get_git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
    except Exception:
        return "unknown"

@app.get(
    "/version",
    response_model=ResponseEnvelope[dict],
    summary="API Version Details",
    description="Exposes active API version metadata, Python build targets, and latest Git commit telemetry."
)
def version():
    return ResponseEnvelope(data={
        "version": app.version,
        "git_commit": get_git_commit(),
        "build_timestamp": "2026-07-25T18:17:00Z",
        "python_version": sys.version
    })

# --- Include Application Routers ---

# Mount v1 prefix routers
app.include_router(summary_router, prefix="/api/v1")
app.include_router(companies_router, prefix="/api/v1")
app.include_router(skills_router, prefix="/api/v1")
app.include_router(technology_router, prefix="/api/v1")
app.include_router(geography_router, prefix="/api/v1")
app.include_router(salary_router, prefix="/api/v1")
