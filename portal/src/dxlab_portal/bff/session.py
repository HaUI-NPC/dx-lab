# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Kho phiên phía server và cookie phiên đã ký.

Token OIDC chỉ nằm trong bộ nhớ của tiến trình portal. Trình duyệt chỉ giữ một cookie httpOnly chứa
mã phiên ngẫu nhiên được ký bằng ``DXLAB_PORTAL_SESSION_SECRET``; khởi động lại portal thì mọi phiên mất
và người dùng đăng nhập lại.
"""

from __future__ import annotations

import asyncio
import secrets
import time
from dataclasses import dataclass, field
from typing import Any

from itsdangerous import BadSignature, URLSafeSerializer
from starlette.responses import Response

COOKIE_NAME = "dxlab_session"
# Thời gian sống tuyệt đối của một phiên, kể cả khi token vẫn gia hạn được.
SESSION_MAX_AGE = 8 * 3600


@dataclass
class Session:
    """Một phiên đăng nhập: token và thông tin người dùng, không bao giờ gửi cho trình duyệt."""

    session_id: str
    access_token: str
    refresh_token: str | None
    id_token: str | None
    expires_at: float
    claims: dict[str, Any]
    created_at: float = field(default_factory=time.time)
    # Chặn hai yêu cầu song song cùng đổi refresh token (Keycloak có thể xoay vòng refresh token).
    refresh_lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)


class SessionStore:
    """Kho phiên trong tiến trình, kèm ký/giải ký cookie."""

    def __init__(self, secret: str, *, secure_cookie: bool) -> None:
        self._signer = URLSafeSerializer(secret, salt="dxlab-portal-session")
        self._secure = secure_cookie
        self._sessions: dict[str, Session] = {}

    def create(
        self,
        *,
        access_token: str,
        refresh_token: str | None,
        id_token: str | None,
        expires_at: float,
        claims: dict[str, Any],
    ) -> Session:
        self._purge()
        session = Session(
            session_id=secrets.token_urlsafe(32),
            access_token=access_token,
            refresh_token=refresh_token,
            id_token=id_token,
            expires_at=expires_at,
            claims=claims,
        )
        self._sessions[session.session_id] = session
        return session

    def get(self, cookie_value: str | None) -> Session | None:
        """Tìm phiên theo giá trị cookie; cookie sai chữ ký hoặc phiên đã hết hạn thì trả ``None``."""
        if not cookie_value:
            return None
        try:
            session_id = self._signer.loads(cookie_value)
        except BadSignature:
            return None
        session = self._sessions.get(session_id) if isinstance(session_id, str) else None
        if session is None:
            return None
        if time.time() - session.created_at > SESSION_MAX_AGE:
            self._sessions.pop(session.session_id, None)
            return None
        return session

    def delete(self, session: Session) -> None:
        self._sessions.pop(session.session_id, None)

    def attach(self, response: Response, session: Session) -> None:
        """Gắn cookie phiên: httpOnly, SameSite=Lax, Secure khi portal chạy HTTPS."""
        response.set_cookie(
            COOKIE_NAME,
            self._signer.dumps(session.session_id),
            max_age=SESSION_MAX_AGE,
            httponly=True,
            samesite="lax",
            secure=self._secure,
            path="/",
        )

    def detach(self, response: Response) -> None:
        response.delete_cookie(COOKIE_NAME, path="/", httponly=True, samesite="lax", secure=self._secure)

    def _purge(self) -> None:
        now = time.time()
        for session_id in [sid for sid, s in self._sessions.items() if now - s.created_at > SESSION_MAX_AGE]:
            del self._sessions[session_id]
