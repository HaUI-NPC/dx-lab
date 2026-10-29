# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Nhận form gửi từ trang: kiểm tra tiếng Việt theo schema do core cấp, rồi gửi sang core.

Trình duyệt chỉ đọc được phản hồi của Prefab ``Fetch`` khi HTTP 2xx, nên các route ở đây luôn trả 200 kèm
một phong bì JSON ``{"ok", "errors", "message", "error", "workflow"}``; trạng thái và lỗi gốc của core nằm
trong ``error``. Chưa đăng nhập thì trả 401 như mọi route của portal.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from dxlab_portal.bff.core_client import CoreResult
from dxlab_portal.bff.proxy import error_response, same_origin
from dxlab_portal.bff.state import current_session, portal_state
from dxlab_portal.pages.forms.spec import FormSpec, build_form
from dxlab_portal.pages.forms.validate import validate_form

router = APIRouter(include_in_schema=False)


class SubmitBody(BaseModel):
    values: dict[str, Any]


def _error_envelope(result: CoreResult) -> dict[str, Any]:
    """Lỗi của core, giữ nguyên ``code``, ``message``, ``request_id`` theo định dạng lỗi chung."""
    error = result.error or {}
    return {
        "code": error.get("code", "INTERNAL"),
        "message": result.error_message(),
        "request_id": error.get("request_id") or result.request_id,
        "status": result.status,
    }


def _envelope(
    spec: FormSpec | None,
    *,
    ok: bool = False,
    errors: dict[str, str] | None = None,
    message: str = "",
    error: dict[str, Any] | None = None,
    workflow: dict[str, Any] | None = None,
) -> JSONResponse:
    field_errors = {f.name: "" for f in spec.fields} if spec else {}
    field_errors.update(errors or {})
    return JSONResponse(
        {"ok": ok, "errors": field_errors, "message": message, "error": error, "workflow": workflow}
    )


def _core_field_errors(result: CoreResult, spec: FormSpec) -> tuple[dict[str, str], list[str]]:
    """Gán lỗi ``VALIDATION_FAILED`` của core (``details.errors[].path``) về từng trường của form."""
    names = {f.name for f in spec.fields}
    per_field: dict[str, str] = {}
    other: list[str] = []
    details = (result.error or {}).get("details")
    items = details.get("errors") if isinstance(details, dict) else None
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path", "")).replace("/", ".").strip(".")
        name = path.removeprefix("data.").removeprefix("body.data.")
        message = str(item.get("message", ""))
        if name in names:
            per_field.setdefault(name, message)
        elif message:
            other.append(f"{path}: {message}" if path else message)
    return per_field, other


@router.post("/ui/forms/start/{app_id}")
async def submit_start_form(app_id: str, body: SubmitBody, request: Request) -> Response:
    state = portal_state(request)
    if not same_origin(request, state.settings.public_url):
        return error_response(
            403, "FORBIDDEN_ORIGIN", "Yêu cầu ghi bị từ chối vì không xuất phát từ trang của portal."
        )
    session = await current_session(request)
    if session is None:
        return error_response(
            401, "UNAUTHENTICATED", "Chưa đăng nhập hoặc phiên đã hết hạn. Vui lòng đăng nhập lại."
        )
    token = session.access_token

    definition = await state.core.call("GET", f"/definitions/{app_id}/start-form", token=token)
    if not definition.ok or not isinstance(definition.json, dict):
        return _envelope(None, error=_error_envelope(definition))
    spec = build_form(definition.json.get("schema") or {}, definition.json.get("uischema"))

    data, errors = validate_form(spec, body.values)
    if errors:
        return _envelope(
            spec, errors=errors, message=f"Vui lòng kiểm tra lại {len(errors)} trường được đánh dấu đỏ."
        )

    created = await state.core.call("POST", "/workflows", token=token, json={"app_id": app_id, "data": data})
    if created.ok and isinstance(created.json, dict):
        return _envelope(spec, ok=True, workflow=created.json)
    if created.status == 422 and (created.error or {}).get("code") == "VALIDATION_FAILED":
        per_field, other = _core_field_errors(created, spec)
        message = (
            "; ".join(other)
            if other
            else (
                "Core từ chối dữ liệu; xem thông báo ở từng trường." if per_field else created.error_message()
            )
        )
        return _envelope(spec, errors=per_field, message=message)
    return _envelope(spec, error=_error_envelope(created))
