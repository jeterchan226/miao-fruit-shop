from app.services.order_service import (
    Amounts,
    _new_order_no,
    compute_amounts,
    initial_status,
)

ORDER_NO_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def test_shipping_free_at_threshold():
    a = compute_amounts(5000)
    assert a == Amounts(subtotal=5000, shipping_fee=0, cod_fee=0, total=5000)


def test_shipping_charged_below_threshold():
    a = compute_amounts(4999)
    assert a == Amounts(subtotal=4999, shipping_fee=150, cod_fee=0, total=5149)


def test_cod_fee_always_zero():
    # 付款只剩轉帳,不再有貨到付款手續費。
    assert compute_amounts(1000).cod_fee == 0


def test_initial_status_is_pending_payment():
    assert initial_status() == "pending_payment"


def test_order_no_format():
    no = _new_order_no()
    assert no.startswith("MM-")
    assert len(no) == 9
    assert all(c in ORDER_NO_ALPHABET for c in no[3:])
