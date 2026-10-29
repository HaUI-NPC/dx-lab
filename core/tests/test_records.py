# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from dxlab_core.audit.service import events_for
from dxlab_core.records.service import InvalidRecordSchema, register_record_type
from sample_data import (
    ADMIN_DX,
    APP_ID,
    CSVC_LAN,
    HeadersFactory,
    QT_SON,
    ROOM_SCHEMA,
    ROOM_TYPE,
    ROOMS,
    ROOMS_LICENSE,
    ROOMS_SOURCE,
    SV_AN,
)

pytestmark = pytest.mark.usefixtures("clean_data")

BASE = f"/api/records/{APP_ID}/{ROOM_TYPE}"


@pytest.fixture
def room_type(app: FastAPI) -> None:
    with app.state.sessionmaker() as session:
        register_record_type(session, APP_ID, ROOM_TYPE, ROOM_SCHEMA)
        session.commit()


def put_room(client: TestClient, headers: dict[str, str], room: dict, **overrides: object):
    body = {"data": room, "source": ROOMS_SOURCE, "license": ROOMS_LICENSE, "source_ref": f"rooms.json#{room['id']}"}
    return client.put(f"{BASE}/{room['id']}", json={**body, **overrides}, headers=headers)


@pytest.fixture
def loaded_rooms(client: TestClient, room_type: None, headers_for: HeadersFactory) -> None:
    for room in ROOMS:
        assert put_room(client, headers_for(*CSVC_LAN), room).status_code == 201


def test_register_record_type_rejects_invalid_schema(app: FastAPI) -> None:
    with app.state.sessionmaker() as session, pytest.raises(InvalidRecordSchema) as caught:
        register_record_type(session, APP_ID, "bad", {"type": "khong-co-kieu-nay"})
    assert caught.value.code == "VALIDATION_FAILED"
    assert caught.value.details["errors"][0]["path"] == "schema.type"


def test_register_record_type_bumps_version_only_when_schema_changes(app: FastAPI) -> None:
    schema = {"type": "object", "properties": {"a": {"type": "string"}}}
    with app.state.sessionmaker() as session:
        first = register_record_type(session, APP_ID, "versioned", schema).version
        again = register_record_type(session, APP_ID, "versioned", dict(schema)).version
        changed = register_record_type(session, APP_ID, "versioned", {**schema, "required": ["a"]}).version
    assert (first, again, changed) == (1, 1, 2)


def test_upsert_creates_then_updates_with_provenance(client: TestClient, room_type: None, headers_for: HeadersFactory) -> None:
    room = ROOMS[0]
    created = put_room(client, headers_for(*CSVC_LAN), room)
    assert created.status_code == 201
    body = created.json()
    assert body["data"] == room
    assert body["source"] == ROOMS_SOURCE
    assert body["license"] == ROOMS_LICENSE
    assert body["source_ref"] == "rooms.json#lab-a1-305"
    assert body["created_by"] == body["updated_by"] == "csvc.lan"
    assert body["created_at"].endswith("Z")
    assert body["schema_version"] == 1

    updated = put_room(client, headers_for(*QT_SON), {**room, "capacity": 42}, source="Kiểm kê lại ngày 30/10")
    assert updated.status_code == 200
    after = updated.json()
    assert after["data"]["capacity"] == 42
    assert after["source"] == "Kiểm kê lại ngày 30/10"
    assert (after["created_by"], after["created_at"]) == (body["created_by"], body["created_at"])
    assert after["updated_by"] == "qt.son"
    assert datetime.fromisoformat(after["updated_at"]) > datetime.fromisoformat(body["created_at"])

    fetched = client.get(f"{BASE}/lab-a1-305", headers=headers_for(*SV_AN))
    assert fetched.status_code == 200
    assert fetched.json() == after


def test_invalid_data_returns_vietnamese_errors_with_paths(client: TestClient, room_type: None, headers_for: HeadersFactory) -> None:
    broken = {"id": "lab-x", "name": "Phòng lỗi", "capacity": "bốn mươi", "status": "dang-sua", "floor": -1, "phong_thua": 1}
    response = put_room(client, headers_for(*CSVC_LAN), broken)
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_FAILED"
    assert error["details"]["errors"] == [
        {"path": "data.capacity", "message": "Phải là số nguyên."},
        {"path": "data.code", "message": "Thiếu trường bắt buộc."},
        {"path": "data.floor", "message": "Giá trị phải từ 0 trở lên."},
        {"path": "data.org_path", "message": "Thiếu trường bắt buộc."},
        {"path": "data.phong_thua", "message": "Trường không được phép."},
        {"path": "data.status", "message": "Giá trị không nằm trong danh sách cho phép: active, inactive."},
    ]
    assert client.get(f"{BASE}/lab-x", headers=headers_for(*CSVC_LAN)).status_code == 404


def test_nested_path_and_pattern_error(client: TestClient, room_type: None, headers_for: HeadersFactory) -> None:
    response = put_room(client, headers_for(*CSVC_LAN), {**ROOMS[0], "org_path": "haui/sai"})
    assert response.status_code == 422
    assert response.json()["error"]["details"]["errors"] == [
        {"path": "data.org_path", "message": "Không đúng định dạng yêu cầu."}
    ]


def test_missing_provenance_is_rejected(client: TestClient, room_type: None, headers_for: HeadersFactory) -> None:
    response = client.put(f"{BASE}/lab-a1-305", json={"data": ROOMS[0]}, headers=headers_for(*CSVC_LAN))
    assert response.status_code == 422
    paths = {item["path"] for item in response.json()["error"]["details"]["errors"]}
    assert paths == {"body.source", "body.license"}


@pytest.mark.parametrize("actor", [SV_AN, ADMIN_DX], ids=["sinh-vien", "system_admin"])
def test_write_denied_for_reporter_and_system_admin(
    client: TestClient, room_type: None, headers_for: HeadersFactory, actor: tuple[str, list[str]]
) -> None:
    response = put_room(client, headers_for(*actor), ROOMS[0])
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN_ROLE"
    assert client.get(f"{BASE}/{ROOMS[0]['id']}", headers=headers_for(*CSVC_LAN)).status_code == 404


def test_read_requires_login_and_blocks_system_admin(client: TestClient, loaded_rooms: None, headers_for: HeadersFactory) -> None:
    assert client.get(BASE).status_code == 401
    assert client.get(BASE, headers=headers_for(*ADMIN_DX)).status_code == 403
    assert client.get(BASE, headers=headers_for(*SV_AN)).status_code == 200


def test_unknown_type_and_bad_key(client: TestClient, room_type: None, headers_for: HeadersFactory) -> None:
    missing = client.get(f"/api/records/{APP_ID}/khong-co", headers=headers_for(*SV_AN))
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "NOT_FOUND"
    bad_key = client.put(
        f"{BASE}/khoa%20co%20dau%20cach",
        json={"data": ROOMS[0], "source": ROOMS_SOURCE, "license": ROOMS_LICENSE},
        headers=headers_for(*CSVC_LAN),
    )
    assert bad_key.status_code == 422
    assert bad_key.json()["error"]["details"]["errors"][0]["path"] == "key"


def test_list_paginates_and_filters(client: TestClient, loaded_rooms: None, headers_for: HeadersFactory) -> None:
    headers = headers_for(*SV_AN)

    page = client.get(BASE, params={"limit": 2, "offset": 1}, headers=headers).json()
    assert page["total"] == 4
    assert [item["key"] for item in page["items"]] == ["lab-a1-306", "lab-a1-601"]

    def keys(**params: str) -> list[str]:
        response = client.get(BASE, params=params, headers=headers)
        assert response.status_code == 200
        return [item["key"] for item in response.json()["items"]]

    assert keys(q="mạng") == ["lab-a1-601"]
    assert keys(q="PHÒNG a1-305") == ["lab-a1-305"]
    assert keys(q="phòng nào không có") == []
    assert keys(unit="/haui/sict") == ["lab-a1-305", "lab-a1-306", "lab-a1-601"]
    assert keys(unit="/haui/sict/khmt/") == ["lab-a1-305", "lab-a1-306"]
    assert keys(unit="/haui/sict/khm") == []
    assert keys(unit="/haui/sict", q="mạng") == ["lab-a1-601"]


def test_upsert_is_audited_without_record_data(app: FastAPI, client: TestClient, room_type: None, headers_for: HeadersFactory) -> None:
    put_room(client, headers_for(*CSVC_LAN), ROOMS[0])
    put_room(client, headers_for(*QT_SON), {**ROOMS[0], "capacity": 41})
    with app.state.sessionmaker() as session:
        events = events_for(session, "record", f"{APP_ID}/{ROOM_TYPE}/lab-a1-305")
    assert [(event.action, event.actor, event.details["created"]) for event in events] == [
        ("record.upsert", "csvc.lan", True),
        ("record.upsert", "qt.son", False),
    ]
    assert events[0].actor_roles == [
        {"role": "facility_officer", "unit": "/haui/ban-csvc"},
        {"role": "rule_admin", "unit": "/haui/ban-csvc"},
    ]
    assert "data" not in events[0].details
