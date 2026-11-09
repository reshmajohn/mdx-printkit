from PIL import Image
from pypdf import PdfReader
import pytest

from mdx_printkit.__main__ import main
from mdx_printkit.convert import convert
from mdx_printkit.render import render_pdf

pytestmark = pytest.mark.pdf


@pytest.mark.parametrize("prefix", [[], ["file"], ["--offline"]])
def test_default_pdf_relative_path_spaces_and_source_unchanged(tmp_path, png, monkeypatch, chromium, capsys, prefix):
    source = tmp_path / "my notes.mdx"
    original = "# Printable notes\n\nSelectable content.\n\n![Diagram](a%20diagram.png)"
    source.write_text(original, encoding="utf-8")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    assert main([*prefix, "../my notes.mdx"]) == 0
    assert "1 image(s)" in capsys.readouterr().out
    output = source.with_suffix(".pdf")
    assert not (elsewhere / "output").exists()
    reader = PdfReader(output)
    assert "Selectable content" in reader.pages[0].extract_text()
    assert len(reader.pages[0].images) >= 1
    assert float(reader.pages[0].mediabox.width) == pytest.approx(612, abs=1)
    assert source.read_text() == original


@pytest.mark.parametrize("custom_output,frames", [(False, 4), (True, 6)])
def test_folder_pdfs_defaults_options_and_source_selection(
    tmp_path, png, animated_gif, monkeypatch, chromium, capsys, custom_output, frames
):
    folder = tmp_path / "course notes"
    folder.mkdir()
    sources = {
        "01 intro.mdx": "# First document\n\n![Diagram](../a%20diagram.png)",
        "02 motion.MDX": "# Second document\n\n![Movement](../moving.gif)",
    }
    for name, content in sources.items():
        (folder / name).write_text(content, encoding="utf-8")
    (folder / "ignored.md").write_text("# Ignored", encoding="utf-8")
    nested = folder / "nested"
    nested.mkdir()
    (nested / "ignored.mdx").write_text("# Nested", encoding="utf-8")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    arguments = ["folder", "../course notes", "--paper", "a4", "--offline"]
    output = folder
    if custom_output:
        arguments.extend(["--output", "../prints", "--gif-frames", str(frames)])
        output = tmp_path / "prints"
    assert main(arguments) == 0
    stdout = capsys.readouterr().out
    assert "2 succeeded, 0 failed" in stdout
    assert stdout.index("01 intro.pdf") < stdout.index("02 motion.pdf")
    first = PdfReader(output / "01 intro.pdf")
    second = PdfReader(output / "02 motion.pdf")
    assert "First document" in first.pages[0].extract_text()
    assert len(first.pages[0].images) == 1
    text = "\n".join(page.extract_text() for page in second.pages)
    assert f"Frame 1/{frames}" in text and f"Frame {frames}/{frames}" in text
    assert sum(len(page.images) for page in second.pages) >= frames
    assert float(first.pages[0].mediabox.width) == pytest.approx(595.28, abs=1)
    assert float(second.pages[0].mediabox.width) == pytest.approx(595.28, abs=1)
    assert sorted(path.name for path in output.glob("*.pdf")) == ["01 intro.pdf", "02 motion.pdf"]
    assert not (nested / "ignored.pdf").exists()
    assert not (elsewhere / "output").exists()
    for name, content in sources.items():
        assert (folder / name).read_text(encoding="utf-8") == content


def test_folder_continues_after_failure_and_keeps_previous_pdf(tmp_path, chromium, capsys):
    (tmp_path / "01 bad.mdx").write_bytes(b"\xff\xfe")
    (tmp_path / "02 good.mdx").write_text("# Valid document", encoding="utf-8")
    previous = tmp_path / "01 bad.pdf"
    previous.write_bytes(b"previous PDF")
    assert main(["folder", str(tmp_path), "--offline"]) == 1
    captured = capsys.readouterr()
    assert "01 bad.mdx" in captured.err
    assert "1 succeeded, 1 failed" in captured.out
    assert "Valid document" in PdfReader(tmp_path / "02 good.pdf").pages[0].extract_text()
    assert previous.read_bytes() == b"previous PDF"


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


@pytest.mark.parametrize("font,regular,bold,italic", [
    ("arial", "ArialMT", "Arial-BoldMT", "Arial-ItalicMT"),
    ("helvetica", "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"),
    ("verdana", "Verdana", "Verdana-Bold", "Verdana-Italic"),
    ("georgia", "Georgia", "Georgia-Bold", "Georgia-Italic"),
    ("times-new-roman", "TimesNewRomanPSMT", "TimesNewRomanPS-BoldMT", "TimesNewRomanPS-ItalicMT"),
    ("palatino", "Palatino-Roman", "Palatino-Bold", "Palatino-Italic"),
])
def test_system_font_pdf_uses_selected_family_and_embeds_it(tmp_path, chromium, font, regular, bold, italic):
    import pymupdf
    from playwright.sync_api import sync_playwright

    # Family availability is OS-dependent; probe independently of the app's face aliases.
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            available = browser.new_page().evaluate("""async name => {
                try { await new FontFace('probe', `local("${name}")`).load(); return true; }
                catch { return false; }
            }""", regular)
        finally:
            browser.close()
    if not available:
        pytest.skip(f"system font {regular} is not installed")

    source = tmp_path / "system-font.mdx"
    source.write_text("# Bold heading\n\nRegular body sample\n\n### Semibold heading\n\n"
                      "*Italic body sample*\n\n`inline_code_token`", encoding="utf-8")
    assert main(["file", str(source), "--font", font, "--offline"]) == 0
    output = source.with_suffix(".pdf")
    expected = {"Regular body sample": regular, "Bold heading": bold,
                "Semibold heading": bold, "Italic body sample": italic,
                "inline_code_token": "IBMPlexMono-Regular"}
    with pymupdf.open(output) as pdf:
        spans = [span for page in pdf for block in page.get_text("dict")["blocks"]
                 if "lines" in block for line in block["lines"] for span in line["spans"]]
        for text, name in expected.items():
            matches = [span for span in spans if text in span["text"]]
            assert matches and all(span["font"] == name for span in matches), (text, matches)
        for span in spans:
            assert span["font"] in expected.values(), span
    for page in PdfReader(output).pages:
        for reference in page["/Resources"]["/Font"].values():
            resource = reference.get_object()
            face = resource["/DescendantFonts"][0].get_object() if "/DescendantFonts" in resource else resource
            descriptor = face["/FontDescriptor"]
            assert any(descriptor.get(key) and descriptor[key].get_data()
                       for key in ["/FontFile", "/FontFile2", "/FontFile3"])


@pytest.mark.parametrize("command", ["file", "folder"])
def test_unavailable_system_font_warns_and_falls_back(tmp_path, monkeypatch, chromium, capsys, command):
    import pymupdf
    from mdx_printkit.typography import SYSTEM_FACES

    missing = ("PrintKitNonexistentFont019abcdef",)
    monkeypatch.setitem(SYSTEM_FACES, "arial", (missing, missing, missing))
    source = tmp_path / "notes.mdx"
    original = "# Heading\n\nBody\n\n*Italic*\n\n### Semibold\n\n`code`"
    source.write_text(original, encoding="utf-8")
    output = source.with_suffix(".pdf")
    output.write_bytes(b"previous PDF")
    assert main([command, str(source if command == "file" else tmp_path), "--font", "arial", "--offline"]) == 0
    captured = capsys.readouterr()
    assert "Warning: System font Arial is unavailable" in captured.err
    assert "using bundled Source Sans Pro" in captured.err
    assert "1 warning(s)" in captured.out
    with pymupdf.open(output) as pdf:
        names = {span["font"] for page in pdf for block in page.get_text("dict")["blocks"]
                 if "lines" in block for line in block["lines"] for span in line["spans"]}
    assert names == {"SourceSansPro-Regular", "SourceSansPro-Bold", "SourceSansPro-It",
                     "SourceSansPro-Semibold", "IBMPlexMono-Regular"}
    assert source.read_text(encoding="utf-8") == original


def test_missing_bundled_fallback_preserves_previous_pdf(tmp_path, monkeypatch, chromium):
    from mdx_printkit.errors import PrintKitError
    from mdx_printkit.typography import SYSTEM_FACES

    missing = ("PrintKitNonexistentFont019abcdef",)
    monkeypatch.setitem(SYSTEM_FACES, "arial", (missing, missing, missing))

    def fail(*args):
        raise PrintKitError("Bundled font is missing; reinstall mdx-printkit")

    monkeypatch.setattr("mdx_printkit.render.prepare_fonts", fail)
    source = tmp_path / "notes.mdx"
    source.write_text("# Heading", encoding="utf-8")
    output = source.with_suffix(".pdf")
    output.write_bytes(b"previous PDF")
    with pytest.raises(PrintKitError, match="Bundled font is missing"):
        convert(source, font="arial", offline=True)
    assert output.read_bytes() == b"previous PDF"


def test_local_resource_file_uri_is_native_and_confined(tmp_path):
    from mdx_printkit.render import _local_resource

    root = tmp_path / "café notes #50%"
    root.mkdir()
    asset = root / "image 100%.png"
    assert _local_resource(asset.as_uri(), root)
    assert _local_resource(asset.as_uri().replace("file:///", "file://localhost/"), root)
    assert not _local_resource((tmp_path / "outside.png").as_uri(), root)
    assert not _local_resource("file://server/share/image.png", root)
    assert not _local_resource("https://example.com/image.png", root)
