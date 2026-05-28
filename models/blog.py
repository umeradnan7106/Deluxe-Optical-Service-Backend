import enum
from sqlalchemy import Column, Integer, String, Boolean, Text, Enum, DateTime, func
from database import Base


class BlogCategoryEnum(str, enum.Enum):
    lens_guide = "lens-guide"
    frame_style = "frame-style"
    eye_health = "eye-health"
    prescription_tips = "prescription-tips"


class Blog(Base):
    __tablename__ = "blogs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    cover_image_url = Column(String(512), nullable=True)
    category = Column(Enum(BlogCategoryEnum), nullable=False)
    content = Column(Text, nullable=False)
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(Text, nullable=True)
    is_published = Column(Boolean, default=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
