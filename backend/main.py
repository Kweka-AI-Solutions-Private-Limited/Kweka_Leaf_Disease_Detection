"""
Standalone Leaf Disease Detector Backend Application
------------------------------------------------------
FastAPI server serving Leaf Disease Analysis, Plant Search, and NACL Recommendations.
"""

import os
import sys
from pathlib import Path

# Add src to python path for internal imports
src_path = Path(__file__).resolve().parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.leaf_disease_router import router as leaf_router
from db.nacl_product_db import seed_nacl_products

app = FastAPI(
    title="Standalone Leaf Disease Detector API",
    description="API for Leaf Disease Identification, Image Quality Validation & NACL Treatment Advisory",
    version="1.0.0"
)

# Enable CORS for frontend development & production hosting
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Global exception handler ensuring CORS headers are ALWAYS attached on server error (500)
from fastapi.responses import JSONResponse
from fastapi import Request, HTTPException

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"[ERROR] Unhandled Exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred.", "error": str(exc)},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Mount Leaf Disease Router
app.include_router(leaf_router, prefix="/api")

@app.on_event("startup")
def on_startup():
    print("[INFO] Initializing Leaf Disease Detector Standalone Backend...")
    try:
        count = seed_nacl_products()
        print(f"[INFO] NACL Product Catalog check complete. Seeded/verified {count} items.")
    except Exception as e:
        print(f"[WARN] Database catalog seed deferred: {e}")

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Standalone Leaf Disease Detector API",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    is_dev = os.getenv("ENV", "production").lower() == "development"
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=is_dev)
