from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class ReviewCreate(BaseModel):
    product_id: int
    order_id: Optional[int] = None
    customer_name: str
    customer_email: str
    rating: int = Field(ge=1, le=5)
    title: str
    body: str
    images: Optional[List[str]] = None  # list of Cloudinary URLs


class ReviewResponse(BaseModel):
    id: int
    product_id: int
    order_id: Optional[int]
    customer_name: str
    rating: int
    title: str
    body: str
    images: Optional[List[str]]
    is_approved: bool
    is_featured: bool
    created_at: datetime


class ReviewListResponse(BaseModel):
    items: List[ReviewResponse]
    total: int
    page: int
    pages: int
