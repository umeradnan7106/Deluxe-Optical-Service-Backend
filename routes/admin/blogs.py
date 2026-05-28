import math
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from database import get_db
from models.blog import Blog
from schemas.blog import BlogCreate, BlogUpdate, BlogResponse, BlogListResponse
from utils.auth import get_current_admin
from utils.helpers import generate_slug
from services.cloudinary import upload_image

router = APIRouter(prefix="/admin/blogs", tags=["admin-blogs"])


def _read_time(content: str) -> int:
    return max(1, round(len(content.split()) / 200))


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
def list_blogs_admin(
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    q = db.query(Blog)
    total = q.count()
    blogs = q.order_by(Blog.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return BlogListResponse(
        items=[_serialize(b) for b in blogs],
        total=total, page=page,
        pages=math.ceil(total / per_page) if total else 0,
    )


@router.get("/{blog_id}", response_model=BlogResponse)
def get_blog_admin(blog_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    return _serialize(blog)


@router.post("", status_code=201)
def create_blog(body: BlogCreate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    slug = generate_slug(body.title)
    existing = db.query(Blog).filter(Blog.slug == slug).first()
    if existing:
        slug = f"{slug}-{int(datetime.now(timezone.utc).timestamp())}"
    blog = Blog(
        title=body.title, slug=slug, category=body.category,
        content=body.content, cover_image_url=body.cover_image_url,
        meta_title=body.meta_title, meta_description=body.meta_description,
        is_published=body.is_published,
        published_at=datetime.now(timezone.utc) if body.is_published else None,
    )
    db.add(blog)
    db.commit()
    db.refresh(blog)
    return {"id": blog.id, "slug": blog.slug}


@router.patch("/{blog_id}")
def update_blog(blog_id: int, body: BlogUpdate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(blog, field, value)
    db.commit()
    return {"message": "Updated"}


@router.delete("/{blog_id}")
def delete_blog(blog_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    db.delete(blog)
    db.commit()
    return {"message": "Deleted"}


@router.post("/{blog_id}/publish")
def publish_blog(blog_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    blog.is_published = True
    blog.published_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Published"}


@router.post("/{blog_id}/unpublish")
def unpublish_blog(blog_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    blog.is_published = False
    db.commit()
    return {"message": "Unpublished"}


@router.post("/upload-cover")
async def upload_cover(file: UploadFile = File(...), _=Depends(get_current_admin)):
    result = await upload_image(file, "blogs")
    return {"url": result["url"]}
