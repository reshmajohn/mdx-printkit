import argparse
import sys

from . import __version__
from .convert import convert
from .errors import PrintKitError


def frame_count(value: str) -> int:
    try:
        count = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("GIF frames must be an integer from 1 to 12") from None
    if not 1 <= count <= 12:
        raise argparse.ArgumentTypeError("GIF frames must be an integer from 1 to 12")
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print a local Markdown/MDX file with embedded images and GIF storyboards.",
        epilog='Example: mdx-printkit "my notes.mdx" --output "prints/Notes.pdf"',
    )
    parser.add_argument("source", help="local UTF-8 .md or .mdx file")
    parser.add_argument("--output", metavar="PATH", help="PDF destination (default: ./output/<input-stem>.pdf)")
    parser.add_argument("--paper", choices=["letter", "a4"], default="letter", help="paper size (default: letter)")
    parser.add_argument("--gif-frames", type=frame_count, default=4, metavar="N",
                        help="maximum distinct GIF frames, 1-12 (default: 4)")
    parser.add_argument("--offline", action="store_true", help="use local images and cached downloads only")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)
    try:
        result = convert(args.source, args.output, paper=args.paper, gif_frames=args.gif_frames,
                         offline=args.offline)
    except PrintKitError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    for warning in result.warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    print(f"PDF: {result.output}\n{result.images} image(s), {result.gifs} animated GIF(s), "
          f"{len(result.warnings)} warning(s)")
    return 0
