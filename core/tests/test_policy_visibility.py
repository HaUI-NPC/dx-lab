# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

from sqlalchemy import select
from sqlalchemy.orm import Session

from dxlab_core.auth.principal import Principal, RoleAssignment
from dxlab_core.workflows.access import can_read, visible_clause
from dxlab_core.workflows.models import Workflow
from test_workflows import activate, task_package


def test_sql_visibility_matches_workflow_access(client, app, headers_for):
    activate(client, headers_for, task_package())
    response = client.post('/api/workflows', headers=headers_for('reporter'),
                           json={'app_id': 'mini', 'data': {'cost': 3500000}})
    assert response.status_code == 201
    people = [Principal('reporter', 'Reporter', ()),
              Principal('other', 'Other', ()),
              Principal('admin', 'Admin', (RoleAssignment('system_admin', '/haui'),)),
              Principal('auditor', 'Auditor', (RoleAssignment('internal_auditor', '/haui'),)),
              Principal('manager', 'Manager', (RoleAssignment('lab_manager', '/haui/tt-cntt'),)),
              Principal('outsider', 'Outsider', (RoleAssignment('lab_manager', '/haui/elsewhere'),)),
              Principal('finance', 'Finance', (RoleAssignment('finance_officer', '/haui'),))]
    with Session(app.state.engine) as session:
        workflows = list(session.scalars(select(Workflow)))
        for principal in people:
            expected = {workflow.id for workflow in workflows if can_read(principal, workflow)}
            selected = set(session.scalars(select(Workflow.id).where(visible_clause(principal))))
            assert selected == expected
