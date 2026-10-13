"""
weed_provider.py — Modular Weed Detection Provider & Inference Engine
----------------------------------------------------------------------
Implements modular provider interface for Phase 3 Weed Detection:
  - Strictly decoupled from plant disease detection, crop ID, and pest detection.
  - Zero calls to Gemini, Kindwise, Plant.id, or paid external APIs.
  - Inspects local filesystem for pretrained model checkpoints (e.g., DeepWeeds ResNet or MH-Weed16 YOLO weights).
  - Returns honest MODEL_UNAVAILABLE status when weights are absent; NEVER invents fake detections.
  - Strictly distinguishes whole-image classification from object detection (never claims bounding boxes unless supported).
"""

import os
import io
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from PIL import Image

from schemas.weed_detection import DetectedWeedItem, WeedBoundingBox, WeedModelInfo
from services.weed_detection.weed_catalog import (
    DEEPWEEDS_CATALOG,
    MHWEED16_CATALOG,
    get_deepweeds_class,
    get_mhweed16_class,
    resolve_weed_class,
)

logger = logging.getLogger(__name__)

_cur_file = Path(__file__).resolve()
# Check potential locations for models/weed: worktree root or backend root
_worktree_models = _cur_file.parents[4] / "models" / "weed" if len(_cur_file.parents) >= 5 else None
_backend_models = _cur_file.parents[3] / "models" / "weed" if len(_cur_file.parents) >= 4 else None

if _worktree_models and _worktree_models.exists():
    DEFAULT_WEED_WEIGHTS_DIR = _worktree_models
elif _backend_models and _backend_models.exists():
    DEFAULT_WEED_WEIGHTS_DIR = _backend_models
else:
    DEFAULT_WEED_WEIGHTS_DIR = _worktree_models or Path("models/weed")

CANDIDATE_WEIGHT_NAMES = [
    "weed_detector.pt",
    "weed_detector.onnx",
    "deepweeds_resnet50.pt",
    "deepweeds_resnet50.onnx",
    "mhweed16_yolo.pt",
    "mhweed16_yolo.onnx",
]


class WeedDetectionProvider(ABC):
    """Abstract Base Class for modular weed detection and classification engines."""

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True only if a validated model checkpoint is loaded and operational."""
        pass

    @abstractmethod
    def get_model_info(self) -> WeedModelInfo:
        """Returns model architecture, license, and checkpoint status."""
        pass

    @abstractmethod
    def detect_weeds(
        self,
        image_bytes: bytes,
        crop_name: Optional[str] = None,
    ) -> Tuple[List[DetectedWeedItem], WeedModelInfo]:
        """
        Executes weed identification on validated image bytes.
        Returns list of detected weeds and model metadata.
        """
        pass


class ModularWeedDetectorProvider(WeedDetectionProvider):
    """
    Modular detector supporting either:
      1. Multi-object detection (e.g. YOLO trained on MH-Weed16 or DeepWeeds with bboxes).
      2. Image classification (e.g. ResNet50 trained on DeepWeeds, without bboxes).
      3. Honest unavailable fallback when weights are absent.
    """

    def __init__(self, checkpoint_path: Optional[str] = None):
        if checkpoint_path:
            self.checkpoint_path = checkpoint_path
        elif os.getenv("WEED_MODEL_PATH"):
            self.checkpoint_path = os.getenv("WEED_MODEL_PATH")
        else:
            self.checkpoint_path = self._discover_checkpoint()

        self._model = None
        self._task_type = "IMAGE_CLASSIFICATION"
        self._supports_boxes = False
        self._dataset_origin = "DeepWeeds (9 Classes) & MH-Weed16 (16 Classes)"
        self._is_loaded = False
        self._status_message = ""
        self._init_model()

    def _discover_checkpoint(self) -> str:
        """Searches candidate directory for known weight files."""
        if DEFAULT_WEED_WEIGHTS_DIR and DEFAULT_WEED_WEIGHTS_DIR.exists():
            for name in CANDIDATE_WEIGHT_NAMES:
                candidate = DEFAULT_WEED_WEIGHTS_DIR / name
                if candidate.exists():
                    return str(candidate)
        return str(DEFAULT_WEED_WEIGHTS_DIR / "weed_detector.pt")

    def _init_model(self) -> None:
        target = Path(self.checkpoint_path)
        if not target.exists():
            self._is_loaded = False
            self._status_message = (
                f"No validated weed detector weights found at '{target.as_posix()}'. "
                f"Architecture configured for DeepWeeds (ResNet50 classification) and MH-Weed16 (YOLO detection). "
                f"Awaiting model checkpoint. Real inference cannot run without weights."
            )
            logger.info("ModularWeedDetectorProvider: %s", self._status_message)
            return

        # Attempt 1: Load via Ultralytics YOLO (Object Detection)
        if "yolo" in target.name.lower() or target.suffix.lower() == ".pt":
            try:
                from ultralytics import YOLO
                yolo = YOLO(str(target))
                if getattr(yolo, "task", None) == "detect":
                    self._model = yolo
                    self._task_type = "OBJECT_DETECTION"
                    self._supports_boxes = True
                    self._dataset_origin = "MH-Weed16 / Custom Agricultural YOLO"
                    self._is_loaded = True
                    self._status_message = f"YOLO weed detector loaded successfully from '{target.as_posix()}'."
                    logger.info("ModularWeedDetectorProvider: %s", self._status_message)
                    return
            except Exception as e:
                logger.debug("YOLO load skipped for %s: %s", target.name, e)

        # Attempt 2: Load via PyTorch / TorchScript (Image Classification)
        try:
            import torch
            model = torch.load(str(target), map_location="cpu")
            if hasattr(model, "eval"):
                model.eval()
            self._model = model
            self._task_type = "IMAGE_CLASSIFICATION"
            self._supports_boxes = False
            self._dataset_origin = "DeepWeeds (ResNet50 / 9 Classes)"
            self._is_loaded = True
            self._status_message = f"PyTorch weed classifier loaded from '{target.as_posix()}'."
            logger.info("ModularWeedDetectorProvider: %s", self._status_message)
            return
        except Exception as e:
            logger.debug("PyTorch load notice: %s", e)

        # Attempt 3: Load via ONNX runtime
        if target.suffix.lower() == ".onnx":
            try:
                import onnxruntime as ort
                session = ort.InferenceSession(str(target), providers=["CPUExecutionProvider"])
                self._model = session
                self._task_type = "OBJECT_DETECTION" if "detect" in target.name.lower() else "IMAGE_CLASSIFICATION"
                self._supports_boxes = (self._task_type == "OBJECT_DETECTION")
                self._dataset_origin = "ONNX Runtime Checkpoint"
                self._is_loaded = True
                self._status_message = f"ONNX runtime session loaded from '{target.as_posix()}'."
                logger.info("ModularWeedDetectorProvider: %s", self._status_message)
                return
            except Exception as e:
                logger.warning("ONNX load failed for %s: %s", target.name, e)

        self._is_loaded = False
        self._status_message = f"Failed to initialize weights at '{target.as_posix()}'."

    def is_available(self) -> bool:
        return self._is_loaded and (self._model is not None)

    def get_model_info(self) -> WeedModelInfo:
        if self._is_loaded and self._supports_boxes:
            arch = "YOLO Object Detector (Spatial Bounding Boxes)"
            task = "OBJECT_DETECTION"
            classes = 16 if "mhweed" in str(self.checkpoint_path).lower() else 9
            license_str = "CC BY 4.0 / Open Source"
        elif self._is_loaded:
            arch = "ResNet50 Image Classifier (Whole-Image Prediction)"
            task = "IMAGE_CLASSIFICATION"
            classes = 9
            license_str = "Apache-2.0"
        else:
            arch = "DeepWeeds ResNet50 / MH-Weed16 YOLO Adapter"
            task = "IMAGE_CLASSIFICATION"
            classes = 25
            license_str = "Apache-2.0 / CC BY 4.0"

        return WeedModelInfo(
            model_id="weed-detector-v1",
            model_name="Agricultural Weed Detector",
            architecture=arch,
            task_type=task,
            supports_bounding_boxes=self._supports_boxes,
            is_operational=self.is_available(),
            checkpoint_path=self.checkpoint_path,
            supported_classes_count=classes,
            dataset_origin=self._dataset_origin,
            framework="PyTorch / Ultralytics / ONNX",
            license=license_str,
            status_message=self._status_message,
        )

    def detect_weeds(
        self,
        image_bytes: bytes,
        crop_name: Optional[str] = None,
    ) -> Tuple[List[DetectedWeedItem], WeedModelInfo]:
        """
        Executes genuine weed detection if operational.
        Returns empty list when no weeds are present or when model is unavailable.
        Never mocks or fabricates results.
        """
        model_info = self.get_model_info()

        if not self.is_available():
            return ([], model_info)

        # Execution Branch 1: Ultralytics YOLO Object Detection
        if self._supports_boxes and hasattr(self._model, "predict"):
            try:
                pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
                results = self._model.predict(
                    source=pil_img,
                    imgsz=640,
                    conf=0.20,
                    verbose=False,
                )

                detections: List[DetectedWeedItem] = []
                if results and len(results) > 0:
                    res0 = results[0]
                    for box in res0.boxes:
                        cls_idx = int(box.cls[0].item())
                        conf_val = float(box.conf[0].item())
                        xyxyn = box.xyxyn[0].tolist()
                        xmin, ymin, xmax, ymax = xyxyn

                        raw_name = None
                        if hasattr(self._model, "names") and isinstance(self._model.names, dict):
                            raw_name = self._model.names.get(cls_idx)
                        meta = resolve_weed_class(cls_idx, raw_name)

                        weed_name = meta.get("name", f"Weed #{cls_idx}")

                        bbox = WeedBoundingBox(
                            ymin=max(0.0, min(1.0, float(ymin))),
                            xmin=max(0.0, min(1.0, float(xmin))),
                            ymax=max(0.0, min(1.0, float(ymax))),
                            xmax=max(0.0, min(1.0, float(xmax))),
                            label=weed_name,
                            confidence=conf_val,
                        )

                        source_ds = "Agricultural YOLO Weeds" if raw_name else "MH-Weed16"

                        detections.append(
                            DetectedWeedItem(
                                weed_name=weed_name,
                                scientific_name=meta.get("scientific_name"),
                                weed_class_id=cls_idx,
                                source_dataset=source_ds,
                                confidence=conf_val,
                                bounding_box=bbox,
                                detection_type="OBJECT_DETECTION",
                                growth_habit=meta.get("growth_habit"),
                                description=meta.get("description"),
                            )
                        )

                detections.sort(key=lambda x: x.confidence, reverse=True)
                return (detections, model_info)

            except Exception as exc:
                logger.error("YOLO weed inference error: %s", exc)
                model_info.status_message = f"Inference execution failed: {str(exc)}"
                return ([], model_info)

        # Execution Branch 2: PyTorch ResNet Whole-Image Classification
        try:
            import torch
            import torchvision.transforms as T

            pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            preprocess = T.Compose([
                T.Resize(256),
                T.CenterCrop(224),
                T.ToTensor(),
                T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])
            tensor = preprocess(pil_img).unsqueeze(0)

            with torch.no_grad():
                logits = self._model(tensor)
                probs = torch.softmax(logits, dim=-1)[0]
                conf, pred_idx = torch.max(probs, dim=0)
                pred_idx = int(pred_idx.item())
                conf_val = float(conf.item())

            meta = get_deepweeds_class(pred_idx) or {
                "name": f"DeepWeeds Class {pred_idx}",
                "scientific_name": None,
                "is_negative": (pred_idx == 8),
                "growth_habit": "weed",
                "description": None,
            }

            # If model predicts Class 8 ("Negative" - background foliage without target weeds)
            if meta.get("is_negative") or conf_val < 0.30:
                return ([], model_info)

            item = DetectedWeedItem(
                weed_name=meta.get("name", f"Weed #{pred_idx}"),
                scientific_name=meta.get("scientific_name"),
                weed_class_id=pred_idx,
                source_dataset="DeepWeeds",
                confidence=conf_val,
                bounding_box=None,  # Classification does not produce bounding boxes
                detection_type="IMAGE_CLASSIFICATION",
                growth_habit=meta.get("growth_habit"),
                description=meta.get("description"),
            )
            return ([item], model_info)

        except Exception as exc:
            logger.error("PyTorch weed classification error: %s", exc)
            model_info.status_message = f"Inference execution failed: {str(exc)}"
            return ([], model_info)


_weed_provider_instance: Optional[WeedDetectionProvider] = None


def get_weed_provider() -> WeedDetectionProvider:
    """Returns singleton instance of the weed detection provider."""
    global _weed_provider_instance
    if _weed_provider_instance is None:
        _weed_provider_instance = ModularWeedDetectorProvider()
    return _weed_provider_instance


def reset_weed_provider_for_testing(provider: Optional[WeedDetectionProvider] = None) -> None:
    """Helper for testing to inject mock/test provider instances."""
    global _weed_provider_instance
    _weed_provider_instance = provider
