# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Định dạng lỗi chung của core (CONTRIBUTING.md, mục "Định dạng lỗi").

Mọi lỗi trả `{"error": {"code", "message", "details", "request_id"}}`. Mã nghiệp vụ ném `ApiError`;
lỗi kiểm tra đầu vào của FastAPI, lỗi HTTP của Starlette và lỗi không lường trước được đổi về cùng dạng.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from dxlab_core.request_id import current_request_id

log = logging.getLogger(__name__)


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = {}
    request_id: str


class ErrorResponse(BaseModel):
    """Dạng phản hồi lỗi; dùng trong `responses=` của route để OpenAPI mô tả đúng."""

    error: ErrorBody


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details or {}


class NotFound(ApiError):
    def __init__(self, message: str = "Không tìm thấy đối tượng.", details: dict[str, Any] | None = None) -> None:
        super().__init__(404, "NOT_FOUND", message, details)


class Conflict(ApiError):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(409, "CONFLICT", message, details)


class ValidationFailed(ApiError):
    """`errors`: danh sách `{"path", "message"}`."""

    def __init__(self, errors: list[dict[str, str]], message: str = "Dữ liệu gửi lên không hợp lệ.") -> None:
        super().__init__(422, "VALIDATION_FAILED", message, {"errors": errors})


def error_response(status: int, code: str, message: str, details: dict[str, Any] | None = None) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorBody(code=code, message=message, details=details or {}, request_id=current_request_id())
    )
    return JSONResponse(status_code=status, content=body.model_dump())


# Thông báo tiếng Việt cho các loại lỗi kiểm tra hay gặp; loại khác giữ thông báo gốc của Pydantic.
_VALIDATION_MESSAGES = {
    "missing": "Thiếu trường bắt buộc.",
    "string_too_short": "Chuỗi quá ngắn.",
    "string_too_long": "Chuỗi quá dài.",
    "string_type": "Phải là chuỗi.",
    "int_parsing": "Phải là số nguyên.",
    "int_type": "Phải là số nguyên.",
    "bool_parsing": "Phải là đúng/sai.",
    "uuid_parsing": "Phải là UUID.",
    "enum": "Giá trị không nằm trong danh sách cho phép.",
    "greater_than_equal": "Giá trị quá nhỏ.",
    "less_than_equal": "Giá trị quá lớn.",
    "json_invalid": "JSON không hợp lệ.",
    "dict_type": "Phải là đối tượng JSON.",
    "extra_forbidden": "Trường không được phép.",
}

_HTTP_CODES = {
    401: ("UNAUTHENTICATED", "Cần đăng nhập."),
    404: ("NOT_FOUND", "Không tìm thấy đường dẫn."),
    405: ("NOT_FOUND", "Đường dẫn không hỗ trợ thao tác này."),
    409: ("CONFLICT", "Dữ liệu đã thay đổi, tải lại rồi thử lại."),
}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
        return error_response(exc.status, exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {
                "path": ".".join(str(part) for part in err.get("loc", ())),
                "message": _VALIDATION_MESSAGES.get(err.get("type", ""), err.get("msg", "")),
            }
            for err in exc.errors()
        ]
        return error_response(422, "VALIDATION_FAILED", "Dữ liệu gửi lên không hợp lệ.", {"errors": errors})

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code, message = _HTTP_CODES.get(exc.status_code, ("INTERNAL", "Lỗi hệ thống."))
        return error_response(exc.status_code, code, message)

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled_error type=%s", type(exc).__name__)
        return error_response(500, "INTERNAL", "Lỗi hệ thống. Báo quản trị kèm mã yêu cầu.")
