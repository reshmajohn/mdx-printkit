from bs4 import BeautifulSoup
import pytest

from mdx_printkit.assets import AssetResolver
from mdx_printkit.document import build_document


def build(source, tmp_path, **kwargs):
    return build_document(source, AssetResolver(tmp_path, cache_dir=tmp_path / "cache", offline=True),
                          tmp_path / "work", **kwargs)


def test_markdown_and_image_order(tmp_path, png):
    source = '''# Title

First *paragraph* and [site](https://example.com).

![sample](a%20diagram.png)

## Next

<div class="flex justify-center"><img src="a diagram.png" alt="second"></div>

- One
- Two

| A | B |
| - | - |
| x | y |

```html
<script>alert("example")</script>
<Widget />
![fake](missing.png)
```
'''
    document = build(source, tmp_path)
    soup = BeautifulSoup(document.html, "html.parser")
    assert document.images == 2 and not document.warnings
    assert soup.find("table") and len(soup.select("li")) == 2
    assert soup.select_one("div.center img")["alt"] == "second"
    assert "<script>" in soup.find("code").get_text()
    assert document.html.index("First") < document.html.index('alt="sample"') < document.html.index("Next")
    for image in soup.select("img"):
        assert (tmp_path / "work" / image["src"]).exists()


@pytest.mark.parametrize("markup", ["![Movement](moving.gif)", '<img src="moving.gif" alt="Movement">',
                                  "[Movement](moving.gif?raw=1#animation)"])
@pytest.mark.parametrize("count", [1, 4, 6])
def test_all_gif_forms_at_original_position(tmp_path, animated_gif, markup, count):
    document = build("Before\n\n" + markup + "\n\nAfter", tmp_path, gif_frames=count)
    soup = BeautifulSoup(document.html, "html.parser")
    assert len(soup.select("figure img")) == count
    assert document.gifs == 1
    assert document.html.index("Before") < document.html.index("<figure") < document.html.index("After")
    assert not soup.select("p figure")
    assert soup.select_one(".frames span").get_text() == f"Frame 1/{count}"


def test_inline_gif_preserves_surrounding_content(tmp_path, animated_gif):
    document = build("Before [demo](moving.gif) after.", tmp_path)
    assert document.html.index("Before") < document.html.index("<figure") < document.html.index("after.")


def test_safety_unsupported_mdx_and_missing_media(tmp_path):
    source = '''# Safe

import Widget from './widget.js'

<Widget dangerous={run()} />

{someExpression()}

<script>window.evil = 1</script>
<iframe src="https://example.com"></iframe>
<style>body{display:none}</style>
<img src="missing.png" onerror="steal()" style="width:9999px">
<img src="file:///etc/passwd" alt="blocked">
<a href="javascript:alert(1)">unsafe</a>
'''
    document = build(source, tmp_path)
    soup = BeautifulSoup(document.html, "html.parser")
    assert not soup.select("script, iframe, widget, [onerror], [style]")
    assert "window.evil" not in soup.get_text()
    assert "Unsupported MDX component: Widget" in soup.get_text()
    assert "{someExpression()}" in soup.get_text()
    assert len(soup.select(".missing-image")) == 2
    assert any("import/export" in warning for warning in document.warnings)
    assert any("MDX expressions" in warning for warning in document.warnings)
    assert any("missing.png" in warning for warning in document.warnings)
    assert soup.find("a").get("href") is None


def test_remote_failure_placeholder(tmp_path, http_images):
    url, _ = http_images
    resolver = AssetResolver(tmp_path, cache_dir=tmp_path / "cache")
    document = build_document(f"![bad]({url}/missing)", resolver, tmp_path / "work")
    assert "Image unavailable: bad" in document.html
    assert "404" in document.warnings[0]


def test_remote_gif_source_caption(tmp_path, animated_gif, monkeypatch):
    resolver = AssetResolver(tmp_path)
    monkeypatch.setattr(resolver, "resolve", lambda ref: animated_gif)
    document = build_document("[Demo](https://example.com/demo.gif?raw=1)", resolver, tmp_path / "work")
    soup = BeautifulSoup(document.html, "html.parser")
    assert soup.select_one("figcaption a")["href"] == "https://example.com/demo.gif?raw=1"
