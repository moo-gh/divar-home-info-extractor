import argparse
import sys
from pathlib import Path

from divar_extractor.extractor import DivarListingExtractor, write_listing_csv


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
    write_listing_csv(listing, sys.stdout, include_header=not args.no_header)


if __name__ == "__main__":
    main()
