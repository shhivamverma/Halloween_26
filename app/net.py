"""Network client with strict offline / local-only security guard."""

from urllib.parse import urlparse
import httpx


def is_local_host(host: str | None) -> bool:
    """Return True if host is localhost or 127.0.0.1."""
    if not host:
        return True
    return host in ("127.0.0.1", "localhost")


def assert_local_url(url: str) -> None:
    """Validate that the given URL points only to localhost or 127.0.0.1."""
    parsed = urlparse(url)
    host = parsed.hostname
    if host and not is_local_host(host):
        raise ValueError(f"Non-local host is forbidden: {host}")


class SafeLocalClient(httpx.Client):
    """HTTP client that blocks any request to a non-local host."""

    def __init__(self, *args, **kwargs):
        base_url = kwargs.get("base_url")
        if base_url:
            assert_local_url(str(base_url))
        super().__init__(*args, **kwargs)

    def send(self, request: httpx.Request, *args, **kwargs) -> httpx.Response:
        assert_local_url(str(request.url))
        return super().send(request, *args, **kwargs)


def local_client(*args, **kwargs) -> SafeLocalClient:
    """Factory for local-only HTTP client."""
    return SafeLocalClient(*args, **kwargs)
