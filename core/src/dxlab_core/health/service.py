# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

import logging
from importlib.metadata import version

from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from dxlab_core.health.schemas import HealthOut

log = logging.getLogger(__name__)


def check(engine: Engine) -> HealthOut:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        database = "ok"
    except SQLAlchemyError as exc:
        log.warning("health_database_error type=%s", type(exc).__name__)
        database = "error"
    return HealthOut(
        status="ok" if database == "ok" else "degraded",
        version=version("dxlab-core"),
        database=database,
    )
