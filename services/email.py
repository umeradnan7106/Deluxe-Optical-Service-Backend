import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "noreply@deluxeopt.com")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

BRAND_ORANGE = "#E8670A"
BRAND_DARK = "#0F0F0F"


def _html_wrapper(body: str, title: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>{title}</title></head>
<body style="background:{BRAND_DARK};color:#ffffff;font-family:Arial,sans-serif;margin:0;padding:0;">
<div style="max-width:600px;margin:0 auto;padding:40px 20px;">
  <div style="border-bottom:2px solid {BRAND_ORANGE};padding-bottom:16px;margin-bottom:24px;">
    <h1 style="color:#ffffff;font-family:Georgia,serif;font-size:28px;margin:0;">
      Deluxe<span style="color:{BRAND_ORANGE};">Opt</span>
    </h1>
  </div>
  {body}
  <div style="margin-top:40px;padding-top:16px;border-top:1px solid #2a2a2a;color:#6b7280;font-size:12px;">
    <p>Deluxe Opt Service · Pakistan's Premium Eyewear</p>
    <p><a href="{FRONTEND_URL}" style="color:{BRAND_ORANGE};">Visit our store</a></p>
  </div>
</div>
</body>
</html>"""


def _send(to: str, subject: str, html: str) -> bool:
    if not RESEND_API_KEY:
        logger.warning(f"RESEND_API_KEY not set. Would send to {to}: {subject}")
        return False
    try:
        import resend
        resend.api_key = RESEND_API_KEY
        resend.Emails.send({
            "from": FROM_EMAIL,
            "to": to,
            "subject": subject,
            "html": html,
        })
        return True
    except Exception as e:
        logger.error(f"Email send failed to {to}: {e}")
        return False


def send_welcome_email(user_name: str, user_email: str) -> bool:
    body = f"""
<h2 style="color:{BRAND_ORANGE};">Welcome to Deluxe Opt!</h2>
<p>Hi {user_name},</p>
<p>Thank you for creating your account. Explore our collection of premium eyewear crafted for Pakistan.</p>
<a href="{FRONTEND_URL}/products" style="display:inline-block;background:{BRAND_ORANGE};color:#ffffff;padding:12px 24px;border-radius:5px;text-decoration:none;margin-top:16px;">Shop Now</a>
"""
    return _send(user_email, "Welcome to Deluxe Opt Service!", _html_wrapper(body, "Welcome"))


def send_order_confirmation(order_number: str, customer_name: str, customer_email: str, total: float) -> bool:
    body = f"""
<h2 style="color:{BRAND_ORANGE};">Order Confirmed!</h2>
<p>Hi {customer_name},</p>
<p>Your order <strong style="color:{BRAND_ORANGE};">{order_number}</strong> has been received and is being reviewed.</p>
<p style="font-size:20px;color:#ffffff;">Total: <strong>Rs. {total:,.0f}</strong></p>
<a href="{FRONTEND_URL}/tracking?order={order_number}" style="display:inline-block;background:{BRAND_ORANGE};color:#ffffff;padding:12px 24px;border-radius:5px;text-decoration:none;margin-top:16px;">Track Order</a>
"""
    return _send(customer_email, f"Order Confirmed — {order_number}", _html_wrapper(body, "Order Confirmed"))


def send_order_processing(order_number: str, customer_name: str, customer_email: str) -> bool:
    body = f"""
<h2 style="color:{BRAND_ORANGE};">Your Order is Being Processed</h2>
<p>Hi {customer_name},</p>
<p>Great news! Order <strong style="color:{BRAND_ORANGE};">{order_number}</strong> is now being processed. Your eyewear is being carefully prepared.</p>
<a href="{FRONTEND_URL}/tracking?order={order_number}" style="display:inline-block;background:{BRAND_ORANGE};color:#ffffff;padding:12px 24px;border-radius:5px;text-decoration:none;margin-top:16px;">Track Order</a>
"""
    return _send(customer_email, f"Order Processing — {order_number}", _html_wrapper(body, "Order Processing"))


def send_order_shipped(order_number: str, customer_name: str, customer_email: str, tracking_number: Optional[str]) -> bool:
    tracking_html = f'<p>Tracking Number: <strong style="color:{BRAND_ORANGE};">{tracking_number}</strong></p>' if tracking_number else ""
    body = f"""
<h2 style="color:{BRAND_ORANGE};">Your Order Has Been Shipped!</h2>
<p>Hi {customer_name},</p>
<p>Order <strong style="color:{BRAND_ORANGE};">{order_number}</strong> is on its way to you.</p>
{tracking_html}
<a href="{FRONTEND_URL}/tracking?order={order_number}" style="display:inline-block;background:{BRAND_ORANGE};color:#ffffff;padding:12px 24px;border-radius:5px;text-decoration:none;margin-top:16px;">Track Order</a>
"""
    return _send(customer_email, f"Order Shipped — {order_number}", _html_wrapper(body, "Order Shipped"))


def send_order_delivered(order_number: str, customer_name: str, customer_email: str) -> bool:
    body = f"""
<h2 style="color:{BRAND_ORANGE};">Order Delivered!</h2>
<p>Hi {customer_name},</p>
<p>Your order <strong style="color:{BRAND_ORANGE};">{order_number}</strong> has been delivered. We hope you love your new eyewear!</p>
<p>If you have any concerns, please contact us via WhatsApp or email.</p>
"""
    return _send(customer_email, f"Order Delivered — {order_number}", _html_wrapper(body, "Order Delivered"))


def send_review_request(order_number: str, customer_name: str, customer_email: str, product_slug: str) -> bool:
    body = f"""
<h2 style="color:{BRAND_ORANGE};">How Are Your New Glasses?</h2>
<p>Hi {customer_name},</p>
<p>We hope you're loving your new eyewear from order <strong>{order_number}</strong>. Share your experience with other customers!</p>
<a href="{FRONTEND_URL}/products/{product_slug}#reviews" style="display:inline-block;background:{BRAND_ORANGE};color:#ffffff;padding:12px 24px;border-radius:5px;text-decoration:none;margin-top:16px;">Write a Review</a>
"""
    return _send(customer_email, "How Are Your New Glasses? Leave a Review!", _html_wrapper(body, "Review Request"))


def send_abandoned_cart(customer_email: str, cart_items: list) -> bool:
    items_html = "".join([
        f'<li style="margin-bottom:8px;color:#e5e7eb;">{item.get("product_name", "Item")} — Rs. {item.get("price", 0):,.0f}</li>'
        for item in cart_items[:3]
    ])
    body = f"""
<h2 style="color:{BRAND_ORANGE};">You Left Something Behind!</h2>
<p>You had items in your cart on Deluxe Opt. Don't miss out!</p>
<ul style="list-style:none;padding:0;">{items_html}</ul>
<a href="{FRONTEND_URL}/cart" style="display:inline-block;background:{BRAND_ORANGE};color:#ffffff;padding:12px 24px;border-radius:5px;text-decoration:none;margin-top:16px;">Complete Your Order</a>
"""
    return _send(customer_email, "You Left Items in Your Cart — Deluxe Opt", _html_wrapper(body, "Abandoned Cart"))


def send_password_reset(customer_email: str, reset_token: str, expires_in_hours: int = 1) -> bool:
    reset_url = f"{FRONTEND_URL}/auth/reset-password?token={reset_token}"
    body = f"""
<h2 style="color:{BRAND_ORANGE};">Password Reset Request</h2>
<p>You requested a password reset. Click the button below to reset your password.</p>
<p style="color:#9ca3af;">This link expires in {expires_in_hours} hour(s).</p>
<a href="{reset_url}" style="display:inline-block;background:{BRAND_ORANGE};color:#ffffff;padding:12px 24px;border-radius:5px;text-decoration:none;margin-top:16px;">Reset Password</a>
<p style="color:#6b7280;font-size:12px;margin-top:16px;">If you didn't request this, ignore this email.</p>
"""
    return _send(customer_email, "Password Reset — Deluxe Opt", _html_wrapper(body, "Password Reset"))
