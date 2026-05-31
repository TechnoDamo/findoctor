#!/usr/bin/env python3
"""
One-shot RAGFlow setup: admin, API key, dataset, models.
Idempotent — skips steps that are already done.
Reads configuration from ../.env, writes results back.
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(SCRIPT_DIR, "..", ".env")


# -- helpers -------------------------------------------------------------

def load_env():
    env = {}
    if not os.path.isfile(ENV_FILE):
        return env
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def save_env(env):
    with open(ENV_FILE) as f:
        content = f.read()
    for key, value in env.items():
        if re.search(rf"^{key}=.*", content, re.MULTILINE):
            content = re.sub(rf"^{key}=.*", f"{key}={value}", content, flags=re.MULTILINE)
        else:
            content = content.rstrip() + f"\n{key}={value}\n"
    with open(ENV_FILE, "w") as f:
        f.write(content)


def encrypt_password(password: str) -> str:
    r = subprocess.run(
        ["bash", os.path.join(SCRIPT_DIR, "encrypt_password.sh"), password],
        capture_output=True, text=True, cwd=SCRIPT_DIR,
    )
    if r.returncode != 0:
        sys.exit(f"Failed to encrypt password: {r.stderr}")
    return r.stdout.strip()


def api_call(method, url, cookie=None, body=None, timeout=30):
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    if cookie:
        headers["Cookie"] = cookie
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.load(resp)
    except urllib.error.HTTPError as e:
        body_bytes = e.read()
        return json.loads(body_bytes)


# -- main ----------------------------------------------------------------

def main():
    env = load_env()

    base = env.get("RAGFLOW_BASE_URL", "http://localhost:9380")
    email = env.get("RAGFLOW_ADMIN_EMAIL", "admin@mail.ru")
    password = env.get("RAGFLOW_ADMIN_PASSWORD", "admin")
    embd_api_key = env.get("EMBEDDING_API_KEY", "")
    llm_api_key = env.get("LLM_API_KEY", embd_api_key)
    embd_base_url = env.get("EMBEDDING_BASE_URL", "https://routerai.ru/api/v1")
    llm_base_url = env.get("LLM_BASE_URL", embd_base_url)
    ds_name = env.get("RAGFLOW_DATASET_NAME", "findoctor-recommendations")
    key_name = "findoctor-backend"

    print(f"RAGFlow setup — {base}")
    print(f"Admin: {email}")
    print()

    # 1. Wait for RAGFlow
    print("[1/6] Waiting for RAGFlow...")
    for i in range(30):
        try:
            resp = urllib.request.urlopen(f"{base}/api/v1/", timeout=2)
            print("  OK: RAGFlow is reachable")
            break
        except urllib.error.HTTPError as e:
            # Any HTTP response means server is up (even 404)
            print("  OK: RAGFlow is reachable")
            break
        except Exception:
            if i % 5 == 0 and i > 0:
                print(f"  ... still waiting ({i * 2}s)")
            time.sleep(2)
    else:
        print("  FAIL: RAGFlow did not become reachable after 60s")
        sys.exit(1)

    # 2. Login / register admin
    print("[2/6] Admin login...")
    enc_pwd = encrypt_password(password)
    login_url = f"{base}/api/v1/auth/login"
    login_body = {"email": email, "password": enc_pwd}

    try:
        req = urllib.request.Request(login_url, data=json.dumps(login_body).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        resp = json.load(urllib.request.urlopen(req, timeout=10))
    except Exception as e:
        print(f"  ERROR: Cannot reach login endpoint: {e}")
        sys.exit(1)

    cookie = None
    if resp.get("code") == 0:
        print("  OK: logged in")
        req2 = urllib.request.Request(login_url, data=json.dumps(login_body).encode(),
                                      headers={"Content-Type": "application/json"}, method="POST")
        resp2 = urllib.request.urlopen(req2, timeout=10)
        cookies = resp2.headers.get_all("Set-Cookie")
        if cookies:
            cookie = cookies[0].split(";")[0].strip()
    elif resp.get("code") == 109:
        print("  Admin not registered — creating...")
        register_url = f"{base}/api/v1/users"
        register_body = {"nickname": "Admin", "email": email, "password": enc_pwd}
        reg_resp = api_call("POST", register_url, body=register_body)
        if reg_resp.get("code") != 0:
            print(f"  FAIL: Registration failed: {reg_resp.get('message', '?')}")
            sys.exit(1)
        print("  OK: admin registered")
        # Login now
        req2 = urllib.request.Request(login_url, data=json.dumps(login_body).encode(),
                                      headers={"Content-Type": "application/json"}, method="POST")
        resp2 = urllib.request.urlopen(req2, timeout=10)
        cookies = resp2.headers.get_all("Set-Cookie")
        if cookies:
            cookie = cookies[0].split(";")[0].strip()
    else:
        print(f"  FAIL: Login error: {resp.get('message', '?')}")
        sys.exit(1)

    if not cookie:
        print("  FAIL: Could not obtain session cookie")
        sys.exit(1)

    # 3. Create API key (if not set)
    api_key = env.get("RAGFLOW_API_KEY", "")
    if api_key:
        print(f"[3/6] API key: already set ({api_key[:20]}...)")
    else:
        print(f"[3/6] Creating API key '{key_name}'...")
        resp = api_call("POST", f"{base}/api/v1/system/tokens?name={key_name}", cookie=cookie)
        if resp.get("code") != 0:
            print(f"  FAIL: {resp.get('message', '?')}")
            sys.exit(1)
        api_key = resp["data"].get("token") or resp["data"].get("access_token")
        if not api_key:
            print("  FAIL: Could not extract token from response")
            sys.exit(1)
        env["RAGFLOW_API_KEY"] = api_key
        save_env({"RAGFLOW_API_KEY": api_key})
        print(f"  OK: {api_key}")

    # 4. Create dataset (if not set)
    ds_id = env.get("RAGFLOW_DATASET_ID", "")
    if ds_id:
        print(f"[4/6] Dataset: already set ({ds_id})")
    else:
        print(f"[4/6] Creating dataset '{ds_name}'...")
        resp = api_call("POST", f"{base}/api/v1/datasets", cookie=cookie,
                        body={"name": ds_name, "description": "FinDoctor recommendation knowledge base"})
        if resp.get("code") != 0:
            print(f"  FAIL: {resp.get('message', '?')}")
            sys.exit(1)
        ds_id = resp["data"]["id"]
        env["RAGFLOW_DATASET_ID"] = ds_id
        save_env({"RAGFLOW_DATASET_ID": ds_id})
        print(f"  OK: {ds_id}")

    # 5. Configure models via API
    print("[5/6] Configuring models (this tests API connectivity, ~60s)...")

    # 5a. Add embedding model
    embd_name = env.get("EMBEDDING_MODEL", "qwen/qwen3-embedding-8b")
    embd_full = f"{embd_name}___OpenAI-API@OpenAI-API-Compatible"

    print(f"  Adding embedding model: {embd_name}")
    resp = api_call("POST", f"{base}/v1/llm/add_llm", cookie=cookie, body={
        "llm_factory": "OpenAI-API-Compatible",
        "llm_name": embd_name,
        "model_type": "embedding",
        "api_key": embd_api_key,
        "api_base": embd_base_url,
        "max_tokens": 8192,
    }, timeout=90)
    if resp.get("code") != 0:
        # Might already exist — try set_api_key instead
        print(f"  Retry via set_api_key...")
        resp = api_call("POST", f"{base}/v1/llm/set_api_key", cookie=cookie, body={
            "llm_factory": "OpenAI-API-Compatible",
            "api_key": embd_api_key,
            "base_url": embd_base_url,
        }, timeout=60)
        if resp.get("code") == 102 and "No models configured" in resp.get("message", ""):
            print("  WARNING: No source models for OpenAI-API-Compatible. add_llm should have worked.")
        elif resp.get("code") != 0:
            print(f"  WARNING: {resp.get('message', '?')}")
    else:
        print(f"  OK: embedding model configured")

    # 5b. Add chat model
    chat_name = env.get("LLM_MODEL", "google/gemini-2.5-flash")
    print(f"  Adding chat model: {chat_name}")
    resp = api_call("POST", f"{base}/v1/llm/add_llm", cookie=cookie, body={
        "llm_factory": "OpenAI-API-Compatible",
        "llm_name": chat_name,
        "model_type": "chat",
        "api_key": llm_api_key,
        "api_base": llm_base_url,
        "max_tokens": 8192,
    }, timeout=90)
    if resp.get("code") != 0:
        print(f"  WARNING: Chat model add returned: {resp.get('message', '?')}")
    else:
        print(f"  OK: chat model configured")

    # 6. Set dataset embedding model
    print(f"[6/6] Setting dataset embedding model...")
    resp = api_call("PUT", f"{base}/api/v1/datasets/{ds_id}", cookie=cookie,
                    body={"embedding_model": embd_full}, timeout=30)
    if resp.get("code") != 0:
        print(f"  WARNING: {resp.get('message', '?')}")
    else:
        embd_set = resp.get("data", {}).get("embedding_model", "")
        print(f"  OK: embedding_model = {embd_set}")

    print()
    print("=" * 60)
    print("RAGFlow setup complete!")
    print(f"  URL:      {base}")
    print(f"  Admin:    {email}")
    print(f"  API key:  {api_key}")
    print(f"  Dataset:  {ds_id}  ({ds_name})")
    print(f"  Embedding: {embd_name}  (RouterAI)")
    print(f"  LLM:      {chat_name}  (RouterAI)")
    print("=" * 60)
    print()
    print("Next: make load-test-docs    (optional — load test documents)")
    print("      make test               (verify retrieval works)")


if __name__ == "__main__":
    main()
