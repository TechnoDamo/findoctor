#!/usr/bin/env python3
"""List documents from the configured dataset with indexing status."""

import json
import os
import sys
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(SCRIPT_DIR, "..", ".env")

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

env = load_env()
base = env.get("RAGFLOW_BASE_URL", "")
api_key = env.get("RAGFLOW_API_KEY", "")
ds_id = env.get("RAGFLOW_DATASET_ID", "")

if not all([base, api_key, ds_id]):
    print("ERROR: RAGFLOW_BASE_URL, RAGFLOW_API_KEY, or RAGFLOW_DATASET_ID not set in .env")
    sys.exit(1)

url = f"{base}/api/v1/datasets/{ds_id}/documents?page=1&page_size=200"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})

try:
    resp = json.load(urllib.request.urlopen(req, timeout=10))
except Exception as e:
    print(f"ERROR: Failed to fetch documents: {e}")
    sys.exit(1)

if resp.get("code") != 0:
    print(f"API error: {resp.get('message', '?')}")
    sys.exit(1)

docs = resp.get("data", {}).get("docs", [])
if not docs:
    print(f"No documents found in dataset {ds_id}")
    sys.exit(0)

status_icons = {
    "DONE":    "DONE",
    "RUNNING": "RUN ",
    "UNSTART": "WAIT",
    "FAIL":    "FAIL",
    "CANCEL":  "CANC",
}

status_colors = {
    "DONE":    "\033[32m",
    "RUNNING": "\033[33m",
    "FAIL":    "\033[31m",
}

done_count = sum(1 for d in docs if d.get("run") == "DONE")
fail_count = sum(1 for d in docs if d.get("run") == "FAIL")
running_count = sum(1 for d in docs if d.get("run") not in ("DONE", "FAIL"))

reset = "\033[0m"

print(f"\nDataset: {ds_id}  |  Total: {len(docs)}  |  Done: {done_count}  |  Running: {running_count}  |  Failed: {fail_count}")
print("-" * 90)
print(f"{'Status':<12s} {'Chunks':>6s} {'Tokens':>7s} {'Progress':>7s} {'Name'}")
print("-" * 90)

for doc in docs:
    run = doc.get("run", "?")
    icon = status_icons.get(run, run)
    color = status_colors.get(run, "")
    name = doc.get("name", "?")
    chunks = doc.get("chunk_count", 0) or 0
    tokens = doc.get("token_count", 0) or 0
    progress = (doc.get("progress", 0) or 0) * 100

    status_str = f"{color}{icon:<12s}{reset}" if color else f"{icon:<12s}"
    print(f"{status_str} {chunks:>6d} {tokens:>7d} {progress:>6.0f}%  {name}")
