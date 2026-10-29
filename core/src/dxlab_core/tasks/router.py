# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from dxlab_core.auth.deps import CurrentPrincipal
from dxlab_core.db import DbSession
from dxlab_core.pagination import PageParams, page_params
from dxlab_core.tasks import service
from dxlab_core.workflows.service import summary

router = APIRouter(prefix="/tasks", tags=["Hộp việc"])


class CompleteTask(BaseModel):
    model_config = ConfigDict(extra="forbid")
    data: dict[str, Any]


@router.get("")
def listing(principal: CurrentPrincipal, session: DbSession, page: Annotated[PageParams, Depends(page_params)],
            workflow_id: uuid.UUID | None = None) -> dict:
    return service.listing(session, principal, page.limit, page.offset, workflow_id)


@router.get("/{task_id}")
def get(task_id: uuid.UUID, principal: CurrentPrincipal, session: DbSession) -> dict:
    return service.detail(session, principal, service.find(session, task_id))


@router.post("/{task_id}/complete")
def complete(task_id: uuid.UUID, body: CompleteTask, principal: CurrentPrincipal, session: DbSession) -> dict:
    return summary(service.complete(session, principal, task_id, body.data))
