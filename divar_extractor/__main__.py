import argparse
import subprocess
import sys
from pathlib import Path

from divar_extractor.extractor import DivarListingExtractor, listing_to_csv


def _copy_to_clipboard(text: str) -> None:
    """Put text on the system clipboard. Tabs survive; terminal copy often breaks them."""
    if sys.platform == "win32":
        subprocess.run(
            ["clip"],
            input=text.encode("utf-16"),
            check=True,
        )
    elif sys.platform == "darwin":
        subprocess.run(
            ["pbcopy"],
            input=text.encode("utf-8"),
            check=True,
        )
    else:
        raise RuntimeError(
            "--clipboard is only supported on Windows and macOS."
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract Divar listing fields from HTML and print CSV."
    )
    parser.add_argument(
        "html_file",
        nargs="?",
        help="Path to HTML file, or '-' for stdin (default: stdin if no path)",
    )
    parser.add_argument(
        "--header",
        action="store_true",
        help="Include the column-name row (use once to label columns, then omit).",
    )
    parser.add_argument(
        "--paste",
        action="store_true",
        help=(
            "Read stdin until a line that equals the paste marker (default: EOF). "
            "Use this when pasting HTML in the terminal instead of relying on Ctrl+Z / EOF."
        ),
    )
    parser.add_argument(
        "--paste-marker",
        default="EOF",
        metavar="TEXT",
        help="Line that ends pasted input when using --paste (default: %(default)s).",
    )
    parser.add_argument(
        "--tsv",
        action="store_true",
        help="Same as --delimiter tab.",
    )
    parser.add_argument(
        "--delimiter",
        choices=("comma", "tab", "pipe"),
        default="comma",
        help=(
            "Field separator: comma (default), tab, or pipe. "
            "For Google Sheets: use pipe, paste into one cell, then Data → Split text to "
            "columns → Separator: custom → |"
        ),
    )
    parser.add_argument(
        "--clipboard",
        action="store_true",
        help=(
            "Copy the output to the system clipboard (Windows: UTF-16 via clip; macOS: UTF-8 via pbcopy). "
            "Use with --delimiter tab so tabs are not lost when copying from the terminal."
        ),
    )
    args = parser.parse_args()
    if args.html_file and args.html_file != "-":
        html = Path(args.html_file).read_text(encoding="utf-8")
    elif args.paste:
        lines: list[str] = []
        marker = args.paste_marker
        for line in sys.stdin:
            if line.rstrip("\r\n") == marker:
                break
            lines.append(line)
        html = "".join(lines)
    else:
        html = sys.stdin.read()
    if not html.strip():
        print(
            "divar_extractor: no HTML to parse (empty file or stdin).",
            file=sys.stderr,
        )
        sys.exit(1)
    extractor = DivarListingExtractor(html)
    listing = extractor.extract()
    if args.tsv:
        delim = "\t"
    else:
        delim = {"comma": ",", "tab": "\t", "pipe": "|"}[args.delimiter]
    text = listing_to_csv(listing, include_header=args.header, delimiter=delim)
    sys.stdout.write(text)
    if args.clipboard:
        try:
            _copy_to_clipboard(text)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            sys.exit(1)
        print("Copied to clipboard.", file=sys.stderr)


if __name__ == "__main__":
    main()
