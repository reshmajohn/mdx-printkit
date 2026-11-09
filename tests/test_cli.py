import pytest

from mdx_printkit.__main__ import main
from mdx_printkit.convert import convert
from mdx_printkit.errors import PrintKitError
from mdx_printkit.typography import FONT_NAMES


def test_help_and_version(capsys):
    with pytest.raises(SystemExit) as result:
        main(["--help"])
    assert result.value.code == 0
    help_text = capsys.readouterr().out
    assert "file" in help_text and "folder" in help_text
    for command in ["file", "folder"]:
        with pytest.raises(SystemExit) as result:
            main([command, "--help"])
        assert result.value.code == 0
        help_text = capsys.readouterr().out
        assert "--gif-frames" in help_text and "--font" in help_text
        for font in FONT_NAMES:
            assert font in "".join(help_text.split())
    with pytest.raises(SystemExit) as result:
        main(["--version"])
    assert result.value.code == 0
    assert "0.1.0" in capsys.readouterr().out


@pytest.mark.parametrize("arguments", [["a.mdx", "--gif-frames", "0"],
                                      ["a.mdx", "--gif-frames", "13"],
                                      ["a.mdx", "--gif-frames", "abc"],
                                      ["a.mdx", "--paper", "legal"],
                                      ["file", "a.mdx", "--gif-frames", "0"],
                                      ["folder", ".", "--gif-frames", "13"],
                                      ["folder", ".", "--paper", "legal"],
                                      ["file", "a.mdx", "--font", "missing"],
                                      ["folder", ".", "--font", "missing"],
                                      ["file"], ["folder"], []])
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


@pytest.mark.parametrize("kwargs", [{"gif_frames": 0}, {"gif_frames": 13}, {"paper": "legal"},
                                   {"font": "missing"}])
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

    def fail(*args, **kwargs):
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
    with pytest.raises(PrintKitError, match="python -m playwright install chromium"):
        render_pdf(tmp_path / "input.html", tmp_path / "out.pdf")


@pytest.mark.parametrize("message", ["Host system is missing dependencies. Run playwright install-deps",
                                   "error while loading shared libraries: libX11.so"])
def test_missing_browser_libraries_action(tmp_path, monkeypatch, message):
    from playwright.sync_api import Error
    from mdx_printkit.render import render_pdf

    def fail():
        raise Error(message)

    monkeypatch.setattr("mdx_printkit.render.sync_playwright", fail)
    with pytest.raises(PrintKitError, match="python -m playwright install --with-deps chromium"):
        render_pdf(tmp_path / "input.html", tmp_path / "out.pdf")


def test_installed_module_help_runs_outside_checkout(tmp_path):
    import subprocess
    import sys

    result = subprocess.run([sys.executable, "-m", "mdx_printkit", "file", "--help"],
                            cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert "--font" in result.stdout


@pytest.mark.parametrize("case", ["missing", "not-directory", "empty", "output-file"])
def test_folder_validation(tmp_path, capsys, case):
    folder = tmp_path / "course"
    folder.mkdir()
    arguments = ["folder", str(folder)]
    if case == "missing":
        arguments[1] = str(tmp_path / "missing")
    elif case == "not-directory":
        source = folder / "notes.mdx"
        source.write_text("# Notes", encoding="utf-8")
        arguments[1] = str(source)
    elif case == "output-file":
        (folder / "notes.mdx").write_text("# Notes", encoding="utf-8")
        output = tmp_path / "existing.pdf"
        output.write_bytes(b"existing")
        arguments.extend(["--output", str(output)])
    assert main(arguments) == 1
    assert "Error:" in capsys.readouterr().err
    assert not (folder / "notes.pdf").exists()


def test_folder_rejects_colliding_destinations_before_writing(tmp_path, capsys):
    folder = tmp_path / "course"
    folder.mkdir()
    for stem in ["one", "two"]:
        (folder / f"{stem}.mdx").write_text(f"# {stem}", encoding="utf-8")
    shared = tmp_path / "shared.pdf"
    shared.write_bytes(b"previous PDF")
    for stem in ["one", "two"]:
        try:
            (folder / f"{stem}.pdf").symlink_to(shared)
        except (OSError, NotImplementedError):
            pytest.skip("symlink creation is unavailable without extra OS privileges")
    assert main(["folder", str(folder)]) == 1
    assert "collision" in capsys.readouterr().err
    assert shared.read_bytes() == b"previous PDF"


def test_folder_passes_selected_font_to_each_input(tmp_path, monkeypatch):
    from mdx_printkit.convert import ConversionResult

    for name in ["one.mdx", "two.mdx"]:
        (tmp_path / name).write_text("# Document", encoding="utf-8")
    selected = []

    def record(source, output, **options):
        selected.append((source.name, options["font"]))
        return ConversionResult(output, 0, 0, [])

    monkeypatch.setattr("mdx_printkit.__main__.convert", record)
    assert main(["folder", str(tmp_path), "--font", "georgia"]) == 0
    assert selected == [("one.mdx", "georgia"), ("two.mdx", "georgia")]
