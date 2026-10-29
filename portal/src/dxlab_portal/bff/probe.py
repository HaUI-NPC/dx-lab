# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Gọi thăm dò có đo thời gian, dùng cho trang trạng thái hệ thống."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx

PROBE_TIMEOUT_SECONDS = 3.0


@dataclass(frozen=True)
class ProbeResult:
    """Kết quả một lần thăm dò: phản hồi (``None`` nếu không tới được), thời gian và lý do lỗi."""

    response: httpx.Response | None
    elapsed_ms: int
    error: str | None = None

    @property
    def json(self) -> Any:
        if self.response is None:
            return None
        try:
            return self.response.json()
        except ValueError:
            return None


async def timed_get(url: str, transport: httpx.AsyncBaseTransport | None) -> ProbeResult:
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(transport=transport, timeout=PROBE_TIMEOUT_SECONDS) as client:
            response = await client.get(url)
    except httpx.TimeoutException:
        error = f"Quá thời gian chờ ({PROBE_TIMEOUT_SECONDS:.0f} giây)"
        return ProbeResult(None, int((time.perf_counter() - start) * 1000), error)
    except httpx.HTTPError:
        return ProbeResult(None, int((time.perf_counter() - start) * 1000), "Không kết nối được")
    return ProbeResult(response, int((time.perf_counter() - start) * 1000))
