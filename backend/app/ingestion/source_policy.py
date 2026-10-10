from __future__ import annotations

import time
import urllib.error
import urllib.request
from collections.abc import Callable
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser


def _http_fetch(url: str) -> bytes:
    class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, request, response, code, message, headers, new_url):
            return None

    request = urllib.request.Request(url, headers={"User-Agent": "MPJobSaathi/1.0 (notification ingestion)"})
    opener = urllib.request.build_opener(NoRedirectHandler)
    with opener.open(request, timeout=30) as response:
        return response.read()


def _http_robots(url: str) -> str | None:
    try:
        return _http_fetch(url).decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError):
        return None


class SourcePolicy:
    def __init__(
        self,
        allowlist: set[str] | None = None,
        min_delay_seconds: float = 2.0,
        robots_fetcher: Callable[[str], str | None] = _http_robots,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.allowlist = allowlist if allowlist is not None else {"esb.mp.gov.in", "mppsc.mp.gov.in"}
        self.min_delay_seconds = min_delay_seconds
        self.robots_fetcher = robots_fetcher
        self.clock = clock
        self.sleeper = sleeper
        self.last_fetch: dict[str, float] = {}
        self.robots_cache: dict[str, RobotFileParser | None] = {}

    def check(self, url: str) -> str:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or host not in self.allowlist:
            raise PermissionError(f"Source URL is not allowlisted for HTTPS fetch: {url}")

        if host not in self.robots_cache:
            robots_url = f"https://{host}/robots.txt"
            text = self.robots_fetcher(robots_url)
            if text is None:
                self.robots_cache[host] = None
            else:
                parser = RobotFileParser(robots_url)
                parser.parse(text.splitlines())
                self.robots_cache[host] = parser
        parser = self.robots_cache[host]
        if parser is None or not parser.can_fetch("MPJobSaathi", url):
            raise PermissionError(f"robots.txt does not permit or could not verify fetch: {url}")
        return host

    def fetch(self, url: str, fetcher: Callable[[str], bytes] = _http_fetch) -> bytes:
        host = self.check(url)
        now = self.clock()
        remaining = self.min_delay_seconds - (now - self.last_fetch.get(host, float("-inf")))
        if remaining > 0:
            self.sleeper(remaining)
        content = fetcher(url)
        self.last_fetch[host] = self.clock()
        return content