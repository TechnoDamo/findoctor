"""Настройка структурированного логирования и отправки событий в Graylog."""

import json
import logging
import os
import socket
import sys
import time
from typing import Any

import structlog

from app.settings import settings


class GraylogProcessor:
    """structlog processor that sends event dictionaries as GELF messages."""

    _CHUNK_SIZE = 8192

    def __init__(
        self,
        host: str,
        port: int,
        facility: str,
        required: bool,
        protocol: str,
    ) -> None:
        self.host = host
        self.port = port
        self.facility = facility
        self.required = required
        self.protocol = protocol.lower()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if required:
            self._check_reachable()

    def _check_reachable(self) -> None:
        try:
            socket.getaddrinfo(self.host, self.port)
        except OSError:
            if self.required:
                raise

    def __call__(
        self,
        logger: Any,
        method_name: str,
        event_dict: dict[str, Any],
    ) -> dict[str, Any]:
        payload = self._build_payload(method_name, event_dict)
        try:
            if self.protocol == "tcp":
                self._send_tcp(payload)
            else:
                self._send_udp(payload)
        except OSError:
            if self.required:
                raise
        return event_dict

    def _build_payload(self, method_name: str, event_dict: dict[str, Any]) -> bytes:
        event_name = str(event_dict.get("event") or method_name)
        level = _syslog_level(method_name)
        extra = {
            f"_{key}": _json_safe(value)
            for key, value in event_dict.items()
            if key not in {"event", "timestamp", "level"}
        }
        message = {
            "version": "1.1",
            "host": socket.gethostname(),
            "short_message": event_name,
            "full_message": json.dumps(event_dict, default=str, ensure_ascii=False),
            "timestamp": time.time(),
            "level": level,
            "facility": self.facility,
            **extra,
        }
        return json.dumps(message, default=str, ensure_ascii=False).encode("utf-8")

    def _send_tcp(self, payload: bytes) -> None:
        with socket.create_connection((self.host, self.port), timeout=2) as sock:
            sock.sendall(payload + b"\0")

    def _send_udp(self, payload: bytes) -> None:
        if len(payload) <= self._CHUNK_SIZE:
            self.sock.sendto(payload, (self.host, self.port))
            return

        message_id = os.urandom(8)
        chunks = [
            payload[index : index + self._CHUNK_SIZE]
            for index in range(0, len(payload), self._CHUNK_SIZE)
        ]
        if len(chunks) > 128:
            raise OSError("GELF UDP message is too large to chunk")

        for sequence, chunk in enumerate(chunks):
            header = b"\x1e\x0f" + message_id + bytes([sequence, len(chunks)])
            self.sock.sendto(header + chunk, (self.host, self.port))


def _syslog_level(method_name: str) -> int:
    return {
        "critical": 2,
        "error": 3,
        "warning": 4,
        "warn": 4,
        "info": 6,
        "debug": 7,
    }.get(method_name, 6)


def _json_safe(value: Any) -> Any:
    try:
        json.dumps(value, default=str)
    except TypeError:
        return str(value)
    return value


def configure_logging() -> None:
    """Настраивает structlog и стандартный logging для всего приложения."""

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    if settings.graylog_enabled:
        shared_processors.append(
            GraylogProcessor(
                host=settings.graylog_host,
                port=settings.graylog_port,
                facility=settings.graylog_facility,
                required=settings.graylog_required,
                protocol=settings.graylog_protocol,
            )
        )

    if settings.app_env == "development":
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(),
        ]
    else:
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )
