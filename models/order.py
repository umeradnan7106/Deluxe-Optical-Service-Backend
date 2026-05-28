import enum
from sqlalchemy import Column, Integer, String, Boolean, Float, Text, Enum, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from database import Base


class PaymentMethodEnum(str, enum.Enum):
    cod = "cod"
    easypaisa = "easypaisa"
    jazzcash = "jazzcash"
    bank_transfer = "bank_transfer"


class PaymentStatusEnum(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"
    refunded = "refunded"


class OrderStatusEnum(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    processing = "processing"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"
    refunded = "refunded"


class PrescriptionMethodEnum(str, enum.Enum):
    upload = "upload"
    manual = "manual"
    later = "later"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(20), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    customer_name = Column(String(255), nullable=False)
    customer_phone = Column(String(20), nullable=False, index=True)
    customer_email = Column(String(255), nullable=False)
    shipping_address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False)
    province = Column(String(100), nullable=False)
    notes = Column(Text, nullable=True)

    # Cart items stored as JSON array
    items = Column(Text, nullable=False)

    # Prescription
    prescription_method = Column(Enum(PrescriptionMethodEnum), nullable=True)
    prescription_url = Column(String(512), nullable=True)
    prescription_data = Column(Text, nullable=True)  # JSON

    # Financials
    payment_method = Column(Enum(PaymentMethodEnum), nullable=False)
    payment_status = Column(Enum(PaymentStatusEnum), default=PaymentStatusEnum.pending)
    subtotal = Column(Float, nullable=False)
    shipping_fee = Column(Float, default=0.0)
    payment_discount = Column(Float, default=0.0)
    coupon_discount = Column(Float, default=0.0)
    total = Column(Float, nullable=False)
    promo_code = Column(String(50), nullable=True)

    status = Column(Enum(OrderStatusEnum), default=OrderStatusEnum.pending)
    tracking_number = Column(String(100), nullable=True)
    review_email_sent = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    reviews = relationship("Review", back_populates="order")


class AbandonedCart(Base):
    __tablename__ = "abandoned_carts"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    cart_data = Column(Text, nullable=False)  # JSON
    email_sent = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
