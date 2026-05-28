import json
import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import get_db
from models.product import Product, ProductVariant, ProductImage
from models.lens import LensOption, ProductLensOption
from schemas.admin_product import ProductCreate, ProductUpdate, VariantCreate, VariantUpdate, ImageReorder, LensOptionAssign
from schemas.product import ProductDetail, ProductListItem, VariantResponse, ImageResponse, LensOptionGrouped, LensOptionResponse, ProductListResponse
from utils.auth import get_current_admin
from utils.helpers import generate_slug
from services.cloudinary import upload_image, delete_image

router = APIRouter(prefix="/admin/products", tags=["admin-products"])


@router.get("", response_model=ProductListResponse)
def list_products_admin(
    search: Optional[str] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    q = db.query(Product)
    if search:
        term = f"%{search}%"
        q = q.filter(or_(Product.name.ilike(term), Product.sku.ilike(term)))
    if category:
        q = q.filter(Product.category == category)
    if is_active is not None:
        q = q.filter(Product.is_active == is_active)

    total = q.count()
    products = q.order_by(Product.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    items = [
        ProductListItem(
            id=p.id, name=p.name, slug=p.slug, sku=p.sku,
            category=p.category.value, gender=p.gender.value,
            base_price=p.base_price, sale_price=p.sale_price,
            is_featured=p.is_featured, thumbnail_url=None,
            average_rating=None, review_count=0,
        )
        for p in products
    ]
    return ProductListResponse(items=items, total=total, page=page, page_size=per_page, pages=math.ceil(total / per_page) if total else 0)


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_product(body: ProductCreate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    import traceback
    try:
        slug = generate_slug(body.name)
        existing = db.query(Product).filter(Product.slug == slug).first()
        if existing:
            slug = f"{slug}-{body.sku.lower()}"

        product = Product(
            name=body.name, slug=slug, sku=body.sku, brand=body.brand,
            category=body.category, gender=body.gender,
            frame_shape=body.frame_shape, rim_type=body.rim_type, material=body.material,
            base_price=body.base_price, sale_price=body.sale_price,
            bullets=json.dumps(body.bullets or []),
            description=body.description,
            is_prescription_required=body.is_prescription_required,
            is_active=body.is_active, is_featured=body.is_featured,
            meta_title=body.meta_title, meta_description=body.meta_description,
            frame_width_mm=body.frame_width_mm, lens_width_mm=body.lens_width_mm,
            bridge_mm=body.bridge_mm, temple_mm=body.temple_mm, lens_height_mm=body.lens_height_mm,
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return {"id": product.id, "slug": product.slug}
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        print(f"[create_product] ERROR: {exc}")
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch("/{product_id}")
def update_product(product_id: int, body: ProductUpdate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    for field, value in body.model_dump(exclude_none=True).items():
        if field == "bullets":
            setattr(product, field, json.dumps(value))
        else:
            setattr(product, field, value)
    db.commit()
    return {"message": "Updated"}


@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Not found")
    product.is_active = False
    db.commit()
    return {"message": "Deactivated"}


@router.post("/{product_id}/variants", status_code=status.HTTP_201_CREATED)
def create_variant(product_id: int, body: VariantCreate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    variant = ProductVariant(product_id=product_id, **body.model_dump())
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return {"id": variant.id}


@router.patch("/variants/{variant_id}")
def update_variant(variant_id: int, body: VariantUpdate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(variant, field, value)
    db.commit()
    return {"message": "Updated"}


@router.delete("/variants/{variant_id}")
def delete_variant(variant_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if variant:
        db.delete(variant)
        db.commit()
    return {"message": "Deleted"}


@router.get("/{product_id}")
def get_product_admin(product_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    import json as _json
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Not found")
    variants = []
    for v in product.variants:
        images = [
            {"id": img.id, "url": img.url, "public_id": img.public_id, "sort_order": img.sort_order}
            for img in sorted(v.images, key=lambda x: x.sort_order)
        ]
        variants.append({
            "id": v.id, "color_name": v.color_name, "color_hex": v.color_hex,
            "size_label": v.size_label, "sku_variant": v.sku_variant,
            "price": v.price, "stock": v.stock, "is_active": v.is_active, "images": images,
        })
    lens_option_ids = [
        plo.lens_option_id for plo in
        db.query(ProductLensOption).filter(ProductLensOption.product_id == product_id).all()
    ]
    return {
        "id": product.id, "name": product.name, "slug": product.slug, "sku": product.sku,
        "brand": product.brand, "category": product.category.value, "gender": product.gender.value,
        "frame_shape": product.frame_shape, "rim_type": product.rim_type, "material": product.material,
        "base_price": product.base_price, "sale_price": product.sale_price,
        "bullets": _json.loads(product.bullets or "[]"),
        "description": product.description or "",
        "is_prescription_required": product.is_prescription_required,
        "is_active": product.is_active, "is_featured": product.is_featured,
        "meta_title": product.meta_title, "meta_description": product.meta_description,
        "frame_width_mm": product.frame_width_mm, "lens_width_mm": product.lens_width_mm,
        "bridge_mm": product.bridge_mm, "temple_mm": product.temple_mm, "lens_height_mm": product.lens_height_mm,
        "variants": variants, "lens_option_ids": lens_option_ids,
    }


@router.post("/{product_id}/images", status_code=status.HTTP_201_CREATED)
async def upload_product_image(
    product_id: int,
    variant_id: Optional[int] = None,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    if variant_id is None:
        first_variant = db.query(ProductVariant).filter(ProductVariant.product_id == product_id).first()
        if not first_variant:
            raise HTTPException(status_code=400, detail="Create a variant before uploading images")
        variant_id = first_variant.id
    result = await upload_image(file, "products")
    sort_order = db.query(ProductImage).filter(ProductImage.variant_id == variant_id).count()
    img = ProductImage(
        variant_id=variant_id,
        url=result["url"],
        public_id=result["public_id"],
        sort_order=sort_order,
    )
    db.add(img)
    db.commit()
    db.refresh(img)
    return {"id": img.id, "url": img.url}


@router.delete("/images/{image_id}")
def delete_product_image(image_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    img = db.query(ProductImage).filter(ProductImage.id == image_id).first()
    if img:
        if img.public_id:
            delete_image(img.public_id)
        db.delete(img)
        db.commit()
    return {"message": "Deleted"}


@router.put("/{product_id}/images/reorder")
def reorder_images(product_id: int, body: ImageReorder, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    for idx, image_id in enumerate(body.image_ids):
        img = db.query(ProductImage).filter(ProductImage.id == image_id).first()
        if img:
            img.sort_order = idx
    db.commit()
    return {"message": "Reordered"}


@router.put("/{product_id}/lens-options")
def assign_lens_options(product_id: int, body: LensOptionAssign, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    db.query(ProductLensOption).filter(ProductLensOption.product_id == product_id).delete()
    for lo_id in body.lens_option_ids:
        db.add(ProductLensOption(product_id=product_id, lens_option_id=lo_id))
    db.commit()
    return {"message": "Lens options assigned"}
