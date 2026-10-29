# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Môi trường Alembic. URL database lấy từ cấu hình (`sqlalchemy.url`) hoặc biến `DXLAB_DATABASE_URL`."""

import os

from alembic import context
from sqlalchemy import engine_from_config, pool

from dxlab_core.config import ConfigError
from dxlab_core.db.models import metadata

config = context.config
if not config.get_main_option("sqlalchemy.url"):
    url = os.environ.get("DXLAB_DATABASE_URL")
    if not url:
        raise ConfigError("Thiếu biến môi trường bắt buộc: DXLAB_DATABASE_URL")
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))


def run_migrations_offline() -> None:
    context.configure(url=config.get_main_option("sqlalchemy.url"), target_metadata=metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
