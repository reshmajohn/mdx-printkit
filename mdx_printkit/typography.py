"""Select body typography and prepare the bundled fonts for local rendering."""

from importlib.resources import files
from pathlib import Path

from .errors import PrintKitError

DEFAULT_FONT = "source-sans-pro"
FONT_NAMES = {
    DEFAULT_FONT: "Source Sans Pro",
    "arial": "Arial",
    "helvetica": "Helvetica",
    "verdana": "Verdana",
    "georgia": "Georgia",
    "times-new-roman": "Times New Roman",
    "palatino": "Palatino",
}

# Full face names and PostScript names cover common macOS and Windows installations.
# Each entry provides regular, bold, and italic; semibold uses the actual bold face.
SYSTEM_FACES = {
    "arial": (("Arial", "ArialMT"), ("Arial Bold", "Arial-BoldMT"), ("Arial Italic", "Arial-ItalicMT")),
    "helvetica": (("Helvetica",), ("Helvetica Bold", "Helvetica-Bold"), ("Helvetica Oblique", "Helvetica-Oblique")),
    "verdana": (("Verdana",), ("Verdana Bold", "Verdana-Bold"), ("Verdana Italic", "Verdana-Italic")),
    "georgia": (("Georgia",), ("Georgia Bold", "Georgia-Bold"), ("Georgia Italic", "Georgia-Italic")),
    "times-new-roman": (("Times New Roman", "TimesNewRomanPSMT"),
                        ("Times New Roman Bold", "TimesNewRomanPS-BoldMT"),
                        ("Times New Roman Italic", "TimesNewRomanPS-ItalicMT")),
    "palatino": (("Palatino", "Palatino-Roman"), ("Palatino Bold", "Palatino-Bold"),
                 ("Palatino Italic", "Palatino-Italic")),
}

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


def font_name(font: str) -> str:
    if font not in FONT_NAMES:
        raise PrintKitError(f"unknown font: {font}; choose one of: {', '.join(FONT_NAMES)}")
    return FONT_NAMES[font]


def required_faces(font: str = DEFAULT_FONT) -> list[tuple[str, int, str]]:
    family = font_name(font)
    if font == DEFAULT_FONT:
        return [face[:3] for face in FONT_FACES]
    return [(f"PrintKit {family}", weight, style) for weight, style in
            [(400, "normal"), (600, "normal"), (700, "normal"), (400, "italic")]] + [
        face[:3] for face in FONT_FACES if face[0] == "IBM Plex Mono"
    ]


def font_css(font: str = DEFAULT_FONT) -> str:
    family = font_name(font)
    if font == DEFAULT_FONT:
        return ""
    regular, bold, italic = SYSTEM_FACES[font]
    rules = []
    for weight, style, names in [(400, "normal", regular), (600, "normal", bold),
                                 (700, "normal", bold), (400, "italic", italic)]:
        sources = ", ".join(f'local("{name}")' for name in names)
        rules.append(f'@font-face {{ font-family: "PrintKit {family}"; src: {sources}; '
                     f'font-weight: {weight}; font-style: {style}; }}')
    fallback = "serif" if font in {"georgia", "times-new-roman", "palatino"} else "sans-serif"
    rules.append(f'html {{ --printkit-body-font: "PrintKit {family}", {fallback}, "Apple Color Emoji", '
                 '"Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji"; }')
    return "\n" + "\n".join(rules)


def prepare_fonts(work_dir: Path, font: str = DEFAULT_FONT) -> None:
    font_name(font)
    resources = files("mdx_printkit").joinpath("fonts")
    for family, _, _, relative_path in FONT_FACES:
        if font != DEFAULT_FONT and family != "IBM Plex Mono":
            continue
        target = work_dir / "fonts" / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        # Chromium can hold font files open on Windows during fallback preparation.
        if target.is_file():
            continue
        try:
            target.write_bytes(resources.joinpath(relative_path).read_bytes())
        except FileNotFoundError as exc:
            raise PrintKitError(
                f"Bundled font is missing: {relative_path}. Reinstall mdx-printkit."
            ) from exc
