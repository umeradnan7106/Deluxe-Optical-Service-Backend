import json
import math
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from database import get_db
from models.product import Product, ProductImage, ProductVariant
from models.lens import LensOption, ProductLensOption
from models.review import Review
from schemas.product import ProductListItem, ProductDetail, ProductListResponse, VariantResponse, ImageResponse, LensOptionGrouped, LensOptionResponse

router = APIRouter(prefix="/products", tags=["products"])


def _thumbnail_url(product: Product) -> Optional[str]:
    if product.variants:
        for variant in product.variants:
            if variant.images:
                return sorted(variant.images, key=lambda i: i.sort_order)[0].url
    return None


def _avg_rating(product: Product, db: Session) -> tuple[Optional[float], int]:
    result = db.query(
        func.avg(Review.rating),
        func.count(Review.id),
    ).filter(Review.product_id == product.id, Review.is_approved == True).first()
    avg = round(float(result[0]), 1) if result[0] else None
    count = result[1] or 0
    return avg, count


def _grouped_lens_options(product_id: int, db: Session) -> LensOptionGrouped:
    rows = (
        db.query(LensOption)
        .join(ProductLensOption, ProductLensOption.lens_option_id == LensOption.id)
        .filter(ProductLensOption.product_id == product_id, LensOption.is_active == True)
        .all()
    )
    grouped = LensOptionGrouped()
    for lo in rows:
        lo_type_val = lo.type.value if lo.type is not None else "addon"
        item = LensOptionResponse.model_validate({
            "id": lo.id,
            "name": lo.name,
            "lens_type": lo_type_val,
            "price": lo.price,
            "description": lo.description,
        })
        if lo_type_val == "lens-type":
            grouped.lens_type.append(item)
        elif lo_type_val == "coating":
            grouped.coating.append(item)
        else:
            grouped.addon.append(item)
    return grouped


@router.get("", response_model=ProductListResponse)
def list_products(
    category: Optional[str] = None,
    gender: Optional[str] = None,
    frame_shape: Optional[str] = None,
    material: Optional[str] = None,
    rim_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    is_featured: Optional[bool] = None,
    sale: Optional[bool] = None,
    search: Optional[str] = Query(default=None, alias="q"),
    sort: str = "newest",
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db),
):
    q = db.query(Product).filter(Product.is_active == True)

    if category:
        q = q.filter(Product.category == category)
    if gender:
        q = q.filter(Product.gender == gender)
    if frame_shape:
        q = q.filter(Product.frame_shape == frame_shape)
    if material:
        q = q.filter(Product.material == material)
    if rim_type:
        q = q.filter(Product.rim_type == rim_type)
    if min_price is not None:
        q = q.filter(func.coalesce(Product.sale_price, Product.base_price) >= min_price)
    if max_price is not None:
        q = q.filter(func.coalesce(Product.sale_price, Product.base_price) <= max_price)
    if is_featured is not None:
        q = q.filter(Product.is_featured == is_featured)
    if sale:
        q = q.filter(Product.sale_price.isnot(None))
    if search:
        term = f"%{search}%"
        q = q.filter(or_(Product.name.ilike(term), Product.brand.ilike(term), Product.sku.ilike(term)))

    sort_map = {
        "newest": Product.created_at.desc(),
        "price_asc": func.coalesce(Product.sale_price, Product.base_price).asc(),
        "price_desc": func.coalesce(Product.sale_price, Product.base_price).desc(),
    }
    q = q.order_by(sort_map.get(sort, Product.created_at.desc()))

    total = q.count()
    products = q.offset((page - 1) * per_page).limit(per_page).all()

    items = []
    for p in products:
        avg, count = _avg_rating(p, db)
        items.append(ProductListItem(
            id=p.id, name=p.name, slug=p.slug, sku=p.sku,
            category=p.category.value, gender=p.gender.value,
            base_price=p.base_price, sale_price=p.sale_price,
            is_featured=p.is_featured, thumbnail_url=_thumbnail_url(p),
            average_rating=avg, review_count=count,
        ))

    return ProductListResponse(
        items=items, total=total, page=page,
        page_size=per_page, pages=math.ceil(total / per_page) if total else 0,
    )


@router.get("/featured", response_model=list[ProductListItem])
def featured_products(db: Session = Depends(get_db)):
    products = (
        db.query(Product)
        .filter(Product.is_active == True, Product.is_featured == True)
        .order_by(Product.created_at.desc())
        .limit(8)
        .all()
    )
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


@router.get("/{slug}", response_model=ProductDetail)
def get_product(slug: str, db: Session = Depends(get_db)):
    from fastapi import HTTPException, status
    product = db.query(Product).filter(Product.slug == slug, Product.is_active == True).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    avg, count = _avg_rating(product, db)

    variants = []
    for v in product.variants:
        images = [
            ImageResponse(id=i.id, url=i.url, alt_text=i.alt_text, sort_order=i.sort_order)
            for i in sorted(v.images, key=lambda x: x.sort_order)
        ]
        variants.append(VariantResponse(
            id=v.id, color_name=v.color_name, color_hex=v.color_hex,
            stock=v.stock, images=images,
        ))

    try:
        bullets = json.loads(product.bullets) if product.bullets else []
    except Exception:
        bullets = []

    return ProductDetail(
        id=product.id, name=product.name, slug=product.slug, sku=product.sku,
        category=product.category.value, gender=product.gender.value,
        frame_shape=product.frame_shape.value if product.frame_shape else None,
        rim_type=product.rim_type.value if product.rim_type else None,
        material=product.material, brand=product.brand,
        base_price=product.base_price, sale_price=product.sale_price,
        frame_width_mm=product.frame_width_mm,
        lens_width_mm=product.lens_width_mm,
        bridge_mm=product.bridge_mm,
        temple_mm=product.temple_mm,
        lens_height_mm=product.lens_height_mm,
        bullets=bullets, description=product.description,
        is_prescription_required=product.is_prescription_required,
        is_featured=product.is_featured, is_active=product.is_active,
        variants=variants,
        lens_options=_grouped_lens_options(product.id, db),
        average_rating=avg, review_count=count,
    )


@router.get("/{slug}/related", response_model=list[ProductListItem])
def related_products(slug: str, db: Session = Depends(get_db)):
    from fastapi import HTTPException, status
    product = db.query(Product).filter(Product.slug == slug).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    products = (
        db.query(Product)
        .filter(Product.category == product.category, Product.is_active == True, Product.id != product.id)
        .order_by(func.random())
        .limit(4)
        .all()
    )
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
