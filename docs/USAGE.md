# Usage and troubleshooting

For installation and common commands, start with the [README](../README.md).

## Platform setup

Windows, macOS, and Linux use the same CLI and conversion pipeline. Python 3.11+ and the Python packages are required, along with the matching Playwright Chromium browser. Linux may also need OS libraries. See [Playwright's supported operating systems](https://playwright.dev/python/docs/intro#system-requirements); an arbitrary OS with Python alone is not sufficient for browser-based PDF rendering.

After activating your virtual environment, `python -m pip install -e .` and `python -m playwright install chromium` work on all three platforms. On a supported Linux distribution, install missing browser libraries with `python -m playwright install --with-deps chromium` (system package installation may require administrator privileges).

Activation is optional. Use the environment's interpreter directly:

| Platform | Python in this checkout |
| --- | --- |
| Windows PowerShell / Command Prompt | `.\.venv\Scripts\python.exe` |
| macOS / Linux | `.venv/bin/python` |

For example, if PowerShell does not permit the activation script:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m mdx_printkit file "C:\Courses\notes.mdx"
```

Use the same interpreter for installation, browser setup, and conversion. CI is configured to run native Windows, Ubuntu, and macOS tests on Python 3.11 and 3.14. A local test run verifies only its host OS; see the [validation record](VALIDATION.md) for results actually run.

## Files and output

Pass a local UTF-8 `.md` or `.mdx` path. Quote paths containing spaces. In an activated environment:

```bash
python -m mdx_printkit file "my course/notes.mdx"
```

`mdx-printkit file notes.mdx` writes `notes.pdf` beside the source, regardless of your current shell directory. This command accepts `.md` and `.mdx` inputs. `--output` selects a relative or absolute `.pdf` path and creates missing parent directories. The original `mdx-printkit notes.mdx` invocation remains a shorthand for `file`.

To convert all `.mdx` files directly in a folder:

```bash
mdx-printkit folder "my course"
mdx-printkit folder "my course" --output "course prints" --paper a4 --gif-frames 6 --offline
```

Each input gets its own `<input-stem>.pdf` in the input folder by default. For `folder`, `--output` selects an output directory, created when needed. Relative overrides resolve from the current shell directory. Subfolders and `.md` files are excluded; `.MDX` extensions are accepted. Files run sequentially in filename order. If an individual conversion fails, the remaining files are still attempted; the final summary reports successes/failures and the command exits nonzero if any failed. Empty or invalid folders fail with an explanation. Colliding PDF destinations are rejected before conversion begins.

Both commands support `--paper {letter,a4}`, `--gif-frames N` (1–12), `--font`, and `--offline`. A successful conversion replaces an existing destination; a failed render leaves it intact. Source files are never changed, and temporary rendering files are kept outside the input directory.

Missing individual images produce placeholders and warnings while conversion continues. Invalid arguments, unreadable input, browser failures, and broken bundled fonts return a nonzero exit status. The final summary counts successfully rendered image occurrences, animated GIF occurrences, and unique warnings.

## Images and GIFs

Local images resolve relative to the source document, including paths with URL-escaped spaces and native Windows separators. Absolute drive-letter image paths are supported on Windows. For portable documents, prefer relative paths with forward slashes; a Windows drive path cannot be resolved on macOS/Linux and receives a warning/placeholder. Remote HTTP(S) images are downloaded before rendering. PNG, JPEG, WEBP, and GIF contents are verified regardless of filename; ordinary images honor EXIF orientation.

Supported forms include:

```md
![A diagram](images/diagram.png)

<div class="flex justify-center"><img src="images/diagram.png" alt="A diagram"></div>

![Movement](images/movement.gif)

[Watch movement](https://example.com/movement.gif?download=1)
```

Animated GIFs become up to four distinct frames in temporal order, normally in a 2x2 grid. Sampling uses elapsed animation time and respects transparency and disposal. Repeated visual states are deduplicated. `--gif-frames N` accepts 1–12; with one frame, the animation's midpoint is used. Single-frame GIFs display as ordinary images. Remote storyboards retain a clickable source link. Animated WEBP uses its first frame.

## Equations

Use `$...$` for inline math and `$$...$$` for centered display equations. For example:

```latex
An inline equation: $S \times S$.

$$\frac{x^2}{\sqrt{y}}$$

$$
\begin{align*}
L_{\text{coord}} &= \sum_{b=0}^{B} x_b^2 \\
L_{\text{class}} &= y^2
\end{align*}
$$
```

Fractions, roots, subscripts/superscripts, sums, accents, common symbols, `align`/`align*`, and `cases` are supported. Double-dollar equations also work within a paragraph. Escape literal dollars as `\$`; fenced and inline code stay literal. Avoid spaces immediately inside single-dollar delimiters.

The Python parser converts TeX notation to MathML, which Chromium typesets using bundled STIX Two Math. Equations and their font work offline for both commands, independently of `--font`. No TeX installation, Node.js, document JavaScript, or external math service is needed. The font is checked before printing and embedded in the PDF.

This supports the converter's TeX math subset, not a complete LaTeX document engine. Custom macros, packages, file inclusion, and TeX hyperlinks are unsupported. Recognized formulas that cannot be converted safely produce a warning and retain their TeX source visibly. Delimiters must be paired; use `align`/`aligned` line breaks for expressions too long for a page. Equations are rendered as authored; mathematical errors in the source are not corrected.

## Cache and offline mode

Downloads use the OS-specific user cache, selected by [platformdirs](https://platformdirs.readthedocs.io/en/latest/api.html#platformdirs.user_cache_path):

| Platform | Usual cache location |
| --- | --- |
| Windows | `%LOCALAPPDATA%\mdx-printkit\Cache` |
| macOS | `~/Library/Caches/mdx-printkit/` |
| Linux | `$XDG_CACHE_HOME/mdx-printkit/`, or `~/.cache/mdx-printkit/` |

URLs, including query parameters, determine cache keys. Repeated references share downloaded and rendered assets. Cache entries remain until you remove them; an online run refreshes a corrupt entry. The previous `~/.cache/mdx-printkit/` location remains readable when using the default cache, including offline. To force a fresh download of an older entry, remove it from both locations if present. The Python API's explicit `cache_dir` override uses only that directory.

`--offline` makes no HTTP requests. Cached and local images render normally; uncached images receive placeholders. Completed PDFs embed their images and used fonts, so viewing and printing require no network access.

## Typography

Body text defaults to Source Sans Pro at 11pt with 1.5 line spacing. Headings use bold or semibold at 21/16/13pt. Its regular, semibold, bold, and italic faces are bundled locally. `--font` changes body text and headings for either command; code blocks and inline code always use bundled IBM Plex Mono.

| `--font` value | Family | Source |
| --- | --- | --- |
| `source-sans-pro` | Source Sans Pro (default) | Bundled with the tool |
| `arial` | Arial | Installed system font |
| `helvetica` | Helvetica | Installed system font |
| `verdana` | Verdana | Installed system font |
| `georgia` | Georgia | Installed system font |
| `times-new-roman` | Times New Roman | Installed system font |
| `palatino` | Palatino | Installed system font |

```bash
mdx-printkit file notes.mdx --font times-new-roman
mdx-printkit folder course --font arial --output prints
```

System fonts use local CSS `@font-face` sources, with no copying, redistribution, or downloads of OS font files. Availability is checked at runtime, rather than assumed from the OS name. If the chosen family or a required regular/bold/italic style is unavailable, the tool prints a warning and uses bundled Source Sans Pro for the document. Both file and folder conversions continue successfully. Semibold headings use the system font's bold face when that family is available.

The renderer checks the selected text faces and bundled code faces, then waits for font layout before printing. Missing/corrupt bundled fonts remain fatal because they are required for dependable output. Used fonts are embedded in the PDF. Fonts can change line wrapping and page counts. Glyphs outside a family's coverage may use system fallbacks; the default Source Sans Pro option retains the original Hugging Face fallback stack.

The bundled Source Sans Pro, IBM Plex Mono, and STIX Two Math fonts retain their SIL Open Font License 1.1 and copyright notices. See [font provenance and licenses](../mdx_printkit/fonts/README.md) for pinned revisions, download URLs, and checksums. Application code has no license pending the owner's choice.

## Limits and document safety

Markdown headings, paragraphs, lists, blockquotes, tables, strikethrough, links, code, and common HTML are supported. Document HTML is sanitized: scripts, event handlers, arbitrary CSS, and embedded pages are removed. MDX imports, exports, expressions, and custom components are never evaluated; recognizable unsupported syntax gets a warning and readable text or a placeholder.

Remote downloads allow public HTTP(S) destinations only. Private networks, localhost, URL credentials, UNC/network image references, and schemes such as `file:` or `data:` are blocked. HTTP requests bypass proxy environment variables. Ordinary hyperlinks are not downloaded. Local paths may point outside the source directory but must contain supported raster images. See the [technical design](TECHNICAL_DESIGN.md) for the download and rendering boundaries.

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
| Command not found | Activate `.venv`, or use its Python interpreter from the platform table with `-m mdx_printkit`. |
| Chromium missing | Run `python -m playwright install chromium` in the same environment. |
| Linux browser libraries missing | Run `python -m playwright install --with-deps chromium` on a supported Linux distribution. |
| Bundled fonts missing or unable to load | Reinstall from a complete checkout with `python -m pip install -e .`, or reinstall the wheel. Keep the packaged `fonts/` directory intact. |
| Selected system font unavailable | The PDF uses Source Sans Pro with a warning. Choose another installed family or omit `--font` to use the default without a warning. |
| PDF destination locked or access denied | Close the PDF in its viewer, particularly on Windows, and check that the destination directory is writable. |
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
