import hashlib
from pathlib import Path
import socket

from PIL import Image
import pytest

from mdx_printkit.assets import AssetResolver, _public_addresses, image_reference_parts, verify_image
from mdx_printkit.errors import AssetError


def test_local_paths_and_verified_formats(tmp_path, png):
    resolver = AssetResolver(tmp_path)
    assert resolver.resolve("a%20diagram.png?x=1#fragment") == png
    assert resolver.resolve(str(png)) == png
    for kind in ["JPEG", "WEBP", "PNG"]:
        path = tmp_path / kind
        Image.new("RGB", (10, 10)).save(path, format=kind)
        assert verify_image(path) == kind


@pytest.mark.parametrize("reference", ["file:///etc/passwd", "data:image/png;base64,xxx",
                                      "javascript:alert(1)", "//example.com/image.png",
                                      r"\\server\share\image.png", "%5C%5Cserver%5Cshare%5Cimage.png",
                                      "", "missing.png"])
def test_invalid_paths(tmp_path, reference):
    with pytest.raises(AssetError):
        AssetResolver(tmp_path).resolve(reference)


def test_remote_cache_query_and_offline(tmp_path, http_images, monkeypatch):
    url, hits = http_images
    cache = tmp_path / "cache"
    resolver = AssetResolver(tmp_path, cache_dir=cache)
    first = resolver.resolve(url + "/image.png?one=1#first")
    assert resolver.resolve(url + "/image.png?one=1#second") == first
    second = resolver.resolve(url + "/image.png?two=2")
    assert first != second
    assert len(hits) == 2
    offline = AssetResolver(tmp_path, cache_dir=cache, offline=True)
    monkeypatch.setattr(offline, "_download", lambda *args: pytest.fail("offline network call"))
    assert offline.resolve(url + "/image.png?one=1") == first
    with pytest.raises(AssetError, match="not cached"):
        offline.resolve(url + "/uncached")
    first.write_bytes(b"broken")
    with pytest.raises(AssetError, match="corrupt"):
        AssetResolver(tmp_path, cache_dir=cache, offline=True).resolve(url + "/image.png?one=1")
    assert verify_image(AssetResolver(tmp_path, cache_dir=cache).resolve(url + "/image.png?one=1")) == "PNG"


def test_redirect_and_failures(tmp_path, http_images):
    url, hits = http_images
    resolver = AssetResolver(tmp_path, cache_dir=tmp_path / "cache", timeout=2)
    assert verify_image(resolver.resolve(url + "/redirect")) == "PNG"
    for endpoint, message in [("missing", "404"), ("corrupt", "valid raster"),
                              ("large", "25 MB"),
                              ("private-redirect", "blocked"), ("loop", "redirects")]:
        with pytest.raises(AssetError, match=message):
            resolver.resolve(url + "/" + endpoint)
    assert not list((tmp_path / "cache").glob("tmp*"))
    assert len(list((tmp_path / "cache").glob("*.image"))) == 1
    with pytest.raises(AssetError, match="timed out"):
        AssetResolver(tmp_path, cache_dir=tmp_path / "cache", timeout=0.05).resolve(url + "/slow")


@pytest.mark.parametrize("ip", ["127.0.0.1", "10.0.0.1", "169.254.169.254", "::1", "::ffff:127.0.0.1"])
def test_non_public_dns_blocked(monkeypatch, ip):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: [(0, 0, 0, "", (ip, 80))])
    with pytest.raises(AssetError, match="blocked"):
        _public_addresses("example.com", 80)


def test_mixed_dns_answers_blocked(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: [
        (0, 0, 0, "", ("8.8.8.8", 80)), (0, 0, 0, "", ("192.168.1.1", 80))])
    with pytest.raises(AssetError):
        _public_addresses("example.com", 80)


def test_request_limit_and_credentials(tmp_path, http_images):
    url, hits = http_images
    with pytest.raises(AssetError, match="request"):
        AssetResolver(tmp_path, cache_dir=tmp_path, max_requests=1).resolve(url + "/redirect")
    with pytest.raises(AssetError, match="credentials"):
        AssetResolver(tmp_path, cache_dir=tmp_path).resolve(url.replace("://", "://user:secret@") + "/image.png")


@pytest.mark.parametrize("reference", [r"C:\course\a%20diagram.png", "C:/course/a%20diagram.png",
                                      "C%3A/course/a%20diagram.png"])
def test_windows_drive_reference_is_not_a_url_scheme(reference):
    parts = image_reference_parts(reference + "?raw=1#figure")
    assert parts.scheme == "" and parts.netloc == ""
    assert parts.path == "C:/course/a diagram.png"
    assert parts.query == "raw=1" and parts.fragment == "figure"


def test_relative_backslashes_and_literal_percent_names(tmp_path, png):
    folder = tmp_path / "images"
    folder.mkdir()
    image = folder / "literal%20name.png"
    image.write_bytes(png.read_bytes())
    resolver = AssetResolver(tmp_path)
    assert resolver.resolve(r"images\literal%2520name.png") == image
    assert resolver.resolve("images%5Cliteral%2520name.png") == image


@pytest.mark.parametrize("native_state", ["absent", "corrupt"])
def test_native_cache_keeps_legacy_images_available_offline(tmp_path, png, monkeypatch, native_state):
    home = tmp_path / "user"
    native = home / "native-cache" / "mdx-printkit"
    legacy = home / ".cache" / "mdx-printkit"
    legacy.mkdir(parents=True)
    url = "https://example.com/image.png?revision=1"
    filename = hashlib.sha256(url.encode()).hexdigest() + ".image"
    cached = legacy / filename
    cached.write_bytes(png.read_bytes())
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    monkeypatch.setattr("mdx_printkit.assets.user_cache_path", lambda *args, **kwargs: native)
    if native_state == "corrupt":
        native.mkdir(parents=True)
        (native / filename).write_bytes(b"broken")
    resolver = AssetResolver(tmp_path, offline=True)
    monkeypatch.setattr(resolver, "_download", lambda *args: pytest.fail("offline network call"))
    assert resolver.cache_dir == native
    assert resolver.resolve(url) == cached
    # An explicit caller-selected cache must not read unrelated user caches.
    with pytest.raises(AssetError, match="not cached"):
        AssetResolver(tmp_path, cache_dir=tmp_path / "explicit", offline=True).resolve(url)
