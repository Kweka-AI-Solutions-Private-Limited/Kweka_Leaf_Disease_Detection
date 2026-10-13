# Consolidated Multi-Detector Verification Test Plan
**Phase 3 Multi-Detector Platform Protocol — KWEKA Platform**

---

## 1. Architectural Scope & Isolation Boundary
This test plan validates the standalone multi-detector testing environment located strictly within `.experimental_phase1_worktree`:
* **Crop Identification:** Live botanical species recognition via Pl@ntNet API v2 (`/v2/identify/all`), featuring cultivated agricultural crop classification, wild flora identification, and input quality assessment.
* **Disease Pathology Detection:** Live foliar disease identification via Pl@ntNet EPPO API (`/v2/diseases/identify`) with strict **>70% confidence gating**, pathology vs insect filtering (`INVALID_CATEGORY`), and host-crop compatibility checks.
* **Insect & Pest Detection:** Genuine offline inference via the IP102 benchmark YOLO11s detector (`models/pest/ip102_yolo11s.pt`), supporting 102 agricultural insect species with spatial bounding box localization and strict >70% confirmation gating.
* **Weed Detection:** Modular dual-architecture provider supporting both image classification (**DeepWeeds** 9 classes) and spatial object detection (**MH-Weed16** 16 classes). Returns honest `MODEL_UNAVAILABLE` until weights are placed in `models/weed/weed_detector.onnx`.
* **Zero Hallucination Guarantee:** Zero mock substitutions presented as real predictions; zero external calls to Gemini or Kindwise; isolated experimental worktree execution.

---

## 2. Test Matrix & Evaluation Scenarios

| Scenario ID | Test Case | Target Input Condition | Crop Detector Expected | Disease Detector Expected | Pest Detector Expected | Weed Detector Expected |
|:---|:---|:---|:---|:---|:---|:---|
| **TC-01** | **Healthy Crop** | Clear photo of clean, non-infected leaf (e.g., healthy Tomato/Corn) | Identifies crop (e.g., *Solanum lycopersicum*), confirms cultivated crop | `NO_DISEASE_DETECTED` (Genuine negative; foliage marked healthy) | `NO_PEST_DETECTED` | `MODEL_UNAVAILABLE` (or `NO_WEED_DETECTED` if weights loaded) |
| **TC-02** | **Diseased Crop (>70% Conf)** | Foliage with unambiguous pathological lesions (e.g., Early Blight) | Identifies host crop | `CONFIRMED` (`confidence > 0.70`, `confidence_gate_passed = True`) | `NO_PEST_DETECTED` | `MODEL_UNAVAILABLE` |
| **TC-03** | **Diseased Crop (≤70% Conf)** | Foliage with subtle/ambiguous lesions yielding 50%–70% confidence | Identifies host crop | `UNCERTAIN` (`confidence_gate_passed = False`; unconfirmed) | `NO_PEST_DETECTED` | `MODEL_UNAVAILABLE` |
| **TC-04** | **Insect / Pest on Foliage** | Foliage infested with an agricultural pest (e.g., beetle, caterpillar) | Identifies host crop | `INVALID_CATEGORY` (Non-pathology finding excluded from Disease panel) | `CONFIRMED` (IP102 species identified with bounding box) | `MODEL_UNAVAILABLE` |
| **TC-05** | **Weed-Containing Field** | Image containing invasive weeds (e.g., Parthenium, Pigweed) | Identifies wild flora or `UNSUPPORTED` | `NO_DISEASE_DETECTED` | `NO_PEST_DETECTED` | `MODEL_UNAVAILABLE` (honest awaiting weights notice; zero hallucination) |
| **TC-06** | **Suboptimal Image (Blurry)** | Image with Laplacian variance < 12.0 (out of focus) | Quality warning attached | Quality warning attached; confidence adjusted | Evaluates with quality awareness | Quality warning attached |
| **TC-07** | **Invalid/Corrupt Image** | Corrupt bytes, empty file (0B), or < 100×100 px resolution | HTTP 400 Bad Request | HTTP 400 Bad Request | HTTP 400 Bad Request | HTTP 400 Bad Request |
| **TC-08** | **Unsupported / Non-Plant Image** | Object image (furniture, tool, animal) | `UNSUPPORTED` ("No recognized botanical species") | `NO_DISEASE_DETECTED` | `NO_PEST_DETECTED` | `MODEL_UNAVAILABLE` |

---

## 3. Operational Inference Breakdown

| Detection Task | Active Inference Provider | Operational Status | Fallback / Degraded Handling |
|:---|:---|:---|:---|
| **Crop Identification** | Pl@ntNet API v2 (`/v2/identify/all`) | **OPERATIONAL (Real Live Inference)** | Identifies cultivated crops vs wild flora; returns `UNSUPPORTED` on non-plant inputs. |
| **Disease Detection** | Pl@ntNet EPPO Diseases API (`/v2/diseases/identify`) | **OPERATIONAL (Real Live Inference)** | Enforces strict `> 70%` gate; excludes arthropod pests via `INVALID_CATEGORY`; checks host compatibility. |
| **Insect / Pest Detection** | IP102 YOLO11s (`models/pest/ip102_yolo11s.pt`) | **OPERATIONAL (Real Local Inference)** | 102 benchmark insect classes with spatial bounding boxes; strict >70% confirmation gate. |
| **Weed Detection** | Modular Weed Detector (`models/weed/weed_detector.onnx`) | **AWAITING WEIGHTS (Architecture Ready)** | Supports DeepWeeds (9 classes) and MH-Weed16 (16 classes); returns honest `MODEL_UNAVAILABLE` until weights deployed. |

---

## 4. Execution Guidance
1. **Frontend Testing Lab:** Accessible via the sidebar menu under **Testing Lab** or directly at route `/test-lab`.
2. **Workflow:** Upload a single image $\rightarrow$ Preview $\rightarrow$ Click **Analyze Image**.
3. **Verification:** Inspect the four independent cards for Crop, Disease, Pest, and Weed, ensuring operational indicators, model sources, bounding box visualizations, and strict confidence thresholds reflect genuine model execution.
