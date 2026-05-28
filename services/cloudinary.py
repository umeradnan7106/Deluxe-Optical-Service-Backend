import os
import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException


cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True,
)


async def upload_image(file: UploadFile, folder: str) -> dict:
    contents = await file.read()
    try:
        result = cloudinary.uploader.upload(
            contents,
            folder=f"deluxe-opt/{folder}",
            resource_type="auto",
        )
        return {"url": result["secure_url"], "public_id": result["public_id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")


def delete_image(public_id: str) -> None:
    try:
        cloudinary.uploader.destroy(public_id)
    except Exception:
        pass
