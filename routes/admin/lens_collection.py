import json
import os
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.lens import LensCollection
from utils.auth import get_current_admin

router = APIRouter(prefix="/admin/lens-collections", tags=["admin-lens-collections"])


class LensCollectionCreate(BaseModel):
    name: str
    video_url: str
    description: Optional[str] = None
    bullets: Optional[List[str]] = None
    price_from: float
    color_dot: str
    is_active: bool = True
    sort_order: int = 0


class LensCollectionUpdate(BaseModel):
    name: Optional[str] = None
    video_url: Optional[str] = None
    description: Optional[str] = None
    bullets: Optional[List[str]] = None
    price_from: Optional[float] = None
    color_dot: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class ReorderItem(BaseModel):
    id: int
    sort_order: int


def _serialize(lc: LensCollection) -> dict:
    bullets = []
    try:
        bullets = json.loads(lc.bullets or "[]")
    except Exception:
        pass
    return {
        "id": lc.id,
        "name": lc.name,
        "video_url": lc.video_url,
        "description": lc.description,
        "bullets": bullets,
        "price_from": lc.price_from,
        "color_dot": lc.color_dot,
        "is_active": lc.is_active,
        "sort_order": lc.sort_order,
    }


@router.get("")
def list_collections(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    collections = db.query(LensCollection).order_by(LensCollection.sort_order).all()
    return [_serialize(lc) for lc in collections]


@router.post("", status_code=201)
def create_collection(body: LensCollectionCreate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    data = body.model_dump()
    data["bullets"] = json.dumps(data.get("bullets") or [])
    lc = LensCollection(**data)
    db.add(lc)
    db.commit()
    db.refresh(lc)
    return _serialize(lc)


@router.patch("/{collection_id}")
def update_collection(
    collection_id: int,
    body: LensCollectionUpdate,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    lc = db.query(LensCollection).filter(LensCollection.id == collection_id).first()
    if not lc:
        raise HTTPException(status_code=404, detail="Lens collection not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        if field == "bullets":
            value = json.dumps(value or [])
        setattr(lc, field, value)
    db.commit()
    db.refresh(lc)
    return _serialize(lc)


@router.delete("/{collection_id}", status_code=204)
def delete_collection(collection_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    lc = db.query(LensCollection).filter(LensCollection.id == collection_id).first()
    if not lc:
        raise HTTPException(status_code=404, detail="Lens collection not found")
    db.delete(lc)
    db.commit()


@router.put("/reorder")
def reorder_collections(items: List[ReorderItem], db: Session = Depends(get_db), _=Depends(get_current_admin)):
    for item in items:
        lc = db.query(LensCollection).filter(LensCollection.id == item.id).first()
        if lc:
            lc.sort_order = item.sort_order
    db.commit()
    return {"ok": True}


@router.post("/upload-video")
async def upload_video(
    file: UploadFile = File(...),
    _=Depends(get_current_admin),
):
    try:
        import cloudinary
        import cloudinary.uploader
        cloudinary.config(
            cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
            api_key=os.environ.get("CLOUDINARY_API_KEY"),
            api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
        )
        contents = await file.read()
        result = cloudinary.uploader.upload(
            contents,
            resource_type="video",
            folder="deluxe-opt/lens-collections",
        )
        return {"url": result["secure_url"], "public_id": result["public_id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
