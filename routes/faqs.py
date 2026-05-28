from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.promo import FAQ

router = APIRouter(prefix="/faqs", tags=["faqs"])


@router.get("")
def list_faqs(category: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(FAQ).filter(FAQ.is_active == True)
    if category and category != "all":
        q = q.filter(FAQ.category == category)
    faqs = q.order_by(FAQ.sort_order).all()
    return [
        {
            "id": f.id, "question": f.question, "answer": f.answer,
            "category": f.category.value, "sort_order": f.sort_order,
        }
        for f in faqs
    ]
