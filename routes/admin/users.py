import math
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from database import get_db
from models.user import User
from models.order import Order
from utils.auth import get_current_admin

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


@router.get("")
def list_users(
    page: int = 1,
    per_page: int = 20,
    search: str | None = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    q = db.query(User).filter(User.is_admin == False)  # noqa: E712
    if search:
        term = f"%{search}%"
        q = q.filter(or_(User.full_name.ilike(term), User.email.ilike(term), User.phone.ilike(term)))
    total = q.count()
    users = q.order_by(User.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    items = []
    for u in users:
        order_agg = db.query(
            func.count(Order.id).label("total_orders"),
            func.coalesce(func.sum(Order.total), 0).label("total_spent"),
            func.max(Order.created_at).label("last_order_date"),
        ).filter(Order.user_id == u.id).first()

        items.append({
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "phone": u.phone,
            "is_active": u.is_active,
            "is_admin": u.is_admin,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "total_orders": order_agg.total_orders if order_agg else 0,
            "total_spent": float(order_agg.total_spent) if order_agg else 0.0,
            "last_order_date": order_agg.last_order_date.isoformat() if order_agg and order_agg.last_order_date else None,
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "pages": math.ceil(total / per_page) if total else 0,
    }


@router.get("/guests")
def list_guest_orders(
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    q = db.query(Order).filter(Order.user_id == None)  # noqa: E711
    total = q.count()
    orders = q.order_by(Order.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    items = []
    for o in orders:
        items.append({
            "order_number": o.order_number,
            "customer_name": o.customer_name,
            "customer_phone": o.customer_phone,
            "customer_email": o.customer_email,
            "total": o.total,
            "status": o.status.value,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        })

    return {"items": items, "total": total, "page": page}
