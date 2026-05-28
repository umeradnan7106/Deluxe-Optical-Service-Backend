import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, Enum, func, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class CategoryEnum(str, enum.Enum):
    eyeglasses = "eyeglasses"
    sunglasses = "sunglasses"
    contact_lenses = "contact-lenses"
    accessories = "accessories"


class GenderEnum(str, enum.Enum):
    men = "men"
    women = "women"
    unisex = "unisex"
    kids = "kids"


class FrameShapeEnum(str, enum.Enum):
    round = "round"
    square = "square"
    oval = "oval"
    cat_eye = "cat-eye"
    aviator = "aviator"
    wayfarer = "wayfarer"
    rectangle = "rectangle"


class RimTypeEnum(str, enum.Enum):
    full_rim = "full-rim"
    half_rim = "half-rim"
    rimless = "rimless"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    sku = Column(String(50), unique=True, nullable=False)
    frame_number = Column(String(50), nullable=True)
    brand = Column(String(100), nullable=True)
    category = Column(Enum(CategoryEnum), nullable=False)
    gender = Column(Enum(GenderEnum), nullable=False)
    frame_shape = Column(Enum(FrameShapeEnum), nullable=True)
    material = Column(String(100), nullable=True)
    rim_type = Column(Enum(RimTypeEnum), nullable=True)
    weight_grams = Column(Float, nullable=True)

    base_price = Column(Float, nullable=False)
    sale_price = Column(Float, nullable=True)

    bullets = Column(Text, nullable=True)       # JSON array of bullet strings
    description = Column(Text, nullable=False, default="")
    description_image_url = Column(String(512), nullable=True)
    spec_image_url = Column(String(512), nullable=True)

    # Frame specs
    frame_width_mm = Column(Integer, nullable=True)
    lens_width_mm = Column(Integer, nullable=True)
    bridge_mm = Column(Integer, nullable=True)
    temple_mm = Column(Integer, nullable=True)
    lens_height_mm = Column(Integer, nullable=True)

    is_prescription_required = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    low_stock_threshold = Column(Integer, default=5)

    meta_title = Column(String(255), nullable=True)
    meta_description = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    lens_options = relationship("ProductLensOption", back_populates="product", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="product")


class ProductImage(Base):
    """Images belong to a variant (each color has its own set of images)."""
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=False, index=True)
    url = Column(String(512), nullable=False)
    public_id = Column(String(255), nullable=True)
    alt_text = Column(String(255), nullable=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    variant = relationship("ProductVariant", back_populates="images")


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    color_name = Column(String(100), nullable=False)
    color_hex = Column(String(7), nullable=True)
    size_label = Column(String(50), nullable=True)
    sku_variant = Column(String(100), unique=True, nullable=True)
    price = Column(Float, nullable=True)          # overrides product.base_price if set
    stock = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    product = relationship("Product", back_populates="variants")
    images = relationship("ProductImage", back_populates="variant", order_by="ProductImage.sort_order", cascade="all, delete-orphan")
