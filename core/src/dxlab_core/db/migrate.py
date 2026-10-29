# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""`python -m dxlab_core.db.migrate`: nâng database lên phiên bản migration mới nhất (chạy khi container khởi động)."""

import os
from pathlib import Path

from alembic import command
from alembic.config import Config

from dxlab_core.config import ConfigError

MIGRATIONS_DIR = Path(__file__).with_name("migrations")


def alembic_config(database_url: str) -> Config:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    # `%` trong mật khẩu phải nhân đôi vì Config dùng ConfigParser.
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return config


def upgrade(database_url: str, revision: str = "head") -> None:
    command.upgrade(alembic_config(database_url), revision)


def main() -> None:
    database_url = os.environ.get("DXLAB_DATABASE_URL")
    if not database_url:
        raise ConfigError("Thiếu biến môi trường bắt buộc: DXLAB_DATABASE_URL")
    upgrade(database_url)


if __name__ == "__main__":
    main()
