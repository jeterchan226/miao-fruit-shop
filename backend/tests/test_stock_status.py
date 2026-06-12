import pytest

from app.services.product_service import derive_stock_status


@pytest.mark.parametrize(
    "qty,threshold,expected",
    [
        (0, 3, "out"),
        (-5, 3, "out"),
        (3, 3, "low"),
        (1, 3, "low"),
        (4, 3, "in"),
        (100, 3, "in"),
    ],
)
def test_derive_stock_status(qty, threshold, expected):
    assert derive_stock_status(qty, threshold) == expected
