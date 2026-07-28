"""
Thin client around the official, public Fantasy Premier League API.

No API key is required. Endpoints used:
  - /bootstrap-static/  -> players, teams, positions, gameweeks (the "big" payload)
  - /fixtures/           -> full season fixture list with difficulty ratings
  - /element-summary/{id}/ -> per-player history and upcoming fixtures

Responses are cached in-memory with a TTL (see config.FPL_CACHE_TTL) since
the upstream data only changes a few times a day and caching keeps the app
fast and avoids being rate-limited.
"""

import time
import threading

import requests

BASE_URL = "https://fantasy.premierleague.com/api"
REQUEST_TIMEOUT = 10

_cache = {}
_cache_lock = threading.Lock()


class FPLApiError(Exception):
    """Raised when the upstream FPL API cannot be reached or errors out."""


def _cached_get(url: str, ttl: int):
    with _cache_lock:
        entry = _cache.get(url)
        if entry and (time.time() - entry["ts"]) < ttl:
            return entry["data"]

    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT, headers={
            "User-Agent": "FPL-Assistant/1.0 (educational project)"
        })
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        # Serve stale cache if we have it rather than failing outright
        with _cache_lock:
            entry = _cache.get(url)
        if entry:
            return entry["data"]
        raise FPLApiError(f"Could not reach FPL API: {exc}") from exc

    with _cache_lock:
        _cache[url] = {"data": data, "ts": time.time()}
    return data


def get_bootstrap(ttl: int = 300):
    """Players, teams, positions ('element_types'), and gameweek ('events') data."""
    return _cached_get(f"{BASE_URL}/bootstrap-static/", ttl)


def get_fixtures(ttl: int = 300):
    """Full season fixture list, including FDR (difficulty 1-5)."""
    return _cached_get(f"{BASE_URL}/fixtures/", ttl)


def get_element_summary(player_id: int, ttl: int = 300):
    """A single player's per-gameweek history plus upcoming fixtures."""
    return _cached_get(f"{BASE_URL}/element-summary/{player_id}/", ttl)


def clear_cache():
    with _cache_lock:
        _cache.clear()
