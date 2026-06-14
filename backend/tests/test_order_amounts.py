from app.services.order_service import (
    Amounts,
    _new_order_no,
    compute_amounts,
    initial_status,
)

ORDER_NO_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def test_shipping_free_at_threshold():
    a = compute_amounts(5000, "linepay")
    assert a == Amounts(subtotal=5000, shipping_fee=0, cod_fee=0, total=5000)


def test_shipping_charged_below_threshold():
    a = compute_amounts(4999, "linepay")
    assert a == Amounts(subtotal=4999, shipping_fee=150, cod_fee=0, total=5149)


def test_cod_fee_added_for_cod():
    a = compute_amounts(1000, "cod")
    assert a == Amounts(subtotal=1000, shipping_fee=150, cod_fee=30, total=1180)


def test_cod_fee_zero_for_non_cod():
    a = compute_amounts(1000, "atm")
    assert a.cod_fee == 0


def test_initial_status_cod_is_pending():
    assert initial_status("cod") == "pending"


def test_initial_status_prepaid_is_pending_payment():
    assert initial_status("linepay") == "pending_payment"
    assert initial_status("card") == "pending_payment"
    assert initial_status("atm") == "pending_payment"


def test_order_no_format():
    no = _new_order_no()
    assert no.startswith("MM-")
    assert len(no) == 9
    assert all(c in ORDER_NO_ALPHABET for c in no[3:])
