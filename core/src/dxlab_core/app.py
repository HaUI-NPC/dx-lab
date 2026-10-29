# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Ứng dụng FastAPI của core. Mọi route nằm dưới `/api`; thêm mảng mới = thêm một dòng `include_router`."""

from importlib.metadata import version

from fastapi import FastAPI

from dxlab_core.auth.router import router as auth_router
from dxlab_core.auth.tokens import TokenVerifier
from dxlab_core.config import Settings, get_settings
from dxlab_core.db import make_engine, make_sessionmaker
from dxlab_core.definitions.router import router as definitions_router
from dxlab_core.errors import ErrorResponse, install_error_handlers
from dxlab_core.health.router import router as health_router
from dxlab_core.request_id import RequestIdMiddleware, configure_logging
from dxlab_core.tasks.router import router as tasks_router
from dxlab_core.workflows.router import router as workflows_router

API_PREFIX = "/api"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="DX-Lab Core API",
        version=version("dxlab-core"),
        description="Tầng 1 – Open-Core headless. Mọi lời gọi đi qua APISIX; xem docs/ARCHITECTURE.md.",
        openapi_url=f"{API_PREFIX}/openapi.json",
        docs_url=f"{API_PREFIX}/docs",
        redoc_url=None,
        responses={500: {"model": ErrorResponse, "description": "Lỗi hệ thống"}},
    )
    app.state.settings = settings
    app.state.engine = make_engine(settings.database_url)
    app.state.sessionmaker = make_sessionmaker(app.state.engine)
    app.state.token_verifier = TokenVerifier(settings)

    install_error_handlers(app)
    app.add_middleware(RequestIdMiddleware)

    app.include_router(health_router, prefix=API_PREFIX)
    app.include_router(auth_router, prefix=API_PREFIX)
    app.include_router(definitions_router, prefix=API_PREFIX)
    app.include_router(workflows_router, prefix=API_PREFIX)
    app.include_router(tasks_router, prefix=API_PREFIX)
    return app


def __getattr__(name: str) -> FastAPI:
    # `uvicorn dxlab_core.app:app`: chỉ tạo ứng dụng (và đọc biến môi trường) khi thật sự được gọi,
    # để import module trong test hay công cụ không đòi đủ biến môi trường.
    if name == "app":
        application = create_app()
        globals()["app"] = application
        return application
    raise AttributeError(name)
