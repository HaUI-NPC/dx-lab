# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Kiểu Pydantic dùng chung cho schema phản hồi."""

from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator

# Thời gian trả ra luôn ở UTC dạng `2026-10-29T08:30:00Z` (CONTRIBUTING.md, "Đặt tên API"), dù database trả múi giờ nào.
UtcDatetime = Annotated[datetime, AfterValidator(lambda value: value.astimezone(UTC))]
