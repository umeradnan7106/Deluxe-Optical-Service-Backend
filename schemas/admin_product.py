from typing import Optional, List
from pydantic import BaseModel


class VariantCreate(BaseModel):
    color_name: str
    color_hex: Optional[str] = None
    size_label: Optional[str] = None
    sku_variant: Optional[str] = None
    price: Optional[float] = None
    stock: int = 0
    is_active: bool = True


class VariantUpdate(BaseModel):
    color_name: Optional[str] = None
    color_hex: Optional[str] = None
    size_label: Optional[str] = None
    sku_variant: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    is_active: Optional[bool] = None


class ProductCreate(BaseModel):
    name: str
    sku: str
    brand: Optional[str] = None
    category: str
    gender: str
    frame_shape: Optional[str] = None
    rim_type: Optional[str] = None
    material: Optional[str] = None
    base_price: float
    sale_price: Optional[float] = None
    bullets: Optional[List[str]] = None
    description: str = ""
    is_prescription_required: bool = False
    is_active: bool = True
    is_featured: bool = False
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    frame_width_mm: Optional[int] = None
    lens_width_mm: Optional[int] = None
    bridge_mm: Optional[int] = None
    temple_mm: Optional[int] = None
    lens_height_mm: Optional[int] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    gender: Optional[str] = None
    frame_shape: Optional[str] = None
    rim_type: Optional[str] = None
    material: Optional[str] = None
    base_price: Optional[float] = None
    sale_price: Optional[float] = None
    bullets: Optional[List[str]] = None
    description: Optional[str] = None
    is_prescription_required: Optional[bool] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    frame_width_mm: Optional[int] = None
    lens_width_mm: Optional[int] = None
    bridge_mm: Optional[int] = None
    temple_mm: Optional[int] = None
    lens_height_mm: Optional[int] = None


class ImageReorder(BaseModel):
    image_ids: List[int]  # In desired order


class LensOptionAssign(BaseModel):
    lens_option_ids: List[int]
