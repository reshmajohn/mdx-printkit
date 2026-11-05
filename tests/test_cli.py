import pytest

from mdx_printkit.cli import main
from mdx_printkit.convert import convert
from mdx_printkit.errors import PrintKitError


def test_help_and_version(capsys):
    with pytest.raises(SystemExit) as result:
        main(["--help"])
    assert result.value.code == 0
    assert "--gif-frames" in capsys.readouterr().out
    with pytest.raises(SystemExit) as result:
        main(["--version"])
    assert result.value.code == 0
    assert "0.1.0" in capsys.readouterr().out


@pytest.mark.parametrize("arguments", [["a.mdx", "--gif-frames", "0"],
                                      ["a.mdx", "--gif-frames", "13"],
                                      ["a.mdx", "--gif-frames", "abc"],
                                      ["a.mdx", "--paper", "legal"], []])
def test_invalid_options(arguments):
    with pytest.raises(SystemExit) as result:
        main(arguments)
    assert result.value.code == 2


def test_input_errors(tmp_path, capsys):
    assert main([str(tmp_path / "missing.mdx")]) == 1
    assert "Error:" in capsys.readouterr().err
    invalid = tmp_path / "invalid.mdx"
    invalid.write_bytes(b"\xff\xfe")
    assert main([str(invalid)]) == 1
    assert main([str(tmp_path / "image.png")]) == 1


@pytest.mark.parametrize("kwargs", [{"gif_frames": 0}, {"gif_frames": 13}, {"paper": "legal"}])
def test_api_validation(tmp_path, kwargs):
    with pytest.raises(PrintKitError):
        convert(tmp_path / "notes.mdx", **kwargs)


def test_source_overwrite_blocked(tmp_path):
    source = tmp_path / "notes.mdx"
    source.write_text("Original", encoding="utf-8")
    with pytest.raises(PrintKitError, match="overwrite"):
        convert(source, source)
    assert source.read_text() == "Original"


def test_fatal_renderer_keeps_existing_pdf(tmp_path, monkeypatch):
    source = tmp_path / "notes.md"
    source.write_text("# Notes", encoding="utf-8")
    output = tmp_path / "previous.pdf"
    output.write_bytes(b"previous PDF")

    def fail(*args):
        raise PrintKitError("Renderer unavailable")

    monkeypatch.setattr("mdx_printkit.convert.render_pdf", fail)
    with pytest.raises(PrintKitError, match="Renderer unavailable"):
        convert(source, output)
    assert output.read_bytes() == b"previous PDF"
    assert list(tmp_path.glob("*.pdf")) == [output]


def test_missing_browser_action(tmp_path, monkeypatch):
    from playwright.sync_api import Error
    from mdx_printkit.render import render_pdf

    def fail():
        raise Error("Executable doesn't exist. Please run playwright install")

    monkeypatch.setattr("mdx_printkit.render.sync_playwright", fail)
    with pytest.raises(PrintKitError, match=r"\.venv/bin/python -m playwright install chromium"):
        render_pdf(tmp_path / "input.html", tmp_path / "out.pdf")
