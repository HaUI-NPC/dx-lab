# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Ứng dụng FastAPI của portal: ``uvicorn dxlab_portal.app:app``."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from urllib.parse import quote

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from pydantic import BaseModel
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.sessions import SessionMiddleware

from dxlab_portal.bff import auth, proxy
from dxlab_portal.bff.core_client import CoreClient
from dxlab_portal.bff.oidc import OidcClient
from dxlab_portal.bff.session import SessionStore
from dxlab_portal.bff.state import PortalState, current_session, portal_state
from dxlab_portal.config import Settings, load_settings
from dxlab_portal.pages import status as status_view
from dxlab_portal.pages.context import PageContext
from dxlab_portal.pages.forms import routes as form_routes
from dxlab_portal.pages.shell import load_tabs, render_html, render_prefab_html
from dxlab_portal.pages.status_probe import check_all
from dxlab_portal.pages.user import user_from_claims, user_from_me

# Cookie tạm giữ state/nonce/PKCE trong lúc chuyển sang Keycloak, khác cookie phiên chính.
OAUTH_COOKIE = "dxlab_oauth"
OAUTH_COOKIE_MAX_AGE = 600

# Renderer Prefab đóng gói sẵn là một khối script nội tuyến; các nguồn khác chỉ cho phép cùng gốc.
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; "
    "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
)

class SearchBody(BaseModel):
    query: str


def create_app(
    settings: Settings | None = None,
    *,
    oidc_transport: httpx.AsyncBaseTransport | None = None,
    core_transport: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    """Tạo ứng dụng. ``*_transport`` chỉ để test thay máy chủ OIDC và core bằng bản giả lập."""
    settings = settings or load_settings()
    logging.basicConfig(
        level=settings.log_level.upper(), format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    state = PortalState(
        settings=settings,
        oidc=OidcClient(settings, transport=oidc_transport),
        sessions=SessionStore(
            settings.session_secret.get_secret_value(), secure_cookie=settings.cookie_secure
        ),
        core=CoreClient(settings.api_url, transport=core_transport),
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        await state.core.aclose()

    app = FastAPI(
        title="DX-Lab Portal",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.portal = state

    @app.middleware("http")
    async def security_headers(request: Request, call_next: Any) -> Response:
        response: Response = await call_next(request)
        response.headers.setdefault("Content-Security-Policy", CONTENT_SECURITY_POLICY)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        if request.url.path != "/healthz":
            response.headers.setdefault("Cache-Control", "no-store")
        return response

    # Thứ tự add_middleware: cái thêm sau bọc ngoài cái thêm trước.
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret.get_secret_value(),
        session_cookie=OAUTH_COOKIE,
        max_age=OAUTH_COOKIE_MAX_AGE,
        same_site="lax",
        https_only=settings.cookie_secure,
    )
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    app.include_router(auth.router)
    app.include_router(proxy.router)
    app.include_router(form_routes.router)

    @app.get("/healthz", include_in_schema=False)
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/ui/search", include_in_schema=False)
    async def search(body: SearchBody, request: Request) -> Response:
        if not proxy.same_origin(request, settings.public_url):
            return proxy.error_response(403, "FORBIDDEN_ORIGIN", "Yêu cầu không xuất phát từ portal.")
        session = await current_session(request)
        if session is None:
            return proxy.error_response(401, "UNAUTHENTICATED", "Vui lòng đăng nhập lại.")
        result = await state.core.call("GET", "/search", token=session.access_token, params={"q": body.query})
        if not result.ok or not isinstance(result.json, dict):
            return JSONResponse(result.json or {"error": {"message": result.error_message()}}, status_code=result.status)
        output = dict(result.json)
        output["items"] = []
        for item in result.json.get("items", []):
            document = item.get("document") or {}
            snippet = item.get("snippet") or {}
            provenance = " · ".join(str(document[k]) for k in ("source", "license", "source_ref") if document.get(k))
            output["items"].append({
                **item,
                "href": f"/api/documents/{quote(str(document.get('id', '')), safe='')}/content",
                "snippet_text": snippet.get("text", ""),
                "provenance": provenance,
            })
        return JSONResponse(output)

    @app.get("/ui/status", include_in_schema=False)
    async def status_json() -> JSONResponse:
        """Trạng thái các thành phần; không cần đăng nhập để vẫn xem được khi Keycloak hỏng."""
        return JSONResponse(await check_all(settings, state.oidc, state.core))

    @app.get("/status", include_in_schema=False, response_class=HTMLResponse)
    async def status_page() -> HTMLResponse:
        return HTMLResponse(render_prefab_html(status_view.build_page()))

    @app.get("/", include_in_schema=False, response_class=HTMLResponse)
    async def index(request: Request, tab: str = "", task_id: str = "", workflow_id: str = "") -> Response:
        session = await current_session(request)
        if session is None:
            target = request.url.path + (f"?{request.url.query}" if request.url.query else "")
            return RedirectResponse(f"/auth/login?next={quote(target, safe='')}", status_code=302)
        user = user_from_claims(session.claims)
        me = await portal_state(request).core.call("GET", "/me", token=session.access_token)
        if me.ok and isinstance(me.json, dict):
            user = user_from_me(me.json, user)
        ctx = PageContext(
            user=user, access_token=session.access_token, core=portal_state(request).core, tab=tab,
            task_id=task_id, workflow_id=workflow_id,
        )
        return HTMLResponse(render_html(ctx, await load_tabs(ctx)))

    return app


def __getattr__(name: str) -> FastAPI:
    # `uvicorn dxlab_portal.app:app` tạo ứng dụng khi được yêu cầu,
    # nên chỉ import module thì không đòi đủ biến môi trường.
    if name == "app":
        application = create_app()
        globals()["app"] = application
        return application
    raise AttributeError(name)
