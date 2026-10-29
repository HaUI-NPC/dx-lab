# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""`dxlab whoami`: hỏi core người đang đăng nhập là ai (`GET /api/me`)."""

import argparse

from dxlab_core.cli.api import api_request
from dxlab_core.cli.context import Context, invoke


def register(subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]") -> None:
    parser = subparsers.add_parser("whoami", help="cho biết tài khoản, vai trò và đơn vị đang đăng nhập")
    parser.set_defaults(func=lambda args: invoke(run, args))


def run(args: argparse.Namespace, ctx: Context) -> int:
    me = api_request(ctx, "GET", "/me").json()
    ctx.say(f"Tài khoản: {me['username']}")
    ctx.say(f"Họ tên:    {me.get('name', '')}")
    roles = me.get("roles") or []
    if roles:
        ctx.say("Vai trò:")
        for item in roles:
            ctx.say(f"  - {item['role']} @ {item['unit']}")
    else:
        ctx.say("Vai trò:   (chỉ có quyền người báo cáo)")
    units = me.get("units") or []
    if units:
        ctx.say(f"Đơn vị:    {', '.join(units)}")
    return 0
