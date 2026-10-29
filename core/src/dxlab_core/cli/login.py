# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""`dxlab login`: device flow (mặc định) hoặc direct grant cho script demo."""

import argparse
import base64
import getpass
import json
import sys
from typing import Any

from dxlab_core.cli.context import CliError, Context
from dxlab_core.cli.oidc import device_login, password_login
from dxlab_core.cli.tokens import save_token


def register(subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]") -> None:
    parser = subparsers.add_parser(
        "login",
        help="đăng nhập Keycloak (device flow) và lưu token",
        description=(
            "Mặc định dùng device flow: mở địa chỉ được in ra trên trình duyệt rồi xác nhận. "
            "Với --username dùng direct grant, chỉ dành cho script demo (seed.sh, demo-e2e.sh)."
        ),
    )
    parser.add_argument("--username", help="tên đăng nhập (direct grant, cho script demo)")
    parser.add_argument("--password", help="mật khẩu; ưu tiên --password-env để mật khẩu không nằm trong lịch sử shell")
    parser.add_argument("--password-env", metavar="TÊN_BIẾN", help="đọc mật khẩu từ biến môi trường này")
    parser.add_argument("--totp", help="mã OTP 6 số nếu tài khoản bật OTP")
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace, ctx: Context) -> int:
    if args.username:
        password = _resolve_password(args, ctx)
        response = password_login(ctx, args.username, password, args.totp)
    else:
        if args.password or args.password_env or args.totp:
            raise CliError("--password, --password-env và --totp chỉ dùng cùng --username.")
        response = device_login(ctx)
    save_token(ctx, response)
    who = _preferred_username(response["access_token"]) or args.username
    ctx.say(f"Đã đăng nhập{f' với tài khoản {who}' if who else ''}. Token lưu tại {ctx.settings.token_file}")
    return 0


def _resolve_password(args: argparse.Namespace, ctx: Context) -> str:
    if args.password:
        return str(args.password)
    if args.password_env:
        value = ctx.env.get(args.password_env)
        if not value:
            raise CliError(f"Biến môi trường {args.password_env} chưa đặt hoặc rỗng.")
        return value
    if not sys.stdin.isatty():
        raise CliError("Thiếu mật khẩu: dùng --password-env TÊN_BIẾN (hoặc chạy trong terminal để nhập tay).")
    return getpass.getpass("Mật khẩu: ")


def _preferred_username(access_token: str) -> str | None:
    """Chỉ để hiển thị; việc kiểm chữ ký token là của core."""
    try:
        payload = access_token.split(".")[1]
        claims: dict[str, Any] = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        return str(claims["preferred_username"])
    except (IndexError, ValueError, KeyError):
        return None
