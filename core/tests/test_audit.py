# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

from fastapi import FastAPI

from dxlab_core.audit.service import events_for, record
from dxlab_core.auth.principal import Principal


def test_audit_history_keeps_actor_roles_and_order(app: FastAPI) -> None:
    actor = Principal.from_claims({"preferred_username": "tk.hai", "groups": ["/haui/sict/khmt/faculty_head"]})
    with app.state.sessionmaker() as session:
        record(session, actor=actor, action="repair.approve", object_type="workflow", object_id="wf-1",
               details={"basis": "GĐ-PC-01/2026"})
        record(session, actor=None, action="workflow.step", object_type="workflow", object_id="wf-1")
        record(session, actor=actor, action="repair.approve", object_type="workflow", object_id="wf-2")
        session.commit()

    with app.state.sessionmaker() as session:
        history = events_for(session, "workflow", "wf-1")

    assert [(e.actor, e.action) for e in history] == [("tk.hai", "repair.approve"), (None, "workflow.step")]
    assert history[0].actor_roles == [{"role": "faculty_head", "unit": "/haui/sict/khmt"}]
    assert history[0].details == {"basis": "GĐ-PC-01/2026"}
