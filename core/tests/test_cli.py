# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Test CLI `dxlab`: phía client, server giả bằng `httpx.MockTransport` (không cần Keycloak hay core)."""

import base64
import io
import json
import stat
from collections.abc import Callable
from email.parser import BytesParser
from email.policy import HTTP
from pathlib import Path
from urllib.parse import parse_qs

import httpx
import pytest

from dxlab_core.cli import main
from dxlab_core.cli.context import CliSettings, Context
from dxlab_core.cli.tokens import get_access_token

ISSUER = "http://kc.test/realms/dxlab"
API = "http://api.test/api"
DEVICE_GRANT = "urn:ietf:params:oauth:grant-type:device_code"
DISCOVERY = {
    "issuer": ISSUER,
    "token_endpoint": f"{ISSUER}/protocol/openid-connect/token",
    "device_authorization_endpoint": f"{ISSUER}/protocol/openid-connect/auth/device",
    "end_session_endpoint": f"{ISSUER}/protocol/openid-connect/logout",
}
Handler = Callable[[httpx.Request], httpx.Response]


class Env:
    """Một lần chạy CLI: đồng hồ giả, `sleep` ghi lại, đầu ra bắt được, mọi request ghi lại."""

    def __init__(self, tmp_path: Path, handler: Handler, environ: dict[str, str] | None = None) -> None:
        self.token_file = tmp_path / "cfg" / "token.json"
        self.clock = 1_000_000.0
        self.sleeps: list[float] = []
        self.requests: list[httpx.Request] = []
        self.out = io.StringIO()
        self.err = io.StringIO()

        def recording(request: httpx.Request) -> httpx.Response:
            self.requests.append(request)
            return handler(request)

        def sleep(seconds: float) -> None:
            self.sleeps.append(seconds)
            self.clock += seconds

        self.ctx = Context(
            settings=CliSettings(issuer=ISSUER, client_id="dxlab-cli", api_url=API, token_file=self.token_file),
            client=httpx.Client(transport=httpx.MockTransport(recording)),
            now=lambda: self.clock,
            sleep=sleep,
            out=self.out,
            err=self.err,
            env=environ or {},
        )

    def run(self, *argv: str) -> int:
        return main(list(argv), ctx=self.ctx)

    def form(self, request: httpx.Request) -> dict[str, str]:
        return {k: v[0] for k, v in parse_qs(request.content.decode()).items()}

    def stored(self) -> dict:
        return json.loads(self.token_file.read_text(encoding="utf-8"))


def jwt(claims: dict) -> str:
    body = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    return f"e30.{body}.sig"


def token_response(username: str = "qt.son", **extra: object) -> dict:
    return {
        "access_token": jwt({"preferred_username": username}),
        "expires_in": 300,
        "refresh_token": "refresh-1",
        "refresh_expires_in": 1800,
        **extra,
    }


def keycloak(token_handler: Handler) -> Handler:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/.well-known/openid-configuration"):
            return httpx.Response(200, json=DISCOVERY)
        return token_handler(request)

    return handler


def login_as(env: Env, **overrides: object) -> None:
    """Ghi sẵn token hợp lệ như sau `dxlab login`."""
    from dxlab_core.cli.tokens import save_token

    save_token(env.ctx, {**token_response(), **overrides})


# --- cấu hình -----------------------------------------------------------------------------------


def test_settings_defaults_and_overrides() -> None:
    default = CliSettings.from_env({})
    assert default.issuer == "http://localhost:8180/realms/dxlab"
    assert default.client_id == "dxlab-cli"
    assert default.api_url == "http://localhost:9080/api"
    assert default.token_file == Path("~/.config/dxlab/token.json").expanduser()

    custom = CliSettings.from_env(
        {
            "DXLAB_OIDC_ISSUER": "https://id.example/realms/x/",
            "DXLAB_CLI_CLIENT_ID": "khac",
            "DXLAB_API_URL": "https://api.example/api/",
            "DXLAB_TOKEN_FILE": "/tmp/t.json",
        }
    )
    assert (custom.issuer, custom.client_id, custom.api_url) == (
        "https://id.example/realms/x",
        "khac",
        "https://api.example/api",
    )
    assert custom.token_file == Path("/tmp/t.json")


def test_no_command_is_usage_error() -> None:
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 2


# --- login: device flow -------------------------------------------------------------------------


def test_device_login_polls_until_approved(tmp_path: Path) -> None:
    polls = iter(["authorization_pending", "slow_down", None])

    def token_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/auth/device"):
            assert env.form(request) == {"client_id": "dxlab-cli", "scope": "openid"}
            return httpx.Response(
                200,
                json={
                    "device_code": "DEV-SECRET-CODE",
                    "user_code": "ABCD-EFGH",
                    "verification_uri": f"{ISSUER}/device",
                    "verification_uri_complete": f"{ISSUER}/device?user_code=ABCD-EFGH",
                    "expires_in": 600,
                    "interval": 5,
                },
            )
        form = env.form(request)
        assert form == {"grant_type": DEVICE_GRANT, "device_code": "DEV-SECRET-CODE", "client_id": "dxlab-cli"}
        error = next(polls)
        if error:
            return httpx.Response(400, json={"error": error})
        return httpx.Response(200, json=token_response())

    env = Env(tmp_path, keycloak(token_handler))
    assert env.run("login") == 0

    assert env.sleeps == [5, 5, 10]  # slow_down cộng 5 giây vào khoảng chờ
    out = env.out.getvalue()
    assert f"{ISSUER}/device?user_code=ABCD-EFGH" in out
    assert "ABCD-EFGH" in out
    assert "DEV-SECRET-CODE" not in out  # device_code là bí mật của phiên, không in
    assert "qt.son" in out

    stored = env.stored()
    assert stored["refresh_token"] == "refresh-1"
    assert stored["expires_at"] == pytest.approx(1_000_000.0 + 20 + 300)
    assert stored["refresh_expires_at"] == pytest.approx(1_000_000.0 + 20 + 1800)
    assert stat.S_IMODE(env.token_file.stat().st_mode) == 0o600
    assert stat.S_IMODE(env.token_file.parent.stat().st_mode) == 0o700
    assert not list(env.token_file.parent.glob(".token-*"))


@pytest.mark.parametrize(
    ("error", "expected"),
    [("access_denied", "từ chối"), ("expired_token", "hết hạn")],
)
def test_device_login_terminal_errors(tmp_path: Path, error: str, expected: str) -> None:
    def token_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/auth/device"):
            return httpx.Response(
                200,
                json={"device_code": "d", "user_code": "U", "verification_uri": "http://v", "expires_in": 600},
            )
        return httpx.Response(400, json={"error": error})

    env = Env(tmp_path, keycloak(token_handler))
    assert env.run("login") == 1
    assert expected in env.err.getvalue()
    assert not env.token_file.exists()


def test_device_login_gives_up_when_code_expires(tmp_path: Path) -> None:
    def token_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/auth/device"):
            return httpx.Response(
                200,
                json={"device_code": "d", "user_code": "U", "verification_uri": "http://v", "expires_in": 12, "interval": 5},
            )
        return httpx.Response(400, json={"error": "authorization_pending"})

    env = Env(tmp_path, keycloak(token_handler))
    assert env.run("login") == 1
    assert "hết hạn" in env.err.getvalue()
    assert env.sleeps == [5, 5, 5]


def test_login_reports_unreachable_server(tmp_path: Path) -> None:
    def down(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    env = Env(tmp_path, down)
    assert env.run("login") == 1
    assert "Không kết nối được" in env.err.getvalue()


# --- login: direct grant ------------------------------------------------------------------------


def test_password_login_with_env_password_and_totp_never_prints_secret(tmp_path: Path) -> None:
    def token_handler(request: httpx.Request) -> httpx.Response:
        form = env.form(request)
        assert form == {
            "grant_type": "password",
            "client_id": "dxlab-cli",
            "username": "qt.son",
            "password": "mat-khau-demo",
            "totp": "123456",
        }
        return httpx.Response(200, json=token_response())

    env = Env(tmp_path, keycloak(token_handler), {"DEMO_PW": "mat-khau-demo"})
    assert env.run("login", "--username", "qt.son", "--password-env", "DEMO_PW", "--totp", "123456") == 0
    assert "mat-khau-demo" not in env.out.getvalue() + env.err.getvalue()
    assert "mat-khau-demo" not in env.token_file.read_text(encoding="utf-8")
    assert "qt.son" in env.out.getvalue()


def test_password_login_with_password_argument(tmp_path: Path) -> None:
    def token_handler(request: httpx.Request) -> httpx.Response:
        assert env.form(request)["password"] == "p"
        assert "totp" not in env.form(request)
        return httpx.Response(200, json=token_response("tv.a"))

    env = Env(tmp_path, keycloak(token_handler))
    assert env.run("login", "--username", "tv.a", "--password", "p") == 0
    assert "tv.a" in env.out.getvalue()


def test_password_login_wrong_credentials(tmp_path: Path) -> None:
    def token_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid_grant", "error_description": "Invalid user credentials"})

    env = Env(tmp_path, keycloak(token_handler))
    assert env.run("login", "--username", "qt.son", "--password", "sai") == 1
    assert "Sai tên đăng nhập, mật khẩu hoặc mã OTP" in env.err.getvalue()
    assert not env.token_file.exists()


def test_password_env_missing_is_error(tmp_path: Path) -> None:
    env = Env(tmp_path, keycloak(lambda r: httpx.Response(500)))
    assert env.run("login", "--username", "qt.son", "--password-env", "KHONG_CO") == 1
    assert "KHONG_CO" in env.err.getvalue()
    assert [r for r in env.requests if r.url.path.endswith("/token")] == []


def test_password_options_require_username(tmp_path: Path) -> None:
    env = Env(tmp_path, keycloak(lambda r: httpx.Response(500)))
    assert env.run("login", "--password", "x") == 1
    assert "--username" in env.err.getvalue()


# --- token: tự làm mới ----------------------------------------------------------------------------


def test_valid_token_is_reused_without_network(tmp_path: Path) -> None:
    env = Env(tmp_path, keycloak(lambda r: httpx.Response(500)))
    login_as(env)
    assert get_access_token(env.ctx) == env.stored()["access_token"]
    assert env.requests == []


def test_expired_token_is_refreshed_and_saved(tmp_path: Path) -> None:
    def token_handler(request: httpx.Request) -> httpx.Response:
        assert env.form(request) == {"grant_type": "refresh_token", "client_id": "dxlab-cli", "refresh_token": "refresh-1"}
        return httpx.Response(200, json=token_response(refresh_token="refresh-2", access_token="new-access"))

    env = Env(tmp_path, keycloak(token_handler))
    login_as(env)
    env.clock += 290  # còn 10 giây < lề 30 giây
    assert get_access_token(env.ctx) == "new-access"
    stored = env.stored()
    assert stored["refresh_token"] == "refresh-2"
    assert stored["expires_at"] == pytest.approx(env.clock + 300)


def test_expired_refresh_token_asks_to_login_again(tmp_path: Path) -> None:
    env = Env(tmp_path, keycloak(lambda r: httpx.Response(500)))
    login_as(env)
    env.clock += 1801
    assert env.run("whoami") == 1
    assert "dxlab login" in env.err.getvalue()
    assert all("/me" not in r.url.path for r in env.requests)


def test_refresh_rejected_asks_to_login_again(tmp_path: Path) -> None:
    env = Env(tmp_path, keycloak(lambda r: httpx.Response(400, json={"error": "invalid_grant"})))
    login_as(env)
    env.clock += 400
    assert env.run("whoami") == 1
    assert "dxlab login" in env.err.getvalue()


def test_corrupt_token_file_is_reported(tmp_path: Path) -> None:
    env = Env(tmp_path, keycloak(lambda r: httpx.Response(500)))
    env.token_file.parent.mkdir(parents=True)
    env.token_file.write_text("không phải json", encoding="utf-8")
    assert env.run("whoami") == 1
    assert "dxlab login" in env.err.getvalue()


# --- logout -------------------------------------------------------------------------------------


def test_logout_ends_session_and_deletes_token(tmp_path: Path) -> None:
    def token_handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/logout")
        assert env.form(request) == {"client_id": "dxlab-cli", "refresh_token": "refresh-1"}
        return httpx.Response(204)

    env = Env(tmp_path, keycloak(token_handler))
    login_as(env)
    assert env.run("logout") == 0
    assert not env.token_file.exists()
    assert env.err.getvalue() == ""


def test_logout_deletes_token_even_when_server_unreachable(tmp_path: Path) -> None:
    def down(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    env = Env(tmp_path, down)
    login_as(env)
    assert env.run("logout") == 0
    assert not env.token_file.exists()
    assert "Cảnh báo" in env.err.getvalue()


def test_logout_when_not_logged_in(tmp_path: Path) -> None:
    env = Env(tmp_path, keycloak(lambda r: httpx.Response(500)))
    assert env.run("logout") == 0
    assert "Chưa đăng nhập" in env.out.getvalue()
    assert env.requests == []


# --- whoami -------------------------------------------------------------------------------------


def test_whoami_prints_identity_with_bearer_token(tmp_path: Path) -> None:
    def api(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url) == f"{API}/me"
        assert request.headers["authorization"] == f"Bearer {env.stored()['access_token']}"
        return httpx.Response(
            200,
            json={
                "username": "qt.son",
                "name": "Tạ Văn Sơn",
                "roles": [{"role": "process_admin", "unit": "/haui/tt-cntt"}],
                "units": ["/haui/tt-cntt"],
            },
        )

    env = Env(tmp_path, api)
    login_as(env)
    assert env.run("whoami") == 0
    out = env.out.getvalue()
    assert "qt.son" in out
    assert "Tạ Văn Sơn" in out
    assert "process_admin @ /haui/tt-cntt" in out


def test_whoami_without_login(tmp_path: Path) -> None:
    env = Env(tmp_path, lambda r: httpx.Response(500))
    assert env.run("whoami") == 1
    assert "dxlab login" in env.err.getvalue()
    assert env.requests == []


def test_whoami_unauthenticated_error_from_core(tmp_path: Path) -> None:
    body = {"error": {"code": "UNAUTHENTICATED", "message": "Token không hợp lệ.", "details": {}, "request_id": "r"}}
    env = Env(tmp_path, lambda r: httpx.Response(401, json=body))
    login_as(env)
    assert env.run("whoami") == 1
    err = env.err.getvalue()
    assert "Token không hợp lệ. [UNAUTHENTICATED]" in err
    assert "dxlab login" in err


def test_whoami_non_dxlab_error_body(tmp_path: Path) -> None:
    env = Env(tmp_path, lambda r: httpx.Response(502, text="<html>Bad Gateway</html>"))
    login_as(env)
    assert env.run("whoami") == 1
    assert "HTTP 502" in env.err.getvalue()


# --- publish ------------------------------------------------------------------------------------


def make_app(tmp_path: Path, name: str = "lab-repair") -> Path:
    app = tmp_path / "apps" / name
    (app / "forms").mkdir(parents=True)
    (app / ".git-keep").write_text("ẩn", encoding="utf-8")
    (app / "forms" / ".swp").write_text("ẩn", encoding="utf-8")
    (app / ".hidden").mkdir()
    (app / ".hidden" / "x.json").write_text("{}", encoding="utf-8")
    (app / "lab-repair.bpmn").write_text("<definitions>Sửa chữa</definitions>", encoding="utf-8")
    (app / "forms" / "report-schema.json").write_text('{"type": "object"}', encoding="utf-8")
    (app / "forms" / "report-uischema.json").write_text("{}", encoding="utf-8")
    return app


def parse_multipart(request: httpx.Request) -> list[tuple[str, str, bytes, str]]:
    """(tên phần, filename, nội dung, content-type) của từng phần."""
    raw = b"Content-Type: " + request.headers["content-type"].encode() + b"\r\n\r\n" + request.content
    message = BytesParser(policy=HTTP).parsebytes(raw)
    return [
        (part.get_param("name", header="content-disposition"), part.get_filename(), part.get_payload(decode=True), part.get_content_type())
        for part in message.iter_parts()
    ]


def test_publish_sends_every_visible_file_and_prints_version(tmp_path: Path) -> None:
    def api(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert str(request.url) == f"{API}/definitions/lab-repair/versions"
        assert request.headers["authorization"].startswith("Bearer ")
        return httpx.Response(
            201,
            json={"app_id": "lab-repair", "version": 3, "status": "pending_approval", "files": ["lab-repair.bpmn"]},
        )

    env = Env(tmp_path, api)
    login_as(env)
    app = make_app(tmp_path)
    assert env.run("publish", str(app) + "/") == 0  # có dấu / cuối vẫn lấy đúng app_id

    parts = parse_multipart(env.requests[-1])
    assert [(name, filename) for name, filename, _, _ in parts] == [
        ("files", "forms/report-schema.json"),
        ("files", "forms/report-uischema.json"),
        ("files", "lab-repair.bpmn"),
    ]
    by_name = {filename: (body, ctype) for _, filename, body, ctype in parts}
    assert by_name["lab-repair.bpmn"][0].decode() == "<definitions>Sửa chữa</definitions>"
    assert by_name["forms/report-schema.json"] == (b'{"type": "object"}', "application/json")
    assert env.out.getvalue().strip() == "Đã nạp lab-repair phiên bản 3, trạng thái pending_approval"


def test_publish_prints_validator_errors_line_by_line(tmp_path: Path) -> None:
    body = {
        "error": {
            "code": "DEFINITION_REJECTED",
            "message": "Gói ứng dụng bị từ chối.",
            "details": {
                "errors": [
                    {"file": "lab-repair.bpmn", "element": "repairing", "message": "Thiếu lane."},
                    {"path": "forms/report-schema.json", "message": "Sai JSON Schema."},
                ]
            },
            "request_id": "r",
        }
    }
    env = Env(tmp_path, lambda r: httpx.Response(422, json=body))
    login_as(env)
    assert env.run("publish", str(make_app(tmp_path))) == 1
    assert env.out.getvalue() == ""
    assert env.err.getvalue().splitlines() == [
        "Lỗi: Gói ứng dụng bị từ chối. [DEFINITION_REJECTED]",
        "  - lab-repair.bpmn (repairing): Thiếu lane.",
        "  - forms/report-schema.json: Sai JSON Schema.",
    ]


def test_publish_forbidden_role(tmp_path: Path) -> None:
    body = {"error": {"code": "FORBIDDEN_ROLE", "message": "Chỉ quản trị quy trình.", "details": {"layer": 1}, "request_id": "r"}}
    env = Env(tmp_path, lambda r: httpx.Response(403, json=body))
    login_as(env)
    assert env.run("publish", str(make_app(tmp_path))) == 1
    assert "Chỉ quản trị quy trình. [FORBIDDEN_ROLE]" in env.err.getvalue()


def test_publish_requires_login(tmp_path: Path) -> None:
    env = Env(tmp_path, lambda r: httpx.Response(500))
    assert env.run("publish", str(make_app(tmp_path))) == 1
    assert "dxlab login" in env.err.getvalue()
    assert env.requests == []


def test_publish_missing_or_empty_directory(tmp_path: Path) -> None:
    env = Env(tmp_path, lambda r: httpx.Response(500))
    login_as(env)
    assert env.run("publish", str(tmp_path / "apps" / "khong-co")) == 1
    assert "Không có thư mục" in env.err.getvalue()

    empty = tmp_path / "apps" / "rong"
    empty.mkdir(parents=True)
    (empty / ".chi-an").write_text("x", encoding="utf-8")
    env.err.truncate(0)
    env.err.seek(0)
    assert env.run("publish", str(empty)) == 1
    assert "không có tệp nào" in env.err.getvalue()
    assert env.requests == []
