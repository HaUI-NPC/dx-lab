# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Nạp model của mọi mảng vào `Base.metadata` để Alembic thấy. Mảng mới có `models.py` → thêm một dòng import."""

from dxlab_core.audit import models as audit_models  # noqa: F401
from dxlab_core.db import Base

metadata = Base.metadata
