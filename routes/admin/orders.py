import json
import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import get_db
from models.order import Order, OrderStatusEnum, PaymentStatusEnum, PaymentMethodEnum
from utils.auth import get_current_admin
from schemas.admin_order import AdminOrderListItem, AdminOrderDetail, OrderStatusUpdate, OrderTrackingUpdate, DraftOrderCreate

router = APIRouter(prefix="/admin/orders", tags=["admin-orders"])

VALID_TRANSITIONS: dict[str, list[str]] = {
    "pending": ["confirmed", "cancelled"],
    "confirmed": ["processing", "cancelled"],
    "processing": ["shipped", "cancelled"],
    "shipped": ["delivered"],
    "delivered": ["refunded"],
    "cancelled": [],
    "refunded": [],
}


@router.post("/draft")
def create_draft_order(body: DraftOrderCreate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    import random
    import string

    def gen_number():
        return "DO-" + "".join(random.choices(string.digits, k=6))

    order_number = gen_number()
    while db.query(Order).filter(Order.order_number == order_number).first():
        order_number = gen_number()

    try:
        pm = PaymentMethodEnum(body.payment_method)
    except ValueError:
        pm = PaymentMethodEnum.cod

    items_json = json.dumps([item.model_dump() for item in body.items])
    order = Order(
        order_number=order_number,
        customer_name=body.customer_name,
        customer_phone=body.customer_phone,
        customer_email=body.customer_email or "",
        shipping_address=body.shipping_address,
        city=body.city,
        province=body.province,
        notes=body.notes,
        items=items_json,
        payment_method=pm,
        payment_status=PaymentStatusEnum.pending,
        subtotal=body.subtotal,
        shipping_fee=body.shipping_fee,
        payment_discount=body.payment_discount,
        coupon_discount=0.0,
        total=body.total,
        status=OrderStatusEnum.pending,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return {"id": order.id, "order_number": order.order_number}


@router.get("")
def list_orders(
    status: Optional[str] = None,
    payment_method: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    q = db.query(Order)
    if status:
        q = q.filter(Order.status == status)
    if payment_method:
        q = q.filter(Order.payment_method == payment_method)
    if search:
        term = f"%{search}%"
        q = q.filter(or_(
            Order.order_number.ilike(term),
            Order.customer_name.ilike(term),
            Order.customer_phone.ilike(term),
        ))
    total = q.count()
    orders = q.order_by(Order.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    items = []
    for o in orders:
        try:
            item_list = json.loads(o.items or "[]")
            item_count = len(item_list)
        except Exception:
            item_count = 0
        items.append(AdminOrderListItem(
            id=o.id, order_number=o.order_number, customer_name=o.customer_name,
            customer_phone=o.customer_phone, customer_email=o.customer_email,
            total=o.total, payment_method=o.payment_method.value,
            payment_status=o.payment_status.value, status=o.status.value,
            created_at=o.created_at, item_count=item_count,
        ))

    return {
        "items": [i.model_dump() for i in items],
        "total": total,
        "page": page,
        "pages": math.ceil(total / per_page) if total else 0,
    }


@router.get("/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    o = db.query(Order).filter(Order.id == order_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    try:
        items = json.loads(o.items or "[]")
    except Exception:
        items = []
    return AdminOrderDetail(
        id=o.id, order_number=o.order_number, customer_name=o.customer_name,
        customer_phone=o.customer_phone, customer_email=o.customer_email,
        shipping_address=o.shipping_address, city=o.city, province=o.province, notes=o.notes,
        items=items, subtotal=o.subtotal, shipping_fee=o.shipping_fee,
        payment_discount=o.payment_discount, coupon_discount=o.coupon_discount,
        total=o.total, payment_method=o.payment_method.value,
        payment_status=o.payment_status.value, status=o.status.value,
        tracking_number=o.tracking_number, promo_code=o.promo_code,
        prescription_method=o.prescription_method.value if o.prescription_method else None,
        prescription_url=o.prescription_url, prescription_data=o.prescription_data,
        created_at=o.created_at, updated_at=o.updated_at,
    )


@router.put("/{order_id}/status")
def update_order_status(
    order_id: int,
    body: OrderStatusUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    o = db.query(Order).filter(Order.id == order_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")

    current = o.status.value
    allowed = VALID_TRANSITIONS.get(current, [])
    if body.status not in allowed:
        raise HTTPException(status_code=400, detail=f"Cannot transition from '{current}' to '{body.status}'")

    o.status = body.status
    db.commit()

    from services.email import (
        send_order_processing, send_order_shipped,
        send_order_delivered,
    )
    if body.status == "processing":
        background_tasks.add_task(
            send_order_processing, o.order_number, o.customer_name, o.customer_email
        )
    elif body.status == "shipped":
        background_tasks.add_task(
            send_order_shipped, o.order_number, o.customer_name, o.customer_email, o.tracking_number
        )
    elif body.status == "delivered":
        background_tasks.add_task(
            send_order_delivered, o.order_number, o.customer_name, o.customer_email
        )
    return {"message": "Status updated", "status": body.status}


@router.put("/{order_id}/tracking")
def update_tracking(order_id: int, body: OrderTrackingUpdate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    o = db.query(Order).filter(Order.id == order_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    o.tracking_number = body.tracking_number
    db.commit()
    return {"message": "Tracking number saved"}
