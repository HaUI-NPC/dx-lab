# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Nạp model của mọi mảng vào `Base.metadata` để Alembic thấy. Mảng mới có `models.py` → thêm một dòng import."""

from dxlab_core.audit import models as audit_models  # noqa: F401
from dxlab_core.db import Base
from dxlab_core.definitions import models as definitions_models  # noqa: F401
from dxlab_core.workflows import models as workflows_models  # noqa: F401
from dxlab_core.documents import models as documents_models  # noqa: F401
from dxlab_core.records import models as records_models  # noqa: F401

metadata = Base.metadata
