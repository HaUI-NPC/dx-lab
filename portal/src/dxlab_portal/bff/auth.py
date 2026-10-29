# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Route đăng nhập: ``/auth/login``, ``/auth/callback``, ``/auth/logout``."""

from __future__ import annotations

import logging
from html import escape
from urllib.parse import urlencode

from authlib.integrations.base_client import OAuthError
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from dxlab_portal.bff.oidc import OidcError, merge_claims
from dxlab_portal.bff.state import current_session, portal_state

log = logging.getLogger("dxlab_portal.auth")
router = APIRouter(prefix="/auth", include_in_schema=False)

NEXT_KEY = "next"


def safe_next(target: str | None) -> str:
    """Chỉ chấp nhận đường dẫn nội bộ làm đích sau đăng nhập, tránh chuyển hướng ra ngoài."""
    if target and target.startswith("/") and not target.startswith("//") and "\\" not in target:
        return target
    return "/"


def error_page(message: str, status: int) -> HTMLResponse:
    body = (
        '<!doctype html><html lang="vi"><head><meta charset="utf-8"><title>Đăng nhập – DX-Lab</title>'
        '<meta name="viewport" content="width=device-width,initial-scale=1"></head>'
        '<body style="font-family:system-ui,sans-serif;max-width:36rem;margin:4rem auto;padding:0 1rem">'
        f"<h1>Không đăng nhập được</h1><p>{escape(message)}</p>"
        '<p><a href="/auth/login">Thử đăng nhập lại</a></p></body></html>'
    )
    return HTMLResponse(body, status_code=status)


@router.get("/login")
async def login(request: Request, next: str | None = None) -> Response:
    state = portal_state(request)
    try:
        await state.oidc.metadata()
    except OidcError as exc:
        return error_page(exc.message, 502)
    request.session.clear()
    request.session[NEXT_KEY] = safe_next(next)
    redirect_uri = f"{state.settings.public_url}/auth/callback"
    return await state.oidc.app.authorize_redirect(request, redirect_uri)  # type: ignore[no-any-return]


@router.get("/callback")
async def callback(request: Request) -> Response:
    state = portal_state(request)
    target = safe_next(request.session.get(NEXT_KEY))
    try:
        await state.oidc.metadata()
        token = await state.oidc.app.authorize_access_token(request)
    except OidcError as exc:
        return error_page(exc.message, 502)
    except OAuthError as exc:
        log.info("login_failed error=%s", exc.error)
        return error_page(
            "Keycloak từ chối hoặc phiên đăng nhập đã hết hạn giữa chừng. Vui lòng đăng nhập lại.", 400
        )
    finally:
        request.session.clear()
    session = state.sessions.create(
        access_token=token["access_token"],
        refresh_token=token.get("refresh_token"),
        id_token=token.get("id_token"),
        expires_at=float(token["expires_at"]),
        claims=merge_claims(token.get("userinfo"), token["access_token"]),
    )
    response = RedirectResponse(target, status_code=303)
    state.sessions.attach(response, session)
    log.info("login_ok username=%s", session.claims.get("preferred_username", "?"))
    return response


@router.get("/logout")
async def logout(request: Request) -> Response:
    """Xóa phiên phía server rồi đăng xuất Keycloak (RP-initiated logout)."""
    state = portal_state(request)
    session = await current_session(request)
    landing = f"{state.settings.public_url}/auth/logged-out"
    response: Response = RedirectResponse(landing, status_code=303)
    if session is not None:
        state.sessions.delete(session)
        try:
            endpoint = (await state.oidc.metadata()).get("end_session_endpoint")
        except OidcError:
            endpoint = None
        if endpoint:
            params = {
                "client_id": state.settings.client_id,
                "post_logout_redirect_uri": landing,
            }
            if session.id_token:
                params["id_token_hint"] = session.id_token
            response = RedirectResponse(f"{endpoint}?{urlencode(params)}", status_code=303)
    state.sessions.detach(response)
    return response


@router.get("/logged-out")
async def logged_out() -> HTMLResponse:
    return HTMLResponse(
        '<!doctype html><html lang="vi"><head><meta charset="utf-8"><title>Đã đăng xuất – DX-Lab</title>'
        '<meta name="viewport" content="width=device-width,initial-scale=1"></head>'
        '<body style="font-family:system-ui,sans-serif;max-width:36rem;margin:4rem auto;padding:0 1rem">'
        '<h1>Bạn đã đăng xuất</h1><p><a href="/auth/login">Đăng nhập lại</a></p></body></html>'
    )
