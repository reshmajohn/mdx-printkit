# MDX PrintKit

Convert a local Markdown or MDX file into a printable PDF with embedded images. Animated GIFs become storyboards of up to four distinct frames. PDFs use bundled Source Sans Pro for text and IBM Plex Mono for code, and can be opened offline.

## Install

Requires Python 3.11 or newer. From the repository:

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/python -m playwright install chromium
source .venv/bin/activate
```

If `.venv` already exists, skip the first command.

## Use

```bash
mdx-printkit "path/to/notes.mdx"
mdx-printkit notes.md --output "prints/Notes.pdf" --paper a4
mdx-printkit notes.mdx --gif-frames 6
mdx-printkit notes.mdx --offline
```

By default, PDFs go to `./output/<input-stem>.pdf`, relative to the directory where you run the command. `--output` selects another destination. The source file stays unchanged.

US Letter and four GIF frames are the defaults. `--gif-frames` accepts 1–12; `--offline` uses local images and cached downloads only. Run `mdx-printkit --help` for all options.

## What it supports

Ordinary Markdown, tables, code, common HTML, and PNG/JPEG/WEBP/GIF images. Local image paths resolve relative to the source document. GIF images and direct Markdown links to `.gif` files both become storyboards. Missing images receive visible placeholders and warnings.

React components and MDX JavaScript are not executed. SVG, video, and authenticated image downloads are unsupported. See the [usage guide](docs/USAGE.md) for image examples, caching, limits, and troubleshooting.

## Development

```bash
.venv/bin/pip install -e '.[test]'
.venv/bin/python -m pytest
```

Tests use synthetic local fixtures; PDF tests require Playwright Chromium. Application code lives in `mdx_printkit/`, with CLI startup in `__main__.py`.

See the [technical design](docs/TECHNICAL_DESIGN.md), [validation record](docs/VALIDATION.md), and [font sources and licenses](mdx_printkit/fonts/README.md). Keep reference inputs, downloaded course assets, and generated PDFs out of Git.
