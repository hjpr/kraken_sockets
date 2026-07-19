"""
Interactive setup for Kraken API credentials.

Run from the project root:

    python setup_env.py

Prompts for your Kraken REST API key pair and writes them to a .env file in the
project root, which kraken_sockets loads for authentication to private websocket
channels and trading endpoints. Optionally validates the credentials against the
Kraken API before finishing. Existing unrelated entries in .env are preserved.

Create an API key at https://pro.kraken.com/app/settings/api — it needs the
"WebSocket interface" permission, plus "Create & modify orders" / "Cancel & close
orders" if you intend to trade.
"""

import base64
import binascii
import getpass
import hashlib
import hmac
import os
import sys
import time
import urllib.parse

import requests

ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
KEY_NAME = "KRAKEN_REST_API_KEY"
SECRET_NAME = "KRAKEN_REST_API_PRIVATE_KEY"


def mask(value: str) -> str:
    """Shows just enough of a stored secret to recognize it."""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def read_env(path: str) -> list[str]:
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return f.read().splitlines()


def upsert(lines: list[str], name: str, value: str) -> list[str]:
    """Replaces the named entry in place, or appends it, preserving all other lines."""
    entry = f'{name}="{value}"'
    replaced = False
    updated = []
    for line in lines:
        if line.strip().replace(" ", "").startswith(f"{name}="):
            if not replaced:
                updated.append(entry)
                replaced = True
        else:
            updated.append(line)
    if not replaced:
        updated.append(entry)
    return updated


def current_value(lines: list[str], name: str) -> str:
    for line in lines:
        stripped = line.strip().replace(" ", "")
        if stripped.startswith(f"{name}="):
            return stripped.split("=", 1)[1].strip('"').strip("'")
    return ""


def validate_credentials(key: str, secret: str) -> tuple[bool, str]:
    """
    Requests a websocket token from the Kraken REST API to confirm the key pair
    works. Mirrors the signing logic in kraken_sockets.api.KrakenAuth.
    """
    urlpath = "/0/private/GetWebSocketsToken"
    nonce = str(int(time.time() * 1000))
    data = {"nonce": nonce}
    postdata = urllib.parse.urlencode(data)
    encoded = (nonce + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()
    try:
        mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    except (binascii.Error, ValueError):
        return False, "Private key is not valid base64 — copy it exactly as shown by Kraken."
    headers = {
        "API-Key": key,
        "API-Sign": base64.b64encode(mac.digest()).decode(),
    }
    try:
        res = requests.post(f"https://api.kraken.com{urlpath}", headers=headers, data=data, timeout=10)
        res.raise_for_status()
        body = res.json()
    except requests.exceptions.RequestException as e:
        return False, f"Could not reach the Kraken API: {e}"
    if body.get("error"):
        return False, f"Kraken rejected the credentials: {body['error']}"
    if body.get("result", {}).get("token"):
        return True, "Credentials accepted — websocket token issued."
    return False, f"Unexpected response from Kraken: {body}"


def main() -> int:
    print("kraken-sockets credential setup")
    print("--------------------------------")
    print("Keys are written to .env in the project root (gitignored).")
    print("Create keys at https://pro.kraken.com/app/settings/api with the")
    print('"WebSocket interface" permission (plus order permissions to trade).\n')

    lines = read_env(ENV_PATH)
    existing_key = current_value(lines, KEY_NAME)
    if existing_key:
        print(f"A key is already configured: {mask(existing_key)}")
        answer = input("Replace it? [y/N]: ").strip().lower()
        if answer not in ("y", "yes"):
            print("Keeping existing credentials. Nothing changed.")
            return 0
        print()

    api_key = input("Kraken API key: ").strip().strip('"').strip("'")
    if not api_key:
        print("No API key entered. Nothing changed.")
        return 1
    private_key = getpass.getpass("Kraken private key (input hidden): ").strip().strip('"').strip("'")
    if not private_key:
        print("No private key entered. Nothing changed.")
        return 1

    lines = upsert(lines, KEY_NAME, api_key)
    lines = upsert(lines, SECRET_NAME, private_key)
    with open(ENV_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")
    os.chmod(ENV_PATH, 0o600)
    print(f"\nWrote credentials to {ENV_PATH} (permissions set to owner-only).")

    answer = input("Validate credentials against the Kraken API now? [Y/n]: ").strip().lower()
    if answer in ("", "y", "yes"):
        ok, detail = validate_credentials(api_key, private_key)
        print(("OK: " if ok else "FAILED: ") + detail)
        if not ok:
            print("Credentials were saved anyway — rerun this script to correct them.")
            return 1
    print("Setup complete. Private channels and trading endpoints are ready to use.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyboardInterrupt, EOFError):
        print("\nAborted. Nothing changed." if not os.path.exists(ENV_PATH) else "\nAborted.")
        sys.exit(130)
