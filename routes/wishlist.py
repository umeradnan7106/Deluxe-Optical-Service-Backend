from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.promo import WishlistItem
from models.product import Product
from schemas.product import ProductListItem
from utils.auth import get_current_user
from routes.products import _thumbnail_url, _avg_rating

router = APIRouter(prefix="/wishlist", tags=["wishlist"])


@router.get("", response_model=list[ProductListItem])
def get_wishlist(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(WishlistItem).filter(WishlistItem.user_id == current_user.id).all()
    product_ids = [i.product_id for i in items]
    products = db.query(Product).filter(Product.id.in_(product_ids), Product.is_active == True).all()
    result = []
    for p in products:
        avg, count = _avg_rating(p, db)
        result.append(ProductListItem(
            id=p.id, name=p.name, slug=p.slug, sku=p.sku,
            category=p.category.value, gender=p.gender.value,
            base_price=p.base_price, sale_price=p.sale_price,
            is_featured=p.is_featured, thumbnail_url=_thumbnail_url(p),
            average_rating=avg, review_count=count,
        ))
    return result


@router.post("", status_code=status.HTTP_201_CREATED)
def add_to_wishlist(product_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing = db.query(WishlistItem).filter(
        WishlistItem.user_id == current_user.id, WishlistItem.product_id == product_id
    ).first()
    if existing:
        return {"message": "Already in wishlist"}

    db.add(WishlistItem(user_id=current_user.id, product_id=product_id))
    db.commit()
    return {"message": "Added to wishlist"}


@router.delete("/{product_id}")
def remove_from_wishlist(product_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(WishlistItem).filter(
        WishlistItem.user_id == current_user.id, WishlistItem.product_id == product_id
    ).first()
    if item:
        db.delete(item)
        db.commit()
    return {"message": "Removed from wishlist"}
