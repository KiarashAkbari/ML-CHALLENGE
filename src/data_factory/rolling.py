"""Rolling window: fetch only what was created since the last run."""
from __future__ import annotations

import json
from dataclasses import replace
from datetime import date
from pathlib import Path

from .config import Config
from .errors import ConfigError, DataError

ROLLING_DIR = "rolling"
DATE_LENGTH = 10


def rolling_manifest_path(manifest_path: Path) -> Path:
    return manifest_path.with_name(
        f"{manifest_path.stem}.{ROLLING_DIR}{manifest_path.suffix}"
    )


def _read_watermark(path: Path) -> date | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as exc:
        raise DataError(f"Manifest is not valid JSON: {path}", context={"path": str(path)}) from exc
    watermark = data.get("watermark") if isinstance(data, dict) else None
    value = watermark.get("max_created_at") if isinstance(watermark, dict) else None
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:DATE_LENGTH])
    except ValueError as exc:
        raise DataError(f"Bad watermark in {path}: {value!r}", context={"path": str(path)}) from exc


def load_watermark(manifest_path: Path) -> date:
    """Latest creation date seen by the previous full or rolling run."""
    found = [
        day
        for day in (
            _read_watermark(rolling_manifest_path(manifest_path)),
            _read_watermark(manifest_path),
        )
        if day is not None
    ]
    if not found:
        raise DataError(
            "No previous run with a watermark found; run the full pipeline first",
            context={"manifest": str(manifest_path)},
        )
    return max(found)


def rolling_config(cfg: Config, since: date, today: date) -> Config:
    """Same pipeline, narrowed to [since, today] with outputs kept apart from the full run."""
    if since > today:
        raise ConfigError("Last-run watermark is after today")
    paths = replace(
        cfg.paths,
        curated_dir=cfg.paths.curated_dir / ROLLING_DIR,
        quarantine_dir=cfg.paths.quarantine_dir / ROLLING_DIR,
        manifest_path=rolling_manifest_path(cfg.paths.manifest_path),
    )
    return replace(cfg, source=replace(cfg.source, start_date=since, end_date=today), paths=paths)