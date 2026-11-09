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

## Single-file destinations and folder conversion

The default is now `<source-directory>/<input-stem>.pdf`. `mdx-printkit file PATH` converts one Markdown/MDX document; `mdx-printkit folder DIR` converts each direct `.mdx` file into a separate PDF in that folder. The folder `--output` override is a directory. Both commands share paper size, GIF frame count, and offline options. The original single-file invocation, including options before the path, remains supported.

`.venv/bin/python -m pytest -q --tb=short` passed **75 tests** with no skips and the same five PyMuPDF/Python 3.14 deprecation warnings. New actual-PDF checks cover default destinations independent of shell directory; `.mdx`/`.MDX` selection without nested folders or `.md`; custom folder output; A4 and four/six GIF frames; original input preservation; and continuing after a bad UTF-8 document while retaining its previous PDF. Empty/invalid folders and output collisions are checked before conversion. Both installed command help screens work outside the checkout; documentation links and `git diff --check` pass. Both private reference MDX checksums are unchanged.

## Font choices — November 9, 2026

Both `file` and `folder` now accept `--font`, with `source-sans-pro` as the unchanged bundled default. The six system alternatives are `arial`, `helvetica`, `verdana`, `georgia`, `times-new-roman`, and `palatino`; both command help screens list every choice. Body text, headings, captions, and placeholders follow the selection. Code continues to use bundled IBM Plex Mono.

System font faces are loaded by their local full/PostScript names through CSS `@font-face`. No OS font files are downloaded, copied, or added to the package. Required regular, bold/semibold, and italic faces are checked before PDF generation, with explicit errors for unavailable families or styles. Source Sans Pro's original CSS and fallback stack are retained when no alternative is selected.

Verification commands:

```bash
.venv/bin/python -m pytest tests/test_typography.py tests/test_cli.py tests/test_pdf.py -k 'font or help' -q --tb=short
.venv/bin/python -m pytest -q --tb=short
.venv/bin/mdx-printkit file --help
.venv/bin/mdx-printkit folder --help
git diff --check
```

The focused checks passed 19 tests. The full suite passed **93 tests**, with no skips and the same five PyMuPDF/Python 3.14 deprecation warnings. All six system fonts were available on this Mac: generated PDFs use their expected regular, bold, and italic PostScript names with embedded font programs. Semibold headings use each system family's bold face. Code text remains IBM Plex Mono. A simulated unavailable font fails explicitly and leaves an existing PDF unchanged. Folder option propagation, invalid font names, default font embedding, documentation links, and both reference-input checksums were also verified. System-family PDF tests skip only when that family is absent on the test OS.

## Windows, Linux, and macOS portability — November 9, 2026

Reviewed every application module, packaging configuration, setup instructions, and synthetic test fixtures for platform assumptions. Changes include:

- Missing system fonts/styles now produce a visible warning and a successful PDF using bundled Source Sans Pro. Both file and folder commands preserve IBM Plex Mono for code. Missing bundled fallback/code fonts remain fatal, preserving an existing destination.
- Windows drive-letter paths are classified before URL schemes; local backslashes and URL escaping are normalized, and colons are safely escaped through HTML sanitization. Relative references and native absolute paths are exercised on each host OS. UNC/network references remain blocked. Foreign drive paths get an image warning/placeholder rather than pretending they are valid local paths.
- Renderer file URLs use Python's native `url2pathname` conversion before containment checks. Tests cover Unicode, spaces, percent/hash characters, local authorities, and blocked paths outside the temporary directory.
- Caches use `platformdirs>=4,<5` native user-cache conventions. Existing entries at `~/.cache/mdx-printkit` remain readable, including offline. Explicit cache overrides remain isolated. No old cached data was moved or deleted.
- Font fallback avoids rewriting files already open in Chromium, which matters for Windows file sharing. Browser diagnostics distinguish a missing executable from missing Linux libraries and use environment-neutral setup commands.
- README/usage setup covers Windows PowerShell and macOS/Linux, including direct virtualenv interpreter paths when activation is unavailable. Existing closed-tempfile/atomic-replacement handling is retained. Symlink-only tests skip if the OS denies creating symlinks; unrelated HTTP checks no longer depend on a 50 ms timeout.

Commands run in this macOS checkout:

```bash
.venv/bin/pip install -e '.[test]'
.venv/bin/python -m pytest tests/test_pdf.py -k 'unavailable_system_font_warns' -vv -s -o faulthandler_timeout=15 --tb=short
.venv/bin/python -m pytest -q --tb=short -o faulthandler_timeout=30
.venv/bin/pip check
git diff --check
```

The final full run passed **109 tests**, no skips, in 15.91 seconds, with the same five PyMuPDF/Python 3.14 deprecation warnings. Both fallback PDF checks passed with actual embedded Source Sans Pro and IBM Plex Mono font identities. The dependency check reported no broken requirements; documentation links and whitespace checks passed. The two original reference MDX checksums remain unchanged. No private course conversion or live image download was needed for this update.

`.github/workflows/tests.yml` configures native Ubuntu 24.04, Windows, and macOS jobs for Python 3.11 and 3.14, including Chromium and Linux libraries. Those CI jobs have **not been run from this session**; the completed results above are macOS results plus platform-path unit checks. This is not a claim that Windows/Linux were executed locally. Runtime support follows Playwright's supported desktop OS versions and architectures; Python packages alone do not supply Chromium or required OS libraries.
