"""Render a prepared local document with scripting and external requests disabled."""

from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import url2pathname

from playwright.sync_api import Error, sync_playwright

from .errors import PrintKitError
from .typography import DEFAULT_FONT, font_name, prepare_fonts, required_faces


def _local_resource(url: str, root: Path) -> bool:
    parts = urlsplit(url)
    if parts.scheme != "file" or parts.netloc.lower() not in {"", "localhost"}:
        return False
    try:
        path = Path(url2pathname(parts.path)).resolve()
        return path.is_relative_to(root.resolve())
    except (OSError, ValueError):
        return False


def _missing_fonts(page, font: str) -> list[str]:
    return page.evaluate("""async faces => {
        const missing = [];
        for (const [family, weight, style] of faces) {
            const font = `${style} ${weight} 11pt "${family}"`;
            try {
                const loaded = await document.fonts.load(font, 'PrintKit');
                if (!loaded.length || loaded.some(face => face.status !== 'loaded')) {
                    missing.push(`${family} ${weight} ${style}`);
                }
            } catch {
                missing.push(`${family} ${weight} ${style}`);
            }
        }
        await document.fonts.ready;
        return missing;
    }""", required_faces(font))


def render_pdf(html_path: Path, output: Path, paper: str = "letter", font: str = DEFAULT_FONT) -> list[str]:
    if paper not in {"letter", "a4"}:
        raise PrintKitError("paper must be 'letter' or 'a4'")
    font_name(font)
    root = html_path.parent.resolve()
    warnings = []

    def allow_local(route):
        if _local_resource(route.request.url, root):
            route.continue_()
        else:
            route.abort()

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                context = browser.new_context(java_script_enabled=False, service_workers="block")
                context.route("**/*", allow_local)
                page = context.new_page()
                page.set_default_timeout(30_000)
                page.emulate_media(media="print")
                page.goto(html_path.resolve().as_uri(), wait_until="load")
                # Only this application-owned expression runs; document scripting stays disabled.
                page.evaluate("() => Promise.all(Array.from(document.images, img => img.decode()))")
                missing = _missing_fonts(page, font)
                if font != DEFAULT_FONT and missing and all(face.startswith("PrintKit ") for face in missing):
                    prepare_fonts(root)
                    page.evaluate("() => document.documentElement.style.setProperty('--printkit-body-font', 'initial')")
                    warnings.append(
                        f"System font {font_name(font)} is unavailable or missing a required style "
                        "on this system; using bundled Source Sans Pro."
                    )
                    missing = _missing_fonts(page, DEFAULT_FONT)
                if missing:
                    raise PrintKitError(
                        "Bundled fonts failed to load: " + ", ".join(missing) +
                        ". Reinstall mdx-printkit to restore its font files."
                    )
                page.pdf(path=str(output), format="Letter" if paper == "letter" else "A4",
                         print_background=True, display_header_footer=False)
            finally:
                browser.close()
        return warnings
    except Error as exc:
        message = str(exc)
        if "Host system is missing dependencies" in message or "error while loading shared libraries" in message:
            raise PrintKitError(
                "Chromium needs operating-system libraries. On a supported Linux distribution, run "
                "python -m playwright install --with-deps chromium in this Python environment. "
                f"Details: {message}"
            ) from exc
        if "Executable doesn't exist" in message:
            raise PrintKitError(
                "Chromium is not installed. In this Python environment, run: "
                "python -m playwright install chromium"
            ) from exc
        raise PrintKitError(f"PDF renderer failed: {message}") from exc

