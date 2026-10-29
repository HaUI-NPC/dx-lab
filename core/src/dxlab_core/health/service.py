# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

import logging
from importlib.metadata import version

from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from dxlab_core.health.schemas import HealthOut
from dxlab_core.search.engine import SearchEngine

log = logging.getLogger(__name__)


def check(engine: Engine, search: SearchEngine) -> HealthOut:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        database = "ok"
    except SQLAlchemyError as exc:
        log.warning("health_database_error type=%s", type(exc).__name__)
        database = "error"
    search_index, embedding_model = search.health(engine)
    return HealthOut(
        # Thiếu mô hình embedding không làm degraded: tìm kiếm vẫn chạy bằng toàn văn.
        status="ok" if database == "ok" and search_index == "ok" else "degraded",
        version=version("dxlab-core"),
        database=database,
        search_index=search_index,
        embedding_model=embedding_model,
    )
