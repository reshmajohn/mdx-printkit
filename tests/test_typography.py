from importlib.resources import files

from bs4 import BeautifulSoup
import pytest

from mdx_printkit.assets import AssetResolver
from mdx_printkit.document import build_document
from mdx_printkit.typography import DEFAULT_FONT, FONT_FACES, FONT_NAMES, font_css


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


@pytest.mark.parametrize("font", [key for key in FONT_NAMES if key != DEFAULT_FONT])
def test_system_font_document_uses_local_faces_and_keeps_code_bundled(tmp_path, font):
    document = build_document("# Typography\n\nBody and `code`", AssetResolver(tmp_path, offline=True),
                              tmp_path, font=font)
    css = font_css(font)
    assert f'font-family: "PrintKit {FONT_NAMES[font]}"' in css
    assert "local(" in css and "url(" not in css
    assert not (tmp_path / "fonts/source-sans-pro").exists()
    assert len(list((tmp_path / "fonts/ibm-plex-mono").glob("*.ttf"))) == 3
    assert css in document.html
    assert 'pre, code { font-family: "IBM Plex Mono"' in document.html


def test_default_font_css_keeps_original_typography():
    assert font_css() == ""
