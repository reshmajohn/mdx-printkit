from importlib.resources import files

from bs4 import BeautifulSoup
from pypdf import PdfReader
import pytest

from mdx_printkit.assets import AssetResolver
from mdx_printkit.convert import convert
from mdx_printkit.document import build_document
from mdx_printkit.errors import PrintKitError
from mdx_printkit.render import render_pdf
from mdx_printkit.typography import MATH_FONT_FACE


EQUATIONS = r"""# Equations

Inline $S \times S$ and $\lambda_{\text{coord}}$ stay in the paragraph.

$$\frac{a+b}{\sqrt{x^2+y^2}}$$

Formally, $$\begin{align}C_i &= P_i \\ D_i &= \sum_{b=0}^{B} x_b\end{align}$$ then continue.

$$
f(x)=\begin{cases}x & \text{if } x > 0 \\ 0.1x & \text{otherwise}\end{cases}
$$
"""


def test_inline_display_fractions_roots_alignment_and_cases(tmp_path):
    document = build_document(EQUATIONS, AssetResolver(tmp_path, offline=True), tmp_path)
    soup = BeautifulSoup(document.html, "html.parser")
    assert not document.warnings
    assert len(soup.find_all("math")) == 5
    assert len(soup.select(".math-inline")) == 2
    assert len(soup.select(".math-display")) == 3
    assert soup.find("mfrac") and soup.find("msqrt")
    tables = soup.find_all("mtable")
    assert len(tables) == 2 and all(len(table.find_all("mtr")) == 2 for table in tables)
    assert tables[0].find("mtd")["columnalign"] == "right"
    assert soup.find("munderover") and soup.find("msub")
    assert not soup.select("p > div")  # $$ in a paragraph must keep a valid HTML tree.
    assert "then continue" in soup.get_text()
    assert (tmp_path / "fonts" / MATH_FONT_FACE[3]).read_bytes()[:4] == b"\0\1\0\0"
    license_text = files("mdx_printkit").joinpath("fonts/stix-two-math/OFL.txt").read_text()
    assert "SIL OPEN FONT LICENSE Version 1.1" in license_text


def test_code_escaped_dollars_and_currency_are_not_equations(tmp_path):
    source = r"""Use `$x_i$` and pay $5 or $10. Escaped \$x\$.

```latex
$$\frac{a}{b}$$
```
"""
    document = build_document(source, AssetResolver(tmp_path, offline=True), tmp_path)
    soup = BeautifulSoup(document.html, "html.parser")
    assert not soup.find("math") and not document.warnings
    assert "$x_i$" in soup.code.get_text()
    assert r"$$\frac{a}{b}$$" in soup.pre.get_text()
    assert "pay $5 or $10" in soup.get_text() and "Escaped $x$." in soup.get_text()
    assert not (tmp_path / "fonts/stix-two-math").exists()


@pytest.mark.parametrize("formula", [
    r"\frac{1}", r"\sqrt{", r"\begin{align}x&=y", r"\unknown{x}",
    r"\input{/etc/passwd}", r"\href{https://example.test}{x}",
    r"\text{<img src='https://example.test/a.png' onerror='alert(1)'>}",
    r"\text{<script>alert(1)</script>}", "{" * 65 + "x" + "}" * 65, "x" * 20_001,
])
def test_invalid_or_unsafe_equations_warn_and_preserve_source(tmp_path, formula):
    document = build_document("$$" + formula + "$$", AssetResolver(tmp_path, offline=True), tmp_path)
    soup = BeautifulSoup(document.html, "html.parser")
    assert len(document.warnings) == 1 and "Equation could not be typeset" in document.warnings[0]
    assert soup.select_one("code.math-error").get_text() == "$$" + formula + "$$"
    assert not soup.find(["math", "script", "img", "a"])
    assert document.images == 0


@pytest.mark.pdf
@pytest.mark.parametrize("paper", ["letter", "a4"])
def test_offline_equation_pdf_has_embedded_math_font_and_readable_layout(tmp_path, chromium, paper):
    import pymupdf

    source = tmp_path / "equations.mdx"
    source.write_text(EQUATIONS, encoding="utf-8")
    result = convert(source, paper=paper, offline=True)
    assert not result.warnings
    assert source.read_text(encoding="utf-8") == EQUATIONS
    with pymupdf.open(result.output) as pdf:
        assert len(pdf) == 1
        text = "".join(page.get_text() for page in pdf)
        assert "$" not in text and "\\frac" not in text
        assert "otherwise" in text and "then continue" in text and "×" in text
        fonts = {font[3].split("+")[-1] for page in pdf for font in page.get_fonts()}
        assert "STIXTwoMath-Regular" in fonts
        assert "SourceSansPro-Regular" in fonts
        for page in pdf:
            for word in page.get_text("words"):
                assert 40 <= word[0] <= word[2] <= page.rect.width - 40
                assert 40 <= word[1] <= word[3] <= page.rect.height - 40
    embedded_math = False
    for page in PdfReader(result.output).pages:
        for ref in page["/Resources"]["/Font"].values():
            font = ref.get_object()
            if "STIXTwoMath-Regular" in str(font.get("/BaseFont")):
                descriptor = font["/DescendantFonts"][0].get_object()["/FontDescriptor"]
                assert descriptor["/FontFile2"].get_data()
                embedded_math = True
    assert embedded_math


@pytest.mark.pdf
def test_missing_math_font_fails_explicitly(tmp_path, chromium):
    document = build_document("$x^2$", AssetResolver(tmp_path, offline=True), tmp_path)
    path = tmp_path / "document.html"
    path.write_text(document.html, encoding="utf-8")
    (tmp_path / "fonts" / MATH_FONT_FACE[3]).unlink()
    output = tmp_path / "equation.pdf"
    with pytest.raises(PrintKitError, match="Bundled fonts failed to load: STIX Two Math"):
        render_pdf(path, output)
    assert not output.exists()


def test_double_struck_and_bold_digits_use_actual_math_characters(tmp_path):
    document = build_document(r"$\mathbb{1}_{ib}$ and $\mathbf{12}$",
                              AssetResolver(tmp_path, offline=True), tmp_path)
    soup = BeautifulSoup(document.html, "html.parser")
    assert not document.warnings
    assert [tag.get_text() for tag in soup.find_all("mn")] == ["𝟙", "𝟏𝟐"]


@pytest.mark.pdf
def test_equals_signs_line_up_in_printed_align_environment(tmp_path, chromium):
    import pymupdf

    source = tmp_path / "aligned.mdx"
    source.write_text(r"$$\begin{align*}x &= 1 \\ \mathcal{L}_{\text{coord}} &= \sum_{b=0}^{B} x_b\end{align*}$$",
                      encoding="utf-8")
    result = convert(source, offline=True)
    assert not result.warnings
    with pymupdf.open(result.output) as pdf:
        equals = [char["bbox"][0] for block in pdf[0].get_text("rawdict")["blocks"]
                  for line in block.get("lines", []) for span in line["spans"]
                  for char in span["chars"] if char["c"] == "="]
    # The third equals sign belongs to the summation limit b=0.
    assert len(equals) == 3
    assert equals[0] == pytest.approx(equals[1], abs=0.5)


@pytest.mark.pdf
def test_math_font_survives_system_body_font_fallback(tmp_path, monkeypatch, chromium):
    import pymupdf
    from mdx_printkit.typography import SYSTEM_FACES

    missing = ("PrintKitNonexistentFont019abcdef",)
    monkeypatch.setitem(SYSTEM_FACES, "arial", (missing, missing, missing))
    source = tmp_path / "fallback.mdx"
    source.write_text(r"Body $\mathbb{1}_{ib}$ and `code`", encoding="utf-8")
    result = convert(source, font="arial", offline=True)
    assert len(result.warnings) == 1 and "using bundled Source Sans Pro" in result.warnings[0]
    with pymupdf.open(result.output) as pdf:
        fonts = {font[3].split("+")[-1] for font in pdf[0].get_fonts()}
        assert fonts == {"STIXTwoMath-Regular", "SourceSansPro-Regular", "IBMPlexMono-Regular"}
        assert "𝟙" in pdf[0].get_text()
