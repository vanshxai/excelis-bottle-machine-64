"""
OUR SIDE. Given a customer's machine fingerprint + which formula subset
they've paid for + how many days it should run, produces two files to
send them:

  out/<name>.enc   -- their formula subset, AES-encrypted (unreadable junk without the license)
  out/<name>.lic   -- the signed license text (this IS the "key" they type in / drop in place)

This is the only script that ever touches issuer_private.pem.
"""
import argparse
import json
import os

from crypto_core import encrypt_payload, issue_license, ensure_issuer_keypair

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, "out")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--machine-id", required=True, help="customer's machine fingerprint")
    ap.add_argument("--subset", required=True, help="path to a subsets/*.json formula file")
    ap.add_argument("--name", required=True, help="short name for the output files, e.g. 'excelis_bottle_001'")
    ap.add_argument("--days", type=int, default=150, help="validity window (default ~5 months)")
    args = ap.parse_args()

    ensure_issuer_keypair()
    os.makedirs(OUT_DIR, exist_ok=True)

    with open(args.subset, "rb") as f:
        plaintext = f.read()

    aes_key = os.urandom(32)  # fresh, random per-issued-license -- never reused
    blob = encrypt_payload(plaintext, aes_key)
    enc_path = os.path.join(OUT_DIR, f"{args.name}.enc")
    with open(enc_path, "wb") as f:
        f.write(blob)

    license_str = issue_license(args.machine_id, os.path.basename(args.subset), aes_key, args.days)
    lic_path = os.path.join(OUT_DIR, f"{args.name}.lic")
    with open(lic_path, "w") as f:
        f.write(license_str)

    print(f"issued -> {enc_path}")
    print(f"issued -> {lic_path}")
    print(f"locked to machine ...{args.machine_id[-12:]}, valid {args.days} days")


if __name__ == "__main__":
    main()
