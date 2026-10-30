# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

import hashlib
import uuid
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select

from dxlab_core.audit.service import events_for
from dxlab_core.config import Settings
from dxlab_core.documents import storage
from dxlab_core.documents.models import Document
from dxlab_core.documents.service import clean_filename
from sample_data import (
    ADMIN_DX,
    APP_ID,
    CSVC_LAN,
    IT_TECH,
    QT_SON,
    SOP_PC,
    SOP_PROJECTOR,
    SV_AN,
    HeadersFactory,
)

pytestmark = pytest.mark.usefixtures("clean_data")

SOP_SOURCE = "data/sop/sop-pc-khong-len-nguon.md của dự án DX-Lab (APP-03)"


def upload(
    client: TestClient,
    headers: dict[str, str],
    content: bytes,
    *,
    filename: str = "sop-pc-khong-len-nguon.md",
    content_type: str = "text/markdown",
    **fields: str,
):
    form = {
        "app_id": APP_ID,
        "kind": "sop",
        "title": "SOP-IT-01: Máy tính không lên nguồn",
        "source": SOP_SOURCE,
        "license": "CC-BY-4.0",
        **fields,
    }
    return client.post("/api/documents", data=form, files={"file": (filename, content, content_type)}, headers=headers)


def test_upload_sop_stores_bytes_by_checksum_and_returns_provenance(
    client: TestClient, settings: Settings, headers_for: HeadersFactory
) -> None:
    content = SOP_PC.encode()
    digest = hashlib.sha256(content).hexdigest()

    response = upload(client, headers_for(*CSVC_LAN), content, source_ref="mục 4")
    assert response.status_code == 201
    doc = response.json()
    assert doc["sha256"] == digest
    assert doc["size"] == len(content)
    assert doc["kind"] == "sop"
    assert doc["app_id"] == APP_ID
    assert doc["filename"] == "sop-pc-khong-len-nguon.md"
    assert doc["content_type"] == "text/markdown"
    assert (doc["source"], doc["license"], doc["source_ref"]) == (SOP_SOURCE, "CC-BY-4.0", "mục 4")
    assert doc["created_by"] == "csvc.lan"
    assert doc["created_at"].endswith("Z")

    assert (settings.documents_dir / digest[:2] / digest).read_bytes() == content

    downloaded = client.get(f"/api/documents/{doc['id']}/content", headers=headers_for(*SV_AN))
    assert downloaded.status_code == 200
    assert downloaded.content == content
    assert downloaded.headers["content-type"].startswith("text/markdown")
    assert downloaded.headers["content-disposition"].startswith("attachment")
    assert "sop-pc-khong-len-nguon.md" in downloaded.headers["content-disposition"]
    assert downloaded.headers["x-content-type-options"] == "nosniff"

    meta = client.get(f"/api/documents/{doc['id']}", headers=headers_for(*SV_AN))
    assert meta.json() == doc


def test_filename_never_becomes_a_path(client: TestClient, settings: Settings, headers_for: HeadersFactory) -> None:
    content = b"noi dung bat ky"
    response = upload(client, headers_for(*QT_SON), content, filename="..\\..\\etc/../passwd.md", content_type="")
    assert response.status_code == 201
    doc = response.json()
    assert doc["filename"] == "passwd.md"
    assert doc["content_type"] == "text/markdown"
    stored = sorted(path.relative_to(settings.documents_dir) for path in settings.documents_dir.rglob("*") if path.is_file())
    digest = hashlib.sha256(content).hexdigest()
    assert stored == [Path(digest[:2]) / digest]


def test_clean_filename_drops_directories_and_control_characters() -> None:
    assert clean_filename("C:\\bao cao\\bao-gia.pdf") == "bao-gia.pdf"
    assert clean_filename("a\x00b\n.md") == "ab.md"
    assert clean_filename("") == "tep-tai-len"
    assert clean_filename(None) == "tep-tai-len"


def test_same_content_is_stored_once_but_each_upload_is_a_document(
    client: TestClient, settings: Settings, headers_for: HeadersFactory
) -> None:
    first = upload(client, headers_for(*CSVC_LAN), SOP_PC.encode()).json()
    second = upload(client, headers_for(*QT_SON), SOP_PC.encode(), title="Bản nạp lại").json()
    assert first["id"] != second["id"]
    assert first["sha256"] == second["sha256"]
    assert len([path for path in settings.documents_dir.rglob("*") if path.is_file()]) == 1


def test_markdown_text_is_extracted_but_binary_is_not(app: FastAPI, client: TestClient, headers_for: HeadersFactory) -> None:
    md = upload(client, headers_for(*CSVC_LAN), SOP_PC.encode()).json()
    pdf = upload(
        client, headers_for(*CSVC_LAN), b"%PDF-1.7\n\x00\x01\xff", filename="bao-gia.pdf", content_type="application/pdf",
        kind="quote", title="Báo giá quạt nguồn",
    ).json()
    with app.state.sessionmaker() as session:
        texts = {
            str(row.id): row.text for row in session.scalars(select(Document).where(Document.id.in_([uuid.UUID(md["id"]), uuid.UUID(pdf["id"])])))
        }
    assert texts[md["id"]] == SOP_PC
    assert texts[pdf["id"]] is None


@pytest.mark.parametrize("actor", [SV_AN, ADMIN_DX], ids=["sinh-vien", "system_admin"])
def test_upload_denied_without_a_catalog_role(client: TestClient, settings: Settings, headers_for: HeadersFactory, actor) -> None:
    response = upload(client, headers_for(*actor), SOP_PC.encode())
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN_ROLE"
    assert not settings.documents_dir.exists() or not any(settings.documents_dir.rglob("*"))


def test_technician_may_attach_quotes_but_not_sop(client: TestClient, headers_for: HeadersFactory) -> None:
    assert upload(client, headers_for(*IT_TECH), b"bao gia 1", kind="quote", title="Báo giá 1").status_code == 201
    assert upload(client, headers_for(*IT_TECH), SOP_PC.encode()).status_code == 403


def test_upload_requires_token(client: TestClient) -> None:
    response = client.post("/api/documents", files={"file": ("a.md", b"x", "text/markdown")})
    assert response.status_code == 401


def test_invalid_form_reports_each_field(client: TestClient, headers_for: HeadersFactory) -> None:
    response = upload(client, headers_for(*CSVC_LAN), SOP_PC.encode(), kind="hop-dong", title="  ", app_id="Lab Repair")
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_FAILED"
    assert {item["path"] for item in error["details"]["errors"]} == {"app_id", "kind", "title"}

    missing = client.post("/api/documents", data={"app_id": APP_ID}, files={"file": ("a.md", b"x", "text/markdown")},
                          headers=headers_for(*CSVC_LAN))
    assert missing.status_code == 422
    assert {item["path"] for item in missing.json()["error"]["details"]["errors"]} == {
        "body.kind", "body.title", "body.source", "body.license",
    }


def test_empty_and_oversized_files_are_rejected_without_leftovers(
    client: TestClient, settings: Settings, headers_for: HeadersFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    empty = upload(client, headers_for(*CSVC_LAN), b"")
    assert empty.status_code == 422
    assert empty.json()["error"]["details"]["errors"] == [{"path": "file", "message": "Tệp rỗng."}]

    monkeypatch.setattr(storage, "MAX_BYTES", 1024)
    big = upload(client, headers_for(*CSVC_LAN), b"x" * 1025)
    assert big.status_code == 422
    assert big.json()["error"]["details"]["errors"][0]["path"] == "file"
    leftovers = [path for path in settings.documents_dir.rglob("*") if path.is_file() and path.stat().st_size > 0]
    assert leftovers == []


def test_quotes_are_hidden_from_reporters(client: TestClient, headers_for: HeadersFactory) -> None:
    sop = upload(client, headers_for(*CSVC_LAN), SOP_PC.encode()).json()
    quote = upload(client, headers_for(*CSVC_LAN), b"bang bao gia", kind="quote", title="Báo giá máy chiếu",
                   filename="bao-gia.txt", content_type="text/plain").json()

    reporter = headers_for(*SV_AN)
    visible = client.get("/api/documents", headers=reporter).json()
    assert [item["id"] for item in visible["items"]] == [sop["id"]]
    assert visible["total"] == 1
    assert client.get(f"/api/documents/{quote['id']}", headers=reporter).status_code == 404
    assert client.get(f"/api/documents/{quote['id']}/content", headers=reporter).status_code == 404

    officer = client.get("/api/documents", headers=headers_for(*CSVC_LAN)).json()
    assert officer["total"] == 2
    assert client.get(f"/api/documents/{quote['id']}/content", headers=headers_for(*QT_SON)).content == b"bang bao gia"
    assert client.get("/api/documents", headers=headers_for(*ADMIN_DX)).status_code == 403


def test_linked_documents_follow_workflow_visibility_and_validate_upload(
    client: TestClient, settings: Settings, headers_for: HeadersFactory
) -> None:
    from test_workflows import activate, task_package

    activate(client, headers_for, task_package())
    creator = headers_for("sv.an")
    created = client.post("/api/workflows", headers=creator, json={"app_id": "mini", "data": {"cost": 3500000}})
    assert created.status_code == 201, created.text
    workflow_id = created.json()["workflow_id"]
    writer = headers_for(*CSVC_LAN)
    for app_id, reference in (("mini", str(uuid.uuid4())), ("other-app", workflow_id)):
        denied = upload(client, writer, b"khong duoc luu", app_id=app_id, workflow_id=reference, kind="quote")
        assert denied.status_code == 404
    outsider = headers_for("outside", ["/haui/sict/it_technician"])
    denied = upload(client, outsider, b"khong duoc luu", app_id="mini", workflow_id=workflow_id, kind="quote")
    assert denied.status_code == 404
    assert not settings.documents_dir.exists() or not any(settings.documents_dir.rglob("*"))

    response = upload(client, writer, b"bao gia phong may", app_id="mini", workflow_id=workflow_id, kind="quote")
    assert response.status_code == 201, response.text
    document_id = response.json()["id"]
    insider = headers_for("inside", ["/haui/tt-cntt/lab_manager"])
    for headers in (creator, insider, writer):
        assert client.get(f"/api/documents/{document_id}", headers=headers).status_code == 200
        assert client.get(f"/api/documents/{document_id}/content", headers=headers).status_code == 200
        assert [item["id"] for item in client.get("/api/documents", headers=headers).json()["items"]] == [document_id]
    assert client.get("/api/documents", headers=outsider).json()["total"] == 0
    assert client.get(f"/api/documents/{document_id}", headers=outsider).status_code == 404
    assert client.get(f"/api/documents/{document_id}/content", headers=outsider).status_code == 404


def test_list_filters_and_paginates(client: TestClient, headers_for: HeadersFactory) -> None:
    csvc = headers_for(*CSVC_LAN)
    upload(client, csvc, SOP_PC.encode(), title="SOP 1")
    upload(client, csvc, SOP_PROJECTOR.encode(), title="SOP 2")
    upload(client, csvc, b"khac", title="Bản vẽ", kind="other", app_id="app-khac", filename="ban-ve.txt")

    def titles(**params: object) -> list[str]:
        response = client.get("/api/documents", params=params, headers=csvc)
        assert response.status_code == 200
        return [item["title"] for item in response.json()["items"]]

    assert titles(app_id="app-khac") == ["Bản vẽ"]
    assert titles(kind="sop") == ["SOP 2", "SOP 1"]
    assert titles(kind="sop", app_id="app-khac") == []
    assert titles(limit=1, offset=1) == ["SOP 2"]
    assert client.get("/api/documents", params={"limit": 1}, headers=csvc).json()["total"] == 3
    assert client.get(f"/api/documents/{uuid.uuid4()}", headers=csvc).status_code == 404


def test_upload_is_audited(app: FastAPI, client: TestClient, headers_for: HeadersFactory) -> None:
    doc = upload(client, headers_for(*CSVC_LAN), SOP_PC.encode()).json()
    with app.state.sessionmaker() as session:
        (event,) = events_for(session, "document", doc["id"])
    assert (event.action, event.actor) == ("document.upload", "csvc.lan")
    assert event.details["sha256"] == doc["sha256"]
    assert event.details["kind"] == "sop"


def test_text_file_below_upload_limit_but_too_big_for_tsvector_is_still_accepted(
    client: TestClient, headers_for: HeadersFactory
) -> None:
    # Từ CJK 3 ký tự phân biệt (mỗi ký tự 3 byte UTF-8): ~492.000 ký tự, dưới giới hạn upload 20 MB nhưng nếu đưa
    # nguyên vào chỉ mục thì biểu diễn tsvector khoảng 1,7 MB, vượt giới hạn 1 MiB của PostgreSQL.
    words = (
        chr(0x4E00 + i % 20000) + chr(0x4E00 + (i // 20000 * 131 + i * 7) % 20000) + chr(0x4E00 + (i * 13 + i // 20000 * 977) % 20000)
        for i in range(123000)
    )
    text = " ".join(words)
    assert len(text) > 400_000

    response = upload(client, headers_for(*CSVC_LAN), text.encode(), filename="lon.txt", content_type="text/plain")

    assert response.status_code == 201, response.text
