# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Cấu hình của portal, đọc từ biến môi trường (docs/ARCHITECTURE.md mục 5).

Thiếu biến bắt buộc thì dừng ngay lúc khởi động và báo đúng tên biến, không in giá trị secret.
"""

from __future__ import annotations

from pydantic import AliasChoices, Field, SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_ISSUER = "http://localhost:8180/realms/dxlab"
DEFAULT_API_URL = "http://localhost:9080/api"


def _env(name: str) -> AliasChoices:
    # Alias là chính tên biến môi trường, để lỗi thiếu cấu hình nêu đúng tên biến.
    return AliasChoices(name)


class Settings(BaseSettings):
    """Biến môi trường của portal."""

    # Biến đặt rỗng coi như chưa đặt (compose có thể truyền chuỗi rỗng).
    model_config = SettingsConfigDict(extra="ignore", populate_by_name=False, env_ignore_empty=True)

    public_url: str = Field(validation_alias=_env("DXLAB_PORTAL_PUBLIC_URL"))
    client_id: str = Field(default="dxlab-portal", validation_alias=_env("DXLAB_PORTAL_CLIENT_ID"))
    client_secret: SecretStr = Field(validation_alias=_env("DXLAB_PORTAL_CLIENT_SECRET"))
    session_secret: SecretStr = Field(validation_alias=_env("DXLAB_PORTAL_SESSION_SECRET"))
    oidc_issuer: str = Field(default=DEFAULT_ISSUER, validation_alias=_env("DXLAB_OIDC_ISSUER"))
    # Không đặt thì dùng chính `DXLAB_OIDC_ISSUER` (chạy ngoài compose).
    oidc_internal_url: str | None = Field(default=None, validation_alias=_env("DXLAB_OIDC_INTERNAL_URL"))
    api_url: str = Field(default=DEFAULT_API_URL, validation_alias=_env("DXLAB_API_URL"))
    log_level: str = Field(default="INFO", validation_alias=_env("DXLAB_LOG_LEVEL"))

    @field_validator("public_url", "oidc_issuer", "api_url")
    @classmethod
    def _strip_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")

    @field_validator("oidc_internal_url")
    @classmethod
    def _strip_internal(cls, value: str | None) -> str | None:
        return value.rstrip("/") if value else None

    @field_validator("client_secret", "session_secret")
    @classmethod
    def _secret_not_blank(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip():
            raise ValueError("không được để trống")
        return value

    @property
    def discovery_url(self) -> str:
        """Địa chỉ discovery OIDC theo kênh nội bộ (hoặc issuer khi chạy ngoài compose)."""
        base = self.oidc_internal_url or self.oidc_issuer
        return f"{base}/.well-known/openid-configuration"

    @property
    def cookie_secure(self) -> bool:
        return self.public_url.startswith("https://")


def load_settings() -> Settings:
    """Đọc cấu hình; thiếu hoặc sai biến thì thoát với thông báo nêu tên biến."""
    try:
        return Settings()  # type: ignore[call-arg]
    except ValidationError as exc:
        lines = []
        for err in exc.errors(include_input=False, include_url=False):
            name = ".".join(str(part) for part in err["loc"])
            lines.append(f"  - {name}: {'thiếu' if err['type'] == 'missing' else err['msg']}")
        raise SystemExit(
            "Cấu hình portal không hợp lệ, kiểm tra các biến môi trường sau:\n" + "\n".join(lines)
        ) from None
