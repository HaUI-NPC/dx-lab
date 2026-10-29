# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Cấu hình core, đọc từ biến môi trường `DXLAB_*` (docs/ARCHITECTURE.md mục 5)."""

from functools import lru_cache
from pathlib import Path

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigError(RuntimeError):
    """Cấu hình thiếu hoặc sai; thông báo chỉ chứa tên biến, không chứa giá trị."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DXLAB_", extra="ignore")

    database_url: str
    oidc_issuer: str = "http://localhost:8180/realms/dxlab"
    oidc_internal_url: str | None = None
    oidc_audience: str = "dxlab-core"
    documents_dir: Path
    search_index_dir: Path
    model_cache_dir: Path | None = None
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    log_level: str = "INFO"

    @property
    def oidc_backchannel_url(self) -> str:
        """URL Keycloak mà tiến trình core gọi được (JWKS); token vẫn mang `iss` = `oidc_issuer`."""
        return self.oidc_internal_url or self.oidc_issuer


def load_settings(**overrides: object) -> Settings:
    """Đọc cấu hình; thiếu hoặc sai biến thì báo đúng tên biến, không in giá trị (có thể là secret)."""
    try:
        return Settings(**overrides)
    except ValidationError as exc:
        names = sorted({f"DXLAB_{str(err['loc'][0]).upper()}" for err in exc.errors() if err["loc"]})
        kinds = {err["type"] for err in exc.errors()}
        reason = "Thiếu biến môi trường bắt buộc" if kinds == {"missing"} else "Biến môi trường thiếu hoặc sai"
        raise ConfigError(f"{reason}: {', '.join(names)}") from None


@lru_cache
def get_settings() -> Settings:
    return load_settings()
