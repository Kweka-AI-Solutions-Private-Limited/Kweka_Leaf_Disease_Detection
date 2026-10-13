from typing import Any, Callable, Optional

Predictor = Callable[[bytes, Optional[str]], dict[str, Any]]

MODEL_REGISTRY: dict[str, dict[str, Any]] = {
    "disease": {
        "model_id": None,
        "predictor": None,
        "supported_crops": [],
        "supported_classes": [],
    },
    "pest": {
        "model_id": None,
        "predictor": None,
        "supported_crops": [],
        "supported_classes": [],
    },
    "weed": {
        "model_id": None,
        "predictor": None,
        "supported_crops": [],
        "supported_classes": [],
    },
}


def get_model_config(task: str) -> dict[str, Any]:
    if task not in MODEL_REGISTRY:
        raise ValueError(f"Unknown detection task: {task}")
    return MODEL_REGISTRY[task]


def register_model(
    task: str,
    model_id: str,
    predictor: Predictor,
    supported_crops: list[str],
    supported_classes: list[str],
) -> None:
    """Register a real, initialized model and its inference function."""
    if task not in MODEL_REGISTRY:
        raise ValueError(f"Unknown detection task: {task}")
    if not callable(predictor):
        raise TypeError("predictor must be callable")

    MODEL_REGISTRY[task].update({
        "model_id": model_id,
        "predictor": predictor,
        "supported_crops": supported_crops,
        "supported_classes": supported_classes,
    })
