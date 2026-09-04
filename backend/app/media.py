"""ImageKit configuration for client-side authenticated uploads."""
from __future__ import annotations

import os
import hashlib
import hmac
import time


def get_imagekit_authentication() -> dict:
    public_key = os.getenv("IMAGEKIT_PUBLIC_KEY", "").strip()
    private_key = os.getenv("IMAGEKIT_PRIVATE_KEY", "").strip()
    url_endpoint = os.getenv("IMAGEKIT_URL_ENDPOINT", "").strip()
    if not public_key or not private_key or not url_endpoint:
        raise RuntimeError("ImageKit is not configured")

    expire = int(time.time()) + 600
    token = os.urandom(16).hex()
    signature = hmac.new(
        private_key.encode("utf-8"), f"{token}{expire}".encode("utf-8"), hashlib.sha1
    ).hexdigest()
    return {
        "publicKey": public_key,
        "urlEndpoint": url_endpoint,
        "token": token,
        "expire": expire,
        "signature": signature,
    }