import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.lens import LensOption, LensTypeEnum
from utils.auth import get_current_admin

router = APIRouter(prefix="/admin/lens-options", tags=["admin-lens-options"])


class LensOptionCreate(BaseModel):
    name: str
    type: LensTypeEnum
    sub_type: Optional[str] = None
    price: float
    description: Optional[str] = None
    sub_options: Optional[str] = None  # JSON string of [{name, price}]
    is_active: bool = True
    sort_order: int = 0


class LensOptionUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[LensTypeEnum] = None
    sub_type: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    sub_options: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class ReorderItem(BaseModel):
    id: int
    sort_order: int


def _serialize(lo: LensOption) -> dict:
    sub_opts = None
    if lo.sub_options:
        try:
            sub_opts = json.loads(lo.sub_options)
        except Exception:
            sub_opts = None
    return {
        "id": lo.id,
        "name": lo.name,
        "type": lo.type.value,
        "sub_type": lo.sub_type,
        "price": lo.price,
        "description": lo.description,
        "sub_options": sub_opts,
        "is_active": lo.is_active,
        "sort_order": lo.sort_order,
    }


@router.get("")
def list_lens_options(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    options = db.query(LensOption).order_by(LensOption.type, LensOption.sort_order).all()
    return [_serialize(o) for o in options]


@router.post("", status_code=201)
def create_lens_option(body: LensOptionCreate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    lo = LensOption(**body.model_dump())
    db.add(lo)
    db.commit()
    db.refresh(lo)
    return _serialize(lo)


@router.patch("/{option_id}")
def update_lens_option(option_id: int, body: LensOptionUpdate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    lo = db.query(LensOption).filter(LensOption.id == option_id).first()
    if not lo:
        raise HTTPException(status_code=404, detail="Lens option not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(lo, field, value)
    db.commit()
    db.refresh(lo)
    return _serialize(lo)


@router.delete("/{option_id}", status_code=204)
def delete_lens_option(option_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    lo = db.query(LensOption).filter(LensOption.id == option_id).first()
    if not lo:
        raise HTTPException(status_code=404, detail="Lens option not found")
    db.delete(lo)
    db.commit()


@router.put("/reorder")
def reorder_lens_options(items: List[ReorderItem], db: Session = Depends(get_db), _=Depends(get_current_admin)):
    for item in items:
        lo = db.query(LensOption).filter(LensOption.id == item.id).first()
        if lo:
            lo.sort_order = item.sort_order
    db.commit()
    return {"ok": True}
