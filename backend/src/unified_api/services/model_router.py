from io import BytesIO
from typing import Optional

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from ..model_registry import get_model_config
from ..schemas import DetectionResponse

MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 25_000_000
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
CONFIDENCE_THRESHOLD = 0.70


async def dispatch_detection(
    task: str,
    image: UploadFile,
    crop: Optional[str] = None,
) -> DetectionResponse:
    image_bytes = await image.read(MAX_IMAGE_BYTES + 1)

    if not image_bytes:
        raise HTTPException(400, detail="The uploaded image is empty.")

    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(
            413, detail="Image exceeds the 10 MB upload limit."
        )

    try:
        with Image.open(BytesIO(image_bytes)) as img:
            image_format = img.format
            width, height = img.size
            img.verify()

        if image_format not in ALLOWED_FORMATS:
            raise HTTPException(
                415, detail="Use a JPEG, PNG, or WEBP image."
            )

        if width * height > MAX_IMAGE_PIXELS:
            raise HTTPException(
                413, detail="Image dimensions are too large."
            )

    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(
            400, detail="The uploaded file is not a valid supported image."
        ) from exc

    config = get_model_config(task)
    predictor = config["predictor"]

    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "MODEL_NOT_CONFIGURED",
                "task": task,
                "message": (
                    f"No validated {task} model is registered yet. "
                    "No prediction was made."
                ),
            },
        )

    try:
        result = predictor(image_bytes, crop)
        predicted_class = result.get("predicted_class")
        confidence = float(result["confidence"])
        model_id = result.get("model_id") or config["model_id"]

        if not predicted_class or not model_id:
            raise ValueError("Model result is missing its class or model ID.")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("Confidence must be between 0 and 1.")

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "code": "MODEL_INFERENCE_FAILED",
                "task": task,
                "message": "The model did not return a valid prediction.",
            },
        ) from exc

    low_confidence = confidence < CONFIDENCE_THRESHOLD

    return DetectionResponse(
        status="low_confidence" if low_confidence else "success",
        task=task,
        crop=crop,
        predicted_class=predicted_class,
        confidence=confidence,
        model_id=model_id,
        message=(
            "Low confidence: this is not a confirmed diagnosis."
            if low_confidence
            else "Prediction returned by the registered model."
        ),
    )
