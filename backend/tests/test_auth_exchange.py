"""
test_auth_exchange.py — Unit Tests for Parent Platform Exchange Code & JWT Flow
---------------------------------------------------------------------------------
Validates:
  1. Token lookup and expiration logic in `auth_router`
  2. Single-use enforcement (`is_used = True`)
  3. HS256 JWT generation with `JWT_SECRET_KEY`
  4. Header extraction of user_id via `Authorization: Bearer <token>`
"""

import os
import pytest
import jwt
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
from bson import ObjectId

from api.auth_router import (
    decode_jwt_token,
    get_current_user_id,
    exchange_code_for_token,
    ExchangeCodeRequest,
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
)
from fastapi import HTTPException


def test_jwt_decode_and_header_extraction():
    test_user_id = "6a75be3faf58c44d1a4526e1"
    now = datetime.now(timezone.utc)
    payload = {
        "sub": test_user_id,
        "user_id": test_user_id,
        "email": "test.agronomist@kweka.ai",
        "name": "Test Agronomist",
        "role": "USER",
        "exp": int((now + timedelta(days=7)).timestamp()),
        "iat": int(now.timestamp()),
    }

    signed_token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    decoded = decode_jwt_token(signed_token)
    assert decoded is not None
    assert decoded["user_id"] == test_user_id
    assert decoded["email"] == "test.agronomist@kweka.ai"

    extracted_id = get_current_user_id(authorization=f"Bearer {signed_token}")
    assert extracted_id == test_user_id


def test_exchange_code_invalid_rejection():
    mock_db = MagicMock()
    mock_db["kp_user_tokens"].find_one.return_value = None

    req = ExchangeCodeRequest(exchange_code="invalid_code_123")
    with pytest.raises(HTTPException) as exc_info:
        exchange_code_for_token(payload=req, db=mock_db)

    assert exc_info.value.status_code == 401
    assert "Invalid or unrecognized" in exc_info.value.detail


def test_exchange_code_already_used_rejection():
    mock_db = MagicMock()
    mock_db["kp_user_tokens"].find_one.return_value = {
        "_id": ObjectId(),
        "token": "code_used",
        "token_type": "EXCHANGE",
        "is_used": True,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
    }

    req = ExchangeCodeRequest(exchange_code="code_used")
    with pytest.raises(HTTPException) as exc_info:
        exchange_code_for_token(payload=req, db=mock_db)

    assert exc_info.value.status_code == 401
    assert "already been used" in exc_info.value.detail


def test_exchange_code_success_issues_jwt():
    user_oid = ObjectId("6a75be3faf58c44d1a4526e1")
    token_oid = ObjectId()

    mock_db = MagicMock()
    mock_db["kp_user_tokens"].find_one.return_value = {
        "_id": token_oid,
        "token": "valid_exchange_code_xyz",
        "token_type": "EXCHANGE",
        "user_id": user_oid,
        "is_used": False,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
    }

    mock_db["kp_users"].find_one.return_value = {
        "_id": user_oid,
        "first_name": "Abhinav",
        "last_name": "Govardhana",
        "email": "abhinav1ras@gmail.com",
        "company": "Kweka",
        "job_title": "Intern",
        "role": "USER",
        "is_active": True,
    }

    req = ExchangeCodeRequest(exchange_code="valid_exchange_code_xyz")
    res = exchange_code_for_token(payload=req, db=mock_db)

    assert res.token is not None
    assert res.user.email == "abhinav1ras@gmail.com"
    assert res.user.name == "Abhinav Govardhana"
    assert res.user.id == str(user_oid)

    # Verify kp_user_tokens was updated to mark used
    mock_db["kp_user_tokens"].update_one.assert_called_once()

    # Verify decoded token
    decoded = decode_jwt_token(res.token)
    assert decoded["user_id"] == str(user_oid)
    assert decoded["email"] == "abhinav1ras@gmail.com"
