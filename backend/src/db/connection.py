"""
Standalone Database Connection Manager
--------------------------------------
Handles MongoDB client initialization using environment variables:
  - MONGODB_URI (e.g. mongodb://localhost:27017)
  - MONGODB_DATABASE (fallback: 'leaf_disease_db')
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database

_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path)

MONGODB_URI = os.getenv("MONGODB_URI", "")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE") or os.getenv("DATABASE_NAME") or "leaf_disease_db"

_mongo_client: MongoClient = None


def get_client() -> MongoClient:
    """Returns or initializes the global PyMongo MongoClient instance."""
    global _mongo_client
    if _mongo_client is None:
        uri = MONGODB_URI or "mongodb://localhost:27017"
        _mongo_client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return _mongo_client


def get_db(db_name: str = None) -> Database:
    """Returns the MongoDB database instance."""
    client = get_client()
    return client[db_name or MONGODB_DATABASE]


def close_connection():
    """Closes the MongoDB client connection."""
    global _mongo_client
    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None
