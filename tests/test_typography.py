from importlib.resources import files

from bs4 import BeautifulSoup

from mdx_printkit.assets import AssetResolver
from mdx_printkit.document import build_document
from mdx_printkit.typography import FONT_FACES


def test_bundled_fonts_and_licenses_are_available(tmp_path):
    document = build_document("# Typography\n\nBody", AssetResolver(tmp_path, offline=True), tmp_path)
    for _, _, _, relative in FONT_FACES:
        assert (tmp_path / "fonts" / relative).read_bytes()[:4] == b"\0\1\0\0"
    root = files("mdx_printkit").joinpath("fonts")
    for license_path in ["source-sans-pro/LICENSE.txt", "ibm-plex-mono/OFL.txt"]:
        license_text = root.joinpath(license_path).read_text(encoding="utf-8")
        assert "SIL OPEN FONT LICENSE Version 1.1" in license_text
    soup = BeautifulSoup(document.html, "html.parser")
    assert "font-src file:" in soup.find("meta", attrs={"http-equiv": "Content-Security-Policy"})["content"]
    assert not soup.select("link[href^='http']")
