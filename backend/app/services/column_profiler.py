import csv
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.models.schema_profile import PhysicalType

DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%d-%b-%Y")
DATETIME_FORMATS = ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S%z")
BOOL_VALUES = {"true", "false", "yes", "no", "y", "n", "0", "1"}


def normalize_column_name(name: str) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name.strip())
    value = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    return re.sub(r"_+", "_", value)


def parse_date(value: str) -> tuple[datetime | None, bool]:
    candidate = value.strip()
    for fmt in DATETIME_FORMATS:
        try:
            return datetime.strptime(candidate, fmt), True
        except ValueError:
            pass
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(candidate, fmt), False
        except ValueError:
            pass
    return None, False


@dataclass
class PhysicalProfile:
    column_index: int
    column_name: str
    normalized_name: str
    physical_type: PhysicalType
    nullable: bool
    null_count: int
    sample_count: int
    unique_count: int
    parse_success_rate: float
    numeric_min: float | None
    numeric_max: float | None
    numeric_mean: float | None
    date_min: str | None
    date_max: str | None
    string_min_length: int | None
    string_max_length: int | None
    sample_values: list[str]
    nonnegative_rate: float
    integer_rate: float


def profile_values(index: int, name: str, values: list[str], preview_limit: int, unique_limit: int) -> PhysicalProfile:
    nonempty = [v.strip() for v in values if v.strip()]
    total = len(values)
    nulls = total - len(nonempty)
    unique = set(nonempty[:unique_limit])
    nums = []
    ints = 0
    dates = []
    datetimes = 0
    for value in nonempty:
        try:
            number = float(value.replace(",", ""))
            nums.append(number)
            ints += number.is_integer()
        except ValueError:
            pass
        parsed, is_datetime = parse_date(value)
        if parsed:
            dates.append(parsed)
            datetimes += is_datetime
    count = len(nonempty)
    numeric_rate = len(nums) / count if count else 0
    date_rate = len(dates) / count if count else 0
    normalized = normalize_column_name(name)
    unique_rate = len(unique) / count if count else 0
    if not count:
        physical = PhysicalType.empty
    elif all(v.lower() in BOOL_VALUES for v in nonempty):
        physical = PhysicalType.boolean
    elif numeric_rate == 1:
        physical = PhysicalType.integer if ints == count else PhysicalType.float
    elif date_rate >= 0.8:
        physical = PhysicalType.datetime if datetimes / max(len(dates), 1) > 0.5 else PhysicalType.date
    elif 0.2 < numeric_rate < 0.8 or 0.2 < date_rate < 0.8:
        physical = PhysicalType.mixed
    elif (normalized.endswith("_id") or normalized == "id") and unique_rate >= 0.8:
        physical = PhysicalType.identifier
    elif unique_rate <= 0.5 or len(unique) <= 50:
        physical = PhysicalType.categorical
    else:
        physical = PhysicalType.text
    lengths = [len(v) for v in nonempty]
    return PhysicalProfile(
        index,
        name,
        normalized,
        physical,
        nulls > 0,
        nulls,
        total,
        len(unique),
        max(numeric_rate, date_rate),
        min(nums) if nums else None,
        max(nums) if nums else None,
        sum(nums) / len(nums) if nums else None,
        min(dates).isoformat() if dates else None,
        max(dates).isoformat() if dates else None,
        min(lengths) if lengths else None,
        max(lengths) if lengths else None,
        list(dict.fromkeys(nonempty))[:preview_limit],
        sum(v >= 0 for v in nums) / len(nums) if nums else 0,
        ints / len(nums) if nums else 0,
    )


def scan_csv(
    path: Path, encoding: str, delimiter: str, limit: int, preview_limit: int, unique_limit: int
) -> tuple[list[PhysicalProfile], list[dict[str, str]]]:
    with path.open("r", encoding=encoding, newline="") as source:
        reader = csv.DictReader(source, delimiter=delimiter, strict=True)
        headers = reader.fieldnames or []
        columns: list[list[str]] = [[] for _ in headers]
        rows = []
        for row_number, row in enumerate(reader):
            if row_number >= limit:
                break
            safe = {header: (row.get(header) or "") for header in headers}
            rows.append(safe)
            for index, header in enumerate(headers):
                columns[index].append(safe[header])
    return [profile_values(i, name, columns[i], preview_limit, unique_limit) for i, name in enumerate(headers)], rows
