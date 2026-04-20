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
    args = parser.parse_args()
    if args.html_file and args.html_file != "-":
        html = Path(args.html_file).read_text(encoding="utf-8")
    else:
        html = sys.stdin.read()
    extractor = DivarListingExtractor(html)
    listing = extractor.extract()
    write_listing_csv(listing, sys.stdout, include_header=not args.no_header)


if __name__ == "__main__":
    main()
