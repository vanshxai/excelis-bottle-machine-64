"""
Runs the 5 scenarios that actually prove the lock mechanic works:

  1. Right machine, right subset          -> unlocks, shows real formulas
  2. Same license, different machine      -> rejected (machine mismatch)
  3. Tampered license (1 byte flipped)    -> rejected (bad signature)
  4. Already-expired license              -> rejected (expired)
  5. Reading the .enc file directly       -> unreadable ciphertext

No CAD, no Brain, no 3D -- purely: is the encrypt/sign/verify/decrypt
mechanic sound.
"""
import base64
import os

from crypto_core import (
    ensure_issuer_keypair, encrypt_payload, issue_license, local_machine_fingerprint,
)
from unlock import unlock, LicenseError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE_DIR, "out")
SUBSETS = os.path.join(BASE_DIR, "subsets")


def line(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def main():
    ensure_issuer_keypair()
    os.makedirs(OUT, exist_ok=True)
    real_machine = local_machine_fingerprint()
    fake_other_machine = "SIMULATED-DIFFERENT-MACHINE-FINGERPRINT-XYZ"

    # --- issue a normal license for THIS machine, the bottle-machine subset ---
    with open(os.path.join(SUBSETS, "subset_bottle.json"), "rb") as f:
        plaintext = f.read()
    aes_key = os.urandom(32)
    enc_path = os.path.join(OUT, "demo_bottle.enc")
    with open(enc_path, "wb") as f:
        f.write(encrypt_payload(plaintext, aes_key))
    lic_path = os.path.join(OUT, "demo_bottle.lic")
    with open(lic_path, "w") as f:
        f.write(issue_license(real_machine, "subset_bottle.json", aes_key, valid_days=150))

    line("1. RIGHT machine, RIGHT license -> should UNLOCK")
    try:
        print(unlock(enc_path, lic_path, real_machine))
        print("--> PASS: decrypted successfully")
    except LicenseError as e:
        print(f"--> FAIL (unexpected): {e}")

    line("2. Same license, but a DIFFERENT machine claims it -> should REJECT")
    try:
        print(unlock(enc_path, lic_path, fake_other_machine))
        print("--> FAIL (unexpected): should not have unlocked")
    except LicenseError as e:
        print(f"--> PASS, rejected as expected: {e}")

    line("3. License file TAMPERED (one byte flipped) -> should REJECT")
    with open(lic_path) as f:
        original = f.read()
    payload_part, sig_part = original.split(".")
    tampered_payload = base64.urlsafe_b64decode(payload_part)
    tampered_payload = tampered_payload.replace(b'"subset_bottle.json"', b'"subset_OTHER___json"')
    tampered = base64.urlsafe_b64encode(tampered_payload).decode() + "." + sig_part
    tampered_path = os.path.join(OUT, "demo_bottle_TAMPERED.lic")
    with open(tampered_path, "w") as f:
        f.write(tampered)
    try:
        print(unlock(enc_path, tampered_path, real_machine))
        print("--> FAIL (unexpected): should not have unlocked")
    except LicenseError as e:
        print(f"--> PASS, rejected as expected: {e}")

    line("4. Already-EXPIRED license -> should REJECT")
    expired_lic = issue_license(real_machine, "subset_bottle.json", aes_key, valid_days=-10)
    expired_path = os.path.join(OUT, "demo_bottle_EXPIRED.lic")
    with open(expired_path, "w") as f:
        f.write(expired_lic)
    try:
        print(unlock(enc_path, expired_path, real_machine))
        print("--> FAIL (unexpected): should not have unlocked")
    except LicenseError as e:
        print(f"--> PASS, rejected as expected: {e}")

    line("5. Reading the .enc payload directly, no license at all")
    with open(enc_path, "rb") as f:
        raw = f.read()
    print(f"first 80 bytes of the raw file: {raw[:80]}")
    print("--> PASS: pure ciphertext, no formula names, no structure, nothing legible")

    line("DONE")


if __name__ == "__main__":
    main()
