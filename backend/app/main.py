from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.middleware import RequestIDMiddleware, TimingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    from app.db.session import engine

    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # Middleware (order matters: last added = first executed)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    from app.domains.auth.router import router as auth_router
    from app.domains.patients.router import router as patients_router
    from app.domains.audit.router import router as audit_router
    from app.domains.planning.router import router as planning_router
    from app.domains.machines.router import router as machines_router
    from app.domains.machines.router import tolerances_router
    from app.domains.treatment.router import router as treatment_router
    from app.domains.imaging.router import router as imaging_router
    from app.domains.scheduling.router import router as scheduling_router
    from app.domains.qa.router import router as qa_router
    from app.domains.reporting.router import router as reporting_router
    from app.dicom.router import router as dicom_router

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(patients_router, prefix="/api/v1")
    app.include_router(audit_router, prefix="/api/v1")
    app.include_router(planning_router, prefix="/api/v1")
    app.include_router(machines_router, prefix="/api/v1")
    app.include_router(tolerances_router, prefix="/api/v1")
    app.include_router(treatment_router, prefix="/api/v1")
    app.include_router(imaging_router, prefix="/api/v1")
    app.include_router(scheduling_router, prefix="/api/v1")
    app.include_router(qa_router, prefix="/api/v1")
    app.include_router(reporting_router, prefix="/api/v1")
    app.include_router(dicom_router, prefix="/api/v1")

    @app.get("/api/health")
    async def health():
        return {"status": "healthy", "version": settings.APP_VERSION}

    return app


app = create_app()
