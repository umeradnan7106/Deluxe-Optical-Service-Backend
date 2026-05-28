import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.lens import LensCollection

router = APIRouter(prefix="/lens-collection", tags=["lens-collection"])


@router.get("")
def list_lens_collections(db: Session = Depends(get_db)):
    collections = db.query(LensCollection).filter(
        LensCollection.is_active == True
    ).order_by(LensCollection.sort_order).all()
    return [
        {
            "id": lc.id, "name": lc.name, "video_url": lc.video_url,
            "description": lc.description,
            "bullets": json.loads(lc.bullets or "[]"),
            "price_from": lc.price_from, "color_dot": lc.color_dot,
            "sort_order": lc.sort_order,
        }
        for lc in collections
    ]
