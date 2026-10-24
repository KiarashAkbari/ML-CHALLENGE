import argparse
import sys

from .config import Config, load_config
from .errors import DataError, PipelineError
from .exit_codes import ExitCode
from .fetch import SocrataSource, fetch_all, query_fingerprint
from .http import HttpClient
from .quality import QualityReport, classify_records, enforce_threshold
from .quarantine import QuarantineWriter
from .store import RawPageStore

DEFAULT_CONFIG = "config/default.toml"
COMMANDS = ("run", "fetch", "validate")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="data-factory")
    parser.add_argument("command", nargs="?", default="run", choices=COMMANDS)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    return parser


def _raw_store(cfg: Config) -> RawPageStore:
    return RawPageStore(cfg.paths.raw_dir / query_fingerprint(cfg.source))


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


def _validate(cfg: Config) -> None:
    store = _raw_store(cfg)
    if store.completed_pages() == 0:
        raise DataError(
            "No raw pages found; run 'fetch' first",
            context={"dir": str(store.directory)},
        )
    report = QualityReport()
    with QuarantineWriter(cfg.paths.quarantine_dir) as writer:
        for record in classify_records(store.iter_rows(), report):
            if not record.is_valid:
                writer.write(record)
    reasons = ",".join(
        f"{code.value}={count}"
        for code, count in sorted(report.by_reason.items(), key=lambda item: item[0].value)
    ) or "none"
    print(
        f"total={report.total} passed={report.passed} quarantined={report.quarantined} "
        f"ratio={report.quarantine_ratio:.6f} reasons={reasons} "
        f"quarantine_file={writer.path}"
    )
    enforce_threshold(
        report,
        max_ratio=cfg.quality.max_quarantine_ratio,
        min_rows=cfg.quality.min_rows_for_threshold,
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        cfg = load_config(args.config)
        if args.command == "fetch":
            _fetch(cfg)
            return int(ExitCode.OK)
        if args.command == "validate":
            _validate(cfg)
            return int(ExitCode.OK)
        print("error: 'run' is not implemented yet", file=sys.stderr)
        return int(ExitCode.UNEXPECTED)
    except PipelineError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return int(exc.exit_code)