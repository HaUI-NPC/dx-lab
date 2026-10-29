# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Trạng thái dùng chung của tiến trình portal và việc lấy phiên hợp lệ từ yêu cầu."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from starlette.requests import Request

from dxlab_portal.bff.core_client import CoreClient
from dxlab_portal.bff.oidc import REFRESH_MARGIN_SECONDS, OidcClient, OidcError
from dxlab_portal.bff.session import COOKIE_NAME, Session, SessionStore
from dxlab_portal.config import Settings

log = logging.getLogger("dxlab_portal.session")


@dataclass
class PortalState:
    settings: Settings
    oidc: OidcClient
    sessions: SessionStore
    core: CoreClient


def portal_state(request: Request) -> PortalState:
    return request.app.state.portal  # type: ignore[no-any-return]


async def current_session(request: Request) -> Session | None:
    """Phiên đăng nhập của yêu cầu, đã gia hạn token nếu sắp hết hạn; không có thì ``None``."""
    state = portal_state(request)
    session = state.sessions.get(request.cookies.get(COOKIE_NAME))
    if session is None:
        return None
    if session.expires_at - time.time() > REFRESH_MARGIN_SECONDS:
        return session
    async with session.refresh_lock:
        # Yêu cầu song song khác có thể đã gia hạn xong trong lúc chờ khóa.
        if session.expires_at - time.time() > REFRESH_MARGIN_SECONDS:
            return session
        if not session.refresh_token:
            state.sessions.delete(session)
            return None
        try:
            token = await state.oidc.refresh(session.refresh_token)
        except OidcError as exc:
            log.info("session_refresh_failed reason=%s", exc.message)
            state.sessions.delete(session)
            return None
        session.access_token = token["access_token"]
        session.refresh_token = token.get("refresh_token", session.refresh_token)
        session.id_token = token.get("id_token", session.id_token)
        session.expires_at = float(token["expires_at"])
        return session
