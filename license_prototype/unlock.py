"""
THEIR SIDE. This is the logic the shipped client app runs at startup.
Only ever needs issuer_public.pem (baked into the app) -- never the
private key, never our signing capability.
"""
import argparse

from crypto_core import (
    decrypt_payload, verify_and_open_license, local_machine_fingerprint, LicenseError,
)


def unlock(enc_path: str, lic_path: str, machine_id: str = None) -> str:
    """Returns the decrypted plaintext on success. Raises LicenseError on
    any failure, with the exact reason a real app would surface to the user."""
    if machine_id is None:
        machine_id = local_machine_fingerprint()

    with open(lic_path, "r") as f:
        license_str = f.read()

    payload = verify_and_open_license(license_str, machine_id)  # raises on bad sig / wrong machine / expired

    with open(enc_path, "rb") as f:
        blob = f.read()

    import base64
    aes_key = base64.b64decode(payload["aes_key"])
    try:
        plaintext = decrypt_payload(blob, aes_key)
    except Exception:
        # a validly-signed license paired with the WRONG .enc file (e.g. one
        # machine's key against a different machine's payload) -- the AES
        # key embedded in this license simply doesn't match that ciphertext
        raise LicenseError("license does not match this payload file -- wrong license/data pair")
    return plaintext.decode()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--enc", required=True)
    ap.add_argument("--lic", required=True)
    ap.add_argument("--as-machine", default=None, help="override for testing; default = this real machine")
    args = ap.parse_args()

    try:
        result = unlock(args.enc, args.lic, args.as_machine)
        print("UNLOCKED. Decrypted formula subset:\n")
        print(result)
    except LicenseError as e:
        print(f"LOCKED — {e}")
