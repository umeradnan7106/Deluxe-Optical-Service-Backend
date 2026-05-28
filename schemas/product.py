from typing import Optional, List
from pydantic import BaseModel


class ImageResponse(BaseModel):
    id: int
    url: str
    alt_text: Optional[str] = None
    sort_order: int

    class Config:
        from_attributes = True


class VariantResponse(BaseModel):
    id: int
    color_name: str
    color_hex: Optional[str] = None
    stock: int
    images: List[ImageResponse] = []

    class Config:
        from_attributes = True


class LensOptionResponse(BaseModel):
    id: int
    name: str
    lens_type: str
    price: float
    description: Optional[str] = None

    class Config:
        from_attributes = True


class LensOptionGrouped(BaseModel):
    lens_type: List[LensOptionResponse] = []
    coating: List[LensOptionResponse] = []
    addon: List[LensOptionResponse] = []


class ProductListItem(BaseModel):
    id: int
    name: str
    slug: str
    sku: str
    category: str
    gender: str
    base_price: float
    sale_price: Optional[float] = None
    is_featured: bool
    thumbnail_url: Optional[str] = None
    average_rating: Optional[float] = None
    review_count: int = 0

    class Config:
        from_attributes = True


class ProductDetail(BaseModel):
    id: int
    name: str
    slug: str
    sku: str
    category: str
    gender: str
    frame_shape: Optional[str] = None
    rim_type: Optional[str] = None
    material: Optional[str] = None
    brand: Optional[str] = None
    base_price: float
    sale_price: Optional[float] = None
    frame_width_mm: Optional[int] = None
    lens_width_mm: Optional[int] = None
    bridge_mm: Optional[int] = None
    temple_mm: Optional[int] = None
    lens_height_mm: Optional[int] = None
    bullets: List[str] = []
    description: str
    is_prescription_required: bool
    is_featured: bool
    is_active: bool
    variants: List[VariantResponse] = []
    lens_options: LensOptionGrouped = LensOptionGrouped()
    average_rating: Optional[float] = None
    review_count: int = 0

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    items: List[ProductListItem]
    total: int
    page: int
    page_size: int
    pages: int
