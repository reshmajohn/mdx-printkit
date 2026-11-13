"""Parse dollar-delimited TeX into inert MathML for Chromium's native typesetter."""

import html
import re
import xml.etree.ElementTree as ET

from latex2mathml.converter import convert
from mdit_py_plugins.dollarmath import dollarmath_plugin

MATH_TAGS = set("math mrow mi mn mo mtext mfrac msqrt mroot msub msup msubsup "
                "munder mover munderover mtable mtr mtd mspace mstyle mpadded "
                "mphantom menclose".split())
MATH_ATTRIBUTES = {
    tag: set("displaystyle scriptlevel mathvariant mathsize mathcolor mathbackground".split())
    for tag in MATH_TAGS
}
MATH_ATTRIBUTES["math"] |= {"xmlns", "display"}
MATH_ATTRIBUTES["mo"] |= set("fence form stretchy symmetric largeop movablelimits accent lspace rspace minsize maxsize separator".split())
MATH_ATTRIBUTES["mspace"] |= {"width", "height", "depth", "linebreak"}
MATH_ATTRIBUTES["mfrac"] |= {"linethickness", "numalign", "denomalign", "bevelled"}
MATH_ATTRIBUTES["mtable"] |= set("columnalign rowalign columnspacing rowspacing columnlines rowlines frame framespacing equalrows equalcolumns width side minlabelspacing".split())
MATH_ATTRIBUTES["mtd"] |= {"columnalign", "rowalign", "columnspan", "rowspan"}
MATH_ATTRIBUTES["mtr"] |= {"columnalign", "rowalign"}
MATH_ATTRIBUTES["mover"] |= {"accent"}
MATH_ATTRIBUTES["munder"] |= {"accentunder"}
MATH_ATTRIBUTES["munderover"] |= {"accent", "accentunder"}
MATH_ATTRIBUTES["mpadded"] |= {"width", "height", "depth", "lspace", "voffset"}
MATH_ATTRIBUTES["menclose"] |= {"notation"}


def _mathml(source: str, display: bool) -> str:
    # Bound nesting before calling the recursive converter. TeX is parsed, never executed.
    if len(source) > 20_000:
        raise ValueError("equation exceeds the 20,000-character limit")
    depth = 0
    for token in re.findall(r"\\.|[{}]", source):
        if token == "{":
            depth += 1
        elif token == "}":
            depth -= 1
        if depth < 0 or depth > 64:
            raise ValueError("unbalanced or excessively nested braces")
    if depth:
        raise ValueError("unbalanced braces")
    markup = convert(source, display="block" if display else "inline")
    # The converter can emit raw content from \text and attributes from \href.
    # Accept only a small MathML vocabulary before it reaches the HTML sanitizer.
    if "<!" in markup:
        raise ValueError("unsupported markup in equation")
    root = ET.fromstring(markup)
    arities = {"mfrac": 2, "mroot": 2, "msub": 2, "msup": 2,
               "msubsup": 3, "munder": 2, "mover": 2, "munderover": 3}
    namespace = "{http://www.w3.org/1998/Math/MathML}"
    for node in root.iter():
        tag = node.tag.removeprefix(namespace)
        if node.tag != namespace + tag or tag not in MATH_TAGS:
            raise ValueError("unsupported markup in equation")
        if set(node.attrib) - MATH_ATTRIBUTES[tag]:
            raise ValueError("unsupported equation attributes")
        if tag in arities and len(node) != arities[tag]:
            raise ValueError("missing equation argument")
        if node.text and re.search(r"\\[a-zA-Z]+", node.text):
            raise ValueError("unsupported TeX command")
    # MathML Core no longer applies legacy mathvariant values to numbers. Use
    # the actual mathematical digits so indicators such as \mathbb{1} print as 𝟙.
    digit_starts = {"bold": 0x1D7CE, "double-struck": 0x1D7D8,
                    "sans-serif": 0x1D7E2, "sans-serif-bold": 0x1D7EC,
                    "monospace": 0x1D7F6}
    for node in root.iter():
        node.tag = node.tag.removeprefix(namespace)
        if node.tag == "mn" and node.get("mathvariant") in digit_starts:
            start = digit_starts[node.attrib.pop("mathvariant")]
            node.text = (node.text or "").translate(str.maketrans({str(i): chr(start + i) for i in range(10)}))
    root.set("xmlns", namespace[1:-1])
    return ET.tostring(root, encoding="unicode")


def enable_equations(parser, warn) -> None:
    parser.use(dollarmath_plugin, double_inline=True, allow_labels=False,
               allow_space=False, allow_digits=False)

    def render(self, tokens, index, options, env):
        token = tokens[index]
        display = token.type != "math_inline"
        source = token.content.strip()
        try:
            content = _mathml(source, display)
        except Exception as exc:
            # Invalid/unsupported TeX must remain visible rather than disappear.
            preview = " ".join(source.split())[:100]
            warn(f"Equation could not be typeset ({type(exc).__name__}): {preview}; preserved as TeX")
            delimiter = "$$" if display else "$"
            content = f'<code class="math-error">{html.escape(delimiter + source + delimiter)}</code>'
        wrapper = "div" if token.type == "math_block" else "span"
        css_class = "math-display" if display else "math-inline"
        return f'<{wrapper} class="{css_class}">{content}</{wrapper}>' + ("\n" if wrapper == "div" else "")

    for token_type in ("math_inline", "math_inline_double", "math_block"):
        parser.add_render_rule(token_type, render)
