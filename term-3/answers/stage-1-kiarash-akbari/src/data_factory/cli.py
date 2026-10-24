import argparse


def main() -> int:
    parser = argparse.ArgumentParser(prog="data-factory")
    parser.add_argument("command", nargs="?", default="run")
    parser.parse_args()
    return 0