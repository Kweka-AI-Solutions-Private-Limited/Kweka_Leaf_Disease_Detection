from typing import Optional

from fastapi import APIRouter, File, UploadFile
from .schemas import DetectionResponse
from .services.disease import detect_disease
from .services.pest import detect_pest
from .services.weed import detect_weed

router = APIRouter(prefix="/unified", tags=["Unified Detection"])


@router.post("/disease", response_model=DetectionResponse)
async def disease_endpoint(
    image: UploadFile = File(...),
    crop: Optional[str] = None,
):
    return await detect_disease(image, crop)


@router.post("/pest", response_model=DetectionResponse)
async def pest_endpoint(
    image: UploadFile = File(...),
    crop: Optional[str] = None,
):
    return await detect_pest(image, crop)


@router.post("/weed", response_model=DetectionResponse)
async def weed_endpoint(
    image: UploadFile = File(...),
    crop: Optional[str] = None,
):
    return await detect_weed(image, crop)
