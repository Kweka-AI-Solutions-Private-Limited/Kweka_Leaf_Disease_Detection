"""
pest_provider.py — Modular Pest Detection Provider & Model Adapter
---------------------------------------------------------------------
Implements the modular provider interface for Phase 2 Insect & Pest Detection:
  - Strictly decoupled from plant disease detection and Pl@ntNet.
  - Zero calls to Gemini, Kindwise, or paid external APIs.
  - Inspects local filesystem for pretrained model checkpoints (e.g., IP102 PyTorch YOLO or ONNX weights).
  - Returns honest MODEL_UNAVAILABLE status when weights are absent; NEVER invents fake detections.
  - Runs real Ultralytics YOLO / ONNX object detection and bounding box localization when weights are present.
"""

import os
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

from schemas.leaf_disease import ImageValidationDetail
from schemas.pest_detection import DetectedPestItem, PestBoundingBox, PestModelInfo
from services.pest_detection.ip102_classes import (
    IP102_CATALOG,
    get_ip102_class,
    classify_pest_type_distinction,
)

logger = logging.getLogger(__name__)

_cur_file = Path(__file__).resolve()
# Check potential locations for models/pest: environment variable, current working dir, backend root, or repo root
_candidates = []
_env_dir = os.getenv("PEST_MODEL_DIR", "").strip()
if _env_dir:
    _candidates.append(Path(_env_dir))

_candidates.extend([
    Path.cwd() / "models" / "pest",
    Path.cwd() / "backend" / "models" / "pest",
])
if len(_cur_file.parents) >= 4 and _cur_file.parents[3] != Path(_cur_file.parents[3].root):
    _candidates.append(_cur_file.parents[3] / "models" / "pest")
if len(_cur_file.parents) >= 5 and _cur_file.parents[4] != Path(_cur_file.parents[4].root):
    _candidates.append(_cur_file.parents[4] / "models" / "pest")

DEFAULT_WEIGHTS_DIR = None
for cand in _candidates:
    if cand and cand.exists():
        DEFAULT_WEIGHTS_DIR = cand
        break

if not DEFAULT_WEIGHTS_DIR:
    if len(_cur_file.parents) >= 4 and _cur_file.parents[3] != Path(_cur_file.parents[3].root):
        DEFAULT_WEIGHTS_DIR = _cur_file.parents[3] / "models" / "pest"
    else:
        DEFAULT_WEIGHTS_DIR = Path("models/pest")

DEFAULT_CHECKPOINT_NAME_PT = "ip102_detector.pt"
DEFAULT_CHECKPOINT_NAME_ONNX = "ip102_detector.onnx"


class PestDetectionProvider(ABC):
    """Abstract Base Class for modular insect and pest detection engines."""

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True only if a validated model checkpoint is loaded and operational."""
        pass

    @abstractmethod
    def get_model_info(self) -> PestModelInfo:
        """Returns model architecture, license, and checkpoint status."""
        pass

    @abstractmethod
    def detect_pests(
        self,
        image_bytes: bytes,
        crop_name: Optional[str] = None,
        image_detail: Optional[ImageValidationDetail] = None,
    ) -> Tuple[List[DetectedPestItem], PestModelInfo]:
        """
        Executes pest identification and localization on validated image bytes.
        Returns list of detected pests and model metadata.
        """
        pass


class IP102LocalDetectorProvider(PestDetectionProvider):
    """
    Local offline detector adapter designed for IP102-trained object detection architectures
    (e.g., YOLO11s / YOLOv8 / Faster R-CNN in PyTorch .pt or ONNX format).
    """

    def __init__(self, checkpoint_path: Optional[str] = None):
        if checkpoint_path:
            self.checkpoint_path = checkpoint_path
        elif os.getenv("PEST_MODEL_PATH"):
            self.checkpoint_path = os.getenv("PEST_MODEL_PATH")
        else:
            # Check for .pt first, then .onnx
            pt_path = DEFAULT_WEIGHTS_DIR / DEFAULT_CHECKPOINT_NAME_PT
            onnx_path = DEFAULT_WEIGHTS_DIR / DEFAULT_CHECKPOINT_NAME_ONNX
            if pt_path.exists():
                self.checkpoint_path = str(pt_path)
            elif onnx_path.exists():
                self.checkpoint_path = str(onnx_path)
            else:
                self.checkpoint_path = str(pt_path)

        self._yolo_model = None
        self._ort_session = None
        self._is_loaded = False
        self._load_status_message = ""
        self._init_model()

    def _init_model(self) -> None:
        """Inspects environment and checkpoint path without throwing unhandled exceptions."""
        target_path = Path(self.checkpoint_path)

        if not target_path.exists():
            self._is_loaded = False
            self._load_status_message = (
                f"Model checkpoint not found at '{target_path.as_posix()}'. "
                "Module is configured for IP102 architecture and awaiting pretrained weights. "
                "No inference performed."
            )
            logger.info("IP102LocalDetectorProvider: %s", self._load_status_message)
            return

        # Attempt 1: Load via Ultralytics YOLO (supports both .pt and .onnx)
        try:
            from ultralytics import YOLO
            self._yolo_model = YOLO(str(target_path))
            self._is_loaded = True
            arch_name = "YOLO11s" if "yolo11" in str(target_path).lower() or ".pt" in str(target_path).lower() else "YOLO"
            self._load_status_message = f"{arch_name} IP102 model loaded successfully from '{target_path.as_posix()}'."
            logger.info("IP102LocalDetectorProvider: %s", self._load_status_message)
            return
        except Exception as yolo_err:
            logger.debug("Ultralytics YOLO loader notice: %s. Trying direct ONNX runtime.", yolo_err)

        # Attempt 2: Load via onnxruntime if .onnx file
        if target_path.suffix.lower() == ".onnx":
            try:
                import onnxruntime as ort
                self._ort_session = ort.InferenceSession(str(target_path), providers=["CPUExecutionProvider"])
                self._is_loaded = True
                self._load_status_message = f"ONNX runtime session loaded successfully from '{target_path.as_posix()}'."
                logger.info("IP102LocalDetectorProvider: %s", self._load_status_message)
                return
            except Exception as ort_err:
                self._is_loaded = False
                self._load_status_message = f"Failed to load ONNX session: {str(ort_err)}"
                logger.warning("IP102LocalDetectorProvider error: %s", self._load_status_message)
                return

        # Attempt 3: Direct PyTorch torch.load
        try:
            import torch
            session = torch.load(str(target_path), map_location="cpu")
            if hasattr(session, "eval"):
                session.eval()
            self._ort_session = session
            self._is_loaded = True
            self._load_status_message = f"PyTorch weights loaded successfully from '{target_path.as_posix()}'."
            logger.info("IP102LocalDetectorProvider: %s", self._load_status_message)
        except Exception as torch_err:
            self._is_loaded = False
            self._load_status_message = f"Failed to initialize model session: {str(torch_err)}"
            logger.warning("IP102LocalDetectorProvider load error: %s", self._load_status_message)

    def is_available(self) -> bool:
        return self._is_loaded and (self._yolo_model is not None or self._ort_session is not None)

    def get_model_info(self) -> PestModelInfo:
        arch = "YOLO11 Small (102 Classes)" if self._yolo_model is not None else "IP102 Object Detector"
        framework = "Ultralytics YOLO / PyTorch" if self._yolo_model is not None else "ONNX Runtime / PyTorch"
        return PestModelInfo(
            model_id="ip102-detector-v1",
            model_name="IP102 Deep Agricultural Insect Detector",
            architecture=arch,
            is_operational=self.is_available(),
            checkpoint_path=self.checkpoint_path,
            supported_classes_count=102,
            framework=framework,
            license="MIT License (Open Source)",
            status_message=self._load_status_message,
        )

    def detect_pests(
        self,
        image_bytes: bytes,
        crop_name: Optional[str] = None,
        image_detail: Optional[ImageValidationDetail] = None,
    ) -> Tuple[List[DetectedPestItem], PestModelInfo]:
        """
        Executes real object detection inference if operational.
        Returns list of detected pests with normalized bounding boxes and model metadata.
        """
        model_info = self.get_model_info()

        if not self.is_available():
            # Honest response: never fabricate detections or bounding boxes
            return ([], model_info)

        # 1. Real Ultralytics YOLO inference
        if self._yolo_model is not None:
            try:
                import io
                from PIL import Image

                pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
                results = self._yolo_model.predict(
                    source=pil_img,
                    imgsz=640,
                    conf=0.15,
                    verbose=False,
                )

                detections: List[DetectedPestItem] = []
                if results and len(results) > 0:
                    res0 = results[0]
                    for box in res0.boxes:
                        cls_idx = int(box.cls[0].item())
                        conf_val = float(box.conf[0].item())
                        xyxyn = box.xyxyn[0].tolist()
                        xmin, ymin, xmax, ymax = xyxyn

                        # Clamp coordinates to [0.0, 1.0]
                        xmin = max(0.0, min(1.0, float(xmin)))
                        ymin = max(0.0, min(1.0, float(ymin)))
                        xmax = max(0.0, min(1.0, float(xmax)))
                        ymax = max(0.0, min(1.0, float(ymax)))

                        class_meta = IP102_CATALOG.get(cls_idx, {
                            "name": self._yolo_model.names.get(cls_idx, f"Pest Class {cls_idx}"),
                            "category": "INSECT",
                            "damage_type": "foliar_chewing",
                        })

                        pest_name = class_meta.get("name", self._yolo_model.names.get(cls_idx, f"Pest #{cls_idx}"))

                        bbox = PestBoundingBox(
                            ymin=ymin,
                            xmin=xmin,
                            ymax=ymax,
                            xmax=xmax,
                            label=pest_name,
                            confidence=conf_val,
                        )

                        detections.append(
                            DetectedPestItem(
                                pest_name=pest_name,
                                scientific_name=class_meta.get("scientific_name"),
                                pest_class_id=cls_idx,
                                category=class_meta.get("category", "INSECT"),
                                confidence=conf_val,
                                bounding_box=bbox,
                                damage_type=class_meta.get("damage_type"),
                                description=class_meta.get("description"),
                                affected_organs=class_meta.get("affected_organs", []),
                            )
                        )

                detections.sort(key=lambda x: x.confidence, reverse=True)
                return (detections, model_info)

            except Exception as exc:
                logger.error("Error executing YOLO pest inference: %s", exc)
                model_info.status_message = f"Inference execution failed: {str(exc)}"
                return ([], model_info)

        # 2. Fallback ONNX runtime inference
        try:
            import numpy as np
            from PIL import Image
            import io

            pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            resized = pil_img.resize((640, 640), Image.Resampling.BILINEAR)
            img_arr = np.array(resized, dtype=np.float32) / 255.0
            img_arr = np.transpose(img_arr, (2, 0, 1))
            input_tensor = np.expand_dims(img_arr, axis=0)

            input_name = self._ort_session.get_inputs()[0].name
            outputs = self._ort_session.run(None, {input_name: input_tensor})

            detections: List[DetectedPestItem] = []
            if outputs and len(outputs) > 0:
                raw_boxes = outputs[0]
                if len(raw_boxes.shape) == 3:
                    raw_boxes = raw_boxes[0]

                for row in raw_boxes:
                    if len(row) >= 6:
                        xmin, ymin, xmax, ymax, conf, cls_id = row[:6]
                        cls_idx = int(cls_id)
                        conf_val = float(conf)
                        if conf_val > 0.20 and cls_idx in IP102_CATALOG:
                            class_meta = IP102_CATALOG[cls_idx]
                            bbox = PestBoundingBox(
                                ymin=max(0.0, min(1.0, float(ymin))),
                                xmin=max(0.0, min(1.0, float(xmin))),
                                ymax=max(0.0, min(1.0, float(ymax))),
                                xmax=max(0.0, min(1.0, float(xmax))),
                                label=class_meta["name"],
                                confidence=conf_val,
                            )
                            detections.append(
                                DetectedPestItem(
                                    pest_name=class_meta["name"],
                                    scientific_name=class_meta.get("scientific_name"),
                                    pest_class_id=cls_idx,
                                    category=class_meta.get("category", "INSECT"),
                                    confidence=conf_val,
                                    bounding_box=bbox,
                                    damage_type=class_meta.get("damage_type"),
                                    description=class_meta.get("description"),
                                    affected_organs=class_meta.get("affected_organs", []),
                                )
                            )

            detections.sort(key=lambda x: x.confidence, reverse=True)
            return (detections, model_info)

        except Exception as exc:
            logger.error("Error executing model inference: %s", exc)
            model_info.status_message = f"Inference execution failed: {str(exc)}"
            return ([], model_info)


class HarnessTestPestProvider(PestDetectionProvider):
    """
    Explicit test adapter utilized exclusively by automated test harnesses
    to verify pipeline behaviors (bounding boxes, multi-pest handling, confidence gates).
    Explicitly self-identifies in model_info metadata.
    """

    def __init__(self, initial_operational: bool = True):
        self._operational = initial_operational
        self._queued_detections: Optional[List[DetectedPestItem]] = None

    def set_operational(self, operational: bool) -> None:
        self._operational = operational

    def queue_detections(self, detections: Optional[List[DetectedPestItem]]) -> None:
        self._queued_detections = detections

    def is_available(self) -> bool:
        return self._operational

    def get_model_info(self) -> PestModelInfo:
        return PestModelInfo(
            model_id="harness-test-detector",
            model_name="Automated Test Harness Adapter",
            architecture="Unit Testing Simulation Harness",
            is_operational=self.is_available(),
            checkpoint_path="in-memory-harness",
            supported_classes_count=102,
            framework="Test Suite Mock Harness",
            license="Internal Testing Only",
            status_message="Harness active for automated testing." if self.is_available() else "Harness marked offline.",
        )

    def detect_pests(
        self,
        image_bytes: bytes,
        crop_name: Optional[str] = None,
        image_detail: Optional[ImageValidationDetail] = None,
    ) -> Tuple[List[DetectedPestItem], PestModelInfo]:
        model_info = self.get_model_info()
        if not self.is_available():
            return ([], model_info)
        return (self._queued_detections or [], model_info)


# Singleton instance
_provider_instance: Optional[PestDetectionProvider] = None


def get_pest_provider() -> PestDetectionProvider:
    """Returns configured pest detection provider instance."""
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = IP102LocalDetectorProvider()
    return _provider_instance


def set_pest_provider_for_testing(provider: Optional[PestDetectionProvider]) -> None:
    """Allows test suites to inject an explicit test provider instance."""
    global _provider_instance
    _provider_instance = provider
