from PIL import Image
from pypdf import PdfReader
import pytest

from mdx_printkit.__main__ import main
from mdx_printkit.convert import convert
from mdx_printkit.render import render_pdf

pytestmark = pytest.mark.pdf


def test_default_pdf_relative_path_spaces_and_source_unchanged(tmp_path, png, monkeypatch, chromium, capsys):
    source = tmp_path / "my notes.mdx"
    original = "# Printable notes\n\nSelectable content.\n\n![Diagram](a%20diagram.png)"
    source.write_text(original, encoding="utf-8")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    assert main(["../my notes.mdx"]) == 0
    assert "1 image(s)" in capsys.readouterr().out
    output = elsewhere / "output" / "my notes.pdf"
    reader = PdfReader(output)
    assert "Selectable content" in reader.pages[0].extract_text()
    assert len(reader.pages[0].images) >= 1
    assert float(reader.pages[0].mediabox.width) == pytest.approx(612, abs=1)
    assert source.read_text() == original


@pytest.mark.parametrize("frames", [1, 4, 6])
def test_a4_gif_forms_and_missing_image(tmp_path, animated_gif, chromium, frames):
    source = tmp_path / "gif.md"
    source.write_text("# GIF test\n\n![Movement](moving.gif)\n\n[Watch GIF](moving.gif)\n\n"
                      '<img src="moving.gif" alt="Movement HTML">\n\n![Missing](missing.png)', encoding="utf-8")
    output = tmp_path / "prints" / "Storyboard.pdf"
    result = convert(source, output, paper="a4", gif_frames=frames, offline=True)
    assert result.images == 3 and result.gifs == 3 and len(result.warnings) == 1
    reader = PdfReader(output)
    text = "\n".join(page.extract_text() for page in reader.pages)
    assert text.count(f"Frame 1/{frames}") == 3
    assert "Image unavailable: Missing" in text
    assert sum(len(page.images) for page in reader.pages) >= frames
    assert float(reader.pages[0].mediabox.width) == pytest.approx(595.28, abs=1)


def test_remote_download_and_cached_offline_pdf(tmp_path, http_images, chromium):
    url, hits = http_images
    source = tmp_path / "remote.md"
    source.write_text(f"# Remote\n\n![Remote]({url}/redirect)", encoding="utf-8")
    cache = tmp_path / "cache"
    online = convert(source, tmp_path / "online.pdf", cache_dir=cache)
    count = len(hits)
    offline = convert(source, tmp_path / "offline.pdf", cache_dir=cache, offline=True)
    assert not online.warnings and not offline.warnings
    assert len(hits) == count
    assert len(PdfReader(offline.output).pages[0].images) == 1


def test_renderer_does_not_fetch_remote_content(tmp_path, http_images, chromium):
    url, hits = http_images
    html = tmp_path / "unsafe.html"
    html.write_text(f'''<html><body><h1>Network blocked</h1>
<script>fetch('{url}/script');document.body.innerHTML='Executed'</script>
<iframe src="{url}/iframe"></iframe><link rel="stylesheet" href="{url}/style">
<img src="{url}/image.png"></body></html>''', encoding="utf-8")
    # A blocked image makes decode fail, which is a fatal error rather than a silent blank.
    from mdx_printkit.errors import PrintKitError
    with pytest.raises(PrintKitError, match="renderer failed"):
        render_pdf(html, tmp_path / "unsafe.pdf")
    assert hits == []


def test_wide_tall_media_and_wrapping_fit_print_area(tmp_path, chromium):
    import pymupdf

    Image.new("RGB", (40, 1800), "green").save(tmp_path / "tall.png")
    Image.new("RGB", (1800, 40), "blue").save(tmp_path / "wide.png")
    source = tmp_path / "layout.md"
    source.write_text("# A long title " + "readable " * 20 + "\n\n![Tall](tall.png)\n\n"
                      "![Wide](wide.png)\n\n```\n" + "long_word_" * 100 + "\n```", encoding="utf-8")
    result = convert(source, tmp_path / "layout.pdf")
    with pymupdf.open(result.output) as pdf:
        for page in pdf:
            for word in page.get_text("words"):
                assert word[0] >= 40 and word[2] <= page.rect.width - 40
                assert word[1] >= 40 and word[3] <= page.rect.height - 40
            for image in page.get_image_info():
                x0, y0, x1, y1 = image["bbox"]
                assert x0 >= 40 and x1 <= page.rect.width - 40
                assert y0 >= 40 and y1 <= page.rect.height - 40


def test_source_sans_variants_and_code_fonts_are_embedded_offline(tmp_path, chromium):
    import pymupdf

    source = tmp_path / "typography.md"
    source.write_text(
        "# Bold heading sample\n\nRegular body sample\n\n### Semibold heading sample\n\n"
        "**Bold body sample**\n\n*Italic body sample*\n\n`inline_code_token`\n\n"
        "**`bold_code_token`**\n\n*`italic_code_token`*\n\n```\nfenced_code_token\n```\n",
        encoding="utf-8",
    )
    result = convert(source, tmp_path / "typography.pdf", offline=True)
    expected = {
        "Regular body sample": "SourceSansPro-Regular",
        "Bold heading sample": "SourceSansPro-Bold",
        "Semibold heading sample": "SourceSansPro-Semibold",
        "Bold body sample": "SourceSansPro-Bold",
        "Italic body sample": "SourceSansPro-It",
        "inline_code_token": "IBMPlexMono-Regular",
        "bold_code_token": "IBMPlexMono-Bold",
        "italic_code_token": "IBMPlexMono-Italic",
        "fenced_code_token": "IBMPlexMono-Regular",
    }
    with pymupdf.open(result.output) as pdf:
        spans = [span for page in pdf for block in page.get_text("dict")["blocks"]
                 if "lines" in block for line in block["lines"] for span in line["spans"]]
        for text, font in expected.items():
            matches = [span for span in spans if text in span["text"]]
            assert matches, text
            assert all(span["font"] == font for span in matches), matches

    embedded = set()
    for page in PdfReader(result.output).pages:
        for font in page["/Resources"]["/Font"].values():
            font = font.get_object()
            name = str(font["/BaseFont"]).split("+")[-1].lstrip("/")
            embedded.add(name)
            descendant = font["/DescendantFonts"][0].get_object()
            descriptor = descendant["/FontDescriptor"]
            assert descriptor["/FontFile2"].get_data(), name
    assert embedded == set(expected.values())


def test_missing_bundled_font_cannot_silently_fall_back(tmp_path, chromium):
    from mdx_printkit.assets import AssetResolver
    from mdx_printkit.document import build_document
    from mdx_printkit.errors import PrintKitError

    document = build_document("# Heading\n\nBody", AssetResolver(tmp_path, offline=True), tmp_path)
    html = tmp_path / "document.html"
    html.write_text(document.html, encoding="utf-8")
    (tmp_path / "fonts/source-sans-pro/SourceSansPro-Regular.ttf").unlink()
    output = tmp_path / "fallback.pdf"
    with pytest.raises(PrintKitError, match="Bundled fonts failed to load: Source Sans Pro 400 normal"):
        render_pdf(html, output)
    assert not output.exists()
