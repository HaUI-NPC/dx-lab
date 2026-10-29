# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from dxlab_core.auth.deps import CurrentPrincipal
from dxlab_core.db import DbSession
from dxlab_core.pagination import Page, PageParams, page_params
from dxlab_core.tasks import service
from dxlab_core.tasks.schemas import TaskDetail, TaskOut
from dxlab_core.workflows.schemas import WorkflowOut
from dxlab_core.workflows.service import summary

router = APIRouter(prefix="/tasks", tags=["Hộp việc"])


class CompleteTask(BaseModel):
    model_config = ConfigDict(extra="forbid")
    data: dict[str, Any]


@router.get("", response_model=Page[TaskOut], summary="Hộp việc theo vai trò và phạm vi của người gọi")
def listing(principal: CurrentPrincipal, session: DbSession, page: Annotated[PageParams, Depends(page_params)],
            workflow_id: uuid.UUID | None = None) -> dict:
    return service.listing(session, principal, page.limit, page.offset, workflow_id)


@router.get("/{task_id}", response_model=TaskDetail, summary="Xem dữ liệu và form của bước được giao")
def get(task_id: uuid.UUID, principal: CurrentPrincipal, session: DbSession) -> dict:
    return service.detail(session, principal, service.find(session, task_id))


@router.post("/{task_id}/complete", response_model=WorkflowOut, summary="Hoàn thành bước và chuyển trạng thái quy trình")
def complete(task_id: uuid.UUID, body: CompleteTask, principal: CurrentPrincipal, session: DbSession) -> dict:
    return summary(service.complete(session, principal, task_id, body.data))
