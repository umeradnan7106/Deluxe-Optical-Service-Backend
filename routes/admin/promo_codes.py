from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.promo import PromoCode, DiscountTypeEnum
from utils.auth import get_current_admin

router = APIRouter(prefix="/admin/promo-codes", tags=["admin-promo-codes"])


class PromoCodeCreate(BaseModel):
    code: str
    discount_type: DiscountTypeEnum
    discount_value: float
    min_order: Optional[float] = None
    max_uses: Optional[int] = None
    is_active: bool = True
    expires_at: Optional[datetime] = None


class PromoCodeUpdate(BaseModel):
    code: Optional[str] = None
    discount_type: Optional[DiscountTypeEnum] = None
    discount_value: Optional[float] = None
    min_order: Optional[float] = None
    max_uses: Optional[int] = None
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None


def _serialize(pc: PromoCode) -> dict:
    return {
        "id": pc.id,
        "code": pc.code,
        "discount_type": pc.discount_type.value,
        "discount_value": pc.discount_value,
        "min_order": pc.min_order,
        "max_uses": pc.max_uses,
        "used_count": pc.used_count,
        "is_active": pc.is_active,
        "expires_at": pc.expires_at.isoformat() if pc.expires_at else None,
    }


@router.get("")
def list_promo_codes(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    codes = db.query(PromoCode).order_by(PromoCode.id.desc()).all()
    return [_serialize(pc) for pc in codes]


@router.post("", status_code=201)
def create_promo_code(body: PromoCodeCreate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    existing = db.query(PromoCode).filter(PromoCode.code == body.code.upper()).first()
    if existing:
        raise HTTPException(status_code=409, detail="Promo code already exists")
    pc = PromoCode(**{**body.model_dump(), "code": body.code.upper()})
    db.add(pc)
    db.commit()
    db.refresh(pc)
    return _serialize(pc)


@router.patch("/{code_id}")
def update_promo_code(
    code_id: int,
    body: PromoCodeUpdate,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    pc = db.query(PromoCode).filter(PromoCode.id == code_id).first()
    if not pc:
        raise HTTPException(status_code=404, detail="Promo code not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        if field == "code" and value:
            value = value.upper()
        setattr(pc, field, value)
    db.commit()
    db.refresh(pc)
    return _serialize(pc)


@router.delete("/{code_id}", status_code=204)
def delete_promo_code(code_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    pc = db.query(PromoCode).filter(PromoCode.id == code_id).first()
    if not pc:
        raise HTTPException(status_code=404, detail="Promo code not found")
    db.delete(pc)
    db.commit()
