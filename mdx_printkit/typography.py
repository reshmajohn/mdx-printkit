"""Make the bundled fonts available inside the isolated render directory."""

from importlib.resources import files
from pathlib import Path

from .errors import PrintKitError

# These faces are explicitly loaded and checked before Chromium prints the page.
FONT_FACES = (
    ("Source Sans Pro", 400, "normal", "source-sans-pro/SourceSansPro-Regular.ttf"),
    ("Source Sans Pro", 600, "normal", "source-sans-pro/SourceSansPro-Semibold.ttf"),
    ("Source Sans Pro", 700, "normal", "source-sans-pro/SourceSansPro-Bold.ttf"),
    ("Source Sans Pro", 400, "italic", "source-sans-pro/SourceSansPro-It.ttf"),
    ("IBM Plex Mono", 400, "normal", "ibm-plex-mono/IBMPlexMono-Regular.ttf"),
    ("IBM Plex Mono", 700, "normal", "ibm-plex-mono/IBMPlexMono-Bold.ttf"),
    ("IBM Plex Mono", 400, "italic", "ibm-plex-mono/IBMPlexMono-Italic.ttf"),
)


def prepare_fonts(work_dir: Path) -> None:
    resources = files("mdx_printkit").joinpath("fonts")
    for _, _, _, relative_path in FONT_FACES:
        target = work_dir / "fonts" / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            target.write_bytes(resources.joinpath(relative_path).read_bytes())
        except FileNotFoundError as exc:
            raise PrintKitError(
                f"Bundled font is missing: {relative_path}. Reinstall mdx-printkit."
            ) from exc
