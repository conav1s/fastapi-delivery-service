from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, StringConstraints, field_serializer

PackageNameType = Annotated[str, Field(max_length=80)]
PackageTypeNameType = Annotated[str, Field(max_length=50)]
PackageWeightType = Annotated[Decimal, Field(gt=0, max_digits=8, decimal_places=3)]
MoneyType = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2)]


class ReadBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PackageCreate(BaseModel):
    name: PackageNameType
    type_id: PositiveInt
    weight: PackageWeightType
    content_cost_usd: MoneyType


class PackageCreateResponse(BaseModel):
    package_id: PositiveInt


class PackageTypeRead(ReadBase):
    id: PositiveInt
    name: PackageTypeNameType


class Pagination(BaseModel):
    limit: Annotated[int, Field(ge=1, le=100)] = 20
    offset: Annotated[int, Field(ge=0)] = 0


class PackageFilters(BaseModel):
    type_id: PositiveInt | None = None
    has_delivery_cost: bool | None = None


class PackageRead(ReadBase):
    id: PositiveInt
    name: PackageNameType
    type: PackageTypeRead
    weight: PackageWeightType
    content_cost_usd: MoneyType
    delivery_cost_rub: MoneyType | None
    company_id: int | None

    @field_serializer("delivery_cost_rub")
    def serialize_delivery_cost_rub(self, delivery_cost_rub: MoneyType | None) -> MoneyType | str:
        return delivery_cost_rub if delivery_cost_rub is not None else "Не рассчитано"


class PackageListResponse(BaseModel):
    items: list[PackageRead]
    total: int
    offset: int
    limit: int


class FillCostsResponse(BaseModel):
    updated: int


class PackageAssign(BaseModel):
    company_id: PositiveInt


class SupportQuestion(BaseModel):
    question: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=500)]


class SupportAnswerResponse(BaseModel):
    answer: str
    sources: list[str] = Field(description="Sections of the rules the answer is based on")
