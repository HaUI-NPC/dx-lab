# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Kiểm JWT do Keycloak cấp, bằng khóa công khai lấy từ JWKS (docs/ARCHITECTURE.md mục 4).

Core tự kiểm chữ ký, `iss`, `aud`, `exp` dù APISIX đã kiểm: không tin client hay gateway nào.
"""

import logging
from collections.abc import Callable, Mapping
from typing import Any

import jwt

from dxlab_core.config import Settings
from dxlab_core.errors import ApiError

log = logging.getLogger(__name__)

ALGORITHMS = ["RS256"]
LEEWAY_SECONDS = 30

KeyResolver = Callable[[str], Any]


class Unauthenticated(ApiError):
    def __init__(self, message: str = "Cần đăng nhập.") -> None:
        super().__init__(401, "UNAUTHENTICATED", message)


def jwks_resolver(settings: Settings) -> KeyResolver:
    """Lấy khóa ký theo `kid` của token từ JWKS của realm; khóa được cache, đổi khóa thì tải lại."""
    client = jwt.PyJWKClient(
        f"{settings.oidc_backchannel_url}/protocol/openid-connect/certs", cache_keys=True, lifespan=300, timeout=5
    )
    return lambda token: client.get_signing_key_from_jwt(token).key


class TokenVerifier:
    def __init__(self, settings: Settings, key_resolver: KeyResolver | None = None) -> None:
        self.issuer = settings.oidc_issuer
        self.audience = settings.oidc_audience
        self._resolve_key = key_resolver or jwks_resolver(settings)

    def verify(self, token: str) -> Mapping[str, Any]:
        try:
            key = self._resolve_key(token)
        except jwt.PyJWKClientConnectionError as exc:
            log.error("jwks_unreachable type=%s", type(exc).__name__)
            raise ApiError(500, "INTERNAL", "Không kiểm được token: dịch vụ đăng nhập không phản hồi.") from None
        except (jwt.PyJWKClientError, jwt.DecodeError) as exc:
            log.info("token_key_rejected type=%s", type(exc).__name__)
            raise Unauthenticated("Token không hợp lệ.") from None
        try:
            return jwt.decode(
                token,
                key,
                algorithms=ALGORITHMS,
                audience=self.audience,
                issuer=self.issuer,
                leeway=LEEWAY_SECONDS,
                options={"require": ["exp", "iat", "iss", "aud"]},
            )
        except jwt.ExpiredSignatureError:
            raise Unauthenticated("Phiên đăng nhập đã hết hạn, đăng nhập lại.") from None
        except jwt.InvalidTokenError as exc:
            log.info("token_rejected type=%s", type(exc).__name__)
            raise Unauthenticated("Token không hợp lệ.") from None
