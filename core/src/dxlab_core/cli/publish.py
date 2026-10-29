# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""`dxlab publish apps/<app>`: đóng gói thư mục ứng dụng và gửi `POST /definitions/{app_id}/versions`."""

import argparse
import mimetypes
from pathlib import Path
from urllib.parse import quote

from dxlab_core.cli.api import api_request
from dxlab_core.cli.context import CliError, Context, invoke


def register(subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]") -> None:
    parser = subparsers.add_parser(
        "publish",
        help="nạp một gói ứng dụng (apps/<app>) thành phiên bản mới, chờ duyệt",
        description="app_id lấy từ tên thư mục. Mọi tệp trong thư mục (trừ tệp ẩn và thư mục eval/) được gửi, tên tệp là đường dẫn tương đối.",
    )
    parser.add_argument("app_dir", metavar="apps/<app>", type=Path, help="thư mục gói ứng dụng")
    parser.set_defaults(func=lambda args: invoke(run, args))


def collect_files(app_dir: Path) -> list[tuple[str, Path]]:
    """Mọi tệp thường trong thư mục, bỏ tệp/thư mục ẩn và thư mục `eval/` ở gốc gói (công cụ đo, validator
    cũng bỏ); sắp theo đường dẫn tương đối (POSIX) cho ổn định."""
    found = []
    for path in app_dir.rglob("*"):
        relative = path.relative_to(app_dir)
        if any(part.startswith(".") for part in relative.parts) or relative.parts[0] == "eval" or not path.is_file():
            continue
        found.append((relative.as_posix(), path))
    return sorted(found)


def run(args: argparse.Namespace, ctx: Context) -> int:
    app_dir: Path = args.app_dir
    if not app_dir.is_dir():
        raise CliError(f"Không có thư mục ứng dụng: {app_dir}")
    app_id = app_dir.resolve().name
    files = collect_files(app_dir)
    if not files:
        raise CliError(f"Thư mục {app_dir} không có tệp nào để nạp.")

    multipart = [
        ("files", (name, path.read_bytes(), mimetypes.guess_type(name)[0] or "application/octet-stream"))
        for name, path in files
    ]
    response = api_request(ctx, "POST", f"/definitions/{quote(app_id, safe='')}/versions", files=multipart)
    result = response.json()
    ctx.say(f"Đã nạp {result['app_id']} phiên bản {result['version']}, trạng thái {result['status']}")
    return 0
