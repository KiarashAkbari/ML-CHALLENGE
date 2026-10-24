"""Streaming classification of records into passed and quarantined."""
from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field

from .contract import UNIQUE_KEY, ReasonCode
from .validate import validate_record


@dataclass(frozen=True)
class ClassifiedRecord:
    row: Mapping[str, object]
    reasons: tuple[ReasonCode, ...]

    @property
    def is_valid(self) -> bool:
        return not self.reasons


@dataclass
class QualityReport:
    total: int = 0
    passed: int = 0
    quarantined: int = 0
    by_reason: Counter[ReasonCode] = field(default_factory=Counter)

    def add(self, reasons: tuple[ReasonCode, ...]) -> None:
        self.total += 1
        if reasons:
            self.quarantined += 1
            self.by_reason.update(reasons)
        else:
            self.passed += 1

    @property
    def quarantine_ratio(self) -> float:
        return self.quarantined / self.total if self.total else 0.0


def classify_records(
    rows: Iterable[Mapping[str, object]], report: QualityReport
) -> Iterator[ClassifiedRecord]:
    """Lazily classify rows; the report is updated as the stream is consumed."""
    seen_keys: set[str] = set()
    for row in rows:
        reasons = list(validate_record(row))
        raw_key = row.get(UNIQUE_KEY)
        key = "" if raw_key is None else str(raw_key).strip()
        if key and key in seen_keys:
            reasons.append(ReasonCode.DUPLICATE_UNIQUE_KEY)
        elif key and not reasons:
            seen_keys.add(key)
        result = ClassifiedRecord(row, tuple(reasons))
        report.add(result.reasons)
        yield result