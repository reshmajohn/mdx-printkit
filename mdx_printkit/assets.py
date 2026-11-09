"""Bounded raster loading, persistent cache, and public-only HTTP downloads."""

from __future__ import annotations

import hashlib
import http.client
import ipaddress
import os
from pathlib import Path
import re
import socket
import ssl
import tempfile
from urllib.parse import SplitResult, unquote, urljoin, urlsplit
import warnings

from PIL import Image
from platformdirs import user_cache_path

from .errors import AssetError

MAX_BYTES = 25 * 1024 * 1024
MAX_PIXELS = 40_000_000
SUPPORTED_FORMATS = {"PNG", "JPEG", "WEBP", "GIF"}


def image_reference_parts(reference: str) -> SplitResult:
    """Parse asset URLs while preserving drive letters and native path separators."""
    if re.match(r"^[A-Za-z]:[/\\]", reference):
        parts = urlsplit("/" + reference.replace("\\", "/"))
        parts = parts._replace(path=parts.path[1:])
    elif reference.startswith("\\\\"):
        # UNC references are network resources, not unrestricted local images.
        return urlsplit(reference.replace("\\", "/"))
    else:
        parts = urlsplit(reference)
    if parts.scheme or parts.netloc:
        return parts
    path = unquote(parts.path).replace("\\", "/")
    if path.startswith("//"):
        return urlsplit(path)._replace(query=parts.query, fragment=parts.fragment)
    return parts._replace(path=path)


def verify_image(path: Path) -> str:
    try:
        if path.stat().st_size > MAX_BYTES:
            raise AssetError("image exceeds the 25 MB limit")
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(path) as image:
                if image.format not in SUPPORTED_FORMATS:
                    raise AssetError("unsupported image format (use PNG, JPEG, WEBP, or GIF)")
                if image.width * image.height > MAX_PIXELS:
                    raise AssetError("image exceeds the 40 megapixel limit")
                kind = image.format
                image.verify()
                return kind
    except AssetError:
        raise
    except (OSError, ValueError, SyntaxError, Image.DecompressionBombError,
            Image.DecompressionBombWarning) as exc:
        raise AssetError(f"cannot read a valid raster image: {exc}") from exc


def _public_addresses(host: str, port: int) -> list[str]:
    """Validate every DNS answer; connections use these exact IPs, avoiding rebinding."""
    addresses = list(dict.fromkeys(
        entry[4][0] for entry in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    ))
    if not addresses or any(not ipaddress.ip_address(ip).is_global for ip in addresses):
        raise AssetError("private, loopback, and non-public network addresses are blocked")
    return addresses


class AssetResolver:
    def __init__(self, source_dir: Path, *, cache_dir: Path | None = None,
                 offline: bool = False, timeout: float = 15, max_requests: int = 100):
        self.source_dir = source_dir
        self.cache_dir = Path(cache_dir) if cache_dir is not None else user_cache_path("mdx-printkit", appauthor=False)
        self.legacy_cache_dir = Path.home() / ".cache" / "mdx-printkit" if cache_dir is None else None
        self.offline = offline
        self.timeout = timeout
        self.max_requests = max_requests
        self.requests = 0
        self._resolved: dict[str, Path] = {}
        self._failures: dict[str, str] = {}

    def resolve(self, reference: str) -> Path:
        if reference in self._resolved:
            return self._resolved[reference]
        if reference in self._failures:
            raise AssetError(self._failures[reference])
        try:
            parts = image_reference_parts(reference)
            if parts.scheme.lower() in {"http", "https"}:
                path = self._remote(reference)
            elif parts.scheme or parts.netloc:
                raise AssetError("only relative/absolute image paths and HTTP(S) URLs are supported")
            else:
                if not parts.path:
                    raise AssetError("missing image path")
                if os.name != "nt" and re.match(r"^[A-Za-z]:/", parts.path):
                    raise AssetError("Windows drive paths require Windows; use a relative image path for portable documents")
                path = (self.source_dir / parts.path).resolve()
                verify_image(path)
            self._resolved[reference] = path
            return path
        except (OSError, ValueError, http.client.HTTPException, AssetError) as exc:
            message = str(exc)
            self._failures[reference] = message
            raise AssetError(message) from exc

    def _remote(self, url: str) -> Path:
        # Fragments are client-side; query strings remain part of the cache identity.
        url = urlsplit(url)._replace(fragment="").geturl()
        filename = hashlib.sha256(url.encode()).hexdigest() + ".image"
        cache = self.cache_dir / filename
        candidates = [cache]
        if self.legacy_cache_dir is not None and self.legacy_cache_dir != self.cache_dir:
            candidates.append(self.legacy_cache_dir / filename)
        corrupt = False
        for candidate in candidates:
            if not candidate.is_file():
                continue
            try:
                verify_image(candidate)
                return candidate
            except AssetError:
                corrupt = True
        if self.offline:
            if corrupt:
                raise AssetError("cached image is corrupt; rerun without --offline to refresh")
            raise AssetError("image is not cached and --offline prevents downloading")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.cache_dir, delete=False) as stream:
                temporary = Path(stream.name)
                self._download(url, stream)
            verify_image(temporary)
            os.replace(temporary, cache)
            return cache
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def _download(self, url: str, stream) -> None:
        for _ in range(6):
            parts = urlsplit(url)
            if parts.scheme not in {"http", "https"} or not parts.hostname:
                raise AssetError("redirect target must be an HTTP(S) URL")
            if parts.username is not None or parts.password is not None:
                raise AssetError("URLs containing credentials are not supported")
            port = parts.port or (443 if parts.scheme == "https" else 80)
            addresses = _public_addresses(parts.hostname, port)
            self.requests += 1
            if self.requests > self.max_requests:
                raise AssetError("document exceeds the 100-request download limit")
            connection = http.client.HTTPConnection(parts.hostname, port, timeout=self.timeout)
            try:
                # Pin DNS resolution, retaining the original HTTP Host and TLS hostname.
                last_error = None
                for address in addresses:
                    try:
                        connection.sock = socket.create_connection((address, port), self.timeout)
                        if parts.scheme == "https":
                            connection.sock = ssl.create_default_context().wrap_socket(
                                connection.sock, server_hostname=parts.hostname
                            )
                        break
                    except OSError as exc:
                        connection.close()
                        last_error = exc
                if connection.sock is None:
                    raise AssetError(f"could not connect: {last_error}")
                target = parts.path or "/"
                if parts.query:
                    target += "?" + parts.query
                connection.request("GET", target, headers={
                    "User-Agent": "mdx-printkit/0.1", "Accept": "image/*", "Accept-Encoding": "identity"
                })
                response = connection.getresponse()
                if response.status in {301, 302, 303, 307, 308}:
                    location = response.getheader("Location")
                    if not location:
                        raise AssetError("redirect has no Location header")
                    url = urljoin(url, location)
                    continue
                if response.status != 200:
                    raise AssetError(f"HTTP {response.status} {response.reason}")
                length = response.getheader("Content-Length")
                if length and int(length) > MAX_BYTES:
                    raise AssetError("image exceeds the 25 MB download limit")
                total = 0
                while chunk := response.read(64 * 1024):
                    total += len(chunk)
                    if total > MAX_BYTES:
                        raise AssetError("image exceeds the 25 MB download limit")
                    stream.write(chunk)
                return
            finally:
                connection.close()
        raise AssetError("too many image redirects (maximum 5)")
