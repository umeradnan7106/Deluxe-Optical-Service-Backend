from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr


class PrescriptionDataSchema(BaseModel):
    method: str
    right_sph: Optional[float] = None
    right_cyl: Optional[float] = None
    right_axis: Optional[int] = None
    right_add: Optional[float] = None
    left_sph: Optional[float] = None
    left_cyl: Optional[float] = None
    left_axis: Optional[int] = None
    left_add: Optional[float] = None
    pd: Optional[float] = None
    prescription_url: Optional[str] = None


class CartItemSchema(BaseModel):
    product_id: int
    variant_id: int
    quantity: int
    selected_lens_options: List[int] = []
    prescription: Optional[PrescriptionDataSchema] = None


class OrderCreate(BaseModel):
    customer_name: str
    customer_email: EmailStr
    customer_phone: str
    shipping_address: str
    city: str
    province: str
    payment_method: str
    items: List[CartItemSchema]
    promo_code: Optional[str] = None
    notes: Optional[str] = None
    prescription_method: Optional[str] = None
    prescription_url: Optional[str] = None
    prescription_data: Optional[PrescriptionDataSchema] = None


class OrderItemResponse(BaseModel):
    product_id: int
    product_name: str
    variant_id: int
    color_name: str
    quantity: int
    base_price: float
    sale_price: Optional[float] = None
    lens_options_price: float
    selected_lens_options: List[int]
    prescription: Optional[Any] = None


class OrderResponse(BaseModel):
    id: int
    order_number: str
    status: str
    payment_method: str
    payment_status: str
    customer_name: str
    customer_email: str
    customer_phone: str
    shipping_address: str
    city: str
    province: str
    subtotal: float
    shipping_fee: float
    payment_discount: float
    coupon_discount: float
    total: float
    notes: Optional[str] = None
    tracking_number: Optional[str] = None
    promo_code: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class OrderTrackResponse(BaseModel):
    order_number: str
    status: str
    payment_method: str
    customer_name: str
    city: str
    province: str
    total: float
    tracking_number: Optional[str] = None
    items_summary: List[dict]
    timeline: List[dict]
    created_at: str


class CouponValidateRequest(BaseModel):
    code: str
    subtotal: float


class CouponValidateResponse(BaseModel):
    id: int
    code: str
    discount_type: str
    discount_value: float
    discount_amount: float


class ShippingRequest(BaseModel):
    subtotal: float


class ShippingResponse(BaseModel):
    shipping_fee: float
    is_free: bool
