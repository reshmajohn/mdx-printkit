# Acceptance tests and validation — MDX PrintKit v1

Build a small automated test suite (pytest) around the parser, media resolver, GIF frame extraction, and PDF renderer. Tests must not rely on third-party servers. Use programmatically created PNG/JPEG/WEBP and GIF fixtures, or a local HTTP fixture server.

## Core automated test cases

| Area | Test | Pass condition |
|---|---|---|
| CLI | Local `.mdx` absolute/relative path, including spaces | Works via `file` and original shorthand; default `<source-directory>/<stem>.pdf` exists independently of shell directory; source not changed |
| CLI | `--output`, `--paper a4`, `--gif-frames 1/4/6`, invalid N | Correct output/behavior; invalid N fails helpfully |
| Folder CLI | Two direct `.mdx` / `.MDX` inputs, nested MDX and adjacent `.md` | Exactly two PDFs in the input folder by default, in filename order; nested and `.md` inputs excluded |
| Folder CLI | Alternate output directory, A4, GIF frame count, offline | One PDF per direct MDX in the override directory; all shared options honored and source-relative images preserved |
| Folder CLI | Empty/missing/non-directory input, file as output directory, colliding PDF destinations | Helpful nonzero failure; destination collisions detected before writing |
| Folder CLI | Unreadable document followed by a valid document | Valid file still converts; nonzero exit and success/failure summary; previous PDF for failed document preserved |
| Markdown | Headings, paragraphs, lists, code fences, link, table | Print HTML contains content in correct order; code fence isn't parsed as HTML |
| Equations | Inline/display TeX, fractions, roots, scripts, sums, align, cases | Real MathML, no Markdown damage; paragraph displays keep valid HTML; equals signs align in actual PDF coordinates |
| Equations | Malformed/unknown TeX, attempted markup or file inclusion, excessive length/nesting | Visible escaped TeX and warning; no execution or image fetch; code/currency/escaped dollars stay literal |
| Equations | Offline Letter/A4 PDFs, missing math font, system body-font fallback | STIX Two Math is identifiable and embedded, equations fit the synthetic page, numeric variants work; missing math font is fatal; fallback keeps math/code fonts |
| HTML | `<div class="flex justify-center"><img src="..." alt="..."></div>` | Image is resolved, centered, scaled; alt description preserved |
| Markdown image | `![sample](local.png)` | Image appears and relative path resolves against input-file location |
| Remote image | Synthetic image served by local HTTP server | Download, cache, and render; second run reuses cache |
| Offline | Cached and uncached image with `--offline` | Cached renders; uncached gives placeholder and warning, never HTTP request |
| Missing asset | 404, timeout, corrupt image | Placeholder and warning; PDF still produced |
| GIF embed | Animated GIF referenced as Markdown image | Up to four distinctive, ordered frames by default |
| GIF HTML | `<img src="demo.gif">` | Same storyboard behavior |
| GIF link | `[view the demo](demo.gif)` or `[https://...gif](https://...gif)` | Link replaced at same position with storyboard, not a dead text link |
| GIF compositing | Transparent moving-object/disposal fixture with differing durations | No black/transparent glitches; representative temporal sampling |
| GIF static | Single-frame GIF | One image rather than four redundant frames |
| PDF | Output from Playwright | Valid PDF with embedded visual content and selectable text |
| Typography | Regular, semibold, bold, italic, and code text in an offline PDF | Extracted text uses the expected Source Sans Pro / IBM Plex Mono PostScript names and the PDF contains nonempty embedded TrueType streams |
| Typography | Missing or corrupt bundled font | Rendering fails explicitly instead of silently using a fallback |
| Font CLI | `file --help`, `folder --help`, valid/invalid `--font` | Both list all seven options and default Source Sans Pro; unknown options fail helpfully; folder selection reaches every input |
| System typography | Offline PDF with each installed alternative | Actual regular, bold/semibold, and italic PDF spans use the chosen family and fonts are embedded; code remains IBM Plex Mono. Skip a family-specific test only if that font is absent on the test OS |
| System typography | Selected family or style unavailable | Visible warning and successful PDF using embedded Source Sans Pro; code remains IBM Plex Mono; verify both file and folder commands |
| System typography | Bundled fallback unavailable | Fatal actionable error and existing destination PDF preserved |
| Platforms | Native absolute image paths, relative backslashes, escaped drive colons | Correct image resolution on the host OS without treating a drive letter as a URL scheme; Windows syntax survives sanitization |
| Platforms | Local renderer URI with Unicode/spaces/percent/hash | Native path conversion succeeds and only files inside the temporary render directory are allowed |
| Platforms | Default native cache with an earlier cached image | Offline conversion can reuse the legacy cache; explicit cache overrides remain isolated |
| Platforms | Browser or Linux libraries missing | Distinct actionable setup commands without hardcoded `.venv/bin` assumptions |
| Packaging | Built wheel and isolated installation | CSS, eight font files, all three original font licenses, and provenance are present; conversion works outside the source checkout |
| Print | Long title, tall/wide image, long code line | No obvious clipping or severe layout corruption |
| Safety | `<script>`, `onerror`, `javascript:` URL, unsupported custom JSX | No execution; warnings/placeholder as applicable; no external renderer fetch |

## Real example smoke test
`reference-input/motivation.mdx` is a **private reference file**, not a public test fixture. It contains:
- H1 `Vision` and subsequent headings, including `Significance of Vision to Humans` and `Pure Programming vs Machine Learning Approach`.
- Three external Hugging Face PNG images, in `<div class="flex justify-center">` blocks: `cropped_motivation.png`, `balls.png`, and `motivation_04.png`.
- Long paragraphs and no GIFs.

When internet access is available, run:

```bash
mdx-printkit file reference-input/motivation.mdx --output output/motivation.pdf
```

Confirm all three images actually appear, the section order is unchanged, paragraphs and images don't clip, and the PDF opens without internet. Don't count merely producing a nonempty PDF as sufficient validation.

## GIF smoke test
Make a **local, synthetic** `.mdx` fixture containing each of:

```md
# GIF test
![Tracking demonstration](moving-object.gif)

[Watch GIF](moving-object.gif)

<img src="moving-object.gif" alt="Movement demonstration">
```

Generate a small animated GIF with at least 8 visually distinct frames and one repeated frame. Confirm all three references render storyboards, with up to four *visually distinct* frames, rather than a static broken GIF. Use an uneven frame-duration fixture to test time-based sampling.

As an **optional live integration test**, make a throwaway local `.mdx` containing the user-provided Hugging Face `self_driving_gif.gif` URL as a Markdown link and confirm it is downloaded and rendered. Avoid hardcoding network dependence into CI tests.

When the private `reference-input/extension-image.mdx` is present, convert it online and again from cache with `--offline`. It includes nine image references, four of which are animated GIFs. Verify four labeled, distinct frames per GIF, embedded font identities, original media order, and readable layout. Keep the input and fetched course assets unchanged and outside version control.

## Final manual review

When `reference-input/yolo.mdx` and its original PDF are available, write the revised conversion to `output/yolo-math.pdf` without replacing either reference. Inspect the piecewise function, aligned probability derivation, sums, indicator digits, and square-root loss terms. Verify all source formulas become MathML, the math font is embedded, media/storyboard order is retained, and reference checksums are unchanged.
- Open or render at least the first page and one page containing a GIF storyboard; check typography, margins, captions, and alignment.
- Check a cached/offline regeneration when feasible.
- Execute `pytest` and report passing/failing counts; run `mdx-printkit --help`.
- In final Codex handoff report: actual installation/run commands, output file paths, tests run, unresolved issues, and any intentionally unsupported MDX constructs.
- Native Windows, Linux, and macOS CI is configured for Python 3.11 and 3.14. Record which environments actually ran; a macOS run alone is not proof of Windows/Linux execution. Skip symlink-only checks when the OS denies symlink creation, and installed-family PDF checks only when that family is absent.
