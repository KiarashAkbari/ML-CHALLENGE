import argparse
import sys

from .config import Config, load_config
from .errors import PipelineError
from .exit_codes import ExitCode
from .fetch import SocrataSource, fetch_all, query_fingerprint
from .http import HttpClient
from .store import RawPageStore

DEFAULT_CONFIG = "config/default.toml"
COMMANDS = ("run", "fetch")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="data-factory")
    parser.add_argument("command", nargs="?", default="run", choices=COMMANDS)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    return parser


def _fetch(cfg: Config) -> None:
    client = HttpClient(cfg.http)
    source = SocrataSource.from_env(client, cfg.source)
    store = RawPageStore(cfg.paths.raw_dir / query_fingerprint(cfg.source))
    result = fetch_all(source, store)
    print(
        f"pages_total={result.pages_total} pages_fetched={result.pages_fetched} "
        f"rows_fetched={result.rows_fetched} resumed_from_page={result.resumed_from_page} "
        f"requests={client.request_count} dir={store.directory}"
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        cfg = load_config(args.config)
        if args.command == "fetch":
            _fetch(cfg)
            return int(ExitCode.OK)
        print("error: 'run' is not implemented yet", file=sys.stderr)
        return int(ExitCode.UNEXPECTED)
    except PipelineError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return int(exc.exit_code)