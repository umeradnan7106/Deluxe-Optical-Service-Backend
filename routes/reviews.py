import json
import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.review import Review
from models.product import Product
from schemas.review import ReviewCreate, ReviewResponse, ReviewListResponse

router = APIRouter(prefix="/reviews", tags=["reviews"])


def _serialize(r: Review) -> ReviewResponse:
    images = []
    try:
        images = json.loads(r.images or "[]")
    except Exception:
        pass
    return ReviewResponse(
        id=r.id, product_id=r.product_id, order_id=r.order_id,
        customer_name=r.customer_name, rating=r.rating,
        title=r.title, body=r.body, images=images,
        is_approved=r.is_approved, is_featured=r.is_featured,
        created_at=r.created_at,
    )


@router.post("", status_code=201)
def create_review(body: ReviewCreate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == body.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    review = Review(
        product_id=body.product_id,
        order_id=body.order_id,
        customer_name=body.customer_name,
        customer_email=body.customer_email,
        rating=body.rating,
        title=body.title,
        body=body.body,
        images=json.dumps(body.images or []),
        is_approved=False,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return {"id": review.id, "message": "Review submitted for approval"}


@router.get("/product/{product_id}", response_model=ReviewListResponse)
def get_product_reviews(
    product_id: int,
    page: int = 1,
    per_page: int = 10,
    db: Session = Depends(get_db),
):
    q = db.query(Review).filter(Review.product_id == product_id, Review.is_approved == True)
    total = q.count()
    reviews = q.order_by(Review.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return ReviewListResponse(
        items=[_serialize(r) for r in reviews],
        total=total,
        page=page,
        pages=math.ceil(total / per_page) if total else 0,
    )


@router.get("/featured")
def featured_reviews(db: Session = Depends(get_db)):
    reviews = db.query(Review).filter(Review.is_approved == True, Review.is_featured == True).limit(8).all()
    return [_serialize(r) for r in reviews]
