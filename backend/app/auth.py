"""Authentication and authorization utilities."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Header
from functools import wraps

SECRET_KEY = os.getenv("APP_SECRET_KEY", "dev-live-python-compiler-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


def create_access_token(user_id: str, role: str = "user", expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {
        "sub": user_id,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(user_id: str) -> str:
    """Create a JWT refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def extract_token_from_header(authorization: str | None) -> str:
    """Extract bearer token from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid bearer token")
    return authorization.split(" ", 1)[1]


async def get_current_user(authorization: str | None = Header(default=None, alias="Authorization")) -> dict:
    """Dependency to get current authenticated user."""
    from .storage import get_user_by_id
    
    token = extract_token_from_header(authorization)
    payload = verify_token(token)
    
    # Only accept access tokens
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    
    user_id = payload.get("sub")
    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return {"id": user_id, **user, "role": payload.get("role", "user")}


async def get_current_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency to ensure current user is admin."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def require_auth(func):
    """Decorator for routes that require authentication."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # This is handled by FastAPI dependencies, this is just for clarity
        return await func(*args, **kwargs)
    return wrapper


def require_role(required_role: str):
    """Decorator to require a specific role."""
    def decorator(func):
        @wraps(func)
        async def wrapper(current_user: dict = Depends(get_current_user), *args, **kwargs):
            if current_user.get("role") != required_role:
                raise HTTPException(status_code=403, detail=f"{required_role.capitalize()} access required")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator
