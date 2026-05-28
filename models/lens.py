import enum
from sqlalchemy import Column, Integer, String, Boolean, Float, Text, Enum, ForeignKey, PrimaryKeyConstraint, func, DateTime
from sqlalchemy.orm import relationship
from database import Base


class LensTypeEnum(str, enum.Enum):
    lens_type = "lens-type"
    coating = "coating"
    addon = "addon"


class LensOption(Base):
    __tablename__ = "lens_options"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(Enum(LensTypeEnum), nullable=False)
    sub_type = Column(String(50), nullable=True)
    price = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    products = relationship("ProductLensOption", back_populates="lens_option")


class ProductLensOption(Base):
    __tablename__ = "product_lens_options"

    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    lens_option_id = Column(Integer, ForeignKey("lens_options.id"), nullable=False)

    __table_args__ = (PrimaryKeyConstraint("product_id", "lens_option_id"),)

    product = relationship("Product", back_populates="lens_options")
    lens_option = relationship("LensOption", back_populates="products")


class LensCollection(Base):
    __tablename__ = "lens_collections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    video_url = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    bullets = Column(Text, nullable=True)  # JSON stored as text
    price_from = Column(Float, nullable=False)
    color_dot = Column(String(7), nullable=False)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
