import argparse
import subprocess
import sys
from pathlib import Path

from divar_extractor.extractor import DivarListingExtractor, listing_to_csv


def _copy_to_clipboard_windows(text: str) -> None:
    """Put text on the clipboard (UTF-16). Tabs survive; terminal copy often breaks them."""
    subprocess.run(
        ["clip"],
        input=text.encode("utf-16"),
        check=True,
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
        "--no-header",
        action="store_true",
        help="Omit CSV header row",
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
            "Copy the output to the Windows clipboard (UTF-16). "
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
    extractor = DivarListingExtractor(html)
    listing = extractor.extract()
    if args.tsv:
        delim = "\t"
    else:
        delim = {"comma": ",", "tab": "\t", "pipe": "|"}[args.delimiter]
    text = listing_to_csv(listing, include_header=not args.no_header, delimiter=delim)
    sys.stdout.write(text)
    if args.clipboard:
        if sys.platform != "win32":
            print("--clipboard is only supported on Windows.", file=sys.stderr)
            sys.exit(1)
        _copy_to_clipboard_windows(text)
        print("Copied to clipboard.", file=sys.stderr)


if __name__ == "__main__":
    main()
