import argparse
import sys

from .config import load_config
from .errors import PipelineError
from .exit_codes import ExitCode

DEFAULT_CONFIG = "config/default.toml"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="data-factory")
    parser.add_argument("command", nargs="?", default="run")
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        load_config(args.config)
    except PipelineError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return int(exc.exit_code)
    return int(ExitCode.OK)