from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from delivery_service.db.models import Package, PackageType

from .exceptions import PackageNotFoundError, PackageTypeNotFoundError


@dataclass(frozen=True)
class PackageData:
    name: str
    type_id: int
    weight: Decimal
    content_cost_usd: Decimal


@dataclass(frozen=True)
class PackageQuery:
    type_id: int | None
    has_delivery_cost: bool | None
    offset: int
    limit: int


@dataclass(frozen=True)
class PackagePage:
    items: list[Package]
    total: int


class PackageService:
    def __init__(self, db_session: AsyncSession) -> None:
        self._db = db_session

    async def create_package(self, data: PackageData, session_id: UUID) -> Package:

        try:
            async with self._db.begin():
                package = Package(
                    name=data.name,
                    type_id=data.type_id,
                    weight=data.weight,
                    content_cost_usd=data.content_cost_usd,
                    session_id=session_id,
                )

                self._db.add(package)
        except IntegrityError as err:
            constraint = getattr(getattr(err.orig, "diag", None), "constraint_name", None)
            if constraint == "fk_packages_type_id_package_types":
                raise PackageTypeNotFoundError(data.type_id) from err
        except:
            raise

        return package

    async def get_package(self, package_id: int, session_id: UUID) -> Package:

        stmt = select(Package).where(Package.id == package_id, Package.session_id == session_id)

        package = await self._db.scalar(stmt)

        if package is None:
            raise PackageNotFoundError(package_id=package_id)

        return package

    async def get_user_package_list(self, session_id: UUID, query: PackageQuery) -> PackagePage:

        stmt = select(Package).where(Package.session_id == session_id)

        if query.type_id is not None:
            stmt = stmt.where(Package.type_id == query.type_id)

        if query.has_delivery_cost is not None:
            if query.has_delivery_cost:
                stmt = stmt.where(Package.delivery_cost_rub.is_not(None))
            else:
                stmt = stmt.where(Package.delivery_cost_rub.is_(None))

        count_stmt = select(func.count()).select_from(stmt.subquery())

        stmt = stmt.offset(query.offset).limit(query.limit).order_by(Package.id)

        total = await self._db.scalar(count_stmt) or 0
        packages_result = await self._db.scalars(stmt)

        return PackagePage(
            items=list(packages_result.all()),
            total=total,
        )

    async def get_package_types(self) -> list[PackageType]:

        stmt = select(PackageType).order_by(PackageType.id)
        res = await self._db.scalars(stmt)

        return list(res.all())
