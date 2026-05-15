import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.admin import router as admin_router
from app.api.admin_catalog import router as admin_catalog_router
from app.api.orders import router as orders_router
from app.api.public_catalog import router as public_catalog_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(title="MilkShake Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

uploads_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Welcome to MilkShake API"}


app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(admin_catalog_router, prefix="/api/admin", tags=["admin"])
app.include_router(public_catalog_router, prefix="/api", tags=["public"])
app.include_router(orders_router, prefix="/api", tags=["orders"])
