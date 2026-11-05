# MDX PrintKit

Turn a local `.md` or `.mdx` file into a printable PDF with embedded images. Animated GIFs become a compact storyboard of up to four distinct frames, including GIFs written as direct Markdown links.

This is a local Python CLI. It supports Markdown and common HTML; it does not run React, MDX JavaScript, or scripts from documents.

PDF text and headings use bundled **Source Sans Pro**, with Regular (400), SemiBold (600), Bold (700), and Italic (400) faces. Body text is 11pt with 1.5 line spacing; headings keep their existing 21/16/13pt sizes. Captions, tables, and placeholders use the same text family. The fallback stack matches the Hugging Face course, including its system and emoji fonts. Code blocks and inline code use bundled **IBM Plex Mono**.

Fonts load from local files through CSS `@font-face`. No system installation or font download is needed during conversion. The renderer loads and checks every bundled face before printing, and fails with an actionable error if one is missing or corrupt. It waits for font layout to settle before producing the PDF. Fonts used by the document are embedded as PDF subsets. Glyphs outside these fonts' coverage may use the original stack's system fallbacks.

Both font families retain their SIL Open Font License 1.1 and copyright notices. [Font sources, pinned revisions, checksums, and licenses](mdx_printkit/fonts/README.md) are bundled with the package.

## Install

Use Python 3.11 or newer. From this repository, create the environment if it does not already exist:

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/python -m playwright install chromium
```

Then activate it to use the command:

```bash
source .venv/bin/activate
mdx-printkit --help
mdx-printkit path/to/notes.mdx
```

On Linux, Chromium may also need system libraries; use `.venv/bin/python -m playwright install --with-deps chromium` if Playwright reports missing dependencies. Installation downloads packages and a browser; conversion needs network access only for uncached remote images.

## Convert a document

```bash
mdx-printkit "./my course/notes.mdx"
mdx-printkit notes.md --output "./prints/Notes.pdf" --paper a4
mdx-printkit notes.mdx --gif-frames 6
mdx-printkit notes.mdx --offline
```

The default output is `./output/<input-stem>.pdf`, relative to your current shell directory. `--output` accepts a relative or absolute `.pdf` path. Parent directories are created automatically. A successful conversion replaces an existing destination; a failed render leaves it intact. The input is never changed. You can also run `.venv/bin/python -m mdx_printkit ...` without activating the environment.

| Option | Behavior |
| --- | --- |
| `--output PATH` | Choose the PDF destination |
| `--paper letter` / `--paper a4` | US Letter by default |
| `--gif-frames N` | Maximum distinct frames, from 1 to 12; default 4 |
| `--offline` | Use local images and cached remote images without HTTP requests |
| `--version` | Print the installed version |

Image failures produce a labeled placeholder and a warning containing the original path or URL. They do not prevent PDF generation. Invalid input, options, or browser failures return a nonzero exit status. The final summary counts successfully rendered image occurrences, animated GIF occurrences, and unique warnings.

## Supported content

Headings, paragraphs, lists, blockquotes, fenced code, inline code, tables, strikethrough, ordinary links, and common HTML are supported. Local image paths resolve relative to the input document, including URL-escaped spaces. PNG, JPEG, WEBP, and GIF contents are verified before use, regardless of filename. EXIF orientation is applied to ordinary images.

These forms all work:

```md
![A diagram](images/diagram.png)

<div class="flex justify-center"><img src="images/diagram.png" alt="A diagram"></div>

![Movement](images/movement.gif)

[Watch movement](https://example.com/movement.gif?download=1)
```

GIF frames are composited with their transparency/disposal rules, sampled across elapsed animation time, deduplicated by pixels, and placed in temporal order. Four frames use a 2x2 grid. If sample times repeat the same visual state, other distinct states fill the remaining slots. With `--gif-frames 1`, the frame at the animation's midpoint is used. Single-frame GIFs display as ordinary images. Remote storyboards retain a small clickable source link.

Downloaded images are cached in `~/.cache/mdx-printkit/`, keyed by URL including query parameters. Repeated references share the same download and render assets. Cache entries persist until you remove them; rerunning online refreshes a corrupt entry. An unavailable uncached image becomes a placeholder in offline mode. Completed PDFs contain the image bytes and can be opened without network access.

## Safety and limits

Document HTML is sanitized before rendering. Scripts, event handlers, arbitrary CSS, embedded pages, and unsafe URL schemes are removed. Imports, exports, JavaScript expressions, and custom MDX components are never evaluated; recognizable unsupported syntax receives a warning, with readable text or a component placeholder retained. Full JSX parsing, React widgets, and source stylesheet reproduction are outside v1.

The downloader follows at most five redirects per asset, checks every destination's DNS results, and connects to the validated public IP while preserving HTTPS certificate checks. Private networks, localhost, embedded URL credentials, and `file:`, `data:`, and other URL schemes are blocked. HTTP requests bypass proxy environment variables. Ordinary non-image links are not downloaded. Local image paths may refer outside the source directory, but must contain a supported raster image. Treat source files as untrusted content and review which local images they reference.

Limits are 25 MB per image, 40 megapixels per image, 100 HTTP requests per document (including redirects), a 15-second socket timeout, and 500 frames / 250 million decoded pixels per GIF. Very large media receive placeholders. Images are downscaled for print; SVG, video, remote webpages, and animated WEBP storyboards are unsupported. Animated WEBP uses its first frame. Complex tables and unusually large figures may need manual print review; Chromium treats page-break avoidance as a layout preference.

## Development and verification

```bash
.venv/bin/pip install -e '.[test]'
.venv/bin/python -m playwright install chromium
.venv/bin/python -m pytest
```

`requirements.txt` lists runtime and verification dependencies. Tests generate their own images and GIFs and use an HTTP server on localhost with the public-address check overridden only inside those tests. They exercise caching, offline mode, redirects, failure placeholders, MDX handling, GIF timing/compositing, CLI errors, and PDF text/image embedding. PDF tests skip if Chromium is not installed; the remaining tests require no browser or public network.

Typography tests inspect the actual fonts attached to extracted PDF text and require embedded TrueType streams for all four Source Sans Pro faces and IBM Plex Mono's regular, bold, and italic faces. A missing-font test verifies that rendering cannot silently fall back.

The Python package is directly under `mdx_printkit/`, without an outer `src/` directory. Its modules separate the CLI, conversion, document transformation, assets/cache, GIF extraction, PDF rendering, and bundled typography. `tests/` contains synthetic fixtures and checks; `docs/` contains the specifications and [validation record](docs/VALIDATION.md). Package discovery is explicit so input files and generated output cannot become part of a wheel.

For the private reference input, when available:

```bash
mdx-printkit reference-input/motivation.mdx --output output/motivation.pdf
mdx-printkit reference-input/motivation.mdx --output output/motivation-offline.pdf --offline
mdx-printkit reference-input/extension-image.mdx --output output/extension-image.pdf
```

The reference input, downloaded course assets, environment, caches, and generated PDFs are ignored by Git. Keep course content outside the public repository. The bundled open-source fonts and their licenses are included deliberately. Application code has no license pending the owner's choice; the font licenses are preserved independently.

## Troubleshooting

- **Chromium missing:** run `.venv/bin/python -m playwright install chromium` in the same environment as the tool.
- **Bundled fonts missing or unable to load:** reinstall with `.venv/bin/pip install -e .` from a complete checkout, or reinstall the wheel. Keep the packaged `fonts/` directory intact; installing a system font is unnecessary.
- **Image unavailable:** inspect the warning for its path, HTTP status, timeout, format, size limit, or blocked network address. Use a local raster copy for authenticated or private-network images.
- **Unexpected MDX output:** simplify custom components to ordinary Markdown/HTML. Code examples inside fences remain literal.
- **Command not found:** activate `.venv`, or use `.venv/bin/python -m mdx_printkit`.
- **Stale remote image:** remove its cache entry (or clear the tool's cache) and run online again. Offline runs never refresh downloads.
