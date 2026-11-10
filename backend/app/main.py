from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.admin import router as admin_router
from app.api.admin_catalog import router as admin_catalog_router
from app.api.orders import router as orders_router
from app.api.public_catalog import router as public_catalog_router
from app.config import get_settings
from app.services.errors import (
    ConflictError,
    ForbiddenError,
    InvalidInputError,
    NotFoundError,
    UnauthorizedError,
)
from app.services.upload_service import UPLOAD_DIR

settings = get_settings()

app = FastAPI(title="MilkShake Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.exception_handler(NotFoundError)
async def _not_found(_: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ConflictError)
async def _conflict(_: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(InvalidInputError)
async def _invalid_input(_: Request, exc: InvalidInputError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(UnauthorizedError)
async def _unauthorized(_: Request, exc: UnauthorizedError) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)},
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(ForbiddenError)
async def _forbidden(_: Request, exc: ForbiddenError) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Welcome to MilkShake API"}


app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(admin_catalog_router, prefix="/api/admin", tags=["admin"])
app.include_router(public_catalog_router, prefix="/api", tags=["public"])
app.include_router(orders_router, prefix="/api", tags=["orders"])
