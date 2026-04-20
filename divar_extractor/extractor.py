from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, fields
from typing import IO, Optional

from bs4 import BeautifulSoup, Tag


def _norm_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


@dataclass
class ExtractedListing:
    title: str
    publish_date: str
    meter: str
    creation_year: str
    number_of_rooms: str
    deposit_price: str
    rent_price: str
    which_floor: str
    has_parking: str
    has_elevator: str

    def as_row_dict(self) -> dict[str, str]:
        return {f.name: getattr(self, f.name) for f in fields(self)}


class DivarListingExtractor:
    """Parse a Divar single-post HTML fragment or full page."""

    def __init__(self, html: str):
        self._soup = BeautifulSoup(html, "lxml")

    def extract(self) -> ExtractedListing:
        meter, creation_year, number_of_rooms = self._extract_meter_area_rooms()
        deposit_price, rent_price = self._extract_deposit_rent()
        return ExtractedListing(
            title=self._extract_title(),
            publish_date=self._extract_publish_date(),
            meter=meter,
            creation_year=creation_year,
            number_of_rooms=number_of_rooms,
            deposit_price=deposit_price,
            rent_price=rent_price,
            which_floor=self._extract_floor(),
            has_parking=self._feature_parking(),
            has_elevator=self._feature_elevator(),
        )

    def _extract_title(self) -> str:
        for sel in (
            "h1",
            "h1.kt-title-row__title",
            ".kt-title-row__title--primary",
            "[data-testid='post-title']",
            "meta[property='og:title']",
        ):
            el = self._soup.select_one(sel)
            if not el:
                continue
            if el.name == "meta":
                content = el.get("content")
                if content:
                    return _norm_ws(content)
            else:
                t = el.get_text()
                if t and t.strip() and t.strip() != "توضیحات":
                    return _norm_ws(t)
        return ""

    def _extract_publish_date(self) -> str:
        for sel in ("time[datetime]", "time", "[class*='post-meta']", "[class*='published']"):
            el = self._soup.select_one(sel)
            if not el:
                continue
            dt = el.get("datetime")
            if dt:
                return _norm_ws(str(dt))
            txt = el.get_text()
            if txt and re.search(r"\d", txt):
                return _norm_ws(txt)
        meta = self._soup.select_one("meta[property='article:published_time']")
        if meta and meta.get("content"):
            return _norm_ws(meta["content"])
        return ""

    def _table_row_by_headers(
        self, header_labels: list[str]
    ) -> tuple[Optional[list[str]], Optional[list[Tag]]]:
        """Find a kt-group-row (or similar) whose header cells match labels in order."""
        for table in self._soup.find_all("table"):
            thead = table.find("thead")
            tbody = table.find("tbody")
            if not thead or not tbody:
                continue
            header_row = thead.find("tr")
            data_row = tbody.find("tr")
            if not header_row or not data_row:
                continue
            ths = header_row.find_all(["th", "td"])
            headers: list[str] = []
            for th in ths:
                title_el = th.select_one(".kt-group-row-item__title") or th
                headers.append(_norm_ws(title_el.get_text()))
            if len(headers) < len(header_labels):
                continue
            match = True
            for i, label in enumerate(header_labels):
                if label not in headers[i]:
                    match = False
                    break
            if not match:
                continue
            tds = data_row.find_all(["td", "th"])
            values = [_norm_ws(td.get_text()) for td in tds]
            return values, tds
        return None, None

    def _extract_meter_area_rooms(self) -> tuple[str, str, str]:
        values, _ = self._table_row_by_headers(
            ["متراژ", "ساخت", "اتاق"]
        )
        if values and len(values) >= 3:
            return values[0], values[1], values[2]
        return "", "", ""

    def _extract_deposit_rent(self) -> tuple[str, str]:
        values, _ = self._table_row_by_headers(
            ["ودیعه", "اجاره"]
        )
        if values and len(values) >= 2:
            return values[0], values[1]
        slider = self._soup.select_one(".convert-slider table")
        if slider:
            tbody = slider.find("tbody")
            if tbody:
                tr = tbody.find("tr")
                if tr:
                    tds = tr.find_all("td")
                    if len(tds) >= 2:
                        return (
                            _norm_ws(tds[0].get_text()),
                            _norm_ws(tds[1].get_text()),
                        )
        return "", ""

    def _unexpandable_value(self, title_text: str) -> str:
        for row in self._soup.select(".kt-unexpandable-row"):
            title_el = row.select_one(".kt-unexpandable-row__title, .kt-base-row__title")
            if not title_el:
                continue
            if title_text in _norm_ws(title_el.get_text()):
                val_el = row.select_one(".kt-unexpandable-row__value")
                if val_el:
                    return _norm_ws(val_el.get_text())
        return ""

    def _extract_floor(self) -> str:
        return self._unexpandable_value("طبقه")

    def _feature_cell_by_icon(self, icon_class_substr: str) -> str:
        for table in self._soup.find_all("table", class_=re.compile(r"group-row")):
            thead = table.find("thead")
            tbody = table.find("tbody")
            if not thead or not tbody:
                continue
            header_row = thead.find("tr")
            data_row = tbody.find("tr")
            if not header_row or not data_row:
                continue
            ths = header_row.find_all("th")
            tds = data_row.find_all("td")
            if len(ths) != len(tds):
                continue
            for th, td in zip(ths, tds):
                icon = th.find("i", class_=re.compile(icon_class_substr))
                if icon:
                    return _norm_ws(td.get_text())
        return ""

    @staticmethod
    def _yes_no_from_feature_text(text: str, keyword: str) -> str:
        t = _norm_ws(text)
        if not t:
            return ""
        low = t.lower()
        if "ندارد" in t or "بدون" in t:
            return "no"
        if "دارد" in t or "هست" in t:
            return "yes"
        if keyword in t and "ن" not in t[: min(3, len(t))]:
            return "yes"
        return t

    def _feature_elevator(self) -> str:
        txt = self._feature_cell_by_icon("elevator")
        if txt:
            return self._yes_no_from_feature_text(txt, "آسانسور")
        for td in self._soup.find_all("td"):
            t = _norm_ws(td.get_text())
            if "آسانسور" in t:
                return self._yes_no_from_feature_text(t, "آسانسور")
        return ""

    def _feature_parking(self) -> str:
        txt = self._feature_cell_by_icon("parking")
        if txt:
            return self._yes_no_from_feature_text(txt, "پارکینگ")
        for td in self._soup.find_all("td"):
            t = _norm_ws(td.get_text())
            if "پارکینگ" in t:
                return self._yes_no_from_feature_text(t, "پارکینگ")
        return ""


CSV_COLUMNS = [
    "title",
    "publish_date",
    "meter",
    "creation_year",
    "number_of_rooms",
    "deposit_price",
    "rent_price",
    "which_floor",
    "has_parking",
    "has_elevator",
]


def listing_to_csv(listing: ExtractedListing, include_header: bool = True) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, quoting=csv.QUOTE_MINIMAL)
    if include_header:
        writer.writerow(CSV_COLUMNS)
    row = [getattr(listing, col) for col in CSV_COLUMNS]
    writer.writerow(row)
    return buf.getvalue()


def write_listing_csv(listing: ExtractedListing, out: IO[str], include_header: bool = True) -> None:
    writer = csv.writer(out, quoting=csv.QUOTE_MINIMAL)
    if include_header:
        writer.writerow(CSV_COLUMNS)
    writer.writerow([getattr(listing, col) for col in CSV_COLUMNS])
