# MDX PrintKit

Convert local Markdown or MDX files into printable PDFs with embedded images, one file or a folder at a time. Animated GIFs become storyboards of up to four distinct frames. PDFs default to bundled Source Sans Pro for text and IBM Plex Mono for code, and can be opened offline.

## Install

Requires Python 3.11 or newer and Playwright Chromium on Windows, macOS, or a supported Linux distribution. From the repository, create and activate an environment:

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Then, on any platform:

```bash
python -m pip install -e .
python -m playwright install chromium
```

Reuse an existing `.venv` if available. See [platform setup](docs/USAGE.md#platform-setup) for Linux libraries and running without activation.

## Use

```bash
mdx-printkit file "path/to/notes.mdx"
mdx-printkit file notes.md --output "prints/Notes.pdf" --paper a4 --font georgia
mdx-printkit folder "path/to/course"
mdx-printkit folder "path/to/course" --output prints --paper a4 --gif-frames 6 --offline
```

PDFs go beside their source files: `course/notes.mdx` becomes `course/notes.pdf`. `file --output` selects a PDF path; `folder --output` selects a directory. Folder conversion processes `.mdx` files directly in that folder, with one PDF per file. Source files stay unchanged.

Both commands default to US Letter and four GIF frames. `--gif-frames` accepts 1–12; `--offline` uses local images and cached downloads only. `--font` selects Source Sans Pro (default) or one of six system fonts; unavailable choices warn and fall back to Source Sans Pro. Run `mdx-printkit file --help` or `mdx-printkit folder --help` for all choices.

## What it supports

Ordinary Markdown, tables, code, common HTML, LaTeX equations (`$...$` and `$$...$$`), and PNG/JPEG/WEBP/GIF images. Equations use a bundled math font and render offline. Local image paths resolve relative to the source document. GIF images and direct Markdown links to `.gif` files both become storyboards. Missing images receive visible placeholders and warnings.

React components and MDX JavaScript are not executed. SVG, video, and authenticated image downloads are unsupported. See the [usage guide](docs/USAGE.md) for image examples, caching, limits, and troubleshooting.

## Development

```bash
python -m pip install -e '.[test]'
python -m pytest
```

Run these in the activated environment. Tests use synthetic local fixtures; PDF tests require Chromium. CI is configured for Windows, Linux, and macOS on Python 3.11 and 3.14. Application code lives in `mdx_printkit/`, with CLI startup in `__main__.py`.

See the [technical design](docs/TECHNICAL_DESIGN.md), [validation record](docs/VALIDATION.md), and [font sources and licenses](mdx_printkit/fonts/README.md).
