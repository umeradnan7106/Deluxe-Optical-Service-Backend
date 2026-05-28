import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.blog import Blog
from schemas.blog import BlogResponse, BlogListResponse

router = APIRouter(prefix="/blogs", tags=["blogs"])


def _read_time(content: str) -> int:
    word_count = len(content.split())
    return max(1, round(word_count / 200))


def _serialize(b: Blog) -> BlogResponse:
    return BlogResponse(
        id=b.id, title=b.title, slug=b.slug,
        category=b.category.value,
        cover_image_url=b.cover_image_url,
        content=b.content,
        meta_title=b.meta_title,
        meta_description=b.meta_description,
        is_published=b.is_published,
        published_at=b.published_at,
        created_at=b.created_at,
        read_time_minutes=_read_time(b.content),
    )


@router.get("", response_model=BlogListResponse)
def list_blogs(
    category: Optional[str] = None,
    page: int = 1,
    per_page: int = 12,
    db: Session = Depends(get_db),
):
    q = db.query(Blog).filter(Blog.is_published == True)
    if category and category != "all":
        q = q.filter(Blog.category == category)
    total = q.count()
    blogs = q.order_by(Blog.published_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return BlogListResponse(
        items=[_serialize(b) for b in blogs],
        total=total, page=page,
        pages=math.ceil(total / per_page) if total else 0,
    )


@router.get("/{slug}", response_model=BlogResponse)
def get_blog(slug: str, db: Session = Depends(get_db)):
    blog = db.query(Blog).filter(Blog.slug == slug, Blog.is_published == True).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    return _serialize(blog)
