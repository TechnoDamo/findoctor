#!/usr/bin/env python3
"""
RAGFlow admin CLI: API key and dataset management.

Reads config from environment (RAGFLOW_BASE_URL, RAGFLOW_ADMIN_EMAIL,
RAGFLOW_ADMIN_PASSWORD). Uses cookie-based auth (encrypted password).

Usage:
  python3 ragflow_admin.py key-create --name=...
  python3 ragflow_admin.py key-list
  python3 ragflow_admin.py key-delete --token=...
  python3 ragflow_admin.py ds-create --name=...
  python3 ragflow_admin.py ds-list
  python3 ragflow_admin.py ds-delete --id=...
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def encrypt_password(password: str) -> str:
    r = subprocess.run(
        ["bash", os.path.join(SCRIPT_DIR, "encrypt_password.sh"), password],
        capture_output=True, text=True, cwd=SCRIPT_DIR,
    )
    if r.returncode != 0:
        sys.exit(f"Failed to encrypt password: {r.stderr}")
    return r.stdout.strip()


def login(base_url: str, email: str, password: str) -> str:
    """Login via cookie-based auth. Returns the session cookie value."""
    enc = encrypt_password(password)
    data = json.dumps({"email": email, "password": enc}).encode()
    req = urllib.request.Request(
        f"{base_url}/api/v1/auth/login",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req, timeout=10)
    cookies = resp.headers.get_all("Set-Cookie")
    if not cookies:
        sys.exit("Login failed: no cookie returned")
    # Extract the session cookie (first cookie, key=value)
    session_cookie = cookies[0].split(";")[0].strip()
    return session_cookie


def api_get(base_url: str, cookie: str, path: str) -> dict:
    req = urllib.request.Request(
        f"{base_url}{path}",
        headers={"Cookie": cookie},
    )
    resp = json.load(urllib.request.urlopen(req, timeout=10))
    if resp.get("code") != 0:
        sys.exit(f"API error: {resp.get('message', '?')}")
    return resp


def api_post(base_url: str, cookie: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        f"{base_url}{path}",
        data=data,
        headers={"Cookie": cookie, "Content-Type": "application/json"},
        method="POST",
    )
    resp = json.load(urllib.request.urlopen(req, timeout=10))
    if resp.get("code") != 0:
        sys.exit(f"API error: {resp.get('message', '?')}")
    return resp


def api_delete(base_url: str, cookie: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        f"{base_url}{path}",
        data=data,
        headers={"Cookie": cookie, "Content-Type": "application/json"},
        method="DELETE",
    )
    resp = json.load(urllib.request.urlopen(req, timeout=10))
    if resp.get("code") != 0:
        sys.exit(f"API error: {resp.get('message', '?')}")
    return resp


def update_env(key: str, value: str) -> None:
    env_path = os.path.join(SCRIPT_DIR, "..", ".env")
    with open(env_path) as f:
        content = f.read()
    import re
    if re.search(rf"^{key}=.*", content, re.MULTILINE):
        content = re.sub(rf"^{key}=.*", f"{key}={value}", content, flags=re.MULTILINE)
    else:
        content = content.rstrip() + f"\n{key}={value}\n"
    with open(env_path, "w") as f:
        f.write(content)


# -- Commands -----------------------------------------------------------

def cmd_key_create(args: argparse.Namespace) -> None:
    base = os.environ["RAGFLOW_BASE_URL"]
    cookie = login(base, os.environ["RAGFLOW_ADMIN_EMAIL"], os.environ["RAGFLOW_ADMIN_PASSWORD"])
    resp = api_post(base, cookie, f"/api/v1/system/tokens?name={args.name}")
    token = resp["data"].get("token") or resp["data"].get("access_token")
    if not token:
        sys.exit("Could not extract token from response")
    print(f"API-ключ создан: {token}")
    update_env("RAGFLOW_API_KEY", token)
    print(f"Записан в .env как RAGFLOW_API_KEY.")


def cmd_key_list(args: argparse.Namespace) -> None:
    base = os.environ["RAGFLOW_BASE_URL"]
    cookie = login(base, os.environ["RAGFLOW_ADMIN_EMAIL"], os.environ["RAGFLOW_ADMIN_PASSWORD"])
    resp = api_get(base, cookie, "/api/v1/system/tokens")
    print(json.dumps(resp.get("data", []), indent=2, ensure_ascii=False))


def cmd_key_delete(args: argparse.Namespace) -> None:
    base = os.environ["RAGFLOW_BASE_URL"]
    cookie = login(base, os.environ["RAGFLOW_ADMIN_EMAIL"], os.environ["RAGFLOW_ADMIN_PASSWORD"])
    api_delete(base, cookie, f"/api/v1/system/tokens/{args.token}")
    print(f"Ключ {args.token} удалён.")


def cmd_ds_create(args: argparse.Namespace) -> None:
    base = os.environ["RAGFLOW_BASE_URL"]
    cookie = login(base, os.environ["RAGFLOW_ADMIN_EMAIL"], os.environ["RAGFLOW_ADMIN_PASSWORD"])
    resp = api_post(base, cookie, "/api/v1/datasets", {
        "name": args.name,
        "description": "FinDoctor recommendation knowledge base",
    })
    ds_id = resp["data"]["id"]
    print(f"Датасет создан: {ds_id}")
    update_env("RAGFLOW_DATASET_ID", ds_id)
    print(f"Записан в .env как RAGFLOW_DATASET_ID.")


def cmd_ds_list(args: argparse.Namespace) -> None:
    base = os.environ["RAGFLOW_BASE_URL"]
    cookie = login(base, os.environ["RAGFLOW_ADMIN_EMAIL"], os.environ["RAGFLOW_ADMIN_PASSWORD"])
    resp = api_get(base, cookie, "/api/v1/datasets?page=1&page_size=50")
    print(json.dumps(resp.get("data", []), indent=2, ensure_ascii=False))


def cmd_ds_delete(args: argparse.Namespace) -> None:
    base = os.environ["RAGFLOW_BASE_URL"]
    cookie = login(base, os.environ["RAGFLOW_ADMIN_EMAIL"], os.environ["RAGFLOW_ADMIN_PASSWORD"])
    resp = api_delete(base, cookie, "/api/v1/datasets", {"ids": [args.id]})
    print(f"Датасет {args.id} удалён.")


def main() -> None:
    parser = argparse.ArgumentParser(description="RAGFlow admin CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("key-create")
    p.add_argument("--name", default="findoctor-backend")
    p.set_defaults(func=cmd_key_create)

    p = sub.add_parser("key-list")
    p.set_defaults(func=cmd_key_list)

    p = sub.add_parser("key-delete")
    p.add_argument("--token", required=True)
    p.set_defaults(func=cmd_key_delete)

    p = sub.add_parser("ds-create")
    p.add_argument("--name", default="findoctor-recommendations")
    p.set_defaults(func=cmd_ds_create)

    p = sub.add_parser("ds-list")
    p.set_defaults(func=cmd_ds_list)

    p = sub.add_parser("ds-delete")
    p.add_argument("--id", required=True)
    p.set_defaults(func=cmd_ds_delete)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
