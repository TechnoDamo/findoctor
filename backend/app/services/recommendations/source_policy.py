"""Allowed-source policy for recommendation search and ingestion."""

from pathlib import Path
from urllib.parse import urlparse


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def resolve_allowed_resources_path(configured_path: str) -> Path:
    """Resolve a configured allowlist path from common runtime locations."""

    path = Path(configured_path).expanduser()
    if path.is_absolute():
        return path

    candidates = [
        Path.cwd() / path,
        Path.cwd().parent / path,
        _repo_root() / path,
        _repo_root() / "backend" / path,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def normalize_host(value: str) -> str | None:
    """Normalize a URL or hostname into a bare lowercase host."""

    raw = value.strip()
    if not raw:
        return None
    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    host = (parsed.netloc or parsed.path).split("/", 1)[0].lower()
    if host.startswith("www."):
        host = host[4:]
    return host or None


def load_allowed_hosts(configured_path: str) -> set[str]:
    """Read allowed URLs/domains from a txt file."""

    path = resolve_allowed_resources_path(configured_path)
    if not path.exists():
        return set()

    hosts: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        host = normalize_host(line)
        if host:
            hosts.add(host)
    return hosts


def is_allowed_url(url: str, allowed_hosts: set[str]) -> bool:
    """Return true when a URL belongs to one of the allowed hosts."""

    host = normalize_host(url)
    if not host:
        return False
    return any(host == allowed or host.endswith(f".{allowed}") for allowed in allowed_hosts)


def constrain_search_query(query: str, allowed_hosts: set[str]) -> str:
    """Add a broad allowed-domain filter when the planner did not provide one."""

    cleaned = query.strip()
    if "site:" in cleaned.lower() or not allowed_hosts:
        return cleaned
    site_clause = " OR ".join(f"site:{host}" for host in sorted(allowed_hosts))
    return f"({site_clause}) {cleaned}"

