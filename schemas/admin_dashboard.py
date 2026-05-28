from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import date


class DailyStats(BaseModel):
    date: str
    orders: int
    revenue: float


class DashboardStats(BaseModel):
    today_orders: int
    today_revenue: float
    pending_orders: int
    low_stock_items: int
    total_revenue: float
    total_orders: int
    unapproved_reviews: int
    orders_7d: List[DailyStats]
    orders_by_status: Dict[str, int]


class RecentOrder(BaseModel):
    id: int
    order_number: str
    customer_name: str
    total_amount: float
    status: str
    payment_method: str
    created_at: str


class PendingReview(BaseModel):
    id: int
    product_name: str
    customer_name: str
    rating: int
    body: str
    created_at: str


class LowStockItem(BaseModel):
    variant_id: int
    product_name: str
    sku_variant: Optional[str]
    color_name: str
    stock: int
    low_stock_threshold: int
