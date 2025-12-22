from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, Header, status, UploadFile, File
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import os

from app.db import get_db
from app.models.admin import Admin
from app.models.item_master import ItemMaster
from app.models.drink import Drink
from app.models.drink_image import DrinkImage
from app.schemas.item_master import ItemMasterCreate, ItemMasterOut, ItemMasterUpdate
from app.schemas.drink import (
    DrinkCreate,
    DrinkImageCreate,
    DrinkImageOut,
    DrinkOut,
    DrinkUpdate,
)

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def require_admin(
    x_admin_id: str = Header(None, alias="X-Admin-Id"),
    db: Session = Depends(get_db),
):
    if not x_admin_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin credentials required.")
    try:
        admin_uuid = uuid.UUID(x_admin_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials.")
    admin = db.query(Admin).filter(Admin.id == admin_uuid).one_or_none()
    if not admin or not admin.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return admin


@router.get("/item-masters", response_model=List[ItemMasterOut])
def list_item_masters(db: Session = Depends(get_db)):
    return db.query(ItemMaster).order_by(ItemMaster.sort_order).all()


@router.post("/item-masters", response_model=ItemMasterOut, status_code=status.HTTP_201_CREATED)
def create_item_master(
    payload: ItemMasterCreate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
):
    item_master = ItemMaster(**payload.dict())
    db.add(item_master)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Item master name already exists.")
    db.refresh(item_master)
    return item_master


@router.patch("/item-masters/{item_master_id}", response_model=ItemMasterOut)
def update_item_master(
    item_master_id: str,
    payload: ItemMasterUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
):
    item_master = db.query(ItemMaster).filter(ItemMaster.id == item_master_id).one_or_none()
    if not item_master:
        raise HTTPException(status_code=404, detail="Item master not found.")
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(item_master, key, value)
    db.add(item_master)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Item master update failed.")
    db.refresh(item_master)
    return item_master


@router.delete("/item-masters/{item_master_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item_master(
    item_master_id: str,
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
):
    item_master = db.query(ItemMaster).filter(ItemMaster.id == item_master_id).one_or_none()
    if not item_master:
        raise HTTPException(status_code=404, detail="Item master not found.")
    db.delete(item_master)
    db.commit()
    return None


@router.get("/drinks", response_model=List[DrinkOut])
def list_drinks(db: Session = Depends(get_db)):
    return db.query(Drink).order_by(Drink.created_at.desc()).all()


@router.post("/drinks", response_model=DrinkOut, status_code=status.HTTP_201_CREATED)
def create_drink(
    payload: DrinkCreate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
):
    if not payload.item_master_ids:
        raise HTTPException(status_code=400, detail="At least one item master is required.")
    item_masters = (
        db.query(ItemMaster)
        .filter(ItemMaster.id.in_(payload.item_master_ids))
        .all()
    )
    if len(item_masters) != len(set(payload.item_master_ids)):
        raise HTTPException(status_code=404, detail="Item master not found.")
    drink = Drink(**payload.dict(exclude={"item_master_ids"}))
    drink.item_masters = item_masters
    db.add(drink)
    db.commit()
    db.refresh(drink)
    return drink


@router.patch("/drinks/{drink_id}", response_model=DrinkOut)
def update_drink(
    drink_id: str,
    payload: DrinkUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
):
    drink = db.query(Drink).filter(Drink.id == drink_id).one_or_none()
    if not drink:
        raise HTTPException(status_code=404, detail="Drink not found.")
    if payload.item_master_ids is not None:
        if not payload.item_master_ids:
            raise HTTPException(status_code=400, detail="At least one item master is required.")
        item_masters = (
            db.query(ItemMaster)
            .filter(ItemMaster.id.in_(payload.item_master_ids))
            .all()
        )
        if len(item_masters) != len(set(payload.item_master_ids)):
            raise HTTPException(status_code=404, detail="Item master not found.")
        drink.item_masters = item_masters
    for key, value in payload.dict(exclude_unset=True, exclude={"item_master_ids"}).items():
        setattr(drink, key, value)
    db.add(drink)
    db.commit()
    db.refresh(drink)
    return drink


@router.delete("/drinks/{drink_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_drink(
    drink_id: str,
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
):
    drink = db.query(Drink).filter(Drink.id == drink_id).one_or_none()
    if not drink:
        raise HTTPException(status_code=404, detail="Drink not found.")
    db.delete(drink)
    db.commit()
    return None


@router.post(
    "/drinks/{drink_id}/images",
    response_model=DrinkImageOut,
    status_code=status.HTTP_201_CREATED,
)
def add_drink_image(
    drink_id: str,
    payload: DrinkImageCreate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
):
    drink = db.query(Drink).filter(Drink.id == drink_id).one_or_none()
    if not drink:
        raise HTTPException(status_code=404, detail="Drink not found.")
    if payload.position < 1 or payload.position > 3:
        raise HTTPException(status_code=400, detail="Image position must be 1-3.")
    image = DrinkImage(drink_id=drink_id, url=payload.url, position=payload.position)
    db.add(image)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Image position already used.")
    db.refresh(image)
    return image


@router.post("/uploads", status_code=status.HTTP_201_CREATED)
def upload_image(
    file: UploadFile = File(...),
    admin: Admin = Depends(require_admin),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are allowed.")
    ext = os.path.splitext(file.filename or "")[1].lower() or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    target_path = os.path.join(UPLOAD_DIR, filename)
    with open(target_path, "wb") as buffer:
        buffer.write(file.file.read())
    return {"url": f"/uploads/{filename}"}
