"""Command-line entry point for both mdx-printkit and python -m mdx_printkit."""

import argparse
from pathlib import Path
import sys

from . import __version__
from .convert import ConversionResult, convert
from .errors import PrintKitError


def frame_count(value: str) -> int:
    try:
        count = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("GIF frames must be an integer from 1 to 12") from None
    if not 1 <= count <= 12:
        raise argparse.ArgumentTypeError("GIF frames must be an integer from 1 to 12")
    return count


def report(result: ConversionResult) -> None:
    for warning in result.warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    print(f"PDF: {result.output}\n{result.images} image(s), {result.gifs} animated GIF(s), "
          f"{len(result.warnings)} warning(s)")


def convert_folder(args: argparse.Namespace) -> int:
    folder = Path(args.source).expanduser().resolve()
    if not folder.is_dir():
        raise PrintKitError(f"input folder does not exist or is not a directory: {folder}")
    sources = sorted(
        (path for path in folder.iterdir() if path.is_file() and path.suffix.lower() == ".mdx"),
        key=lambda path: (path.name.casefold(), path.name),
    )
    if not sources:
        raise PrintKitError(f"no .mdx files found directly in {folder}")
    output = Path(args.output).expanduser().resolve() if args.output is not None else folder
    if output.exists() and not output.is_dir():
        raise PrintKitError(f"folder --output must be a directory: {output}")
    # Check all destinations before writing so two inputs cannot replace the same PDF.
    destinations: dict[str, Path] = {}
    for source in sources:
        destination = output / f"{source.stem}.pdf"
        key = str(destination.resolve()).casefold()
        if key in destinations:
            raise PrintKitError(f"PDF output collision: {destinations[key].name} and {source.name}; "
                                "use distinct filenames and PDF destinations")
        destinations[key] = source

    succeeded = failed = 0
    for source in sources:
        try:
            result = convert(source, output / f"{source.stem}.pdf", paper=args.paper,
                             gif_frames=args.gif_frames, offline=args.offline)
            report(result)
            succeeded += 1
        except PrintKitError as exc:
            print(f"Error: {source.name}: {exc}", file=sys.stderr)
            failed += 1
    print(f"Folder: {succeeded} succeeded, {failed} failed ({len(sources)} .mdx file(s))")
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print local Markdown/MDX files with embedded images and GIF storyboards.",
        epilog="Run 'mdx-printkit file --help' or 'mdx-printkit folder --help' for options.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    options = argparse.ArgumentParser(add_help=False)
    options.add_argument("--paper", choices=["letter", "a4"], default="letter", help="paper size (default: letter)")
    options.add_argument("--gif-frames", type=frame_count, default=4, metavar="N",
                         help="maximum distinct GIF frames, 1-12 (default: 4)")
    options.add_argument("--offline", action="store_true", help="use local images and cached downloads only")
    commands = parser.add_subparsers(dest="command", required=True)
    file_command = commands.add_parser("file", parents=[options], help="convert one .md or .mdx file")
    file_command.add_argument("source", help="local UTF-8 .md or .mdx file")
    file_command.add_argument("--output", metavar="PATH", help="PDF path (default: beside the input file)")
    folder_command = commands.add_parser("folder", parents=[options], help="convert .mdx files directly in a folder")
    folder_command.add_argument("source", help="folder containing UTF-8 .mdx files (no subfolders)")
    folder_command.add_argument("--output", metavar="DIR", help="output directory (default: the input folder)")
    arguments = list(sys.argv[1:] if argv is None else argv)
    # Keep the original single-file invocation working as a shorthand.
    if arguments and arguments[0] not in {"file", "folder", "-h", "--help", "--version"}:
        arguments.insert(0, "file")
    args = parser.parse_args(arguments)
    try:
        if args.command == "folder":
            return convert_folder(args)
        result = convert(args.source, args.output, paper=args.paper, gif_frames=args.gif_frames,
                         offline=args.offline)
    except (PrintKitError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    report(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
