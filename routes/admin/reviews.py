import json
import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.review import Review
from utils.auth import get_current_admin

router = APIRouter(prefix="/admin/reviews", tags=["admin-reviews"])


def _fmt(r: Review) -> dict:
    images = []
    try:
        images = json.loads(r.images or "[]")
    except Exception:
        pass
    return {
        "id": r.id, "product_id": r.product_id,
        "product_name": r.product.name if r.product else "Unknown",
        "order_id": r.order_id, "customer_name": r.customer_name,
        "customer_email": r.customer_email, "rating": r.rating,
        "title": r.title, "body": r.body, "images": images,
        "is_approved": r.is_approved, "is_featured": r.is_featured,
        "created_at": r.created_at.isoformat(),
    }


@router.get("")
def list_reviews(
    is_approved: Optional[bool] = None,
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    q = db.query(Review)
    if is_approved is not None:
        q = q.filter(Review.is_approved == is_approved)
    total = q.count()
    reviews = q.order_by(Review.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return {
        "items": [_fmt(r) for r in reviews],
        "total": total,
        "page": page,
        "pages": math.ceil(total / per_page) if total else 0,
    }


@router.put("/{review_id}/approve")
def approve_review(review_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    r = db.query(Review).filter(Review.id == review_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Review not found")
    r.is_approved = True
    db.commit()
    return {"message": "Approved"}


@router.put("/{review_id}/reject")
def reject_review(review_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    r = db.query(Review).filter(Review.id == review_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Review not found")
    db.delete(r)
    db.commit()
    return {"message": "Rejected and deleted"}


@router.put("/{review_id}/feature")
def feature_review(review_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    r = db.query(Review).filter(Review.id == review_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Review not found")
    r.is_featured = not r.is_featured
    db.commit()
    return {"message": "Featured" if r.is_featured else "Unfeatured", "is_featured": r.is_featured}
