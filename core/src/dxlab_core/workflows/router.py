# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from dxlab_core.auth.deps import CurrentPrincipal
from dxlab_core.db import DbSession
from dxlab_core.pagination import Page, PageParams, page_params
from dxlab_core.workflows import service
from dxlab_core.workflows.models import Workflow
from dxlab_core.workflows.schemas import WorkflowDetail, WorkflowOut

router = APIRouter(prefix="/workflows", tags=["Phiếu công việc"])


class CreateWorkflow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    app_id: str = Field(min_length=1, max_length=64)
    data: dict[str, Any]


@router.post("", status_code=201, response_model=WorkflowOut, summary="Tạo phiếu từ phiên bản ứng dụng đang áp dụng")
def create(body: CreateWorkflow, principal: CurrentPrincipal, session: DbSession) -> dict:
    return service.summary(service.create(session, principal, body.app_id, body.data))


@router.get("", response_model=Page[WorkflowDetail], summary="Danh sách phiếu trong phạm vi được xem")
def listing(principal: CurrentPrincipal, session: DbSession, page: Annotated[PageParams, Depends(page_params)],
            app_id: str | None = None, status: str | None = None) -> dict:
    query = select(Workflow).order_by(Workflow.created_at.desc(), Workflow.id)
    if app_id:
        query = query.where(Workflow.app_id == app_id)
    if status:
        query = query.where(Workflow.status == status)
    visible = [w for w in session.scalars(query) if service.can_read(principal, w)]
    return {"items": [service.detail(session, principal, w) for w in visible[page.offset:page.offset + page.limit]],
            "total": len(visible)}


@router.get("/{workflow_id}", response_model=WorkflowDetail, summary="Xem phiếu và lịch sử xử lý")
def get(workflow_id: uuid.UUID, principal: CurrentPrincipal, session: DbSession) -> dict:
    return service.detail(session, principal, service.find(session, workflow_id))
