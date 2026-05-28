from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.promo import FAQ, FAQCategoryEnum
from utils.auth import get_current_admin

router = APIRouter(prefix="/admin/faqs", tags=["admin-faqs"])


class FAQCreate(BaseModel):
    question: str
    answer: str
    category: FAQCategoryEnum
    sort_order: int = 0
    is_active: bool = True


class FAQUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    category: Optional[FAQCategoryEnum] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class ReorderItem(BaseModel):
    id: int
    sort_order: int


def _serialize(f: FAQ) -> dict:
    return {
        "id": f.id,
        "question": f.question,
        "answer": f.answer,
        "category": f.category.value,
        "sort_order": f.sort_order,
        "is_active": f.is_active,
    }


@router.get("")
def list_faqs(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    faqs = db.query(FAQ).order_by(FAQ.sort_order).all()
    return [_serialize(f) for f in faqs]


@router.post("", status_code=201)
def create_faq(body: FAQCreate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    faq = FAQ(**body.model_dump())
    db.add(faq)
    db.commit()
    db.refresh(faq)
    return _serialize(faq)


@router.patch("/{faq_id}")
def update_faq(faq_id: int, body: FAQUpdate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(faq, field, value)
    db.commit()
    db.refresh(faq)
    return _serialize(faq)


@router.delete("/{faq_id}", status_code=204)
def delete_faq(faq_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    db.delete(faq)
    db.commit()


@router.put("/reorder")
def reorder_faqs(items: List[ReorderItem], db: Session = Depends(get_db), _=Depends(get_current_admin)):
    for item in items:
        faq = db.query(FAQ).filter(FAQ.id == item.id).first()
        if faq:
            faq.sort_order = item.sort_order
    db.commit()
    return {"ok": True}
