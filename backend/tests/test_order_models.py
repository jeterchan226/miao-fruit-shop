import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base
from app.models import Order, OrderItem


def test_order_tables_registered_on_metadata():
    tables = set(Base.metadata.tables)
    assert "orders" in tables
    assert "order_items" in tables


def test_order_has_expected_columns():
    cols = set(Order.__table__.columns.keys())
    assert {
        "id", "order_no", "status", "customer_name", "customer_phone",
        "customer_email", "line_user_id", "line_display_name", "line_picture_url",
        "line_friendship_status", "line_notification_consent",
        "ship_zipcode", "ship_city", "ship_district",
        "ship_street", "preferred_date", "delivery_window", "payment_method",
        "note", "subtotal", "shipping_fee", "cod_fee", "total",
        "created_at", "updated_at",
    } <= cols


def test_order_item_has_snapshot_columns():
    cols = set(OrderItem.__table__.columns.keys())
    assert {
        "id", "order_id", "product_id", "spec_id", "product_name",
        "spec_label", "unit_price", "qty", "line_total",
    } <= cols


async def _insert_order(session: AsyncSession, order_no: str, key: str | None) -> None:
    await session.execute(
        text(
            """
            INSERT INTO orders (
                order_no, status, customer_name, customer_phone, ship_zipcode, ship_city,
                ship_district, ship_street, preferred_date, delivery_window, payment_method,
                line_notification_consent, subtotal, shipping_fee, cod_fee, total,
                idempotency_key
            ) VALUES (
                :order_no, 'pending_payment', 'n', 'p', 'z', 'c', 'd', 's', '2026-10-12',
                'any', 'transfer', false, 0, 0, 0, 0, :key
            )
            """
        ),
        {"order_no": order_no, "key": key},
    )


async def test_idempotency_key_unique(db_session: AsyncSession):
    await _insert_order(db_session, "MM-IDEM01", "key-1")

    with pytest.raises(IntegrityError):
        await _insert_order(db_session, "MM-IDEM02", "key-1")


async def test_idempotency_key_allows_multiple_nulls(db_session: AsyncSession):
    await _insert_order(db_session, "MM-IDEM01", None)
    await _insert_order(db_session, "MM-IDEM02", None)
