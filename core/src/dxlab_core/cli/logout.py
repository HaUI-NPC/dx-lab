# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""`dxlab logout`: hủy phiên trên Keycloak (nếu được) và xóa tệp token."""

import argparse

from dxlab_core.cli.context import CliError, Context
from dxlab_core.cli.oidc import end_session
from dxlab_core.cli.tokens import delete_token, load_token


def register(subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]") -> None:
    parser = subparsers.add_parser("logout", help="đăng xuất và xóa token đã lưu")
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace, ctx: Context) -> int:
    path = ctx.settings.token_file
    stored = load_token(path)
    if stored is None:
        ctx.say("Chưa đăng nhập.")
        return 0
    if stored.get("refresh_token"):
        try:
            end_session(ctx, stored["refresh_token"])
        except CliError as exc:
            # Token cục bộ vẫn phải xóa; phiên phía máy chủ tự hết hạn.
            print(f"Cảnh báo: {exc.message}. Phiên trên máy chủ sẽ tự hết hạn.", file=ctx.err)
    delete_token(path)
    ctx.say(f"Đã đăng xuất, đã xóa {path}")
    return 0
