# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from dxlab_core.auth.deps import CurrentPrincipal
from dxlab_core.db import DbSession
from dxlab_core.delegations import service
from dxlab_core.delegations.schemas import CreateDelegation, DelegationOut
from dxlab_core.pagination import Page, PageParams, page_params

router = APIRouter(prefix="/delegations", tags=["Ủy quyền"])


@router.post("", status_code=201, response_model=DelegationOut,
             summary="Ủy quyền TUQ. có thời hạn cho người cùng đơn vị")
def create(body: CreateDelegation, principal: CurrentPrincipal, session: DbSession) -> dict:
    return service.out(service.create(session, principal, **body.model_dump()))


@router.get("", response_model=Page[DelegationOut], summary="Ủy quyền mình đã giao hoặc được nhận")
def listing(principal: CurrentPrincipal, session: DbSession,
            page: Annotated[PageParams, Depends(page_params)]) -> dict:
    return service.listing(session, principal, page.limit, page.offset)


@router.post("/{delegation_id}/revoke", response_model=DelegationOut, summary="Thu hồi ủy quyền")
def revoke(delegation_id: uuid.UUID, principal: CurrentPrincipal, session: DbSession) -> dict:
    return service.out(service.revoke(session, principal, delegation_id))
