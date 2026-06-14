import pytest
from pydantic import ValidationError

from app.schemas.order import (
    AdminOrderListResponse,
    AdminOrderRead,
    OrderRead,
    OrderStatusUpdate,
)


def test_admin_order_read_has_admin_only_fields():
    fields = set(AdminOrderRead.model_fields)
    assert {"id", "customer_email", "ship_city", "updated_at", "items"} <= fields


def test_public_order_read_has_no_admin_fields():
    fields = set(OrderRead.model_fields)
    assert "customer_name" not in fields
    assert "ship_city" not in fields
    assert "updated_at" not in fields


def test_admin_order_list_response_structure():
    resp = AdminOrderListResponse(total=0, page=1, page_size=20, items=[])
    assert resp.total == 0
    assert resp.items == []


def test_order_status_update_forbids_extra():
    with pytest.raises(ValidationError):
        OrderStatusUpdate(status="confirmed", extra_field="oops")


def test_order_status_update_rejects_legacy_statuses():
    for status in ("shipped", "completed"):
        with pytest.raises(ValidationError):
            OrderStatusUpdate(status=status)
