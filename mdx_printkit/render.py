"""Render a prepared local document with scripting and external requests disabled."""

from pathlib import Path
from urllib.parse import unquote, urlsplit

from playwright.sync_api import Error, sync_playwright

from .errors import PrintKitError
from .typography import FONT_FACES


def render_pdf(html_path: Path, output: Path, paper: str = "letter") -> None:
    if paper not in {"letter", "a4"}:
        raise PrintKitError("paper must be 'letter' or 'a4'")
    root = html_path.parent.resolve()

    def allow_local(route):
        parts = urlsplit(route.request.url)
        path = Path(unquote(parts.path)).resolve()
        if parts.scheme == "file" and path.is_relative_to(root):
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
                missing = page.evaluate("""async faces => {
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
                }""", [face[:3] for face in FONT_FACES])
                if missing:
                    raise PrintKitError(
                        "Bundled fonts failed to load: " + ", ".join(missing) +
                        ". Reinstall mdx-printkit to restore its font files."
                    )
                page.pdf(path=str(output), format="Letter" if paper == "letter" else "A4",
                         print_background=True, display_header_footer=False)
            finally:
                browser.close()
    except Error as exc:
        message = str(exc)
        if "Executable doesn't exist" in message or "playwright install" in message:
            raise PrintKitError(
                "Chromium is not installed. Run: .venv/bin/python -m playwright install chromium"
            ) from exc
        raise PrintKitError(f"PDF renderer failed: {message}") from exc

