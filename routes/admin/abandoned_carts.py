import json
import math
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models.order import AbandonedCart
from utils.auth import get_current_admin

router = APIRouter(prefix="/admin/abandoned-carts", tags=["admin-abandoned-carts"])


@router.get("")
def list_abandoned_carts(
    email_sent: Optional[bool] = None,
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    q = db.query(AbandonedCart)
    if email_sent is not None:
        q = q.filter(AbandonedCart.email_sent == email_sent)
    total = q.count()
    total_all = db.query(func.count(AbandonedCart.id)).scalar() or 0
    total_sent = db.query(func.count(AbandonedCart.id)).filter(AbandonedCart.email_sent == True).scalar() or 0  # noqa: E712
    carts = q.order_by(AbandonedCart.updated_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    items = []
    for c in carts:
        try:
            cart_items = json.loads(c.cart_data or "[]")
            item_count = len(cart_items) if isinstance(cart_items, list) else 0
        except Exception:
            item_count = 0
        items.append({
            "id": c.id,
            "session_id": c.session_id,
            "email": c.email,
            "phone": c.phone,
            "item_count": item_count,
            "email_sent": c.email_sent,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "pages": math.ceil(total / per_page) if total else 0,
        "stats": {
            "total": total_all,
            "email_sent": total_sent,
            "not_contacted": total_all - total_sent,
        },
    }
