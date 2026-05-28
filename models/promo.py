import enum
from sqlalchemy import Column, Integer, String, Boolean, Float, Text, Enum, DateTime, func, UniqueConstraint
from database import Base


class DiscountTypeEnum(str, enum.Enum):
    percentage = "percentage"
    fixed = "fixed"


class FAQCategoryEnum(str, enum.Enum):
    orders = "orders"
    prescription = "prescription"
    payments = "payments"
    fitting = "fitting"
    general = "general"


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    discount_type = Column(Enum(DiscountTypeEnum), nullable=False)
    discount_value = Column(Float, nullable=False)
    min_order = Column(Float, nullable=True)
    max_uses = Column(Integer, nullable=True)
    used_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)


class FAQ(Base):
    __tablename__ = "faqs"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String(512), nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(Enum(FAQCategoryEnum), nullable=False)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)


class WishlistItem(Base):
    __tablename__ = "wishlist_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    product_id = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_wishlist_user_product"),
    )
