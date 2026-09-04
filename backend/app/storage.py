from __future__ import annotations

import hashlib
import hmac
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

try:
    from pymongo import ASCENDING, MongoClient, ReturnDocument
    from pymongo.errors import PyMongoError
except ImportError:  # MongoDB is optional when using the local JSON fallback.
    ASCENDING = MongoClient = ReturnDocument = PyMongoError = None

DATA_DIR = Path(__file__).resolve().parent / "data"
USERS_PATH = DATA_DIR / "users.json"
CODES_PATH = DATA_DIR / "saved_codes.json"
PERMISSIONS_PATH = DATA_DIR / "permissions.json"


class StorageUnavailableError(RuntimeError):
    """Raised when the configured production storage cannot be reached."""

MONGODB_URI = os.getenv("MONGODB_URI", "").strip()
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "live_python_compiler")
if MONGODB_URI and MongoClient is None:
    raise RuntimeError("MONGODB_URI is configured but pymongo is not installed")
_mongo_client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=3000,
    connectTimeoutMS=3000,
) if MONGODB_URI else None
_mongo_db = _mongo_client[MONGODB_DATABASE] if _mongo_client else None


def _use_mongodb() -> bool:
    return _mongo_db is not None


def _mongo_document(document: dict | None) -> dict | None:
    if document is None:
        return None
    document.pop("_id", None)
    return document


def _users_collection():
    collection = _mongo_db.users
    collection.create_index([("email", ASCENDING)], unique=True)
    return collection


def _user_view(user: dict) -> dict:
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user.get("role", "user"),
        "ai_plan": user.get("ai_plan", "free"),
        "ai_subscription_status": user.get("ai_subscription_status", "active"),
        "avatar_url": user.get("avatar_url", ""),
        "created_at": user.get("created_at", ""),
        "updated_at": user.get("updated_at", ""),
    }


def _ensure_file(path: Path, default):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(json.dumps(default, indent=2), encoding="utf-8")


def _read_json(path: Path, default):
    _ensure_file(path, default)
    try:
        raw = path.read_text(encoding="utf-8").strip()
        if not raw:
            return default
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def _write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return salt.hex() + ":" + digest.hex()


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, digest_hex = stored_hash.split(":", 1)
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    expected = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return hmac_compare(expected.hex(), digest_hex)


def hmac_compare(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)


# User Management
def list_users() -> list[dict]:
    if _use_mongodb():
        return [_mongo_document(user) for user in _users_collection().find({}, {"_id": 0})]
    return _read_json(USERS_PATH, [])


def save_users(users: list[dict]) -> None:
    if _use_mongodb():
        collection = _users_collection()
        collection.delete_many({})
        if users:
            collection.insert_many(users)
        return
    _write_json(USERS_PATH, users)


def create_user(name: str, email: str, password: str, role: str = "user") -> dict:
    normalized_email = email.strip().lower()
    try:
        if _use_mongodb() and _users_collection().find_one({"email": normalized_email}):
            raise ValueError("An account already exists for this email.")
        users = list_users()
        if not _use_mongodb() and any(user["email"].lower() == normalized_email for user in users):
            raise ValueError("An account already exists for this email.")
    except ValueError:
        raise
    except PyMongoError as exc:
        raise StorageUnavailableError(
            "MongoDB is unavailable. Set MONGODB_URI to a reachable production database."
        ) from exc

    user = {
        "id": f"user_{uuid.uuid4().hex[:10]}",
        "name": name.strip() or "User",
        "email": normalized_email,
        "password_hash": hash_password(password),
        "role": role,  # "user" or "admin"
        "ai_plan": "free",
        "ai_subscription_status": "active",
        "avatar_url": "",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if _use_mongodb():
        try:
            _users_collection().insert_one(user)
        except PyMongoError as exc:
            if "duplicate key" in str(exc).lower():
                raise ValueError("An account already exists for this email.") from exc
            raise StorageUnavailableError(
                "MongoDB is unavailable. Set MONGODB_URI to a reachable production database."
            ) from exc
    else:
        users.append(user)
        save_users(users)
    return _user_view(user)


def authenticate_user(email: str, password: str) -> dict | None:
    users = ([_users_collection().find_one({"email": email.strip().lower()}, {"_id": 0})]
             if _use_mongodb() else list_users())
    for user in users:
        if user and (user["email"].lower() == email.strip().lower()
            and user.get("is_active", True)
            and verify_password(password, user["password_hash"])):
            return _user_view(user)
    return None


def get_user_by_id(user_id: str) -> dict | None:
    if _use_mongodb():
        user = _users_collection().find_one({"id": user_id}, {"_id": 0})
        return _user_view(user) if user else None
    for user in list_users():
        if user["id"] == user_id:
            return _user_view(user)
    return None


def update_user(user_id: str, **kwargs) -> dict | None:
    """Update user fields (name, email, etc)."""
    if _use_mongodb():
        update_data = {field: value for field, value in kwargs.items() if field in {"name", "email", "avatar_url"}}
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        result = _users_collection().find_one_and_update(
            {"id": user_id}, {"$set": update_data}, return_document=ReturnDocument.AFTER
        )
        return _user_view(result) if result else None
    users = list_users()
    for user in users:
        if user["id"] == user_id:
            # Don't allow direct role or password updates here
            allowed_fields = {"name", "email", "avatar_url"}
            for field, value in kwargs.items():
                if field in allowed_fields:
                    user[field] = value
            user["updated_at"] = datetime.now(timezone.utc).isoformat()
            save_users(users)
            return {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user.get("role", "user"),
                "ai_plan": user.get("ai_plan", "free"),
                "ai_subscription_status": user.get("ai_subscription_status", "active"),
                "created_at": user.get("created_at", ""),
                "updated_at": user.get("updated_at", ""),
            }
    return None


def change_password(user_id: str, old_password: str, new_password: str) -> bool:
    """Change user password."""
    if _use_mongodb():
        user = _users_collection().find_one({"id": user_id})
        if user and verify_password(old_password, user["password_hash"]):
            _users_collection().update_one({"id": user_id}, {"$set": {
                "password_hash": hash_password(new_password),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }})
            return True
        return False
    users = list_users()
    for user in users:
        if user["id"] == user_id and verify_password(old_password, user["password_hash"]):
            user["password_hash"] = hash_password(new_password)
            user["updated_at"] = datetime.now(timezone.utc).isoformat()
            save_users(users)
            return True
    return False


def delete_user(user_id: str) -> bool:
    """Delete a user and all their data."""
    if _use_mongodb():
        _users_collection().delete_one({"id": user_id})
        _mongo_db.codes.delete_many({"user_id": user_id})
        _mongo_db.permissions.delete_many({"$or": [{"user_id": user_id}, {"shared_with": user_id}]})
        return True
    users = list_users()
    users = [u for u in users if u["id"] != user_id]
    save_users(users)
    
    # Delete user's saved codes
    codes = _read_json(CODES_PATH, [])
    codes = [c for c in codes if c.get("user_id") != user_id]
    _write_json(CODES_PATH, codes)
    
    # Delete user's permissions
    permissions = _read_json(PERMISSIONS_PATH, [])
    permissions = [p for p in permissions if p.get("user_id") != user_id and p.get("shared_with") != user_id]
    _write_json(PERMISSIONS_PATH, permissions)
    
    return True


# Code Management
def list_saved_codes(user_id: str) -> list[dict]:
    if _use_mongodb():
        return [_mongo_document(entry) for entry in _mongo_db.codes.find({"user_id": user_id}, {"_id": 0})]
    entries = _read_json(CODES_PATH, [])
    return [entry for entry in entries if entry.get("user_id") == user_id]


def save_user_code(user_id: str, title: str, code: str, language: str = "python", is_public: bool = False) -> dict:
    item = {
        "id": f"code_{uuid.uuid4().hex[:10]}",
        "user_id": user_id,
        "title": title.strip() or "Untitled script",
        "language": language,
        "code": code,
        "is_public": is_public,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if _use_mongodb():
        _mongo_db.codes.insert_one(item)
    else:
        entries = _read_json(CODES_PATH, [])
        entries.append(item)
        _write_json(CODES_PATH, entries)
    return item


def get_saved_code(code_id: str, user_id: str) -> dict | None:
    """Get code by ID if user is owner."""
    if _use_mongodb():
        return _mongo_document(_mongo_db.codes.find_one({"id": code_id, "user_id": user_id}, {"_id": 0}))
    for entry in list_saved_codes(user_id):
        if entry["id"] == code_id:
            return entry
    return None


def update_saved_code(code_id: str, user_id: str, **kwargs) -> dict | None:
    """Update saved code (title, code, is_public)."""
    if _use_mongodb():
        updates = {field: value for field, value in kwargs.items() if field in {"title", "code", "is_public"}}
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        return _mongo_document(_mongo_db.codes.find_one_and_update(
            {"id": code_id, "user_id": user_id}, {"$set": updates}, return_document=ReturnDocument.AFTER,
            projection={"_id": 0},
        ))
    entries = _read_json(CODES_PATH, [])
    for entry in entries:
        if entry["id"] == code_id and entry.get("user_id") == user_id:
            allowed_fields = {"title", "code", "is_public"}
            for field, value in kwargs.items():
                if field in allowed_fields:
                    entry[field] = value
            entry["updated_at"] = datetime.now(timezone.utc).isoformat()
            _write_json(CODES_PATH, entries)
            return entry
    return None


def delete_saved_code(code_id: str, user_id: str) -> bool:
    """Delete a saved code."""
    if _use_mongodb():
        result = _mongo_db.codes.delete_one({"id": code_id, "user_id": user_id})
        if result.deleted_count:
            _mongo_db.permissions.delete_many({"code_id": code_id})
            return True
        return False
    entries = _read_json(CODES_PATH, [])
    original_len = len(entries)
    entries = [e for e in entries if not (e["id"] == code_id and e.get("user_id") == user_id)]
    if len(entries) < original_len:
        _write_json(CODES_PATH, entries)
        # Also delete permissions for this code
        permissions = _read_json(PERMISSIONS_PATH, [])
        permissions = [p for p in permissions if p.get("code_id") != code_id]
        _write_json(PERMISSIONS_PATH, permissions)
        return True
    return False


def get_public_codes() -> list[dict]:
    """Get all public codes."""
    if _use_mongodb():
        return [_mongo_document(entry) for entry in _mongo_db.codes.find({"is_public": True}, {"_id": 0})]
    entries = _read_json(CODES_PATH, [])
    return [entry for entry in entries if entry.get("is_public", False)]


# Code Permissions/Sharing
def share_code(code_id: str, user_id: str, shared_with_user_id: str, permission: Literal["view", "edit"] = "view") -> dict | None:
    """Share code with another user."""
    if _use_mongodb():
        if not _mongo_db.codes.find_one({"id": code_id, "user_id": user_id}):
            return None
        now = datetime.now(timezone.utc).isoformat()
        item = _mongo_db.permissions.find_one_and_update(
            {"code_id": code_id, "shared_with": shared_with_user_id},
            {"$set": {"permission": permission, "updated_at": now}, "$setOnInsert": {
                "id": f"perm_{uuid.uuid4().hex[:10]}", "user_id": user_id,
                "created_at": now,
            }}, upsert=True, return_document=ReturnDocument.AFTER, projection={"_id": 0},
        )
        return _mongo_document(item)
    # Verify code exists and belongs to user
    codes = _read_json(CODES_PATH, [])
    code = next((c for c in codes if c["id"] == code_id and c.get("user_id") == user_id), None)
    if not code:
        return None
    
    permissions = _read_json(PERMISSIONS_PATH, [])
    
    # Check if already shared
    existing = next(
        (p for p in permissions 
         if p.get("code_id") == code_id and p.get("shared_with") == shared_with_user_id),
        None
    )
    
    if existing:
        existing["permission"] = permission
        existing["updated_at"] = datetime.now(timezone.utc).isoformat()
    else:
        existing = {
            "id": f"perm_{uuid.uuid4().hex[:10]}",
            "code_id": code_id,
            "user_id": user_id,
            "shared_with": shared_with_user_id,
            "permission": permission,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        permissions.append(existing)
    
    _write_json(PERMISSIONS_PATH, permissions)
    return existing


def get_shared_codes(user_id: str) -> list[dict]:
    """Get codes shared with user."""
    if _use_mongodb():
        result = []
        for permission in _mongo_db.permissions.find({"shared_with": user_id}, {"_id": 0}):
            code = _mongo_db.codes.find_one({"id": permission.get("code_id")}, {"_id": 0})
            if code:
                result.append({**code, "permission": permission.get("permission"), "shared_by": permission.get("user_id")})
        return result
    permissions = _read_json(PERMISSIONS_PATH, [])
    codes = _read_json(CODES_PATH, [])
    
    shared_codes = []
    for perm in permissions:
        if perm.get("shared_with") == user_id:
            code = next((c for c in codes if c["id"] == perm.get("code_id")), None)
            if code:
                shared_codes.append({
                    **code,
                    "permission": perm.get("permission"),
                    "shared_by": perm.get("user_id"),
                })
    
    return shared_codes


def check_code_access(code_id: str, user_id: str) -> tuple[bool, str | None]:
    """Check if user has access to code. Returns (has_access, permission)."""
    if _use_mongodb():
        code = _mongo_db.codes.find_one({"id": code_id}, {"_id": 0})
        if not code:
            return False, None
        if code.get("user_id") == user_id:
            return True, "own"
        if code.get("is_public", False):
            return True, "view"
        permission = _mongo_db.permissions.find_one({"code_id": code_id, "shared_with": user_id})
        return (True, permission.get("permission")) if permission else (False, None)
    codes = _read_json(CODES_PATH, [])
    code = next((c for c in codes if c["id"] == code_id), None)
    
    if not code:
        return False, None
    
    # Owner has full access
    if code.get("user_id") == user_id:
        return True, "own"
    
    # Check if public
    if code.get("is_public", False):
        return True, "view"
    
    # Check permissions
    permissions = _read_json(PERMISSIONS_PATH, [])
    perm = next(
        (p for p in permissions 
         if p.get("code_id") == code_id and p.get("shared_with") == user_id),
        None
    )
    
    if perm:
        return True, perm.get("permission")
    
    return False, None


def revoke_code_access(code_id: str, user_id: str, revoke_from_user_id: str) -> bool:
    """Revoke shared access to code."""
    if _use_mongodb():
        result = _mongo_db.permissions.delete_one({
            "code_id": code_id, "user_id": user_id, "shared_with": revoke_from_user_id,
        })
        return result.deleted_count > 0
    permissions = _read_json(PERMISSIONS_PATH, [])
    original_len = len(permissions)
    permissions = [
        p for p in permissions
        if not (p.get("code_id") == code_id 
                and p.get("user_id") == user_id 
                and p.get("shared_with") == revoke_from_user_id)
    ]
    
    if len(permissions) < original_len:
        _write_json(PERMISSIONS_PATH, permissions)
        return True
    return False
