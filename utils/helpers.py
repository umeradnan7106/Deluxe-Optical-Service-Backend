import re
import unicodedata
from datetime import datetime
from sqlalchemy.orm import Session


def generate_order_number(db: Session) -> str:
    from models.order import Order
    year = datetime.utcnow().year
    count = db.query(Order).filter(
        Order.order_number.like(f"DOS-{year}-%")
    ).count()
    return f"DOS-{year}-{str(count + 1).zfill(4)}"


def calculate_shipping(subtotal: float) -> float:
    return 0.0 if subtotal >= 3000 else 200.0


def calculate_payment_discount(subtotal: float, method: str) -> float:
    online_methods = {"easypaisa", "jazzcash", "bank_transfer"}
    if method.lower() in online_methods:
        return round(subtotal * 0.15, 2)
    return 0.0


def generate_slug(name: str) -> str:
    value = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[-\s]+", "-", value)
