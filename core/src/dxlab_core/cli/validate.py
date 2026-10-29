# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""`dxlab validate <thư mục>`: chạy đúng validator của `/api/definitions` trên máy, trước khi nạp hay mở PR.

Thư mục là một ứng dụng (có `process_model.json`) hoặc thư mục cha chứa nhiều ứng dụng (ví dụ `apps/`).
"""

import argparse
import sys
from pathlib import Path

from dxlab_core.definitions.engine import PROCESS_MODEL
from dxlab_core.definitions.validator import package_files, validate_package


def read_app_dir(app_dir: Path) -> dict[str, bytes]:
    files = {str(p.relative_to(app_dir).as_posix()): p.read_bytes() for p in app_dir.rglob("*") if p.is_file()}
    return package_files(files)


def find_apps(root: Path) -> list[Path]:
    if (root / PROCESS_MODEL).is_file():
        return [root]
    return sorted(p.parent for p in root.glob(f"*/{PROCESS_MODEL}"))


def run(args: argparse.Namespace) -> int:
    root = Path(args.path)
    if not root.is_dir():
        print(f"Không có thư mục {root}.", file=sys.stderr)
        return 2
    apps = find_apps(root)
    if not apps:
        print(f"Không tìm thấy ứng dụng nào (thư mục có {PROCESS_MODEL}) trong {root}.", file=sys.stderr)
        return 2
    failed = 0
    for app_dir in apps:
        issues = validate_package(read_app_dir(app_dir))
        if issues:
            failed += 1
            print(f"✗ {app_dir.name}: {len(issues)} lỗi")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"✓ {app_dir.name}: hợp lệ")
    return 1 if failed else 0


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("validate", help="Kiểm gói ứng dụng bằng validator của core")
    parser.add_argument("path", help="Thư mục ứng dụng hoặc thư mục chứa các ứng dụng (ví dụ apps/)")
    parser.set_defaults(func=run)
