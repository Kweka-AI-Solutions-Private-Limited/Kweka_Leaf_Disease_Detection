# 🌿 Kweka Leaf Disease Detection & Agricultural Advisory System

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React_18-61DAFB?style=flat-square&logo=react)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Bundler-Vite-646CFF?style=flat-square&logo=vite)](https://vitejs.dev/)
[![MongoDB](https://img.shields.io/badge/Database-MongoDB-47A248?style=flat-square&logo=mongodb)](https://www.mongodb.com/)
[![Gemini AI](https://img.shields.io/badge/AI-Gemini_2.5_Flash-4285F4?style=flat-square&logo=google)](https://ai.google.dev/)

An enterprise-grade, standalone **AI-powered Leaf Disease Detection, Crop Pathology Identification, and NACL Agrochemical Advisory System** built for **Kweka AI Solutions**.

---

## 🏗️ Project Architecture & Directory Structure

```
leaf_disease_detector/
├── backend/
│   ├── main.py                     # FastAPI Application Entrypoint & Startup Hooks
│   ├── requirements.txt            # Python Backend Dependencies
│   ├── .env.example                # Template Environment Variables File
│   └── src/
│       ├── api/
│       │   └── leaf_disease_router.py  # REST API Routes (/analyze, /history, /activity-logs, /catalog)
│       ├── services/leaf_disease/
│       │   ├── diagnosis_validator.py       # Diagnosis Quality & Evidence Calibration
│       │   ├── disease_provider.py         # Disease Classifier & Provider Router
│       │   ├── gemini_leaf_fallback.py     # Gemini 2.5 Vision AI Second-Opinion & Fallback
│       │   ├── image_validator.py          # Multi-Image Blur, Brightness & Format Validator
│       │   ├── nacl_recommendation_engine.py# Deterministic RAG & Agrochemical Treatment Engine
│       │   ├── plant_identifier.py         # Crop / Species Identification
│       │   └── plant_search_service.py     # Pl@ntNet & Gemini Botanical Species Search
│       ├── schemas/
│       │   ├── leaf_disease.py            # Pydantic Schemas for Analysis & Validation
│       │   └── nacl_catalog.py            # Schemas for Agrochemical Products & Treatment
│       ├── db/
│       │   ├── connection.py              # PyMongo Client & Database Manager
│       │   ├── activity_logger.py         # Centralized Activity Logging (`activity_logs`)
│       │   └── nacl_product_db.py         # Product Catalog Queries & Seeder (`ldd_nacl_products`)
│       └── data/
│           └── nacl_catalog.json          # Verified Agrochemical Catalog Seed Data
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── index.html
    └── src/
        ├── App.tsx                        # Main App Shell & Routing Setup
        ├── main.tsx                       # React Entrypoint
        ├── pages/
        │   ├── DashboardPage.tsx          # Real-time Metrics & Live Activity Stream
        │   ├── LeafDiseasePage.tsx         # Multi-Image Diagnosis & Treatment Interface
        │   ├── HistoryPage.tsx            # Historical Inspection Records (`ldd_inspections`)
        │   ├── CatalogPage.tsx            # Interactive NACL Agrochemical Directory
        │   ├── AnalyticsPage.tsx          # Telemetry & Pathology Statistics
        │   └── SettingsPage.tsx           # Platform Settings & API Configuration
        ├── components/
        │   ├── common/                    # UI Components (Cards, Modals, Tour)
        │   └── layout/                    # Industrial Terracotta Sidebar & Layout
        └── api/
            ├── client.ts                  # Axios Client Instance
            └── leafDisease.ts             # API Client Methods & Activity Log Fetcher
```

---

## 🗄️ MongoDB Database Collections

The backend connects to MongoDB database `leaf_disease_db` *(configurable via `MONGODB_DATABASE`)* using **project-specific collection prefixes**:

| Collection Name | Primary Purpose | Key Fields / Data Stored |
| :--- | :--- | :--- |
| **`ldd_inspections`** | Inspection Run History | `analysis_id`, `status`, `crop`, `disease`, `validation`, `diagnosis`, `nacl_recommendations`, `filenames`, `created_at` |
| **`ldd_nacl_products`** | NACL Product Catalog | `product_id`, `product_name`, `category`, `active_ingredient`, `crop_applications`, `dosage`, `frac_group`, `source_url` |
| **`activity_logs`** | Platform Activity Log Feed | `user_id`, `prototype_id`, `action`, `category`, `description`, `status`, `metadata`, `created_at`, `updated_at` |

---

## 📡 REST API Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/leaf-disease/analyze` | Accepts up to 5 leaf images, executes quality validation, crop ID, disease detection, Gemini second opinion, and persists run to `ldd_inspections`. |
| `GET` | `/api/leaf-disease/history` | Retrieves historical analysis runs from `ldd_inspections` (supports filtering by `status` and `crop_name`). |
| `GET` | `/api/leaf-disease/history/{id}` | Retrieves details for a specific analysis run by ID. |
| `DELETE`| `/api/leaf-disease/history/{id}` | Deletes a specific run record and logs deletion activity. |
| `DELETE`| `/api/leaf-disease/history` | Clears all run history records and logs activity. |
| `GET` | `/api/leaf-disease/activity-logs` | Retrieves real-time platform activity logs from `activity_logs` collection. |
| `GET` | `/api/leaf-disease/catalog` | Returns categorized NACL product directory from `ldd_nacl_products`. |
| `GET` | `/api/leaf-disease/plants/search` | Searches botanical plant species dynamically via Pl@ntNet API and Gemini fallback. |

---

## ⚡ Quick Start & Local Setup

### 1. Backend Setup (FastAPI)

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # Windows PowerShell:
   venv\Scripts\activate
   # Linux / macOS:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables (`backend/.env`):
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   MONGODB_URI=mongodb://localhost:27017
   MONGODB_DATABASE=leaf_disease_db
   PORT=8000
   ```
5. Start the backend server:
   ```bash
   python main.py
   # Or using uvicorn directly:
   uvicorn main:app --reload --port 8000
   ```
   Interactive API documentation will be available at: **`http://localhost:8000/docs`**

---

### 2. Frontend Setup (React + Vite)

1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```
4. Open your browser at **`http://localhost:5173`**.

---

## 🚀 Key Features

* **Multi-Image Quality Validation**: Evaluates blur score, brightness levels, resolution, and format compliance for up to 5 uploaded leaf images.
* **Intelligent Crop & Species Identification**: Integrates Pl@ntNet API with Gemini 2.5 Vision fallback.
* **Dual AI Second-Opinion Verification**: Reconciles primary pathology classifiers with independent Gemini VLM second opinion when confidence is low or evidence is conflicting.
* **Deterministic Agrochemical Advisory RAG Engine**: Matches verified crop diseases against NACL products with exact dosage verification, FRAC resistance management groups, and safety precautions.
* **Dynamic Dashboard & Real-Time Activity Feed**: Live metrics powered by `ldd_inspections`, `ldd_nacl_products`, and `activity_logs`.

---

© 2026 Kweka AI Solutions Private Limited. All rights reserved.
