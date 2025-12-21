from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.api.admin import router as admin_router

app = FastAPI(title="MilkShake Backend")

# CORS settings
origins = [
    origin.strip()
    for origin in os.getenv("BACKEND_CORS_ORIGINS", "").split(",")
    if origin.strip()
]
if not origins:
    origins = ["http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Welcome to MilkShake API dY?1"}


app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
