from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel

from services import supabase_service

router = APIRouter()


class UploadResponse(BaseModel):
    photo_url: str


@router.post("/upload-photo", response_model=UploadResponse)
async def upload_photo(file: UploadFile) -> UploadResponse:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    try:
        url = await supabase_service.upload_photo(file_bytes, file.content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

    return UploadResponse(photo_url=url)
