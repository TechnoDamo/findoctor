#!/usr/bin/env python3
"""Create FinDoctor Graylog streams and stream rules."""

from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any


API_URL = os.environ.get("GRAYLOG_API_URL", "http://localhost:19001").rstrip("/")
USERNAME = os.environ.get("GRAYLOG_ROOT_USERNAME", "admin")
PASSWORD = os.environ.get("GRAYLOG_ROOT_PASSWORD", "admin")
FACILITY = os.environ.get("GRAYLOG_FACILITY", "findoctor-backend")

EXACT = 1
REGEX = 2


def main() -> None:
    default_index_set_id = get_default_index_set_id()

    backend_stream = ensure_stream(
        title="FinDoctor Backend",
        description="All FinDoctor backend logs.",
        matching_type="AND",
        index_set_id=default_index_set_id,
    )
    ensure_rule(backend_stream, "facility", EXACT, FACILITY, "FinDoctor facility")
    resume_stream(backend_stream)

    http_stream = ensure_stream(
        title="FinDoctor HTTP Traffic",
        description="Full HTTP request and response logs for FinDoctor.",
        matching_type="AND",
        index_set_id=default_index_set_id,
    )
    remove_rules_for_field(http_stream, "event")
    ensure_rule(http_stream, "facility", EXACT, FACILITY, "FinDoctor facility")
    ensure_rule(http_stream, "message", REGEX, r"^http_", "HTTP request/response events")
    resume_stream(http_stream)

    db_stream = ensure_stream(
        title="FinDoctor DB Writes",
        description="Database write audit events for FinDoctor.",
        matching_type="AND",
        index_set_id=default_index_set_id,
    )
    remove_rules_for_field(db_stream, "event")
    ensure_rule(db_stream, "facility", EXACT, FACILITY, "FinDoctor facility")
    ensure_rule(db_stream, "message", EXACT, "db_write", "DB write events")
    resume_stream(db_stream)

    print("FinDoctor Graylog streams are configured")


def get_default_index_set_id() -> str:
    data = request_json("GET", "/api/system/indices/index_sets")
    for item in data.get("index_sets", []):
        if item.get("default"):
            return item["id"]
    raise RuntimeError("Graylog has no default index set")


def ensure_stream(
    *,
    title: str,
    description: str,
    matching_type: str,
    index_set_id: str,
) -> str:
    existing = find_stream(title)
    if existing:
        return existing["id"]

    data = request_json(
        "POST",
        "/api/streams",
        {
            "title": title,
            "description": description,
            "matching_type": matching_type,
            "remove_matches_from_default_stream": False,
            "index_set_id": index_set_id,
        },
    )
    return data["stream_id"]


def find_stream(title: str) -> dict[str, Any] | None:
    data = request_json("GET", "/api/streams")
    for stream in data.get("streams", []):
        if stream.get("title") == title:
            return stream
    return None


def ensure_rule(
    stream_id: str,
    field: str,
    rule_type: int,
    value: str,
    description: str,
) -> None:
    existing = request_json("GET", f"/api/streams/{stream_id}/rules")
    for rule in existing.get("stream_rules", []):
        if (
            rule.get("field") == field
            and rule.get("type") == rule_type
            and rule.get("value") == value
            and not rule.get("inverted", False)
        ):
            return

    request_json(
        "POST",
        f"/api/streams/{stream_id}/rules",
        {
            "field": field,
            "type": rule_type,
            "value": value,
            "inverted": False,
            "description": description,
        },
    )


def remove_rules_for_field(stream_id: str, field: str) -> None:
    existing = request_json("GET", f"/api/streams/{stream_id}/rules")
    for rule in existing.get("stream_rules", []):
        if rule.get("field") == field:
            request("DELETE", f"/api/streams/{stream_id}/rules/{rule['id']}")


def resume_stream(stream_id: str) -> None:
    request("POST", f"/api/streams/{stream_id}/resume")


def request_json(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = request(method, path, payload)
    if not body:
        return {}
    return json.loads(body)


def request(method: str, path: str, payload: dict[str, Any] | None = None) -> str:
    data = None
    headers = {
        "Accept": "application/json",
        "X-Requested-By": "findoctor",
        "Authorization": "Basic " + base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode(),
    }
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(API_URL + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return response.read().decode()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        print(f"{method} {path} failed: HTTP {exc.code}: {body}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
