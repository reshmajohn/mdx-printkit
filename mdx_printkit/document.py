"""Parse Markdown, sanitize document HTML, and replace media in reading order."""

from __future__ import annotations

from dataclasses import dataclass, field
import html
from importlib.resources import files
from pathlib import Path
import re
from urllib.parse import urlsplit

from bs4 import BeautifulSoup
from markdown_it import MarkdownIt
import nh3

from .assets import AssetResolver, verify_image
from .errors import AssetError
from .gif import extract_frames, normalize_image
from .typography import prepare_fonts

TAGS = set("p div span h1 h2 h3 h4 h5 h6 br hr strong em b i s del u sub sup "
           "ul ol li blockquote pre code a img table thead tbody tfoot tr th td "
           "figure figcaption dl dt dd details summary kbd mark".split())


@dataclass
class Document:
    html: str = ""
    images: int = 0
    gifs: int = 0
    warnings: list[str] = field(default_factory=list)

    def warn(self, message: str) -> None:
        if message not in self.warnings:
            self.warnings.append(message)


def _markdown(source: str, report: Document) -> str:
    parser = MarkdownIt("commonmark", {"html": True}).enable(["table", "strikethrough"])
    tokens = parser.parse(source)

    def inspect(token):
        if token.type in {"fence", "code_block", "code_inline"}:
            return
        if token.type in {"html_inline", "html_block"}:
            names = re.findall(r"<([A-Z][\w.:-]*)\b", token.content)
            for name in dict.fromkeys(names):
                if name.lower() not in TAGS:
                    report.warn(f"Unsupported MDX component: {name}; JavaScript/React is not executed")
                    token.content = re.sub(
                        rf"(<{re.escape(name)}\b)",
                        f"<span>[Unsupported MDX component: {html.escape(name)}]</span>\\1",
                        token.content,
                    )
        if token.type in {"text", "inline", "html_inline", "html_block"}:
            if re.search(r"(?m)^\s*(?:import|export)\s", token.content):
                report.warn("Unsupported MDX import/export preserved as text; code is not executed")
            if token.type == "text" and re.search(r"\{[^{}\n]+\}", token.content):
                report.warn("MDX expressions preserved as text; code is not executed")
        for child in token.children or []:
            inspect(child)

    for token in tokens:
        inspect(token)
    return parser.renderer.render(tokens, parser.options, {})


def _sanitize(markup: str, report: Document) -> BeautifulSoup:
    soup = BeautifulSoup(markup, "html.parser")
    for tag in soup.find_all(True):
        if tag.name in {"script", "iframe", "style", "object", "embed", "link", "base", "form"}:
            report.warn(f"Removed unsafe/unsupported HTML element: {tag.name}")
        if any(key.startswith("on") for key in tag.attrs):
            report.warn("Removed HTML event handlers")
        # Preserve the original image reference for a helpful failure placeholder,
        # including URLs the sanitizer would otherwise silently remove.
        if tag.name == "img":
            ref = tag.get("src", "")
            try:
                parts = urlsplit(ref)
                unsafe = parts.scheme.lower() not in {"", "http", "https"} or bool(parts.netloc and not parts.scheme)
            except ValueError:
                unsafe = True
            if unsafe:
                report.warn(f"Image unavailable: {ref}: unsupported image URL scheme")
                placeholder = soup.new_tag("span")
                placeholder["class"] = "missing-image"
                placeholder.string = f"[Image unavailable: {tag.get('alt', '') or ref}]"
                tag.replace_with(placeholder)
                continue
        if tag.name == "div" and "justify-center" in tag.get("class", []):
            tag["class"] = "center"
    safe = nh3.clean(
        str(soup), tags=TAGS,
        clean_content_tags={"script", "style", "iframe", "object", "embed", "template"},
        attributes={"img": {"src", "alt", "title"},
                    "a": {"href", "title"}, "ol": {"start"},
                    "th": {"colspan", "rowspan"}, "td": {"colspan", "rowspan"}},
        allowed_classes={"div": {"center"}, "span": {"missing-image"}},
        url_schemes={"http", "https", "mailto"},
    )
    return BeautifulSoup(safe, "html.parser")


def build_document(source: str, resolver: AssetResolver, work_dir: Path,
                   *, gif_frames: int = 4, title: str = "Notes") -> Document:
    report = Document()
    soup = _sanitize(_markdown(source, report), report)
    assets = work_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    media = list(soup.find_all(["img", "a"]))
    rendered: dict[str, tuple[list[Path], bool]] = {}
    for index, tag in enumerate(media):
        if tag.parent is None:
            continue
        ref = tag.get("src" if tag.name == "img" else "href", "")
        if tag.name == "a":
            try:
                is_gif_link = urlsplit(ref).path.lower().endswith(".gif")
            except ValueError:
                is_gif_link = False
            if not is_gif_link or tag.find("img"):
                continue
        description = tag.get("alt", "") if tag.name == "img" else tag.get_text(" ", strip=True)
        try:
            if ref not in rendered:
                path = resolver.resolve(ref)
                kind = verify_image(path)
                if kind == "GIF":
                    storyboard = extract_frames(path, assets / f"gif-{index}", gif_frames)
                    rendered[ref] = storyboard.paths, storyboard.animated
                else:
                    output = assets / f"image-{index}.png"
                    normalize_image(path, output)
                    rendered[ref] = [output], False
            paths, animated = rendered[ref]
            report.images += 1
            if animated:
                report.gifs += 1
            if not animated and tag.name == "img":
                tag["src"] = paths[0].relative_to(work_dir).as_posix()
                continue
            figure = soup.new_tag("figure")
            figure["class"] = "gif-storyboard" if len(paths) > 1 else "single-frame"
            grid = soup.new_tag("div")
            grid["class"] = f"frames count-{len(paths)}"
            for number, path in enumerate(paths, 1):
                cell = soup.new_tag("div")
                image = soup.new_tag("img", src=path.relative_to(work_dir).as_posix())
                image["alt"] = f"{description or 'Animation'} - frame {number}/{len(paths)}"
                cell.append(image)
                if animated:
                    label = soup.new_tag("span")
                    label.string = f"Frame {number}/{len(paths)}"
                    cell.append(label)
                grid.append(cell)
            figure.append(grid)
            caption = soup.new_tag("figcaption")
            caption.append(description or ("Animation frames" if animated else "GIF image"))
            try:
                remote = urlsplit(ref).scheme in {"http", "https"}
            except ValueError:
                remote = False
            if remote:
                caption.append(" · ")
                link = soup.new_tag("a", href=ref)
                link.string = "Source"
                caption.append(link)
            figure.append(caption)
            tag.replace_with(figure)
        except AssetError as exc:
            report.warn(f"Image unavailable: {ref}: {exc}")
            placeholder = soup.new_tag("span")
            placeholder["class"] = "missing-image"
            placeholder.string = f"[Image unavailable: {description or ref or 'missing source'}]"
            tag.replace_with(placeholder)

    # A block figure cannot live inside a Markdown-generated paragraph or link.
    for figure in list(soup.find_all("figure")):
        if figure.parent and figure.parent.name == "a":
            figure.parent.unwrap()
        parent = figure.parent
        if parent and parent.name == "p":
            before = soup.new_tag("p")
            for sibling in list(parent.contents):
                if sibling is figure:
                    break
                before.append(sibling.extract())
            parent.insert_before(before)
            parent.insert_before(figure.extract())
            if not before.get_text(strip=True) and not before.find("img"):
                before.decompose()
            if not parent.get_text(strip=True) and not parent.find(["img", "figure"]):
                parent.decompose()

    heading = soup.find("h1")
    title = heading.get_text(" ", strip=True) if heading else title
    prepare_fonts(work_dir)
    css = files("mdx_printkit").joinpath("styles.css").read_text(encoding="utf-8")
    report.html = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; '
        'img-src file:; font-src file:; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">'
        f"<title>{html.escape(title)}</title><style>{css}</style></head><body><main>"
        f"{soup}</main></body></html>"
    )
    return report
