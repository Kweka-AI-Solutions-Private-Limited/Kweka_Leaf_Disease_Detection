from typing import Optional
from fastapi import UploadFile
from .model_router import dispatch_detection
from ..schemas import DetectionResponse


async def detect_weed(
    image: UploadFile, crop: Optional[str] = None
) -> DetectionResponse:
    return await dispatch_detection("weed", image, crop)
