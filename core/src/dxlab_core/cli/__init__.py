# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Lệnh `dxlab`. Mỗi lệnh con là một module `dxlab_core.cli.<tên>` có `register(subparsers)`."""

import argparse
import importlib
import sys
from collections.abc import Sequence

COMMANDS = ["login", "logout", "whoami", "publish", "validate"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dxlab", description="Công cụ dòng lệnh của DX-Lab.")
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="<lệnh>")
    for name in COMMANDS:
        importlib.import_module(f"dxlab_core.cli.{name}").register(subparsers)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
