import json
import math
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models.order import Order, OrderStatusEnum
from models.product import Product, ProductVariant
from models.review import Review
from utils.auth import get_current_admin
from schemas.admin_dashboard import DashboardStats, DailyStats, RecentOrder, PendingReview, LowStockItem, TopProduct

router = APIRouter(prefix="/admin", tags=["admin-dashboard"])


@router.get("/stats", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    today_orders_q = db.query(Order).filter(Order.created_at >= today_start)
    today_orders = today_orders_q.count()
    today_revenue = sum(o.total for o in today_orders_q.all())

    pending_orders = db.query(Order).filter(Order.status == OrderStatusEnum.pending).count()
    unapproved_reviews = db.query(Review).filter(Review.is_approved == False).count()

    # Fix: low_stock_threshold is on Product, not ProductVariant — join required
    low_stock_variants = (
        db.query(ProductVariant)
        .join(Product, ProductVariant.product_id == Product.id)
        .filter(ProductVariant.stock <= Product.low_stock_threshold, Product.is_active == True)
        .count()
    )

    total_orders = db.query(Order).count()
    total_revenue = db.query(func.sum(Order.total)).scalar() or 0.0

    # Orders last 7 days
    orders_7d = []
    for i in range(6, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        day_orders = db.query(Order).filter(Order.created_at >= day_start, Order.created_at < day_end).all()
        orders_7d.append(DailyStats(
            date=day_start.strftime("%m/%d"),
            orders=len(day_orders),
            revenue=sum(o.total for o in day_orders),
        ))

    # Orders by status
    status_counts: dict[str, int] = {}
    for status_val in OrderStatusEnum:
        count = db.query(Order).filter(Order.status == status_val).count()
        if count > 0:
            status_counts[status_val.value] = count

    return DashboardStats(
        today_orders=today_orders,
        today_revenue=today_revenue,
        pending_orders=pending_orders,
        low_stock_items=low_stock_variants,
        total_revenue=total_revenue,
        total_orders=total_orders,
        unapproved_reviews=unapproved_reviews,
        orders_7d=orders_7d,
        orders_by_status=status_counts,
    )


@router.get("/recent-orders")
def recent_orders(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    orders = db.query(Order).order_by(Order.created_at.desc()).limit(10).all()
    return [
        RecentOrder(
            id=o.id, order_number=o.order_number, customer_name=o.customer_name,
            total_amount=o.total, status=o.status.value, payment_method=o.payment_method.value,
            created_at=o.created_at.isoformat(),
        )
        for o in orders
    ]


@router.get("/pending-reviews")
def pending_reviews(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    reviews = db.query(Review).filter(Review.is_approved == False).order_by(Review.created_at.desc()).limit(10).all()
    return [
        PendingReview(
            id=r.id, product_name=r.product.name if r.product else "Unknown",
            customer_name=r.customer_name, rating=r.rating,
            body=r.body[:120] + ("…" if len(r.body) > 120 else ""),
            created_at=r.created_at.isoformat(),
        )
        for r in reviews
    ]


@router.get("/low-stock")
def low_stock(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    # Fix: low_stock_threshold is on Product, not ProductVariant
    variants = (
        db.query(ProductVariant)
        .join(Product, ProductVariant.product_id == Product.id)
        .filter(ProductVariant.stock <= Product.low_stock_threshold, Product.is_active == True)
        .order_by(ProductVariant.stock)
        .limit(20)
        .all()
    )
    return [
        LowStockItem(
            variant_id=v.id, product_name=v.product.name,
            sku_variant=v.sku_variant, color_name=v.color_name,
            stock=v.stock, low_stock_threshold=v.product.low_stock_threshold,
        )
        for v in variants
    ]


@router.get("/top-products")
def top_products(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    orders = db.query(Order).filter(Order.created_at >= month_start).all()

    product_stats: dict[int, dict] = {}
    for order in orders:
        try:
            items = json.loads(order.items) if isinstance(order.items, str) else (order.items or [])
            for item in items:
                pid = item.get("product_id")
                if not pid:
                    continue
                qty = int(item.get("quantity", 1))
                price = float(item.get("sale_price") or item.get("base_price") or 0)
                if pid not in product_stats:
                    product_stats[pid] = {
                        "product_id": pid,
                        "product_name": item.get("product_name", ""),
                        "units": 0,
                        "revenue": 0.0,
                    }
                product_stats[pid]["units"] += qty
                product_stats[pid]["revenue"] += price * qty
        except Exception:
            continue

    sorted_products = sorted(product_stats.values(), key=lambda x: x["units"], reverse=True)[:10]

    result = []
    for p in sorted_products:
        avg = db.query(func.avg(Review.rating)).filter(
            Review.product_id == p["product_id"], Review.is_approved == True
        ).scalar()
        result.append(TopProduct(
            product_id=p["product_id"],
            product_name=p["product_name"],
            units_sold=p["units"],
            revenue=round(p["revenue"], 2),
            avg_rating=round(float(avg), 1) if avg else None,
        ))

    return result
