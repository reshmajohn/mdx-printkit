# Product specification — MDX PrintKit v1

## Goal and audience
A small local command-line utility to print educational Markdown/MDX reading material with all its visual examples intact. The user has `.mdx` files on a laptop, often from GitHub or Hugging Face, and wants **offline, printable PDFs**, including meaningful static alternatives to animated GIFs.

## Scope
### Input
- A **local file path** to a UTF-8 `.md` or `.mdx` document; CLI must give an actionable error for missing/unreadable/unsupported input.
- The file may contain ordinary Markdown: headings, paragraphs, emphasis, links, lists, blockquotes, fenced code, inline code, tables, horizontal rules.
- It may also contain modest embedded HTML, especially `<div class="flex justify-center">` and `<img src="..." alt="...">` from `reference-input/motivation.mdx`.
- Support standard Markdown image syntax `![alt](path-or-url)`, HTML `<img src="...">`, and direct Markdown links `[animation](path-or-url.gif)` / `[https://...gif](https://...gif)`.
- Assets may be `https://`/`http://` URLs or paths relative to the input file's directory. Treat query strings/fragments correctly when recognizing file extensions.
- Not in v1: executing MDX JSX/React components, evaluating JavaScript imports/expressions, rendering remote webpages, notebooks, or arbitrary embedded widgets. Detect conspicuous unsupported MDX syntax, preserve readable plain text when possible, and warn instead of silently erasing content.

### Output
- A portable **PDF with actual image bytes embedded**, no need for internet to view or print it.
- Default output path: `./output/<input-stem>.pdf` relative to current working directory; create `output` when needed. `--output` overrides this with a full or relative path.
- Default page size: US Letter; switchable to A4 with `--paper a4`.
- Clean, white, legible layout with heading hierarchy, modest margins, clickable hyperlinks, readable monospace/code blocks, centered images where appropriate, and image aspect ratios preserved.
- Avoid cut-off text and images, stranded headings, splitting a figure/storyboard across pages when feasible, and an excessive number of nearly empty pages.
- Preserve paragraphs' original order and the document's title/content; no cover page, table of contents, or decorative branding required.

### Image behavior
- PNG, JPEG, WEBP supported; use browsers to display decoded raster images or normalize to PNG where needed.
- Remote images downloaded before rendering and saved to persistent local cache so repeated runs can reuse them.
- Local relative images resolved against the **source file directory**, not the current shell directory.
- Render a clearly labeled, readable placeholder for an unreachable/unsupported image; emit a CLI warning (including original URL/path) and **continue generating the PDF**.
- No silent blank images or missing images. Never replace a failed download with an unrelated picture.
- `<div class="flex justify-center">` should be treated as a centered image block even if the source document's original CSS framework is unavailable.
- Preserve `alt` text as an accessibility/placeholder description; ordinary images need not have visible captions unless the document provides one.

### GIF behavior (important)
- Default option B: convert an animated GIF to a print-friendly **storyboard of up to 4 distinct frames**, in temporal order, labeled `1/4`, `2/4`, etc. Prefer a compact 2x2 grid at four frames; arrange two/three frames neatly.
- Sample frames across *elapsed animation time* including beginning and near end, not simply the first four adjacent frames; respect frame durations, transparency, disposal and compositing. Deduplicate frames when the animation is static/repetitive.
- Never print only a broken/animated GIF element or automatically use just the first frame.
- A `.gif` used in Markdown image syntax, HTML `<img>`, **or linked directly as `[text](file.gif)`** becomes a storyboard at its original document position. Keep a discreet clickable source link/caption so readers can reach the original animation online if desired.
- `--gif-frames N` accepts integer 1–12 and changes the maximum distinct frames. If N=1, choose a representative frame rather than introducing a grid.
- Do not produce a large poster-style contact sheet unless the user explicitly opts for more frames. Limit frame dimensions to fit the page.
- Static (single-frame) GIFs should display as one normal image.

### CLI
Required flags: `--output PATH`, `--paper {letter,a4}`, `--gif-frames N`, `--offline`, `--help`. A clear `--version` is useful but optional.

Behavior:
- Print destination and a concise status summary (image count, GIF count, warnings).
- Exit nonzero for CLI errors, unreadable input, fatal renderer/browser errors, invalid arguments; missing individual images should warn but not make an otherwise valid PDF fail.
- Show a clear action for a missing Playwright browser install (`python -m playwright install chromium`).
- Preserve input unchanged. Avoid writing downloaded files or temporary HTML into the input directory.

## Non-goals for the first release
No GUI, no drag-and-drop, no batch-folder CLI, no URL-to-MDX fetch, no live web-service hosting, no automatic screenshot of React widgets, no cloud infrastructure, no OCR, no LLM calls, and no user accounts.

## Acceptance summary
`motivation.mdx` yields legible, correct-order text plus its three PNG images. A test MDX with a remote or local GIF yields up to four correctly ordered representative frames. Broken remote images show a diagnostic placeholder, not a blank hole. The PDF opens without network access.
