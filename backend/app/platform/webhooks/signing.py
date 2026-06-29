from __future__ import annotations

import hashlib
import hmac
import secrets
import time


def generate_webhook_secret() -> str:
    return f"whsec_{secrets.token_hex(32)}"


def hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def sign_payload(secret: str, payload: bytes, timestamp: int | None = None) -> str:
    ts = timestamp or int(time.time())
    signed = hmac.new(secret.encode(), f"{ts}.".encode() + payload, hashlib.sha256).hexdigest()
    return f"t={ts},v1={signed}"


def verify_signature(secret: str, payload: bytes, signature_header: str, tolerance: int = 300) -> bool:
    try:
        parts = dict(p.split("=", 1) for p in signature_header.split(","))
        ts = int(parts["t"])
        sig = parts["v1"]
    except (KeyError, ValueError):
        return False

    if abs(int(time.time()) - ts) > tolerance:
        return False

    expected = hmac.new(secret.encode(), f"{ts}.".encode() + payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)