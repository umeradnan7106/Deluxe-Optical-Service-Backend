import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

FRONTEND_URL = os.environ.get("FRONTEND_URL", "")

_env_origins = [o.strip() for o in FRONTEND_URL.split(",") if o.strip()]
_hardcoded_origins = [
    "https://deluxe-optical-service.vercel.app",
    "http://localhost:3000",
]
_dev_ports = [3001, 3002, 3003, 3004, 3005]
ALLOWED_ORIGINS = list({
    *_env_origins,
    *_hardcoded_origins,
    *[f"http://localhost:{p}" for p in _dev_ports],
})


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run Alembic migrations on startup if enabled
    import subprocess
    if os.getenv("RUN_MIGRATIONS") == "true":
        subprocess.run(["alembic", "upgrade", "head"], check=True)

    # Startup: initialize APScheduler
    from services.scheduler import start_scheduler, stop_scheduler
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()


app = FastAPI(title="Deluxe Opt Service API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routes.auth import router as auth_router
from routes.products import router as products_router
from routes.cart import router as cart_router
from routes.upload import router as upload_router
from routes.orders import router as orders_router
from routes.wishlist import router as wishlist_router
from routes.admin.products import router as admin_products_router
from routes.admin.inventory import router as admin_inventory_router
from routes.admin.dashboard import router as admin_dashboard_router
from routes.admin.orders import router as admin_orders_router
from routes.reviews import router as reviews_router
from routes.admin.reviews import router as admin_reviews_router
from routes.blogs import router as blogs_router
from routes.admin.blogs import router as admin_blogs_router
from routes.admin.promo_codes import router as admin_promo_codes_router
from routes.admin.faqs import router as admin_faqs_router
from routes.admin.lens_options import router as admin_lens_options_router
from routes.admin.lens_collection import router as admin_lens_collection_router
from routes.lens_collection import router as lens_collection_router
from routes.faqs import router as faqs_router

app.include_router(auth_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(cart_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
app.include_router(wishlist_router, prefix="/api")
app.include_router(reviews_router, prefix="/api")
app.include_router(admin_products_router, prefix="/api")
app.include_router(admin_inventory_router, prefix="/api")
app.include_router(admin_dashboard_router, prefix="/api")
app.include_router(admin_orders_router, prefix="/api")
app.include_router(admin_reviews_router, prefix="/api")
app.include_router(blogs_router, prefix="/api")
app.include_router(admin_blogs_router, prefix="/api")
app.include_router(admin_promo_codes_router, prefix="/api")
app.include_router(admin_faqs_router, prefix="/api")
app.include_router(admin_lens_options_router, prefix="/api")
app.include_router(admin_lens_collection_router, prefix="/api")
app.include_router(lens_collection_router, prefix="/api")
app.include_router(faqs_router, prefix="/api")
