from decimal import Decimal

import pytest

from delivery_service.services.delivery_cost import calc_delivery_cost


@pytest.mark.parametrize(
    ("weight,content_cost,usd_rate,expected"),
    [
        (Decimal("16"), Decimal("729"), Decimal("83.80"), Decimal("1281.3020")),
        (Decimal("10"), Decimal("0")  , Decimal("90.00"), Decimal(" 450.0000")),
        (Decimal("26"), Decimal("708"), Decimal("81.41"), Decimal("1634.7128")),
        (Decimal("52"), Decimal("749"), Decimal("75.11"), Decimal("2515.4339")),
        (Decimal("22"), Decimal("817"), Decimal("77.23"), Decimal("1480.4991")),
        (Decimal("58"), Decimal("416"), Decimal("77.46"), Decimal("2568.5736")),
    ]
)
def test_calc_delivery_cost(
    weight: Decimal,
    content_cost: Decimal,
    usd_rate: Decimal,
    expected: Decimal
) -> None:

    delivery_cost = calc_delivery_cost(weight, content_cost, usd_rate)

    assert delivery_cost == expected
