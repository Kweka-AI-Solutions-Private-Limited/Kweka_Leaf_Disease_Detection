from typing import Literal, Optional
from pydantic import BaseModel, Field


class DetectionResponse(BaseModel):
    status: Literal["success", "low_confidence"]
    task: Literal["disease", "pest", "weed"]
    crop: Optional[str] = None
    predicted_class: str
    confidence: float = Field(ge=0.0, le=1.0)
    model_id: str
    message: str
