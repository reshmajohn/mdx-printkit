# Technical design — MDX PrintKit v1

## Stack and approach
Use Python 3.11+ and an installable `pyproject.toml` with a console-script entry point `mdx-printkit = mdx_printkit.__main__:main`. Keep dependencies light and maintained:

- `markdown-it-py` for Markdown parsing/rendering with HTML enabled for the supported HTML subset; optionally enable table/strikethrough features if necessary.
- `beautifulsoup4` for DOM-level asset transformations and tolerant handling of real-world HTML such as non-self-closing `<img>` tags.
- `nh3` or equivalent maintained sanitizer for untrusted HTML: allow only print-relevant tags/attributes, remove unsafe tags/events/CSS/JS while retaining text.
- `httpx` or `requests` for remote downloads with timeouts, redirects and explicit error handling.
- `Pillow` for GIF inspection, frame compositing/conversion and PNG output.
- `playwright` with installed **Chromium** to print local HTML to a PDF (`page.pdf`).
- `pytest` for tests, `pypdf` optionally in test dependencies for structural PDF validation.

Pin appropriate compatible dependency ranges in `pyproject.toml` (avoid unreviewed strict old versions). If a library detail differs from this sketch, use its current documented API.

## Processing pipeline
1. **CLI and source:** `file` validates a local `.md`/`.mdx` path and defaults to a PDF beside it. `folder` enumerates direct `.mdx` files in filename order, validates output destinations, and invokes the same conversion pipeline sequentially. Its `--output` override is a directory; each file keeps its stem. Both commands share paper, GIF frame count, and offline options. Individual folder failures are reported while remaining files continue. For each file, read UTF-8 and build a temporary working directory for rendering.
2. **Parse:** Markdown -> HTML using `markdown-it-py` with raw HTML support. Do NOT regex-rewrite the raw Markdown; this would corrupt code fences or literal examples. Support embedded HTML as actual HTML.
3. **Normalize/sanitize:** parse rendered HTML into a DOM. Remove script/iframe/style/event-handler/unsafe URL content and detect obvious MDX-only code or components; preserve ordinary text with warnings. Keep only sanitized markup in the printable document.
4. **Resolve assets:** walk image tags and direct links with a `.gif` path. Download supported HTTP(S) raster assets into a persistent cache; resolve relative local files against input file parent. Do not dereference arbitrary external hyperlinks. MIME sniff/verify image contents and use bounded downloads.
5. **Transform GIFs:** decode animated images, sample up to N temporally distributed, composited frames; write PNGs under a temporary render assets directory; replace image or direct GIF link with a `figure.gif-storyboard` containing frames and labels. Preserve a human-readable indication of the original hyperlink/alt text.
6. **Build HTML:** wrap sanitized content and rewritten relative, local asset paths in one minimal print template + local CSS; create a local HTML file in the same working tree as the copied/converted assets. Copy the packaged fonts into that temporary tree for local `@font-face` loading. Permit only local fonts in the document's content security policy.
7. **PDF:** launch Playwright Chromium, navigate to the local `file://` HTML path, use print media, wait for local image decoding, explicitly load and validate every bundled font face, await `document.fonts.ready`, and print with PDF format Letter/A4 and consistent margins. Missing/corrupt fonts are fatal instead of silently falling back. No external page resources are needed or permitted at render time.
8. **Report:** save finished PDF to requested path, print a summary/warnings; clean temporary files, leave persistent cache alone.

Prefer clean small functions and dataclasses/typed results for warnings/asset metadata. The CLI and module startup share `__main__.py`. Conversion orchestration, document transformation, asset handling, GIF processing, rendering, and typography each have one module; shared exceptions stay in `errors.py` to avoid circular imports.

The package now lives directly at `mdx_printkit/`, with explicit setuptools discovery. `typography.py` copies the bundled faces into each isolated render directory. Package data includes the print CSS, seven unmodified TrueType font files, both font licenses, and font provenance/checksums. The CLI entry point and Python import name are unchanged.

## Asset fetching/cache
- Cache directory: user-specific standard cache (`~/.cache/mdx-printkit` on macOS/Linux is acceptable for v1; platform-specific cache via `platformdirs` is nicer). Use a URL hash for names so query strings/duplicate basenames do not collide.
- On each run, load from cache when available; `--offline` must never make HTTP requests. Download missing URLs only if online.
- Support redirects from Hugging Face `/resolve/...` URLs. Respect reasonable connect/read timeouts; limit per-file download size (e.g. 25 MB) and number of requests; handle 4xx/5xx gracefully.
- Accept only verified supported image types, not arbitrary downloaded HTML. Handle paths with spaces and URL-escaped characters.
- The file input may contain user-authored links; never execute JavaScript or fetch `file://`, `data:`, `javascript:` or internal/private-network URLs as remote resources. Avoid exposing sensitive local files by restricting inclusion to supported image formats and sensible file sizes.
- Use the same resolved/cached file for repeated references to one asset in a document.
- Do not require source images to remain accessible when opening the final PDF. The PDF has to be self-contained.

## GIF temporal selection and layout
- Read GIF logical frames via Pillow; ensure each PNG represents the *visually composited* frame, not an isolated transparent delta. GIF disposal and transparency are important; test rather than assume decoder behavior.
- Respect `duration` metadata and the animation's time axis. For N >= 2 pick representative times spanning the sequence, ideally including the opening and near-final visual states; when durations are zero/missing, use a sane default.
- Deduplicate identical output frames using hashes of fully composited pixel data (not source frame bytes). For very large GIFs, impose safe bounds and avoid writing hundreds of intermediate full-resolution files.
- Downscale extremely large frames sensibly for print while retaining readable annotations; maintain aspect ratio.
- Label output `Frame 1/N` ... `Frame N/N` with a caption such as "Animation frames" and a small source hyperlink. For a one-frame/static GIF, use a normal figure.
- A direct Markdown `.gif` link should become a storyboard (not just remain a link); normal document hyperlinks remain normal links.

## Print CSS
- White page, near-black text, Source Sans Pro at 11pt/1.5; heading sizes 21/16/13pt with 700 weight for H1/H2 and 600 for H3-H6. Regular, semibold, bold, and italic use separate bundled font files. Code alone uses IBM Plex Mono at 9pt. Captions and placeholders inherit Source Sans Pro.
- Retain the exact Hugging Face text fallback stack: `"Source Sans Pro", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", "Noto Sans", Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji"`. System fallbacks may supply glyphs outside the bundled fonts' coverage.
- Use `@page` margins ~0.6–0.7 in and Playwright PDF's `format` setting for Letter/A4; do not accidentally conflict on paper sizing.
- Responsive image sizing (`max-width: 100%; height: auto`), centered images, avoid overflow.
- Use `break-after: avoid` on headings and `break-inside: avoid` on figures/storyboards where feasible; storyboards should not cause huge blank gaps.
- Code blocks use a subtle gray background, legible monospace and safe wrapping; no dark background/inverted pages. Tables may wrap but should not clip.
- Make ordinary links visibly distinguishable in grayscale and clickable in PDF. Do not print full lengthy URLs on their own unless they already appear in source.

## MDX boundary and safety
This is a **printable Markdown + common HTML** converter, not a full MDX runtime. `reference-input/motivation.mdx` is well within the supported subset. For `import`, `export`, JSX components (especially capitalized tags), and JS expressions, do not run code. Warn clearly and preserve readable text or display an explicit `[Unsupported MDX component: Name]` placeholder. Do not silently turn a whole section blank.

Sanitize all document-origin HTML before injecting it into the browser. Do not enable network access in the browser renderer; all remote assets should already be fetched through the controlled asset pipeline. Never expose arbitrary user-provided `file://` links as images.

## Developer ergonomics
- Create `README.md` with local setup, virtualenv, `pip install -e .`, `python -m playwright install chromium`, commands, support/limitations, and troubleshooting.
- Create `.gitignore` that excludes `reference-input/`, output, cache, PDFs, venvs, and developer-local files.
- Tests should run without depending on public servers by using generated fixture images and an optional local HTTP test server. Real Hugging Face download is an optional smoke test, not required for CI.
- Provide CLI help with sensible defaults and clear examples.
