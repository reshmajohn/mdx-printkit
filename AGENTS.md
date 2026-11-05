# Codex Instructions — MDX PrintKit

This workspace uses a Python virtual environment at ./.venv.
Always run Python with .venv/bin/python and install packages with .venv/bin/pip install <pkg>. Never use the system python or pip.
When you install a package, also add it to requirements.txt.

Read `CODEX_START_HERE.md` first, then `docs/PRODUCT_SPEC.md`, `docs/TECHNICAL_DESIGN.md`, and `docs/ACCEPTANCE_TESTS.md`. These define the implementation and acceptance criteria.

## Mission
Build a working, small, local-first Python CLI that converts a **local `.md` or `.mdx` file** into a readable, printable PDF, embedding remote/local images and converting GIFs to static multi-frame storyboards. Do the full implementation, not just a framework or proof of concept.

## Working approach
- Implement in one cohesive pass, then run tests and fix issues. Do not break the task into numerous tiny user-facing checkpoints.
- Prefer simple, maintained libraries and a straightforward package layout. No web app, GUI, API server, database, JavaScript build system, or AI model.
- Keep responsibilities separate enough to test: CLI, markdown/HTML transformation, asset resolution/cache, GIF processing, print HTML/CSS, PDF rendering.
- Do not execute MDX JavaScript/React, arbitrary HTML scripts, or shell commands embedded in source files.
- Produce helpful errors and warnings, particularly for missing images and unsupported custom MDX components.
- Use a local virtual environment; document setup and Playwright Chromium installation.
- Write actual functional code, tests, and a good `README.md`. The README **must be created by Codex**, not omitted.
- Do not copy learning-course content or remote assets into the public Git repository. `reference-input/`, `output/`, caches, virtualenvs, and generated PDFs should be gitignored.
- Never commit API keys, credentials, or downloaded private content. This project needs no secrets.
- Do not push to GitHub, create a remote repository, or publish a package without user approval. Local git init/commits are fine if requested.

## Completion standard
- A person can follow the README, install the tool, and run `mdx-printkit path/to/file.mdx` to get a PDF.
- The provided `reference-input/motivation.mdx` renders with its three Hugging Face PNG images in the correct reading order (given network access).
- A GIF, whether embedded as an image or written as a direct Markdown hyperlink to `.gif`, yields a **4-frame storyboard by default** (or fewer genuinely distinct frames).
- Synthetic, offline tests cover success and failure cases. The full test suite is run, and a PDF smoke test is performed when Chromium is available.
- Do not call something "done" if its tests or sample conversion fail. State unresolved issues explicitly.

## When tradeoffs arise
Prioritize (1) correct readable print output, (2) dependable local/remote image handling, (3) GIF frame usefulness, (4) simple UX, (5) broader MDX compatibility. Full React/JSX MDX rendering is out of scope for v1.
