from typing import get_args

from app.core.constants import (
    ORDER_SOURCE_ADMIN,
    ORDER_SOURCE_STOREFRONT,
    PAYMENT_METHOD_TRANSFER,
    OrderSource,
    PaymentMethod,
)


def test_order_source_literal_matches_constants():
    assert get_args(OrderSource) == (ORDER_SOURCE_STOREFRONT, ORDER_SOURCE_ADMIN)


def test_payment_method_literal_matches_constants():
    assert get_args(PaymentMethod) == (PAYMENT_METHOD_TRANSFER,)
