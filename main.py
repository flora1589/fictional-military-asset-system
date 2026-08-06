import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import engine, Base
from app.seed.seed_data import seed_database

from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.assets import router as assets_router
from app.api.missions import router as missions_router
from app.api.requests import router as requests_router
from app.api.maintenance import router as maintenance_router
from app.api.inventory import router as inventory_router
from app.api.notifications import router as notifications_router
from app.api.reports import router as reports_router
from app.api.audit import router as audit_router

# Create Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for dev/portfolio demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error_summary": str(exc)}
    )

# Include Routers under API V1
api_prefix = settings.API_V1_STR
app.include_router(auth_router, prefix=api_prefix)
app.include_router(users_router, prefix=api_prefix)
app.include_router(assets_router, prefix=api_prefix)
app.include_router(missions_router, prefix=api_prefix)
app.include_router(requests_router, prefix=api_prefix)
app.include_router(maintenance_router, prefix=api_prefix)
app.include_router(inventory_router, prefix=api_prefix)
app.include_router(notifications_router, prefix=api_prefix)
app.include_router(reports_router, prefix=api_prefix)
app.include_router(audit_router, prefix=api_prefix)

@app.on_event("startup")
def on_startup():
    # Automatically seed demo data on app launch if missing
    seed_database()

@app.get("/")
def root():
    return {
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "Operational",
        "docs": "/docs",
        "health": "Green"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
