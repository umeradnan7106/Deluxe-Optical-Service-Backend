from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.promo import PromoCode
from schemas.order import CouponValidateRequest, CouponValidateResponse, ShippingRequest, ShippingResponse
from utils.helpers import calculate_shipping

router = APIRouter(prefix="/cart", tags=["cart"])


@router.post("/validate-coupon", response_model=CouponValidateResponse)
def validate_coupon(body: CouponValidateRequest, db: Session = Depends(get_db)):
    promo = (
        db.query(PromoCode)
        .filter(PromoCode.code == body.code.upper(), PromoCode.is_active == True)
        .first()
    )
    if not promo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid or inactive coupon code")

    now = datetime.now(timezone.utc)
    if promo.expires_at and promo.expires_at < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon has expired")

    if promo.max_uses is not None and promo.used_count >= promo.max_uses:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon usage limit reached")

    if promo.min_order and body.subtotal < promo.min_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum order of Rs. {promo.min_order:,.0f} required for this coupon",
        )

    if promo.discount_type.value == "percentage":
        discount_amount = round(body.subtotal * promo.discount_value / 100, 2)
    else:
        discount_amount = min(promo.discount_value, body.subtotal)

    return CouponValidateResponse(
        id=promo.id,
        code=promo.code,
        discount_type=promo.discount_type.value,
        discount_value=promo.discount_value,
        discount_amount=discount_amount,
    )


@router.post("/calculate-shipping", response_model=ShippingResponse)
def get_shipping(body: ShippingRequest):
    fee = calculate_shipping(body.subtotal)
    return ShippingResponse(shipping_fee=fee, is_free=fee == 0)
