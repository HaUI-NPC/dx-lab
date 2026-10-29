# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Máy khách HTTP tối giản cho `seed.py`: đăng nhập tài khoản demo và gọi API qua APISIX.

Chỉ dùng thư viện chuẩn. Mỗi tài khoản đăng nhập MỘT lần bằng direct grant của `dxlab-cli`
(mật khẩu `DXLAB_DEMO_PASSWORD`, mã TOTP tính từ `DXLAB_DEMO_OTP_SECRET`); sau đó chỉ dùng lại
token và làm mới bằng refresh token (không cần TOTP). Không có tài khoản dịch vụ nào.
"""

import hashlib
import hmac
import json
import mimetypes
import os
import struct
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

TOTP_PERIOD = 30


def load_env(root: Path) -> dict[str, str]:
    """Đọc `.env` ở gốc repo; biến môi trường của tiến trình ghi đè."""
    env: dict[str, str] = {}
    env_file = root / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip().strip("'\"")
    env.update({k: v for k, v in os.environ.items() if k.startswith(("DXLAB_", "KC_", "POSTGRES_"))})
    return env


def totp(secret: str, now: float | None = None) -> str:
    """TOTP RFC 6238 (SHA-1, 6 số, 30 giây). Keycloak lưu secret dạng chuỗi nên khóa là byte UTF-8 của chuỗi đó."""
    counter = int((now if now is not None else time.time()) // TOTP_PERIOD)
    digest = hmac.new(secret.encode("utf-8"), struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = (struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
    return f"{code:06d}"


class ApiError(Exception):
    """Lỗi HTTP từ API; giữ nguyên mã, thân lỗi của core (hoặc của gateway) để in ra rõ ràng."""

    def __init__(self, method: str, path: str, status: int, body: Any, user: str) -> None:
        self.method, self.path, self.status, self.body, self.user = method, path, status, body, user
        super().__init__(self.describe())

    def error_code(self) -> str | None:
        if isinstance(self.body, dict) and isinstance(self.body.get("error"), dict):
            return self.body["error"].get("code")
        return None

    def describe(self) -> str:
        head = f"{self.method} {self.path} ({self.user}) → HTTP {self.status}"
        if isinstance(self.body, dict) and isinstance(self.body.get("error"), dict):
            err = self.body["error"]
            text = f"{err.get('code')}: {err.get('message')}"
            if err.get("details"):
                text += f" | chi tiết: {json.dumps(err['details'], ensure_ascii=False)}"
            if err.get("request_id"):
                text += f" | request_id={err['request_id']}"
            return f"{head}\n    {text}"
        snippet = self.body if isinstance(self.body, str) else json.dumps(self.body, ensure_ascii=False)
        return f"{head}\n    {snippet[:400]}"


class LoginError(Exception):
    pass


@dataclass
class _Session:
    access_token: str
    refresh_token: str
    expires_at: float


@dataclass
class Client:
    api_url: str
    issuer: str
    password: str
    otp_secret: str
    client_id: str = "dxlab-cli"
    sessions: dict[str, _Session] = field(default_factory=dict)

    # --- đăng nhập -----------------------------------------------------------------------------

    def _token_request(self, form: dict[str, str]) -> tuple[int, Any]:
        data = urllib.parse.urlencode(form).encode()
        request = urllib.request.Request(
            f"{self.issuer}/protocol/openid-connect/token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        return _send(request)

    def _store(self, user: str, body: dict[str, Any]) -> None:
        self.sessions[user] = _Session(
            access_token=body["access_token"],
            refresh_token=body.get("refresh_token", ""),
            expires_at=time.time() + int(body.get("expires_in", 300)),
        )

    def login(self, user: str) -> None:
        """Direct grant với mật khẩu demo và TOTP. Keycloak không cho dùng lại một mã trong cùng chu kỳ 30 giây
        (ví dụ chạy seed hai lần liền nhau): gặp 400 thì đợi sang chu kỳ kế rồi thử lại đúng một lần."""
        for attempt in (1, 2):
            form = {
                "client_id": self.client_id,
                "grant_type": "password",
                "username": user,
                "password": self.password,
                "totp": totp(self.otp_secret),
            }
            status, body = self._token_request(form)
            if status == 200:
                self._store(user, body)
                return
            if status == 400 and attempt == 1:
                wait = TOTP_PERIOD - (time.time() % TOTP_PERIOD) + 1
                print(f"    {user}: Keycloak từ chối ({_oauth_text(body)}); đợi {wait:.0f} giây sang chu kỳ TOTP kế tiếp rồi thử lại")
                time.sleep(wait)
                continue
            raise LoginError(f"Không đăng nhập được {user}: HTTP {status} {_oauth_text(body)}")

    def _refresh(self, user: str) -> None:
        session = self.sessions[user]
        status, body = self._token_request(
            {"client_id": self.client_id, "grant_type": "refresh_token", "refresh_token": session.refresh_token}
        )
        if status == 200:
            self._store(user, body)
        else:  # phiên Keycloak hết hạn: đăng nhập lại
            del self.sessions[user]
            self.login(user)

    def token(self, user: str) -> str:
        if user not in self.sessions:
            self.login(user)
        elif self.sessions[user].expires_at - time.time() < 30:
            self._refresh(user)
        return self.sessions[user].access_token

    # --- gọi API -------------------------------------------------------------------------------

    def request(
        self,
        user: str,
        method: str,
        path: str,
        *,
        json_body: Any = None,
        multipart: list[tuple[str, str | None, bytes]] | None = None,
        ok: tuple[int, ...] = (200, 201),
    ) -> tuple[int, Any]:
        """Gọi `{api_url}{path}` bằng token của `user`. Trả `(mã, thân JSON)`; mã ngoài `ok` ném `ApiError`."""
        headers = {"Authorization": f"Bearer {self.token(user)}", "Accept": "application/json"}
        data: bytes | None = None
        if json_body is not None:
            data = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        elif multipart is not None:
            boundary = uuid.uuid4().hex
            data = _multipart(boundary, multipart)
            headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        request = urllib.request.Request(self.api_url + path, data=data, headers=headers, method=method)
        status, body = _send(request)
        if status not in ok:
            raise ApiError(method, path, status, body, user)
        return status, body


def _oauth_text(body: Any) -> str:
    if isinstance(body, dict):
        return f"{body.get('error', '')}: {body.get('error_description', '')}".strip(": ")
    return str(body)[:200]


def _send(request: urllib.request.Request) -> tuple[int, Any]:
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status, _decode(response.read())
    except urllib.error.HTTPError as error:
        return error.code, _decode(error.read())
    except urllib.error.URLError as error:
        raise ConnectionError(f"Không kết nối được {request.full_url}: {error.reason}. Stack đã chạy chưa (scripts/up.sh)?") from error


def _decode(raw: bytes) -> Any:
    if not raw:
        return None
    text = raw.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _multipart(boundary: str, parts: list[tuple[str, str | None, bytes]]) -> bytes:
    """Mỗi phần là `(tên trường, tên tệp hoặc None, nội dung)`; phần có tên tệp là tệp tải lên."""
    out = bytearray()
    for name, filename, content in parts:
        out += f"--{boundary}\r\n".encode()
        if filename is None:
            out += f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
        else:
            quoted = filename.replace("\\", "\\\\").replace('"', '\\"')
            guessed = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            out += f'Content-Disposition: form-data; name="{name}"; filename="{quoted}"\r\n'.encode()
            out += f"Content-Type: {guessed}\r\n\r\n".encode()
        out += content + b"\r\n"
    out += f"--{boundary}--\r\n".encode()
    return bytes(out)

