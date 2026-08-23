"""Polite HTTP access to PhilEvents.

PhilPapers' terms severely restrict redistribution of their data and invite
developers to make contact before building on it. We are a private,
personal-use client: we identify ourselves, we rate-limit, and we store
references and derived scores rather than mirroring their corpus.
"""
from __future__ import annotations

import time

import requests

from .errors import FetchError


class PoliteSession:
    """A requests session with a fixed inter-request delay and bounded retries."""

    def __init__(self, user_agent: str, delay_seconds: float = 0.5,
                 timeout: int = 30, max_retries: int = 3):
        self.delay = delay_seconds
        self.timeout = timeout
        self.max_retries = max_retries
        self._last_request_at = 0.0
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": user_agent})

    def _wait_turn(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)

    def get(self, url: str) -> str:
        """Fetch a URL, returning its text. Raises FetchError once retries are spent."""
        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            self._wait_turn()
            try:
                response = self._session.get(url, timeout=self.timeout)
                self._last_request_at = time.monotonic()
                response.raise_for_status()
                return response.text
            except Exception as exc:  # noqa: BLE001 - re-raised as FetchError below
                self._last_request_at = time.monotonic()
                last_error = exc
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
        raise FetchError(f"GET {url} failed after {self.max_retries} attempts: {last_error}")
