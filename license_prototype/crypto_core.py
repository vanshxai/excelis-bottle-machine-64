"""
Shared primitives for the license-key prototype.

Design (mirrors real licensed-software practice, e.g. FlexNet/HASP-style
node-locked licensing):

  - We hold an Ed25519 PRIVATE key. Only we can sign a license.
  - The client app ships with our Ed25519 PUBLIC key baked in. It can
    verify a signature but can never forge one.
  - Each customer's formula subset is encrypted with a random AES-256-GCM
    key. That AES key is embedded INSIDE the signed license payload, so
    the license and the decryption key are the same artifact -- you
    can't separate "proof this is valid" from "the actual key."
  - The signed payload also carries machine_id + expiry, so tampering
    with either breaks the signature and the license is rejected outright.
"""
import base64
import json
import os
import platform
import subprocess
import uuid
from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import serialization

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Keys live in a writable per-user location, not next to this file -- a
# packaged/signed .app's own bundle directory is read-only at runtime, so
# writing the keypair there would silently fail once this isn't run as a
# plain script anymore.
_APP_SUPPORT = os.path.expanduser("~/Library/Application Support/FaulterAI")
os.makedirs(os.path.join(_APP_SUPPORT, "keys"), exist_ok=True)
PRIV_KEY_FILE = os.path.join(_APP_SUPPORT, "keys", "issuer_private.pem")
PUB_KEY_FILE = os.path.join(_APP_SUPPORT, "keys", "issuer_public.pem")


# ---------------------------------------------------------------------------
# Issuer keypair -- generated once, PRIV never leaves our side
# ---------------------------------------------------------------------------

def ensure_issuer_keypair():
    if os.path.exists(PRIV_KEY_FILE) and os.path.exists(PUB_KEY_FILE):
        return
    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()
    with open(PRIV_KEY_FILE, "wb") as f:
        f.write(priv.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ))
    with open(PUB_KEY_FILE, "wb") as f:
        f.write(pub.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ))
    os.chmod(PRIV_KEY_FILE, 0o600)


def load_private_key() -> Ed25519PrivateKey:
    with open(PRIV_KEY_FILE, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def load_public_key() -> Ed25519PublicKey:
    with open(PUB_KEY_FILE, "rb") as f:
        return serialization.load_pem_public_key(f.read())


# ---------------------------------------------------------------------------
# Machine fingerprint -- what a real product would swap for the OS-specific
# stable hardware ID (Windows: WMI ComputerSystemProduct.UUID, Mac:
# IOPlatformUUID via `ioreg`, Linux: /etc/machine-id). Prototype reads the
# real Mac hardware UUID so the mechanism is genuine, not faked.
# ---------------------------------------------------------------------------

def local_machine_fingerprint() -> str:
    if platform.system() == "Darwin":
        try:
            out = subprocess.check_output(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"], text=True,
            )
            for line in out.splitlines():
                if "IOPlatformUUID" in line:
                    return line.split('"')[-2]
        except Exception:
            pass
    # fallback, any platform: hash of the MAC address
    return f"fallback-{uuid.getnode():012x}"


# ---------------------------------------------------------------------------
# AES-256-GCM payload encryption (the actual formula-subset content)
# ---------------------------------------------------------------------------

def encrypt_payload(plaintext: bytes, aes_key: bytes) -> bytes:
    nonce = os.urandom(12)
    ct = AESGCM(aes_key).encrypt(nonce, plaintext, None)
    return nonce + ct  # nonce prepended, standard practice


def decrypt_payload(blob: bytes, aes_key: bytes) -> bytes:
    nonce, ct = blob[:12], blob[12:]
    return AESGCM(aes_key).decrypt(nonce, ct, None)


# ---------------------------------------------------------------------------
# License token = base64(payload_json) . base64(signature)
# ---------------------------------------------------------------------------

def issue_license(machine_id: str, subset_name: str, aes_key: bytes, valid_days: int) -> str:
    ensure_issuer_keypair()
    priv = load_private_key()
    now = datetime.now(timezone.utc)
    payload = {
        "machine_id": machine_id,
        "subset": subset_name,
        "aes_key": base64.b64encode(aes_key).decode(),
        "issued": now.isoformat(),
        "expires": (now + timedelta(days=valid_days)).isoformat(),
    }
    payload_bytes = json.dumps(payload, sort_keys=True).encode()
    signature = priv.sign(payload_bytes)
    return base64.urlsafe_b64encode(payload_bytes).decode() + "." + base64.urlsafe_b64encode(signature).decode()


class LicenseError(Exception):
    pass


def verify_and_open_license(license_str: str, claimed_machine_id: str) -> dict:
    """Returns the verified payload dict, or raises LicenseError with a
    specific human-readable reason -- this is exactly what the shipped
    client app would show the user."""
    try:
        payload_b64, sig_b64 = license_str.strip().split(".")
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        signature = base64.urlsafe_b64decode(sig_b64)
    except Exception:
        raise LicenseError("license file is malformed / corrupted")

    pub = load_public_key()
    try:
        pub.verify(signature, payload_bytes)
    except Exception:
        raise LicenseError("signature invalid -- license has been tampered with, or was not issued by us")

    payload = json.loads(payload_bytes)

    # Decided: no hardware/PC lock (the "Unreal Engine model" -- enforcement
    # is the signed contract + expiry, not a machine fingerprint). client_id
    # stays in the signed payload as a record of who it was issued to, not
    # as a check performed here.

    expires = datetime.fromisoformat(payload["expires"])
    if datetime.now(timezone.utc) > expires:
        raise LicenseError(f"license expired on {expires.date().isoformat()}")

    return payload
