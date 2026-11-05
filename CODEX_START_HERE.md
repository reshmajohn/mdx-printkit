# Start here: Codex implementation handoff

## Project identity
- **Repository name:** `mdx-printkit`
- **Python package:** `mdx_printkit`
- **CLI command:** `mdx-printkit`
- **Short GitHub description:** "Turn local Markdown/MDX course notes into printable PDFs with embedded images and GIF storyboards."
- **Suggested GitHub topics:** `mdx`, `markdown`, `pdf`, `python`, `cli`, `study-notes`, `gif`, `printing`
- **Suggested license for original tool code:** MIT (ask owner before applying if they prefer something else). Course content and downloaded images are **not** covered by this license.

## What the user will do
Pass the **path to a local input file**, not a URL:

```bash
mdx-printkit ~/Downloads/course/motivation.mdx
```

Expected default output: `./output/motivation.pdf`, relative to the directory from which the command runs. The input file stays unchanged. Spaces in file names must work when the path is quoted. All external images should be fetched and embedded before the PDF is rendered.

Other intended commands:

```bash
mdx-printkit "./my course/motivation.mdx" --output "./prints/Vision Notes.pdf"
mdx-printkit ./notes.mdx --gif-frames 6 --paper a4
mdx-printkit ./notes.mdx --offline
mdx-printkit --help
```

`--offline` may only use local image files and previously cached remote images; missing remote images receive visible placeholders/warnings.

## Implementation request to paste into Codex

> Implement the complete `mdx-printkit` repository from the attached specifications. Read `AGENTS.md`, `docs/PRODUCT_SPEC.md`, `docs/TECHNICAL_DESIGN.md`, and `docs/ACCEPTANCE_TESTS.md` before writing code. Treat `reference-input/motivation.mdx` as a private real-world smoke test (do not commit it). Build a working installable Python package and CLI, download/cache external images, convert animated GIFs into 4-frame storyboards by default, render safe Markdown/HTML to print-friendly PDF using Chromium, and provide tests, `pyproject.toml`, a generated `README.md`, `.gitignore`, and appropriate MIT LICENSE if approved. Implement the whole tool, run tests, actually generate and inspect a sample PDF when dependencies/network allow, fix failures, and report the exact commands run and any limitations. Do not stop after creating scaffolding; do not request approval for each small implementation step. Never push or publish without my approval.

## Suggested delivery sequence (just 2 substantial steps)
1. **Implement everything:** package, parser, asset processing, GIF handling, printable CSS, PDF renderer, CLI, README, local fixtures, tests.
2. **Validate and polish:** install dependencies/browser; run offline tests; perform sample and GIF smoke conversions; review pages/image placement, fix problems, then summarize the result.

No need to implement a folder-batch command or GUI in v1; keep the code extensible.

## GitHub guidance
1. Create an empty GitHub repo named `mdx-printkit` when ready (public or private is user's choice).
2. Have Codex create `.gitignore` with at least `.venv/`, `__pycache__/`, `.pytest_cache/`, `.cache/`, `output/`, `reference-input/`, `*.pdf`, and local environment files.
3. Commit only tool code, synthetic test fixtures, documentation, and license. **Do not commit `motivation.mdx` or downloaded course assets** without checking their reuse terms.
4. Add a README demo screenshot/GIF only if it is original or reuse is permitted; no demo assets are necessary for v1.

## Source reference
`reference-input/motivation.mdx` is copied unchanged from the example the user provided. It has Markdown paragraphs/headings and three `<div class="flex justify-center"><img src="https://huggingface.co/..." alt="..."></div>` image blocks. It contains no GIF; GIF behavior must be separately tested. A sample user-provided GIF URL to use *only when testing external downloading* is:

`https://huggingface.co/datasets/hf-vision/course-assets/resolve/743a2a115b53f258c9e6bc7744534d9e03b8a124/self_driving_gif.gif`

That URL is a reference to download at conversion time, not an asset to vendor in source control.
