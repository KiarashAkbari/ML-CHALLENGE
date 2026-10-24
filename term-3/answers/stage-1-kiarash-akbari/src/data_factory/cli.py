import argparse
import sys

from .config import Config, ReferenceConfig, load_config
from .errors import ConfigError, DataError, PipelineError
from .exit_codes import ExitCode
from .fetch import SocrataSource, fetch_all, query_fingerprint
from .http import HttpClient
from .manifest import build_manifest, utc_now_iso, write_manifest
from .pipeline import process
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


def _require_raw(store: RawPageStore) -> None:
    if store.completed_pages() == 0:
        raise DataError(
            "No raw pages found; run 'fetch' first",
            context={"dir": str(store.directory)},
        )


def _fetch(cfg: Config, client: HttpClient) -> None:
    source = SocrataSource.from_env(client, cfg.source)
    store = _raw_store(cfg)
    result = fetch_all(source, store)
    print(
        f"pages_total={result.pages_total} pages_fetched={result.pages_fetched} "
        f"rows_fetched={result.rows_fetched} resumed_from_page={result.resumed_from_page} "
        f"requests={client.request_count} dir={store.directory}"
    )


def _fetch_reference(cfg: Config, client: HttpClient) -> None:
    ref = _reference_config(cfg)
    rows = fetch_reference(client, ref)
    write_reference(rows, ref.path)
    print(f"reference_rows={len(rows)} requests={client.request_count} path={ref.path}")


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


def _build(cfg: Config, requests: int, started_at: str) -> None:
    ref = _reference_config(cfg)
    zip_index = build_zip_index(read_reference(ref.path))
    store = _raw_store(cfg)
    _require_raw(store)
    result = process(store.iter_rows(), cfg, zip_index)
    manifest = build_manifest(
        cfg=cfg,
        result=result,
        requests=requests,
        started_at=started_at,
        finished_at=utc_now_iso(),
    )
    write_manifest(cfg.paths.manifest_path, manifest)
    report, stats = result.report, result.stats
    print(
        f"total={report.total} passed={report.passed} quarantined={report.quarantined} "
        f"matched={stats.matched} missing_zip={stats.missing_zip} "
        f"unmatched_zip={stats.unmatched_zip} "
        f"top_unmatched={stats.unmatched_by_zip.most_common(TOP_UNMATCHED_ZIPS)} "
        f"ambiguous={stats.ambiguous} requests={requests} "
        f"manifest={cfg.paths.manifest_path}"
    )


def _run(cfg: Config) -> None:
    started_at = utc_now_iso()
    client = HttpClient(cfg.http)
    _fetch(cfg, client)
    ref = _reference_config(cfg)
    if not ref.path.is_file():
        _fetch_reference(cfg, client)
    _build(cfg, client.request_count, started_at)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        cfg = load_config(args.config)
        if args.command == "run":
            _run(cfg)
        elif args.command == "fetch":
            _fetch(cfg, HttpClient(cfg.http))
        elif args.command == "fetch-reference":
            _fetch_reference(cfg, HttpClient(cfg.http))
        elif args.command == "validate":
            _validate(cfg)
        else:
            _build(cfg, 0, utc_now_iso())
        return int(ExitCode.OK)
    except PipelineError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return int(exc.exit_code)