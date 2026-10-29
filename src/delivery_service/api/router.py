from typing import Annotated
import uuid

from fastapi import Depends, Request
from fastapi.routing import APIRouter

from delivery_service.services.delivery_cost import DeliveryCostService
from delivery_service.services.packages import PackageData, PackageQuery, PackageService
from delivery_service.services.support import SupportService

from .dependencies import get_package_service, get_support_service, get_user_session_id
from .schemas import (
    FillCostsResponse,
    PackageAssign,
    PackageCreate,
    PackageCreateResponse,
    PackageFilters,
    PackageListResponse,
    PackageRead,
    PackageTypeRead,
    Pagination,
    SupportAnswerResponse,
    SupportQuestion,
)

router = APIRouter(tags=["packages"])


@router.post("/packages", status_code=201)
async def create_package(
    package_input: PackageCreate,
    service: Annotated[PackageService, Depends(get_package_service)],
    user_session_id: Annotated[uuid.UUID, Depends(get_user_session_id)],
) -> PackageCreateResponse:

    created_package = await service.create_package(
        data=PackageData(
            name=package_input.name,
            type_id=package_input.type_id,
            weight=package_input.weight,
            content_cost_usd=package_input.content_cost_usd,
        ),
        session_id=user_session_id,
    )

    return PackageCreateResponse(package_id=created_package.id)


@router.get("/package-types")
async def list_package_types(
    service: Annotated[PackageService, Depends(get_package_service)],
) -> list[PackageTypeRead]:

    package_types = await service.get_package_types()

    return [PackageTypeRead.model_validate(pt) for pt in package_types]


@router.get("/packages/{package_id}")
async def get_package(
    package_id: int,
    service: Annotated[PackageService, Depends(get_package_service)],
    user_session_id: Annotated[uuid.UUID, Depends(get_user_session_id)],
) -> PackageRead:

    package = await service.get_package(package_id, user_session_id)

    return PackageRead.model_validate(package)


@router.get("/packages")
async def list_packages(
    pagination: Annotated[Pagination, Depends()],
    filters: Annotated[PackageFilters, Depends()],
    service: Annotated[PackageService, Depends(get_package_service)],
    user_session_id: Annotated[uuid.UUID, Depends(get_user_session_id)],
) -> PackageListResponse:

    package_page = await service.get_user_package_list(
        session_id=user_session_id,
        query=PackageQuery(
            type_id=filters.type_id,
            has_delivery_cost=filters.has_delivery_cost,
            offset=pagination.offset,
            limit=pagination.limit,
        ),
    )

    return PackageListResponse(
        items=[PackageRead.model_validate(package) for package in package_page.items],
        total=package_page.total,
        offset=pagination.offset,
        limit=pagination.limit,
    )


@router.put("/packages/{package_id}/company", status_code=204)
async def assign_package_to_company(
    package_id: int,
    assignment_data: PackageAssign,
    service: Annotated[PackageService, Depends(get_package_service)],
) -> None:

    await service.assign_package(company_id=assignment_data.company_id, package_id=package_id)


router_support = APIRouter(tags=["support"])


@router_support.post("/support/questions")
async def ask_support(
    body: SupportQuestion,
    service: Annotated[SupportService, Depends(get_support_service)],
) -> SupportAnswerResponse:
    result = await service.answer(body.question)

    return SupportAnswerResponse(answer=result.answer, sources=result.sources)


router_debug = APIRouter(tags=["debug"])


@router_debug.post("/packages/fill-missing-costs")
async def update_packages_delivery_cost(request: Request) -> FillCostsResponse:
    service: DeliveryCostService = request.app.state.delivery_cost_service
    updated = await service.fill_missing_costs()

    return FillCostsResponse(updated=updated)
