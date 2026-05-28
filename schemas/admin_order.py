from typing import Optional, Any
from pydantic import BaseModel
from datetime import datetime


class AdminOrderListItem(BaseModel):
    id: int
    order_number: str
    customer_name: str
    customer_phone: str
    customer_email: Optional[str]
    total: float
    payment_method: str
    payment_status: str
    status: str
    created_at: datetime
    item_count: int


class AdminOrderDetail(BaseModel):
    id: int
    order_number: str
    customer_name: str
    customer_phone: str
    customer_email: Optional[str]
    shipping_address: str
    city: str
    province: str
    notes: Optional[str]
    items: Any
    subtotal: float
    shipping_fee: float
    payment_discount: float
    coupon_discount: float
    total: float
    payment_method: str
    payment_status: str
    status: str
    tracking_number: Optional[str]
    promo_code: Optional[str]
    prescription_method: Optional[str]
    prescription_url: Optional[str]
    prescription_data: Optional[str]
    created_at: datetime
    updated_at: datetime


class OrderStatusUpdate(BaseModel):
    status: str


class OrderTrackingUpdate(BaseModel):
    tracking_number: str
