"""
Generic API client: retries, timeouts, and disk-based response caching.
Every specific client (fpl_client.py, api_football_client.py,
football_data_org_client.py) builds on this rather than calling `requests`
directly, so caching/retry behavior is consistent and only lives in one
place.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import requests

from config.settings import API_CACHE_DIR


class ApiClientError(Exception):
    pass


def _cache_path(cache_key: str) -> Path:
    digest = hashlib.sha256(cache_key.encode()).hexdigest()[:24]
    return API_CACHE_DIR / f"{digest}.json"


def _read_cache(cache_key: str, ttl_seconds: int) -> dict | None:
    path = _cache_path(cache_key)
    if not path.exists():
        return None
    if time.time() - path.stat().st_mtime > ttl_seconds:
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _write_cache(cache_key: str, data: dict) -> None:
    try:
        API_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _cache_path(cache_key).write_text(json.dumps(data))
    except OSError:
        pass  # caching is an optimization, never a hard requirement — never let a disk error break a live call


def is_cached(cache_key: str, ttl_seconds: int) -> bool:
    """Public helper: true if a fresh cached response exists for this key, without
    reading/parsing it. Lets a self-throttled client (e.g. api_football_client.py)
    check quota-safety before deciding whether a call will hit the network."""
    return _read_cache(cache_key, ttl_seconds) is not None


def get_json(
    url: str,
    params: dict | None = None,
    headers: dict | None = None,
    timeout: int = 10,
    cache_key: str | None = None,
    cache_ttl_seconds: int = 300,
    max_retries: int = 2,
) -> dict:
    """
    GET a URL, parse JSON, cache the result to disk. If cache_key is given
    and a fresh cached response exists, returns it without a network call
    at all — this is what keeps polling-heavy jobs (data/live_updater.py)
    from hammering free APIs.
    """
    if cache_key:
        cached = _read_cache(cache_key, cache_ttl_seconds)
        if cached is not None:
            return cached

    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            if cache_key:
                _write_cache(cache_key, data)
            return data
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt < max_retries:
                time.sleep(0.5 * (attempt + 1))  # small linear backoff — free APIs don't need anything fancier
    raise ApiClientError(f"GET {url} failed after {max_retries + 1} attempts: {last_error}") from last_error
