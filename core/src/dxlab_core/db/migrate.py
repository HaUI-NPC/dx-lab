# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""`python -m dxlab_core.db.migrate`: nâng database lên phiên bản migration mới nhất (chạy khi container khởi động)."""

from pathlib import Path

from alembic import command
from alembic.config import Config

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
    from dxlab_core.config import get_settings

    upgrade(get_settings().database_url)


if __name__ == "__main__":
    main()
