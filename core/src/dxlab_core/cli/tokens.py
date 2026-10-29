# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Lưu và làm mới token của CLI trong `DXLAB_TOKEN_FILE` (quyền 0600, ghi nguyên tử)."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from dxlab_core.cli.context import CliError, Context
from dxlab_core.cli.oidc import refresh_grant

# Làm mới trước khi hết hạn thật để token không chết giữa chừng một request.
EXPIRY_MARGIN_SECONDS = 30


def save_token(ctx: Context, response: dict[str, Any]) -> dict[str, Any]:
    """Ghi phản hồi của token endpoint ra tệp token; trả về nội dung đã ghi."""
    now = ctx.now()
    stored: dict[str, Any] = {
        "issuer": ctx.settings.issuer,
        "client_id": ctx.settings.client_id,
        "access_token": response["access_token"],
        "expires_at": now + float(response.get("expires_in", 0)),
        "refresh_token": response.get("refresh_token"),
        "refresh_expires_at": None,
    }
    refresh_expires_in = response.get("refresh_expires_in")
    if stored["refresh_token"] and refresh_expires_in:
        stored["refresh_expires_at"] = now + float(refresh_expires_in)
    _write_private(ctx.settings.token_file, stored)
    return stored


def load_token(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError):
        raise CliError(f"Tệp token {path} hỏng hoặc không đọc được. Chạy `dxlab login` để đăng nhập lại.") from None
    if not isinstance(data, dict) or "access_token" not in data:
        raise CliError(f"Tệp token {path} không đúng định dạng. Chạy `dxlab login` để đăng nhập lại.")
    return data


def delete_token(path: Path) -> bool:
    try:
        path.unlink()
    except FileNotFoundError:
        return False
    return True


def get_access_token(ctx: Context) -> str:
    """Access token còn hạn; tự làm mới bằng refresh token khi sắp hết hạn."""
    stored = load_token(ctx.settings.token_file)
    if stored is None:
        raise CliError("Chưa đăng nhập. Chạy `dxlab login`.")
    if ctx.now() < float(stored.get("expires_at", 0)) - EXPIRY_MARGIN_SECONDS:
        return str(stored["access_token"])

    refresh_token = stored.get("refresh_token")
    refresh_expires_at = stored.get("refresh_expires_at")
    if not refresh_token or (refresh_expires_at is not None and ctx.now() >= float(refresh_expires_at)):
        raise CliError("Phiên đăng nhập đã hết hạn. Chạy `dxlab login` để đăng nhập lại.")
    try:
        response = refresh_grant(ctx, refresh_token)
    except CliError:
        raise CliError("Không làm mới được phiên đăng nhập. Chạy `dxlab login` để đăng nhập lại.") from None
    return str(save_token(ctx, response)["access_token"])


def _write_private(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".token-", suffix=".tmp")  # mkstemp tạo tệp 0600
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
