"""
backend/app/crypto/sign.py

Ed25519 digital signature service for SAKSHI credentials.
- Generates and persists server Ed25519 keypair in backend/keys/ (gitignored).
- Produces canonical JSON (sorted keys, compact separators).
- Signs credential payloads using PyNaCl.
- Verifies signatures (for self-test, verification endpoint, and tamper detection).
"""
import base64
import json
from pathlib import Path
from typing import Any, Optional, Tuple
import nacl.signing

KEYS_DIR = Path(__file__).resolve().parent.parent.parent / "keys"
PRIVATE_KEY_PATH = KEYS_DIR / "private.key"
PUBLIC_KEY_PATH = KEYS_DIR / "public.key"


def get_or_create_keypair() -> Tuple[nacl.signing.SigningKey, nacl.signing.VerifyKey]:
    """
    Loads existing Ed25519 keypair from disk, or generates and saves a new one.
    """
    KEYS_DIR.mkdir(parents=True, exist_ok=True)
    if PRIVATE_KEY_PATH.exists() and PUBLIC_KEY_PATH.exists():
        try:
            private_bytes = PRIVATE_KEY_PATH.read_bytes()
            signing_key = nacl.signing.SigningKey(private_bytes)
            return signing_key, signing_key.verify_key
        except Exception:
            # If key file is corrupted, regenerate
            pass

    signing_key = nacl.signing.SigningKey.generate()
    verify_key = signing_key.verify_key
    PRIVATE_KEY_PATH.write_bytes(signing_key.encode())
    PUBLIC_KEY_PATH.write_bytes(verify_key.encode())
    return signing_key, verify_key


def canonical_json(payload: dict[str, Any]) -> bytes:
    """
    Converts dict into canonical JSON bytes: keys sorted lexicographically,
    no whitespace between tokens (separators=(',', ':')).
    Identical representation across Python backend and TweetNaCl in browser.
    """
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_payload(payload_dict: dict[str, Any]) -> Tuple[str, str]:
    """
    Signs canonical JSON representation of payload with server Ed25519 private key.
    Returns: (signature_b64, pubkey_b64)
    """
    signing_key, verify_key = get_or_create_keypair()
    data = canonical_json(payload_dict)
    signed = signing_key.sign(data)
    signature_b64 = base64.b64encode(signed.signature).decode("utf-8")
    pubkey_b64 = base64.b64encode(verify_key.encode()).decode("utf-8")
    return signature_b64, pubkey_b64


def verify_signature(
    payload_dict: dict[str, Any],
    signature_b64: str,
    pubkey_b64: Optional[str] = None,
) -> bool:
    """
    Verifies that the Ed25519 signature corresponds to payload_dict.
    Uses provided pubkey_b64 or default server public key.
    Returns True if valid, False if tampered or invalid.
    """
    try:
        if pubkey_b64:
            vk = nacl.signing.VerifyKey(base64.b64decode(pubkey_b64))
        else:
            _, vk = get_or_create_keypair()

        data = canonical_json(payload_dict)
        sig_bytes = base64.b64decode(signature_b64)
        vk.verify(data, sig_bytes)
        return True
    except Exception:
        return False


def get_public_key_b64() -> str:
    """
    Returns server public key in Base64 encoding.
    """
    _, verify_key = get_or_create_keypair()
    return base64.b64encode(verify_key.encode()).decode("utf-8")
