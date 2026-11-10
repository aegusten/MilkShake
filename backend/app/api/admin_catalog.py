import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Security,
    UploadFile,
    status,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.admin import Admin
from app.schemas.drink import (
    DrinkCreate,
    DrinkImageCreate,
    DrinkImageOut,
    DrinkOut,
    DrinkUpdate,
)
from app.schemas.item_master import ItemMasterCreate, ItemMasterOut, ItemMasterUpdate
from app.services import auth_service, catalog_service, upload_service

router = APIRouter()

bearer_scheme = HTTPBearer(auto_error=False)


async def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Admin:
    """HTTP-layer wrapper around ``auth_service.verify_access_token``.

    Pulls the bearer token out of the ``Authorization`` header (an HTTP
    concern) and delegates verification to the service layer.
    """
    token = credentials.credentials if credentials else None
    return await auth_service.verify_access_token(db, token)


def _parse_uuid(value: str, name: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail=f"Invalid {name}."
        ) from exc


# --- Item master endpoints ---


@router.get("/item-masters", response_model=list[ItemMasterOut])
async def list_item_masters(db: AsyncSession = Depends(get_db)):
    return await catalog_service.list_item_masters(db)


@router.post(
    "/item-masters",
    response_model=ItemMasterOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_item_master(
    payload: ItemMasterCreate,
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.create_item_master(db, payload)


@router.patch(
    "/item-masters/{item_master_id}",
    response_model=ItemMasterOut,
    dependencies=[Depends(require_admin)],
)
async def update_item_master(
    item_master_id: str,
    payload: ItemMasterUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.update_item_master(
        db, _parse_uuid(item_master_id, "item_master_id"), payload
    )


@router.delete(
    "/item-masters/{item_master_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
async def delete_item_master(
    item_master_id: str,
    db: AsyncSession = Depends(get_db),
):
    await catalog_service.delete_item_master(
        db, _parse_uuid(item_master_id, "item_master_id")
    )


# --- Drink endpoints ---


@router.get("/drinks", response_model=list[DrinkOut])
async def list_drinks(db: AsyncSession = Depends(get_db)):
    return await catalog_service.list_drinks(db)


@router.post(
    "/drinks",
    response_model=DrinkOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_drink(
    payload: DrinkCreate,
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.create_drink(db, payload)


@router.patch(
    "/drinks/{drink_id}",
    response_model=DrinkOut,
    dependencies=[Depends(require_admin)],
)
async def update_drink(
    drink_id: str,
    payload: DrinkUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.update_drink(
        db, _parse_uuid(drink_id, "drink_id"), payload
    )


@router.delete(
    "/drinks/{drink_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
async def delete_drink(
    drink_id: str,
    db: AsyncSession = Depends(get_db),
):
    await catalog_service.delete_drink(db, _parse_uuid(drink_id, "drink_id"))


@router.post(
    "/drinks/{drink_id}/images",
    response_model=DrinkImageOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def add_drink_image(
    drink_id: str,
    payload: DrinkImageCreate,
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.add_drink_image(
        db, _parse_uuid(drink_id, "drink_id"), payload
    )


@router.post(
    "/uploads",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def upload_image(file: UploadFile = File(...)) -> dict[str, str]:
    url = await upload_service.save_image_upload(file)
    return {"url": url}
