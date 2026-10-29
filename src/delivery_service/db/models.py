from datetime import datetime
from decimal import Decimal
from typing import Annotated
import uuid

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    MetaData,
    Numeric,
    String,
    func,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

intpk = Annotated[int, mapped_column(primary_key=True)]
Money = Annotated[Decimal, mapped_column(Numeric(10, 2))]
# Wide enough for the largest weight and content cost the columns allow at any
# realistic rate: (99_999.999 * 0.5 + 99_999_999.99 * 0.01) * rate ~ 1.05e6 * rate,
# so up to ~950 000 RUB/USD. With Numeric(10, 2) a single big package overflowed
# at ~95 RUB/USD and rolled back the cost update for every package.
RubMoney = Annotated[Decimal, mapped_column(Numeric(14, 2))]
PackageName = Annotated[str, mapped_column(String(80))]
PackageTypeName = Annotated[str, mapped_column(String(50), unique=True)]


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class PackageType(Base):
    __tablename__ = "package_types"

    id: Mapped[intpk]
    name: Mapped[PackageTypeName]

    packages: Mapped[list[Package]] = relationship(back_populates="type")


class Package(Base):
    __tablename__ = "packages"

    id: Mapped[intpk]
    type_id: Mapped[int] = mapped_column(ForeignKey("package_types.id", ondelete="RESTRICT"))
    name: Mapped[PackageName]
    weight: Mapped[Decimal] = mapped_column(Numeric(8, 3))
    content_cost_usd: Mapped[Money]
    exchange_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    delivery_cost_rub: Mapped[RubMoney | None]
    company_id: Mapped[int | None]
    session_id: Mapped[uuid.UUID]

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    type: Mapped[PackageType] = relationship(back_populates="packages", lazy="selectin")

    __table_args__ = (
        CheckConstraint("weight > 0", name="weight_positive"),
        CheckConstraint("content_cost_usd >= 0", name="content_cost_usd_non_negative"),
        CheckConstraint("exchange_rate > 0", name="exchange_rate_positive"),
        CheckConstraint("delivery_cost_rub >= 0", name="delivery_cost_rub_non_negative"),
        CheckConstraint(
            "(exchange_rate IS NULL) = (delivery_cost_rub IS NULL)",
            name="cost_and_rate_defining_together",
        ),
        CheckConstraint("company_id > 0", name="company_id_positive"),
        # The user's list: WHERE session_id = ? [AND type_id = ?]. Also serves
        # session_id-only lookups (leftmost column), so a separate index is not needed.
        Index("ix_packages_session_id_type_id", "session_id", "type_id"),
        # The background cost job: WHERE delivery_cost_rub IS NULL. Partial, so it
        # holds only the few not-yet-priced packages instead of the whole table.
        Index(
            "ix_packages_delivery_cost_pending",
            "id",
            postgresql_where=text("delivery_cost_rub IS NULL"),
        ),
    )
