# Divar Extractor

Small Python tool that parses **saved Divar listing HTML** (a post page or the main content fragment) and prints one **CSV** row with common fields: title, date, size, prices, floor, parking, and elevator.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## CLI

```bash
python -m divar_extractor listing.html
cat listing.html | python -m divar_extractor
```

Use `--no-header` if you only want the data row.

### Copy/paste (no HTML file)

You do **not** need to save HTML to a file.

**macOS — clipboard:** copy the HTML from the browser (e.g. DevTools → copy outer HTML), then:

```bash
pbpaste | python -m divar_extractor
```

**stdin — paste in the terminal:** run the command with no file (or with `-`), paste the HTML, then end input with **Ctrl+D** (macOS/Linux) or **Ctrl+Z** then Enter (Windows cmd):

```bash
python -m divar_extractor
# or: python -m divar_extractor -
```

**In Python:** assign your pasted HTML to a string and pass it to the extractor (no file involved):

```python
from divar_extractor.extractor import DivarListingExtractor, listing_to_csv

html = r"""PASTE_HTML_HERE"""
print(listing_to_csv(DivarListingExtractor(html).extract()))
```

## Output columns

`title`, `publish_date`, `meter`, `creation_year`, `number_of_rooms`, `deposit_price`, `rent_price`, `which_floor`, `has_parking`, `has_elevator`

Parking and elevator are `yes` / `no` when the page text clearly says دارد / ندارد.

**Title** is taken from `h1.kt-page-title__title` when present. **Publish date** prefers the line `انتشار آگهی: …` inside the info row; otherwise it uses `p.kt-info-row__title` (e.g. «۱ هفته پیش در …»), then `<time>` / meta tags.

## Library use

```python
from divar_extractor.extractor import DivarListingExtractor, listing_to_csv

html = open("listing.html", encoding="utf-8").read()
listing = DivarListingExtractor(html).extract()
print(listing_to_csv(listing))
```

For best results, copy HTML from the saved page or DevTools (full markup helps title and publish date).
