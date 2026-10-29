# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Giao tiếp OIDC với Keycloak: discovery, device authorization grant, direct grant, refresh, logout."""

from typing import Any

import httpx

from dxlab_core.cli.context import CliError, Context

DEVICE_GRANT = "urn:ietf:params:oauth:grant-type:device_code"
SLOW_DOWN_STEP_SECONDS = 5


def discover(ctx: Context) -> dict[str, Any]:
    url = f"{ctx.settings.issuer}/.well-known/openid-configuration"
    response = _call(ctx, "GET", url)
    if response.status_code != 200:
        raise CliError(f"Không lấy được cấu hình OIDC từ {url} (HTTP {response.status_code}).")
    return response.json()


def device_login(ctx: Context) -> dict[str, Any]:
    """Device Authorization Grant (RFC 8628): in mã cho người dùng, chờ họ xác nhận trên trình duyệt."""
    meta = discover(ctx)
    endpoint = meta.get("device_authorization_endpoint")
    if not endpoint:
        raise CliError("Máy chủ OIDC không hỗ trợ device flow (thiếu device_authorization_endpoint).")
    response = _call(ctx, "POST", endpoint, data={"client_id": ctx.settings.client_id, "scope": "openid"})
    if response.status_code != 200:
        raise _token_error(response, "Không bắt đầu được device flow")
    grant = response.json()

    ctx.say("Mở địa chỉ sau trên trình duyệt để đăng nhập:")
    ctx.say(f"  {grant.get('verification_uri_complete') or grant['verification_uri']}")
    ctx.say(f"Mã xác nhận: {grant['user_code']}")
    ctx.say("Đang chờ bạn xác nhận…")

    deadline = ctx.now() + float(grant.get("expires_in", 600))
    interval = float(grant.get("interval", 5))
    while True:
        ctx.sleep(interval)
        if ctx.now() >= deadline:
            raise CliError("Mã xác nhận đã hết hạn. Chạy lại `dxlab login`.")
        poll = _call(
            ctx,
            "POST",
            meta["token_endpoint"],
            data={"grant_type": DEVICE_GRANT, "device_code": grant["device_code"], "client_id": ctx.settings.client_id},
        )
        if poll.status_code == 200:
            return poll.json()
        error = _error_code(poll)
        if error == "authorization_pending":
            continue
        if error == "slow_down":
            interval += SLOW_DOWN_STEP_SECONDS
            continue
        if error == "access_denied":
            raise CliError("Bạn đã từ chối yêu cầu đăng nhập.")
        if error == "expired_token":
            raise CliError("Mã xác nhận đã hết hạn. Chạy lại `dxlab login`.")
        raise _token_error(poll, "Đăng nhập thất bại")


def password_login(ctx: Context, username: str, password: str, totp: str | None) -> dict[str, Any]:
    """Direct Access Grant: chỉ cho script demo (seed.sh, demo-e2e.sh). Không bao giờ in mật khẩu."""
    meta = discover(ctx)
    data = {"grant_type": "password", "client_id": ctx.settings.client_id, "username": username, "password": password}
    if totp:
        data["totp"] = totp
    response = _call(ctx, "POST", meta["token_endpoint"], data=data)
    if response.status_code != 200:
        if _error_code(response) == "invalid_grant":
            raise CliError("Sai tên đăng nhập, mật khẩu hoặc mã OTP.")
        raise _token_error(response, "Đăng nhập thất bại")
    return response.json()


def refresh_grant(ctx: Context, refresh_token: str) -> dict[str, Any]:
    meta = discover(ctx)
    response = _call(
        ctx,
        "POST",
        meta["token_endpoint"],
        data={"grant_type": "refresh_token", "client_id": ctx.settings.client_id, "refresh_token": refresh_token},
    )
    if response.status_code != 200:
        raise _token_error(response, "Làm mới token thất bại")
    return response.json()


def end_session(ctx: Context, refresh_token: str) -> None:
    """Hủy phiên phía Keycloak (OIDC RP-initiated logout bằng refresh token, không cần trình duyệt)."""
    meta = discover(ctx)
    endpoint = meta.get("end_session_endpoint")
    if not endpoint:
        raise CliError("Máy chủ OIDC không có end_session_endpoint.")
    response = _call(ctx, "POST", endpoint, data={"client_id": ctx.settings.client_id, "refresh_token": refresh_token})
    if response.status_code not in (200, 204):
        raise _token_error(response, "Không hủy được phiên trên máy chủ")


def _call(ctx: Context, method: str, url: str, **kwargs: Any) -> httpx.Response:
    try:
        return ctx.client.request(method, url, **kwargs)
    except httpx.HTTPError:
        raise CliError(f"Không kết nối được tới {url}. Kiểm tra stack đã chạy và DXLAB_OIDC_ISSUER.") from None


def _error_code(response: httpx.Response) -> str:
    try:
        return str(response.json().get("error", ""))
    except (ValueError, AttributeError):
        return ""


def _token_error(response: httpx.Response, prefix: str) -> CliError:
    try:
        body = response.json()
        detail = body.get("error_description") or body.get("error") or ""
    except (ValueError, AttributeError):
        detail = ""
    suffix = f": {detail}" if detail else ""
    return CliError(f"{prefix} (HTTP {response.status_code}){suffix}")
