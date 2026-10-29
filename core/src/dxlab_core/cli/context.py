# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Ngữ cảnh chạy chung của các lệnh `dxlab`: cấu hình từ môi trường, HTTP client, đồng hồ, đầu ra."""

import argparse
import os
import sys
import time
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO

import httpx

DEFAULT_ISSUER = "http://localhost:8180/realms/dxlab"
DEFAULT_CLIENT_ID = "dxlab-cli"
DEFAULT_API_URL = "http://localhost:9080/api"
DEFAULT_TOKEN_FILE = "~/.config/dxlab/token.json"
HTTP_TIMEOUT = 30.0


class CliError(Exception):
    """Lỗi người dùng nhìn thấy: in `Lỗi: <message>` ra stderr và thoát mã 1. `lines` in thụt lề bên dưới."""

    def __init__(self, message: str, lines: list[str] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.lines = lines or []


@dataclass(frozen=True)
class CliSettings:
    """Biến môi trường của CLI (docs/ARCHITECTURE.md mục 5)."""

    issuer: str = DEFAULT_ISSUER
    client_id: str = DEFAULT_CLIENT_ID
    api_url: str = DEFAULT_API_URL
    token_file: Path = field(default_factory=lambda: Path(DEFAULT_TOKEN_FILE).expanduser())

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "CliSettings":
        env = os.environ if env is None else env
        return cls(
            issuer=env.get("DXLAB_OIDC_ISSUER", DEFAULT_ISSUER).rstrip("/"),
            client_id=env.get("DXLAB_CLI_CLIENT_ID", DEFAULT_CLIENT_ID),
            api_url=env.get("DXLAB_API_URL", DEFAULT_API_URL).rstrip("/"),
            token_file=Path(env.get("DXLAB_TOKEN_FILE", DEFAULT_TOKEN_FILE)).expanduser(),
        )


@dataclass
class Context:
    settings: CliSettings
    client: httpx.Client
    now: Callable[[], float] = time.time
    sleep: Callable[[float], None] = time.sleep
    out: TextIO = field(default_factory=lambda: sys.stdout)
    err: TextIO = field(default_factory=lambda: sys.stderr)
    env: Mapping[str, str] = field(default_factory=lambda: os.environ)

    def say(self, text: str = "") -> None:
        print(text, file=self.out, flush=True)


_override: Context | None = None


@contextmanager
def use_context(ctx: Context) -> Iterator[Context]:
    """Dùng `ctx` thay cho ngữ cảnh mặc định (từ môi trường) trong khối `with`; dành cho test."""
    global _override
    previous, _override = _override, ctx
    try:
        yield ctx
    finally:
        _override = previous


def invoke(run: Callable[[argparse.Namespace, Context], int], args: argparse.Namespace) -> int:
    """Chạy một lệnh với ngữ cảnh hiện hành; đổi `CliError` thành thông báo stderr và mã thoát 1."""
    owned = _override is None
    ctx = _override or Context(settings=CliSettings.from_env(), client=httpx.Client(timeout=HTTP_TIMEOUT))
    try:
        return int(run(args, ctx))
    except CliError as exc:
        print(f"Lỗi: {exc.message}", file=ctx.err)
        for line in exc.lines:
            print(f"  {line}", file=ctx.err)
        return 1
    except KeyboardInterrupt:
        print("Đã hủy.", file=ctx.err)
        return 130
    finally:
        if owned:
            ctx.client.close()
