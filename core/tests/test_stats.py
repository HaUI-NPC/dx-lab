# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Thống kê dùng dữ liệu PostgreSQL thật và không vượt quyền xem phiếu."""
import uuid
from datetime import UTC, datetime, timedelta

from dxlab_core.definitions.models import DefinitionVersion
from dxlab_core.workflows.models import Workflow, WorkflowTask


def test_stats_visible_workflows_filters_and_closed_deadlines(client, app, headers_for):
    now = datetime.now(UTC)
    with app.state.sessionmaker.begin() as session:
        definitions = {}
        for app_id in ("lab-repair", "other"):
            definitions[app_id] = DefinitionVersion(
                app_id=app_id, version=1, status="active", display_name=app_id,
                process_id="main", checksum="a" * 64, published_by="admin",
            )
            session.add(definitions[app_id])
        session.flush()

        def add(app_id, owner, status, unit, approved, actual, due, ready):
            workflow = Workflow(
                id=uuid.uuid4(), app_id=app_id, definition=definitions[app_id], created_by=owner,
                status=status, status_name=status, due_at=due, engine_state={},
                data={"room_unit": unit, "approved_amount_vnd": approved,
                      "actual_cost_vnd": actual, "reporter_name": "THÔNG TIN CÁ NHÂN"},
            )
            session.add(workflow)
            session.flush()
            if ready:
                session.add(WorkflowTask(workflow_id=workflow.id, engine_task_id=str(uuid.uuid4()),
                                         step_id=status, step_name=status, lane="reporter", status="ready"))

        add("lab-repair", "alice", "repairing", "/haui/a", 100, 60, now - timedelta(days=1), True)
        add("lab-repair", "alice", "completed", "/haui/b", 200, 150, now - timedelta(days=1), False)
        add("lab-repair", "bob", "repairing", "/haui/c", 900, 800, now - timedelta(days=1), True)
        add("other", "alice", "pending", None, 30, 10, now + timedelta(days=1), True)

    alice = headers_for("alice")
    result = client.get("/api/stats", headers=alice)
    assert result.status_code == 200, result.text
    assert result.json() == {
        "by_status": [{"status": "completed", "status_name": "completed", "count": 1},
                      {"status": "pending", "status_name": "pending", "count": 1},
                      {"status": "repairing", "status_name": "repairing", "count": 1}],
        "by_unit": [{"unit": None, "count": 1}, {"unit": "/haui/a", "count": 1},
                    {"unit": "/haui/b", "count": 1}],
        "overdue": 1, "cost": {"approved_total": 330, "actual_total": 220},
    }
    assert "THÔNG TIN CÁ NHÂN" not in result.text
    filtered = client.get("/api/stats", params={"app_id": "lab-repair"}, headers=alice).json()
    assert filtered["cost"] == {"approved_total": 300, "actual_total": 210}
    assert sum(item["count"] for item in filtered["by_status"]) == 2
    assert filtered["overdue"] == 1
    empty = client.get("/api/stats", params={"app_id": "missing"}, headers=alice).json()
    assert empty == {"by_status": [], "by_unit": [], "overdue": 0,
                     "cost": {"approved_total": 0, "actual_total": 0}}
    manager = headers_for("manager", ["/haui/a/lab_manager"])
    scoped = client.get("/api/stats", headers=manager).json()
    assert scoped == {"by_status": [{"status": "repairing", "status_name": "repairing", "count": 1}],
                      "by_unit": [{"unit": "/haui/a", "count": 1}], "overdue": 1,
                      "cost": {"approved_total": 100, "actual_total": 60}}
    director = headers_for("director", ["/haui/ban-csvc/facility_director"])
    all_visible = client.get("/api/stats", headers=director).json()
    assert all_visible["cost"] == {"approved_total": 1230, "actual_total": 1020}
    assert all_visible["overdue"] == 2
    assert sum(item["count"] for item in all_visible["by_status"]) == 4
    assert client.get("/api/stats").status_code == 401
