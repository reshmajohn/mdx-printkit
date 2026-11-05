from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
import threading
import time

from PIL import Image, ImageDraw
import pytest

from mdx_printkit import assets


@pytest.fixture
def png(tmp_path):
    path = tmp_path / "a diagram.png"
    Image.new("RGB", (120, 70), "royalblue").save(path)
    return path


@pytest.fixture
def animated_gif(tmp_path):
    frames = []
    for index in range(9):
        frame = Image.new("RGB", (180, 90), "white")
        ImageDraw.Draw(frame).rectangle((index * 17, 25, index * 17 + 20, 60), fill="red")
        frames.append(frame)
    frames.append(frames[1].copy())
    path = tmp_path / "moving.gif"
    frames[0].save(path, save_all=True, append_images=frames[1:], loop=0,
                   duration=[100, 100, 900, 100, 100, 100, 100, 100, 100, 100], disposal=2)
    return path


@pytest.fixture
def http_images(monkeypatch):
    payload = BytesIO()
    Image.new("RGB", (20, 12), "green").save(payload, format="PNG")
    hits = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            hits.append(self.path)
            if self.path == "/slow":
                time.sleep(0.2)
            if self.path == "/redirect":
                self.send_response(302)
                self.send_header("Location", "/image.png")
                self.end_headers()
                return
            if self.path == "/private-redirect":
                self.send_response(302)
                self.send_header("Location", "http://10.0.0.1/private.png")
                self.end_headers()
                return
            if self.path == "/loop":
                self.send_response(302)
                self.send_header("Location", "/loop")
                self.end_headers()
                return
            if self.path == "/missing":
                self.send_error(404)
                return
            self.send_response(200)
            if self.path == "/large":
                self.send_header("Content-Length", str(assets.MAX_BYTES + 1))
            self.end_headers()
            body = b"<html>not an image</html>" if self.path == "/corrupt" else payload.getvalue()
            try:
                self.wfile.write(body)
            except BrokenPipeError:
                pass

        def log_message(self, *args):
            pass

    original = assets._public_addresses

    def test_addresses(host, port):
        return ["127.0.0.1"] if host == "localhost" else original(host, port)

    monkeypatch.setattr(assets, "_public_addresses", test_addresses)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://localhost:{server.server_port}", hits
    server.shutdown()
    server.server_close()
    thread.join()


@pytest.fixture
def chromium():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as playwright:
        executable = Path(playwright.chromium.executable_path)
    if not executable.exists():
        pytest.skip("Playwright Chromium is not installed")
