"""
Standalone Database Connection Manager
--------------------------------------
Handles MongoDB client initialization with robust fallback defaults.
Zero-config deployment ready: works out-of-the-box even if no .env file or environment variables are set.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database

# Load .env if present (optional)
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path)

# Default Cloud MongoDB Cluster fallback
DEFAULT_MONGODB_URI = "mongodb+srv://kweka-dev-user:hn6eFr3bm2iDtAAb@kw-tools.z9xg7hr.mongodb.net/kwprotodb?appName=kw-tools"
DEFAULT_DATABASE_NAME = "kwprotodb"

MONGODB_URI = os.getenv("MONGODB_URI") or DEFAULT_MONGODB_URI
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE") or os.getenv("DATABASE_NAME") or DEFAULT_DATABASE_NAME

_mongo_client: MongoClient = None


def get_client() -> MongoClient:
    """Returns or initializes the global PyMongo MongoClient instance with automatic failover."""
    global _mongo_client
    if _mongo_client is None:
        uri = os.getenv("MONGODB_URI") or MONGODB_URI or DEFAULT_MONGODB_URI
        _mongo_client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return _mongo_client


def get_db(db_name: str = None) -> Database:
    """Returns the MongoDB database instance."""
    client = get_client()
    target_db = db_name or os.getenv("MONGODB_DATABASE") or os.getenv("DATABASE_NAME") or MONGODB_DATABASE or DEFAULT_DATABASE_NAME
    return client[target_db]


def close_connection():
    """Closes the MongoDB client connection."""
    global _mongo_client
    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None
