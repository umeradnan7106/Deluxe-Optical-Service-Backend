from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from services.cloudinary import upload_image
from utils.auth import get_current_admin

router = APIRouter(prefix="/upload", tags=["upload"])

MAX_PRESCRIPTION_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/image")
async def upload_product_image(
    file: UploadFile = File(...),
    _=Depends(get_current_admin),
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only JPEG, PNG, or WebP images allowed")
    return await upload_image(file, "products")


@router.post("/prescription")
async def upload_prescription(file: UploadFile = File(...)):
    allowed = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only image or PDF files allowed")

    contents = await file.read()
    if len(contents) > MAX_PRESCRIPTION_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size must be under 10 MB")

    # Re-create UploadFile-like object for the upload helper
    import io
    from fastapi import UploadFile as FU
    fake = FU(filename=file.filename, file=io.BytesIO(contents))
    fake.content_type = file.content_type
    return await upload_image(fake, "prescriptions")
