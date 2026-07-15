import csv
import math
from dataclasses import dataclass
from pathlib import Path

from app.core.config import Settings
from app.core.exceptions import DatasetParseError, InvalidDatasetError


@dataclass(frozen=True)
class ParsedDataset:
    encoding: str
    delimiter: str
    columns: list[str]
    row_count: int
    preview: list[dict[str, str | None]]
    warnings: list[dict[str, str]]


def _detect_encoding(path: Path) -> str:
    with path.open("rb") as source:
        sample = source.read(65536)
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            sample.decode(encoding, errors="strict")
            return encoding
        except UnicodeDecodeError:
            continue
    raise DatasetParseError("Dataset encoding is unsupported")


def _safe_cell(value: object, limit: int) -> str | None:
    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    text = str(value)
    return text if len(text) <= limit else f"{text[: limit - 1]}…"


def parse_csv(path: Path, settings: Settings) -> ParsedDataset:
    encoding = _detect_encoding(path)
    try:
        with path.open("r", encoding=encoding, newline="") as source:
            sample = source.read(65536)
            source.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
            except csv.Error as exc:
                raise DatasetParseError("CSV delimiter could not be detected") from exc
            reader = csv.reader(source, dialect=dialect, strict=True)
            try:
                headers = next(reader)
            except StopIteration as exc:
                raise InvalidDatasetError("CSV must contain a header row") from exc
            headers = [header.lstrip("\ufeff").strip() for header in headers]
            if not headers or all(not header for header in headers):
                raise InvalidDatasetError("CSV header is empty")
            if len(headers) > settings.dataset_max_columns:
                raise InvalidDatasetError("CSV exceeds the configured column limit")
            if len(set(headers)) != len(headers):
                raise InvalidDatasetError("CSV headers must be unique")
            preview: list[dict[str, str | None]] = []
            row_count = 0
            for row_number, row in enumerate(reader, start=2):
                if len(row) != len(headers):
                    raise DatasetParseError(f"Malformed CSV row {row_number}: expected {len(headers)} columns")
                row_count += 1
                if len(preview) < settings.dataset_preview_rows:
                    preview.append(
                        {
                            header: _safe_cell(value, settings.dataset_max_cell_length)
                            for header, value in zip(headers, row, strict=True)
                        }
                    )
    except UnicodeError as exc:
        raise DatasetParseError("CSV contains invalid text encoding") from exc
    except csv.Error as exc:
        raise DatasetParseError("CSV structure is malformed") from exc
    return ParsedDataset(encoding, dialect.delimiter, headers, row_count, preview, [])
