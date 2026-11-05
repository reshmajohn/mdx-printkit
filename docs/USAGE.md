# Usage and troubleshooting

For installation and common commands, start with the [README](../README.md).

## Files and output

Pass a local UTF-8 `.md` or `.mdx` path. Quote paths containing spaces. You can run the tool without activating the environment:

```bash
.venv/bin/python -m mdx_printkit file "my course/notes.mdx"
```

`mdx-printkit file notes.mdx` writes `notes.pdf` beside the source, regardless of your current shell directory. This command accepts `.md` and `.mdx` inputs. `--output` selects a relative or absolute `.pdf` path and creates missing parent directories. The original `mdx-printkit notes.mdx` invocation remains a shorthand for `file`.

To convert all `.mdx` files directly in a folder:

```bash
mdx-printkit folder "my course"
mdx-printkit folder "my course" --output "course prints" --paper a4 --gif-frames 6 --offline
```

Each input gets its own `<input-stem>.pdf` in the input folder by default. For `folder`, `--output` selects an output directory, created when needed. Relative overrides resolve from the current shell directory. Subfolders and `.md` files are excluded; `.MDX` extensions are accepted. Files run sequentially in filename order. If an individual conversion fails, the remaining files are still attempted; the final summary reports successes/failures and the command exits nonzero if any failed. Empty or invalid folders fail with an explanation. Colliding PDF destinations are rejected before conversion begins.

Both commands support `--paper {letter,a4}`, `--gif-frames N` (1–12), and `--offline`. A successful conversion replaces an existing destination; a failed render leaves it intact. Source files are never changed, and temporary rendering files are kept outside the input directory.

Missing individual images produce placeholders and warnings while conversion continues. Invalid arguments, unreadable input, browser failures, and broken bundled fonts return a nonzero exit status. The final summary counts successfully rendered image occurrences, animated GIF occurrences, and unique warnings.

## Images and GIFs

Local images resolve relative to the source document, including paths with URL-escaped spaces. Remote HTTP(S) images are downloaded before rendering. PNG, JPEG, WEBP, and GIF contents are verified regardless of filename; ordinary images honor EXIF orientation.

Supported forms include:

```md
![A diagram](images/diagram.png)

<div class="flex justify-center"><img src="images/diagram.png" alt="A diagram"></div>

![Movement](images/movement.gif)

[Watch movement](https://example.com/movement.gif?download=1)
```

Animated GIFs become up to four distinct frames in temporal order, normally in a 2x2 grid. Sampling uses elapsed animation time and respects transparency and disposal. Repeated visual states are deduplicated. `--gif-frames N` accepts 1–12; with one frame, the animation's midpoint is used. Single-frame GIFs display as ordinary images. Remote storyboards retain a clickable source link. Animated WEBP uses its first frame.

## Cache and offline mode

Downloads persist in `~/.cache/mdx-printkit/`, keyed by URL including query parameters. Repeated references share downloaded and rendered assets. Cache entries remain until you remove them; an online run refreshes a corrupt entry.

`--offline` makes no HTTP requests. Cached and local images render normally; uncached images receive placeholders. Completed PDFs embed their images and used fonts, so viewing and printing require no network access.

## Typography

Body text is Source Sans Pro at 11pt with 1.5 line spacing. Headings use bold or semibold at 21/16/13pt. Regular, semibold, bold, and italic faces are bundled locally. Code blocks and inline code use IBM Plex Mono.

CSS `@font-face` rules load packaged fonts without a system installation or runtime download. The renderer checks every face and waits for font layout before printing; missing or corrupt fonts cause an explicit error. Used fonts are embedded as PDF subsets. Glyphs outside their coverage may use system fonts from the original Hugging Face fallback stack.

Both families retain their SIL Open Font License 1.1 and copyright notices. See [font provenance and licenses](../mdx_printkit/fonts/README.md) for pinned revisions, download URLs, and checksums. Application code has no license pending the owner's choice.

## Limits and document safety

Markdown headings, paragraphs, lists, blockquotes, tables, strikethrough, links, code, and common HTML are supported. Document HTML is sanitized: scripts, event handlers, arbitrary CSS, and embedded pages are removed. MDX imports, exports, expressions, and custom components are never evaluated; recognizable unsupported syntax gets a warning and readable text or a placeholder.

Remote downloads allow public HTTP(S) destinations only. Private networks, localhost, URL credentials, and schemes such as `file:` or `data:` are blocked. HTTP requests bypass proxy environment variables. Ordinary hyperlinks are not downloaded. Local paths may point outside the source directory but must contain supported raster images. See the [technical design](TECHNICAL_DESIGN.md) for the download and rendering boundaries.

| Resource | Limit |
| --- | --- |
| Image file | 25 MB, 40 megapixels |
| HTTP requests | 100 per document, including redirects |
| Redirects | Five per asset |
| Socket timeout | 15 seconds |
| GIF decoding | 500 frames / 250 million decoded pixels |

Oversized or unavailable media receive placeholders. SVG, video, remote webpages, authenticated image downloads, and full React/JSX rendering are unsupported. Complex tables and unusually large figures may need manual print review.

## Troubleshooting

| Problem | Action |
| --- | --- |
| Command not found | Activate `.venv`, or use `.venv/bin/python -m mdx_printkit`. |
| Chromium missing | Run `.venv/bin/python -m playwright install chromium`. On Linux, use `install --with-deps chromium` if system libraries are missing. |
| Bundled fonts missing or unable to load | Reinstall from a complete checkout with `.venv/bin/pip install -e .`, or reinstall the wheel. Keep the packaged `fonts/` directory intact. |
| Image unavailable | Read the warning for its path, HTTP status, timeout, format, size limit, or blocked address. Use a local raster copy for authenticated or private-network images. |
| Stale remote image | Remove its cache entry, or clear the tool's cache, and rerun online. |
| Unexpected MDX output | Replace custom components with ordinary Markdown/HTML. Fenced code examples remain literal. |

## Private reference checks

When the reference inputs are available locally:

```bash
mdx-printkit file reference-input/motivation.mdx --output output/motivation.pdf
mdx-printkit file reference-input/motivation.mdx --output output/motivation-offline.pdf --offline
mdx-printkit folder reference-input --output output/reference-pdfs --offline
```

Inputs, downloaded course assets, caches, virtual environments, and generated PDFs are ignored by Git. Bundled open-source fonts and their licenses are included deliberately. The [acceptance criteria](ACCEPTANCE_TESTS.md) describe the synthetic tests; the [validation record](VALIDATION.md) records completed checks.
