from dataclasses import dataclass
import os
from pathlib import Path
import tempfile

from .assets import AssetResolver
from .document import build_document
from .errors import PrintKitError
from .render import render_pdf
from .typography import DEFAULT_FONT, font_name


@dataclass(frozen=True)
class ConversionResult:
    output: Path
    images: int
    gifs: int
    warnings: list[str]


def convert(source: Path | str, output: Path | str | None = None, *, paper: str = "letter",
            gif_frames: int = 4, offline: bool = False,
            cache_dir: Path | None = None, font: str = DEFAULT_FONT) -> ConversionResult:
    font_name(font)
    source = Path(source).expanduser().resolve()
    if source.suffix.lower() not in {".md", ".mdx"}:
        raise PrintKitError("input must be a local .md or .mdx file")
    if not 1 <= gif_frames <= 12:
        raise PrintKitError("GIF frame count must be between 1 and 12")
    if paper not in {"letter", "a4"}:
        raise PrintKitError("paper must be 'letter' or 'a4'")
    destination = (Path(output).expanduser() if output is not None else source.with_suffix(".pdf")).resolve()
    if destination == source:
        raise PrintKitError("output must not overwrite the input document")
    if destination.suffix.lower() != ".pdf":
        raise PrintKitError("output path must end in .pdf")
    staged = None
    try:
        text = source.read_text(encoding="utf-8")
        resolver = AssetResolver(source.parent, cache_dir=cache_dir, offline=offline)
        with tempfile.TemporaryDirectory(prefix="mdx-printkit-") as temporary:
            work_dir = Path(temporary)
            document = build_document(text, resolver, work_dir, gif_frames=gif_frames,
                                      title=source.stem, font=font)
            html = work_dir / "document.html"
            html.write_text(document.html, encoding="utf-8")
            destination.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=destination.parent, suffix=".pdf", delete=False) as stream:
                staged = Path(stream.name)
            render_pdf(html, staged, paper, font=font)
            os.replace(staged, destination)
        return ConversionResult(destination, document.images, document.gifs, document.warnings)
    except (OSError, UnicodeError) as exc:
        raise PrintKitError(f"cannot convert {source}: {exc}") from exc
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)
