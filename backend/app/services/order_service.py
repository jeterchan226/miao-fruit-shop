import secrets
from typing import NamedTuple

from app.core.constants import COD_FEE, FREE_SHIPPING_THRESHOLD, SHIPPING_FEE

ORDER_NO_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


class Amounts(NamedTuple):
    subtotal: int
    shipping_fee: int
    cod_fee: int
    total: int


def compute_amounts(subtotal: int, payment_method: str) -> Amounts:
    shipping_fee = 0 if subtotal >= FREE_SHIPPING_THRESHOLD else SHIPPING_FEE
    cod_fee = COD_FEE if payment_method == "cod" else 0
    return Amounts(
        subtotal=subtotal,
        shipping_fee=shipping_fee,
        cod_fee=cod_fee,
        total=subtotal + shipping_fee + cod_fee,
    )


def initial_status(payment_method: str) -> str:
    return "pending" if payment_method == "cod" else "pending_payment"


def _new_order_no() -> str:
    suffix = "".join(secrets.choice(ORDER_NO_ALPHABET) for _ in range(6))
    return f"MM-{suffix}"
