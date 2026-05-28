import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.product import ProductVariant, Product
from utils.auth import get_current_admin

router = APIRouter(prefix="/admin/inventory", tags=["admin-inventory"])


class StockUpdate(BaseModel):
    stock: int


@router.get("")
def list_inventory(
    status_filter: Optional[str] = None,
    page: int = 1,
    per_page: int = 50,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    q = db.query(ProductVariant).join(Product).filter(Product.is_active == True, ProductVariant.is_active == True)

    variants = q.all()
    result = []
    for v in variants:
        stock_status = "out_of_stock" if v.stock == 0 else "low_stock" if v.stock <= (v.product.low_stock_threshold or 5) else "in_stock"
        if status_filter and stock_status != status_filter:
            continue
        result.append({
            "variant_id": v.id,
            "product_id": v.product_id,
            "product_name": v.product.name,
            "sku": v.product.sku,
            "sku_variant": v.sku_variant,
            "color_name": v.color_name,
            "size_label": v.size_label,
            "stock": v.stock,
            "low_stock_threshold": v.product.low_stock_threshold,
            "status": stock_status,
        })

    total = len(result)
    paginated = result[(page - 1) * per_page : page * per_page]
    return {"items": paginated, "total": total, "page": page, "page_size": per_page, "pages": math.ceil(total / per_page) if total else 0}


@router.put("/{variant_id}")
def update_stock(variant_id: int, body: StockUpdate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    variant.stock = body.stock
    db.commit()
    return {"message": "Stock updated", "new_stock": body.stock}
