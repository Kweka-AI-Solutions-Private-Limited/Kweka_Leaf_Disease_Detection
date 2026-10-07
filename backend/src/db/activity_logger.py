"""
activity_logger.py — Centralized Activity Logging for MongoDB activity_logs Collection
--------------------------------------------------------------------------------------
Formats and writes activity records to the `activity_logs` collection.
Structure matches parent platform standards:
{
  "user_id": str,
  "prototype_id": str,
  "action": str,
  "category": str,
  "description": str,
  "status": str,
  "metadata": dict,
  "created_at": datetime,
  "updated_at": datetime
}
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pymongo.database import Database

logger = logging.getLogger(__name__)

COLLECTION_NAME = "activity_logs"


def log_activity(
    db: Database,
    action: str,
    category: str,
    description: str,
    status: str = "SUCCESS",
    user_id: str = "system",
    prototype_id: str = "leaf_disease_detector",
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Inserts a standardized activity log entry into the `activity_logs` MongoDB collection.
    """
    if db is None:
        return None

    now = datetime.now(timezone.utc)
    log_doc = {
        "user_id": user_id or "system",
        "prototype_id": prototype_id or "leaf_disease_detector",
        "action": action,
        "category": category,
        "description": description,
        "status": status,
        "metadata": metadata or {},
        "created_at": now,
        "updated_at": now
    }

    try:
        res = db[COLLECTION_NAME].insert_one(log_doc)
        log_id = str(res.inserted_id)
        logger.info(f"[ACTIVITY_LOG] Action: '{action}' | Status: '{status}' | Log ID: '{log_id}'")
        return log_id
    except Exception as e:
        logger.warning(f"[ACTIVITY_LOG_WARN] Failed to write activity log: {e}")
        return None
