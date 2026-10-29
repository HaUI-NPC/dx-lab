# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

import pytest

from dxlab_core.auth.principal import Principal, RoleAssignment, unit_contains
from dxlab_core.config import ConfigError, load_settings


def test_groups_split_into_role_and_unit() -> None:
    principal = Principal.from_claims(
        {
            "preferred_username": "pgd.minh",
            "name": "Trịnh Văn Minh",
            "groups": ["/haui/ban-giam-doc/vice_president", "/haui/ban-giam-doc/process_owner", "/haui"],
        }
    )

    assert principal.roles == (
        RoleAssignment(role="vice_president", unit="/haui/ban-giam-doc"),
        RoleAssignment(role="process_owner", unit="/haui/ban-giam-doc"),
    )
    assert principal.units_for("process_owner") == ("/haui/ban-giam-doc",)


def test_every_signed_in_user_is_reporter_but_not_admin() -> None:
    principal = Principal.from_claims({"preferred_username": "sv.an", "groups": []})

    assert principal.has_role("reporter")
    assert not principal.has_role("lab_manager")
    assert not principal.is_system_admin


def test_system_admin_detected_from_group() -> None:
    principal = Principal.from_claims({"preferred_username": "admin.dx", "groups": ["/haui/tt-cntt/system_admin"]})

    assert principal.is_system_admin


@pytest.mark.parametrize(
    ("ancestor", "unit", "expected"),
    [
        ("/haui/sict/khmt", "/haui/sict/khmt/lab-a1-305", True),
        ("/haui/sict/khmt", "/haui/sict/khmt", True),
        ("/haui/sict/khmt", "/haui/sict/khmt-cu/lab-x", False),
        ("/haui/truong-dien-dien-tu/khoa-dien", "/haui/sict/khmt/lab-a1-305", False),
    ],
)
def test_unit_tree_containment(ancestor: str, unit: str, expected: bool) -> None:
    assert unit_contains(ancestor, unit) is expected


def test_missing_required_settings_named_without_values(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("DXLAB_DATABASE_URL", "DXLAB_DOCUMENTS_DIR", "DXLAB_SEARCH_INDEX_DIR"):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(ConfigError) as excinfo:
        load_settings()

    assert str(excinfo.value) == (
        "Thiếu biến môi trường bắt buộc: DXLAB_DATABASE_URL, DXLAB_DOCUMENTS_DIR, DXLAB_SEARCH_INDEX_DIR"
    )
