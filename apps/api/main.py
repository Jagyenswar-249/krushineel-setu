import os
import contextlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.api.config import settings
from apps.api.database import Base, engine, SessionLocal
from apps.api.models import User
from tools.seed_demo_data import seed

# Routers
from apps.api.routers.auth import router as auth_router
from apps.api.routers.coldwatch import router as coldwatch_router
from apps.api.routers.ingest import router as ingest_router
from apps.api.routers.gradelens import router as gradelens_router
from apps.api.routers.sagarsuraksha import router as sagarsuraksha_router
from apps.api.routers.mandimitra import router as mandimitra_router
from apps.api.routers.matsyaconnect import router as matsyaconnect_router
from apps.api.routers.sms import router as sms_router
from apps.api.routers.notifications import router as notifications_router
from apps.api.routers.admin import router as admin_router


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    # Auto-seed if empty
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        if user_count == 0:
            print("[Startup] Empty database detected. Seeding realistic Odisha demo data...")
            seed()
    except Exception as e:
        print(f"[Startup Warning] Seeding check: {e}")
    finally:
        db.close()

    yield
    # Shutdown logic if any


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="One unified offline-first platform for Odisha's farmers, FPOs and fisherfolk.",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers under API_V1_STR
api_prefix = settings.API_V1_STR
app.include_router(auth_router, prefix=api_prefix)
app.include_router(coldwatch_router, prefix=api_prefix)
app.include_router(ingest_router, prefix=api_prefix)
app.include_router(gradelens_router, prefix=api_prefix)
app.include_router(sagarsuraksha_router, prefix=api_prefix)
app.include_router(mandimitra_router, prefix=api_prefix)
app.include_router(matsyaconnect_router, prefix=api_prefix)
app.include_router(sms_router, prefix=api_prefix)
app.include_router(notifications_router, prefix=api_prefix)
app.include_router(admin_router, prefix=api_prefix)


@app.get("/healthz", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "demo_mode": settings.DEMO_MODE
    }


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to KrushiNeel Setu API",
        "docs_url": "/docs",
        "healthz": "/healthz",
        "modules": [
            "ColdWatch (cold room spoilage, alerts & ingest)",
            "GradeLens (phone-photo grading & certificate)",
            "SagarSuraksha (marine safety, checkins & geofence)",
            "MandiMitra (mandi prices, forecast & hold/sell advisor)",
            "MatsyaConnect (catch marketplace & buyer matching)"
        ]
    }
