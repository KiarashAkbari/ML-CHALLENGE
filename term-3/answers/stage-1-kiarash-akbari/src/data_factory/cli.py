import argparse
import sys

from .clean import JoinStats, clean_stream
from .config import Config, ReferenceConfig, load_config
from .errors import ConfigError, DataError, PipelineError
from .exit_codes import ExitCode
from .fetch import SocrataSource, fetch_all, query_fingerprint
from .http import HttpClient
from .population import build_zip_index, fetch_reference, read_reference, write_reference
from .quality import QualityReport, classify_records, enforce_threshold
from .quarantine import QuarantineWriter
from .store import RawPageStore

DEFAULT_CONFIG = "config/default.toml"
COMMANDS = ("run", "fetch", "fetch-reference", "validate", "clean")
TOP_UNMATCHED_ZIPS = 5


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="data-factory")
    parser.add_argument("command", nargs="?", default="run", choices=COMMANDS)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    return parser


def _raw_store(cfg: Config) -> RawPageStore:
    return RawPageStore(cfg.paths.raw_dir / query_fingerprint(cfg.source))


def _reference_config(cfg: Config) -> ReferenceConfig:
    if cfg.reference is None:
        raise ConfigError("Missing config section: [reference]")
    return cfg.reference


def _fetch(cfg: Config) -> None:
    client = HttpClient(cfg.http)
    source = SocrataSource.from_env(client, cfg.source)
    store = _raw_store(cfg)
    result = fetch_all(source, store)
    print(
        f"pages_total={result.pages_total} pages_fetched={result.pages_fetched} "
        f"rows_fetched={result.rows_fetched} resumed_from_page={result.resumed_from_page} "
        f"requests={client.request_count} dir={store.directory}"
    )


def _fetch_reference(cfg: Config) -> None:
    ref = _reference_config(cfg)
    client = HttpClient(cfg.http)
    rows = fetch_reference(client, ref)
    write_reference(rows, ref.path)
    print(f"reference_rows={len(rows)} requests={client.request_count} path={ref.path}")


def _require_raw(store: RawPageStore) -> None:
    if store.completed_pages() == 0:
        raise DataError(
            "No raw pages found; run 'fetch' first",
            context={"dir": str(store.directory)},
        )


def _format_reasons(report: QualityReport) -> str:
    return ",".join(
        f"{code.value}={count}"
        for code, count in sorted(report.by_reason.items(), key=lambda item: item[0].value)
    ) or "none"


def _validate(cfg: Config) -> None:
    store = _raw_store(cfg)
    _require_raw(store)
    report = QualityReport()
    with QuarantineWriter(cfg.paths.quarantine_dir) as writer:
        for record in classify_records(store.iter_rows(), report, cfg.source.timezone):
            if not record.is_valid:
                writer.write(record)
    print(
        f"total={report.total} passed={report.passed} quarantined={report.quarantined} "
        f"ratio={report.quarantine_ratio:.6f} reasons={_format_reasons(report)} "
        f"quarantine_file={writer.path}"
    )
    enforce_threshold(
        report,
        max_ratio=cfg.quality.max_quarantine_ratio,
        min_rows=cfg.quality.min_rows_for_threshold,
    )


def _clean(cfg: Config) -> None:
    ref = _reference_config(cfg)
    zip_index = build_zip_index(read_reference(ref.path))
    store = _raw_store(cfg)
    _require_raw(store)
    report = QualityReport()
    stats = JoinStats()
    classified = classify_records(store.iter_rows(), report, cfg.source.timezone)
    with QuarantineWriter(cfg.paths.quarantine_dir) as writer:
        for _ in clean_stream(_tee_quarantine(classified, writer), cfg.source.timezone,
                              zip_index, stats):
            pass
    top = stats.unmatched_by_zip.most_common(TOP_UNMATCHED_ZIPS)
    print(
        f"total={report.total} passed={report.passed} quarantined={report.quarantined} "
        f"rows_in={stats.rows_in} rows_out={stats.rows_out} matched={stats.matched} "
        f"missing_zip={stats.missing_zip} unmatched_zip={stats.unmatched_zip} "
        f"unmatched_distinct_zips={len(stats.unmatched_by_zip)} top_unmatched={top} "
        f"null_population={stats.null_population} ambiguous={stats.ambiguous}"
    )
    enforce_threshold(
        report,
        max_ratio=cfg.quality.max_quarantine_ratio,
        min_rows=cfg.quality.min_rows_for_threshold,
    )


def _tee_quarantine(records, writer):
    for record in records:
        if not record.is_valid:
            writer.write(record)
        yield record


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        cfg = load_config(args.config)
        if args.command == "fetch":
            _fetch(cfg)
            return int(ExitCode.OK)
        if args.command == "fetch-reference":
            _fetch_reference(cfg)
            return int(ExitCode.OK)
        if args.command == "validate":
            _validate(cfg)
            return int(ExitCode.OK)
        if args.command == "clean":
            _clean(cfg)
            return int(ExitCode.OK)
        print("error: 'run' is not implemented yet", file=sys.stderr)
        return int(ExitCode.UNEXPECTED)
    except PipelineError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return int(exc.exit_code)