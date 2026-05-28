import json
import logging
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)
_scheduler = BackgroundScheduler(timezone="UTC")


def _check_abandoned_carts() -> None:
    try:
        from database import SessionLocal
        from models.order import AbandonedCart
        from services.email import send_abandoned_cart

        db = SessionLocal()
        cutoff = datetime.now(timezone.utc) - timedelta(hours=2)
        carts = db.query(AbandonedCart).filter(
            AbandonedCart.email_sent == False,
            AbandonedCart.email.isnot(None),
            AbandonedCart.created_at <= cutoff,
        ).all()
        for cart in carts:
            try:
                items = json.loads(cart.cart_data or "[]")
                send_abandoned_cart(cart.email, items)
                cart.email_sent = True
            except Exception as e:
                logger.error(f"Abandoned cart email failed for cart {cart.id}: {e}")
        db.commit()
        db.close()
    except Exception as e:
        logger.error(f"Abandoned cart check failed: {e}")


def _check_review_requests() -> None:
    try:
        from database import SessionLocal
        from models.order import Order, OrderStatusEnum

        db = SessionLocal()
        cutoff = datetime.now(timezone.utc) - timedelta(days=3)
        orders = db.query(Order).filter(
            Order.status == OrderStatusEnum.delivered,
            Order.review_email_sent == False,
            Order.updated_at <= cutoff,
        ).all()
        for order in orders:
            try:
                from services.email import send_review_request
                items = json.loads(order.items or "[]")
                product_slug = items[0].get("product_slug", "") if items else ""
                send_review_request(
                    order.order_number, order.customer_name,
                    order.customer_email, product_slug,
                )
                order.review_email_sent = True
            except Exception as e:
                logger.error(f"Review request email failed for order {order.id}: {e}")
        db.commit()
        db.close()
    except Exception as e:
        logger.error(f"Review request check failed: {e}")


def start_scheduler() -> None:
    if not _scheduler.running:
        _scheduler.add_job(
            _check_abandoned_carts, "interval", minutes=30,
            id="abandoned_carts", replace_existing=True,
        )
        _scheduler.add_job(
            _check_review_requests, "interval", minutes=15,
            id="review_requests", replace_existing=True,
        )
        _scheduler.start()
        logger.info("Scheduler started")


def stop_scheduler() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
