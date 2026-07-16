import csv
import hashlib
import math
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from app.core.config import Settings

NULL_TOKENS = {"", "null", "none", "na", "n/a", "nan", "missing"}
DATE_FORMATS = ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y")


def parse_number(value: str) -> float | None:
    text = value.strip().replace(",", "")
    if text.lower() in NULL_TOKENS or text.startswith(("$", "₹", "€", "£")):
        return None
    try:
        number = float(text.rstrip("%"))
        return number if math.isfinite(number) else None
    except ValueError:
        return None


def parse_date(value: str) -> datetime | None:
    text = value.strip()
    for pattern in DATE_FORMATS:
        try:
            return datetime.strptime(text, pattern)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


@dataclass
class ColumnScan:
    missing: int = 0
    values: list[str] = field(default_factory=list)
    row_indices: list[int] = field(default_factory=list)
    frequencies: Counter[str] = field(default_factory=Counter)


@dataclass
class QualityScan:
    columns: dict[str, ColumnScan]
    rows: list[dict[str, str]]
    duplicate_count: int
    duplicate_indices: list[int]
    scanned_rows: int


def scan_csv(path: Path, encoding: str, delimiter: str, settings: Settings) -> QualityScan:
    columns: dict[str, ColumnScan] = {}
    rows: list[dict[str, str]] = []
    fingerprints: set[str] = set()
    duplicate_count = 0
    duplicate_indices: list[int] = []
    with path.open("r", encoding=encoding, newline="") as stream:
        reader = csv.DictReader(stream, delimiter=delimiter)
        names = reader.fieldnames or []
        columns = {name: ColumnScan() for name in names}
        for index, raw in enumerate(reader, start=2):
            if len(rows) >= settings.data_quality_max_scan_rows:
                break
            row = {name: (raw.get(name) or "").strip() for name in names}
            digest = hashlib.sha256("\x1f".join(row[name] for name in names).encode()).hexdigest()
            if digest in fingerprints:
                duplicate_count += 1
                if len(duplicate_indices) < settings.data_quality_evidence_rows:
                    duplicate_indices.append(index)
            else:
                fingerprints.add(digest)
            rows.append(row)
            for name, value in row.items():
                profile = columns[name]
                if value.lower() in NULL_TOKENS:
                    profile.missing += 1
                else:
                    profile.values.append(value)
                    profile.frequencies[value] += 1
                    if len(profile.row_indices) < settings.data_quality_evidence_rows:
                        profile.row_indices.append(index)
    return QualityScan(columns, rows, duplicate_count, duplicate_indices, len(rows))
