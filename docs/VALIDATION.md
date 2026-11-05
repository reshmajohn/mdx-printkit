# Implementation validation

Verified on macOS with Python 3.14 and Playwright Chromium on November 5, 2026.

## Commands run

```bash
.venv/bin/pip install -e '.[test]'
.venv/bin/python -m playwright install chromium
.venv/bin/python -m pytest -m 'not pdf' -q --tb=short
.venv/bin/python -m pytest -q --tb=short
.venv/bin/mdx-printkit --help
.venv/bin/python -m mdx_printkit reference-input/motivation.mdx --output output/motivation.pdf
.venv/bin/python -m mdx_printkit reference-input/motivation.mdx --output output/motivation-offline.pdf --offline
.venv/bin/python -m mdx_printkit output/gif-fixture/storyboards.mdx --output output/gif-storyboards.pdf --offline
git diff --check
```

The GIF smoke input was generated locally: nine distinct moving-object frames plus a repeated frame, uneven durations, and Markdown image, direct Markdown hyperlink, and HTML image references. The fixture and all outputs are under the ignored `output/` directory.

## Results

- Offline unit/integration suite: **50 passed**; seven PDF tests excluded in that run.
- Full suite: **57 passed**, no skips. Five deprecation warnings came from PyMuPDF's SWIG bindings on Python 3.14.
- Help command: all required flags and defaults present.
- Reference conversion: **three images, zero warnings, four pages**, both online and offline.
- PDF image occurrences match source order and original dimensions: 954x630, 1456x392, 941x941. All source headings occur in their original order when PDF extraction whitespace is normalized.
- Synthetic GIF conversion: **three animated GIF occurrences, zero warnings, two pages**, each storyboard with four distinct frames and labels; 12 embedded image occurrences total.
- All four reference pages and both GIF pages were rasterized with PyMuPDF and visually inspected for margins, image placement, typography, clipping, and storyboard alignment.
- `git diff --check` passed.

The private reference input's SHA-256 was identical before and after validation:

```text
326d1df636d85bf6db6772ae17ff4bf8680c6892d06460a7c8a6ec88a3c41099
```

The sandbox blocked package downloads and localhost binding. Dependency installation, browser installation, HTTP fixture tests, and Chromium smoke conversions ran with approved external execution. The tests themselves use synthetic offline fixtures and no third-party servers.

## Remaining boundaries

Full React/JSX execution, JavaScript expressions, source stylesheets, authenticated image downloads, private-network images, SVG, and video are unsupported. Oversized or unavailable images produce placeholders. Animated WEBP uses its first frame. Complex documents may still need manual print review. Application code has no license pending the owner's choice; the bundled fonts retain their own licenses. Nothing was committed or published by Codex.

## Typography and package layout update

The current package is directly under `mdx_printkit/`, with no outer `src/` layer. Setuptools discovery is explicit, and the installed CLI works from outside the checkout. Application media processing, image dimensions, storyboard layout, and page margins were retained.

Seven original TrueType files are bundled: Source Sans Pro Regular, SemiBold, Bold, Italic, and IBM Plex Mono Regular, Bold, Italic. Their upstream licenses, pinned revisions, download URLs, and SHA-256 values are preserved in `mdx_printkit/fonts/`. The renderer copies the fonts into the temporary render directory, loads each CSS face, checks for failures, and awaits settled font layout before printing. Body text uses 11pt/1.5 typography, headings use bold/semibold, and code alone uses IBM Plex Mono.

Additional commands run:

```bash
.venv/bin/pip install -e '.[test]'
.venv/bin/python -m pytest -q --tb=short
.venv/bin/pip wheel . --no-deps --wheel-dir output/wheels
.venv/bin/pip install --no-index --no-deps --target output/wheel-install output/wheels/mdx_printkit-0.1.0-py3-none-any.whl
.venv/bin/python -I output/check-installed-wheel.py
.venv/bin/python -m mdx_printkit reference-input/motivation.mdx --output output/motivation-source-sans-pro.pdf --offline
.venv/bin/python -m mdx_printkit reference-input/extension-image.mdx --output output/extension-image.pdf
.venv/bin/python -m mdx_printkit reference-input/extension-image.mdx --output output/extension-image-offline.pdf --offline
```

The wheel check script is an ignored local smoke-test helper. It changed to the system temporary directory, imported the installed wheel's package explicitly, checked the archive contents, generated an offline typography specimen, and inspected the resulting embedded font streams. No public package was published.

Results:

- Full current suite: **60 passed**, no skips; the same five PyMuPDF/Python 3.14 deprecation warnings.
- Actual PDF text spans use `SourceSansPro-Regular`, `SourceSansPro-Semibold`, `SourceSansPro-Bold`, and `SourceSansPro-It`; code spans use `IBMPlexMono-Regular`, `IBMPlexMono-Bold`, and `IBMPlexMono-Italic`. Every used font has a nonempty embedded TrueType stream in the PDF.
- Deleting a local bundled font causes an explicit render failure, with no fallback PDF written.
- The wheel contains all seven fonts, both original licenses, CSS, and font provenance. It contains no reference content or outer `src/` directory. Its isolated installation successfully renders offline outside the source checkout.
- Updated motivation sample: **four pages, three images, zero warnings**; its actual text fonts are Source Sans Pro Regular and Bold.
- New `extension-image.mdx` sample, online and cached/offline: **11 pages, nine source image references, four animated GIFs, zero warnings**. The four GIFs each yield four distinct labeled frames, giving 21 embedded image occurrences including the five still images. Headings and media remain in source order, and images fit the print area.
- All four updated motivation pages and all 11 new-input pages were rasterized and visually reviewed. The font specimen was also inspected.
- Both private input checksums remain unchanged. The extension input's SHA-256 is `0e9e4537c8fab1521f178a8db4df2c82158a0d747ccef865c4af30eaaf50b387`.

Font changes naturally affect line wrapping. System fallbacks from the original Hugging Face stack remain available for glyphs absent from the bundled fonts.

## README and entry-point cleanup

The README was reduced from 113 to 46 lines; detailed usage, caching, typography, limits, and troubleshooting moved to `docs/USAGE.md`. CLI parsing and module startup now share `mdx_printkit/__main__.py`, removing `cli.py`. The installed console-script target was updated and refreshed with `.venv/bin/pip install -e . --no-deps`.

The full suite passed again: **60 tests**, including default output location, media processing, and embedded-font checks. Both the installed command and `.venv/bin/python -m mdx_printkit` displayed help successfully from outside the checkout. Documentation links and `git diff --check` passed. The default output remains `./output/<input-stem>.pdf` relative to the current working directory; no output-path behavior was changed.
