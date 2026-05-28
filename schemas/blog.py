from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class BlogCreate(BaseModel):
    title: str
    category: str
    content: str
    cover_image_url: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    is_published: bool = False


class BlogUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    cover_image_url: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    is_published: Optional[bool] = None


class BlogResponse(BaseModel):
    id: int
    title: str
    slug: str
    category: str
    cover_image_url: Optional[str]
    content: str
    meta_title: Optional[str]
    meta_description: Optional[str]
    is_published: bool
    published_at: Optional[datetime]
    created_at: datetime
    read_time_minutes: int = 3


class BlogListResponse(BaseModel):
    items: List[BlogResponse]
    total: int
    page: int
    pages: int
