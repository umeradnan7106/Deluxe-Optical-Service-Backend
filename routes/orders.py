import json
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session

from database import get_db
from models.order import Order, OrderStatusEnum
from models.product import ProductVariant
from models.lens import LensOption
from models.promo import PromoCode
from schemas.order import OrderCreate, OrderResponse, OrderTrackResponse
from utils.auth import get_current_user, get_optional_user
from utils.helpers import generate_order_number, calculate_shipping, calculate_payment_discount

router = APIRouter(prefix="/orders", tags=["orders"])

ORDER_STATUS_STEPS = ["pending", "confirmed", "processing", "shipped", "delivered"]


def _build_timeline(order: Order) -> list[dict]:
    labels = {
        "pending": "Order Placed",
        "confirmed": "Order Confirmed",
        "processing": "Processing",
        "shipped": "Shipped",
        "delivered": "Delivered",
    }
    current_idx = ORDER_STATUS_STEPS.index(order.status.value) if order.status.value in ORDER_STATUS_STEPS else 0
    return [
        {
            "status": s,
            "label": labels[s],
            "completed": i <= current_idx,
            "current": i == current_idx,
        }
        for i, s in enumerate(ORDER_STATUS_STEPS)
    ]


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(body: OrderCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user=Depends(get_optional_user)):
    # Validate payment method
    valid_methods = {"cod", "easypaisa", "jazzcash", "bank_transfer"}
    if body.payment_method not in valid_methods:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment method")

    subtotal = 0.0
    items_data = []

    for item in body.items:
        variant = db.query(ProductVariant).filter(ProductVariant.id == item.variant_id).first()
        if not variant:
            raise HTTPException(status_code=404, detail=f"Variant {item.variant_id} not found")
        if variant.stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for variant {item.variant_id}")

        product = variant.product
        price = variant.price if variant.price else (product.sale_price or product.base_price)

        lens_price = 0.0
        if item.selected_lens_options:
            lens_opts = db.query(LensOption).filter(LensOption.id.in_(item.selected_lens_options)).all()
            lens_price = sum(lo.price for lo in lens_opts)

        line_total = (price + lens_price) * item.quantity
        subtotal += line_total

        items_data.append({
            "product_id": product.id,
            "product_name": product.name,
            "variant_id": variant.id,
            "color_name": variant.color_name,
            "quantity": item.quantity,
            "base_price": product.base_price,
            "sale_price": product.sale_price,
            "lens_options_price": lens_price,
            "selected_lens_options": item.selected_lens_options,
            "prescription": item.prescription.model_dump() if item.prescription else None,
        })

    # Coupon
    coupon_discount = 0.0
    promo = None
    if body.promo_code:
        promo = db.query(PromoCode).filter(
            PromoCode.code == body.promo_code.upper(), PromoCode.is_active == True
        ).first()
        if promo:
            now = datetime.now(timezone.utc)
            if (not promo.expires_at or promo.expires_at > now) and \
               (promo.max_uses is None or promo.used_count < promo.max_uses) and \
               (not promo.min_order or subtotal >= promo.min_order):
                if promo.discount_type.value == "percentage":
                    coupon_discount = round(subtotal * promo.discount_value / 100, 2)
                else:
                    coupon_discount = min(promo.discount_value, subtotal)

    shipping_fee = calculate_shipping(subtotal)
    payment_discount = calculate_payment_discount(subtotal, body.payment_method)
    total = subtotal + shipping_fee - payment_discount - coupon_discount

    order_number = generate_order_number(db)

    order = Order(
        order_number=order_number,
        user_id=current_user.id if current_user else None,
        customer_name=body.customer_name,
        customer_email=body.customer_email,
        customer_phone=body.customer_phone,
        shipping_address=body.shipping_address,
        city=body.city,
        province=body.province,
        payment_method=body.payment_method,
        items=json.dumps(items_data),
        subtotal=subtotal,
        shipping_fee=shipping_fee,
        payment_discount=payment_discount,
        coupon_discount=coupon_discount,
        total=total,
        promo_code=body.promo_code,
        notes=body.notes,
        prescription_method=body.prescription_method,
        prescription_url=body.prescription_url,
        prescription_data=json.dumps(body.prescription_data.model_dump()) if body.prescription_data else None,
    )
    db.add(order)

    # Decrement stock and increment promo usage
    for item in body.items:
        variant = db.query(ProductVariant).filter(ProductVariant.id == item.variant_id).first()
        variant.stock -= item.quantity

    if promo and coupon_discount > 0:
        promo.used_count += 1

    db.commit()
    db.refresh(order)

    from services.email import send_order_confirmation
    background_tasks.add_task(
        send_order_confirmation, order.order_number, order.customer_name,
        order.customer_email, order.total,
    )

    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        status=order.status.value,
        payment_method=order.payment_method.value,
        payment_status=order.payment_status.value,
        customer_name=order.customer_name,
        customer_email=order.customer_email,
        customer_phone=order.customer_phone,
        shipping_address=order.shipping_address,
        city=order.city,
        province=order.province,
        subtotal=order.subtotal,
        shipping_fee=order.shipping_fee,
        payment_discount=order.payment_discount,
        coupon_discount=order.coupon_discount,
        total=order.total,
        notes=order.notes,
        tracking_number=order.tracking_number,
        promo_code=order.promo_code,
        created_at=order.created_at.isoformat(),
    )


@router.get("/track", response_model=OrderTrackResponse)
def track_order(
    order_number: Optional[str] = Query(default=None),
    phone: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    if not order_number and not phone:
        raise HTTPException(status_code=400, detail="Provide order_number or phone")

    q = db.query(Order)
    if order_number:
        q = q.filter(Order.order_number == order_number)
    else:
        q = q.filter(Order.customer_phone == phone)

    order = q.first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    try:
        items_data = json.loads(order.items) if order.items else []
    except Exception:
        items_data = []

    items_summary = [
        {"product_name": i.get("product_name"), "quantity": i.get("quantity"), "color": i.get("color_name")}
        for i in items_data
    ]

    return OrderTrackResponse(
        order_number=order.order_number,
        status=order.status.value,
        payment_method=order.payment_method.value,
        customer_name=order.customer_name,
        city=order.city,
        province=order.province,
        total=order.total,
        tracking_number=order.tracking_number,
        items_summary=items_summary,
        timeline=_build_timeline(order),
        created_at=order.created_at.isoformat(),
    )


@router.get("/my-orders", response_model=list[OrderResponse])
def my_orders(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    orders = (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return [
        OrderResponse(
            id=o.id, order_number=o.order_number, status=o.status.value,
            payment_method=o.payment_method.value, payment_status=o.payment_status.value,
            customer_name=o.customer_name, customer_email=o.customer_email,
            customer_phone=o.customer_phone, shipping_address=o.shipping_address,
            city=o.city, province=o.province,
            subtotal=o.subtotal, shipping_fee=o.shipping_fee,
            payment_discount=o.payment_discount, coupon_discount=o.coupon_discount,
            total=o.total, notes=o.notes, tracking_number=o.tracking_number,
            promo_code=o.promo_code, created_at=o.created_at.isoformat(),
        )
        for o in orders
    ]


@router.get("/{order_number}", response_model=OrderResponse)
def get_order(order_number: str, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    order = (
        db.query(Order)
        .filter(Order.order_number == order_number, Order.user_id == current_user.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return OrderResponse(
        id=order.id, order_number=order.order_number, status=order.status.value,
        payment_method=order.payment_method.value, payment_status=order.payment_status.value,
        customer_name=order.customer_name, customer_email=order.customer_email,
        customer_phone=order.customer_phone, shipping_address=order.shipping_address,
        city=order.city, province=order.province,
        subtotal=order.subtotal, shipping_fee=order.shipping_fee,
        payment_discount=order.payment_discount, coupon_discount=order.coupon_discount,
        total=order.total, notes=order.notes, tracking_number=order.tracking_number,
        promo_code=order.promo_code, created_at=order.created_at.isoformat(),
    )
