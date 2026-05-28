from typing import Optional, List
from pydantic import BaseModel


class FAQResponse(BaseModel):
    id: int
    question: str
    answer: str
    category: str
    sort_order: int
    is_active: bool


class FAQListResponse(BaseModel):
    items: List[FAQResponse]
    total: int
