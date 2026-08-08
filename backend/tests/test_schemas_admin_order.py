import pytest
from pydantic import ValidationError

from app.schemas.order import (
    AdminOrderItemUpdate,
    AdminOrderListResponse,
    AdminOrderRead,
    AdminOrderTransferUpdate,
    AdminOrderUpdate,
    OrderRead,
    OrderStatusUpdate,
)


def test_admin_order_read_has_admin_only_fields():
    fields = set(AdminOrderRead.model_fields)
    assert {
        "id",
        "customer_email",
        "line_user_id",
        "line_display_name",
        "line_notification_consent",
        "ship_city",
        "updated_at",
        "items",
        "transfer_last5",
        "transfer_payer_name",
        "transfer_note",
    } <= fields


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
        OrderStatusUpdate(status="shipping", extra_field="oops")


def test_order_status_update_rejects_legacy_statuses():
    # delivered(已送達)已移除,連同其他舊狀態都要拒絕。
    for status in ("shipped", "completed", "delivered"):
        with pytest.raises(ValidationError):
            OrderStatusUpdate(status=status)


def test_admin_order_update_all_fields_optional():
    update = AdminOrderUpdate()
    assert update.customer_name is None
    assert update.items is None


def test_admin_order_update_forbids_extra():
    with pytest.raises(ValidationError):
        AdminOrderUpdate(status="shipping")


def test_admin_order_item_update_requires_positive_qty():
    with pytest.raises(ValidationError):
        AdminOrderItemUpdate(spec_id=1, qty=0)


def test_admin_order_transfer_update_forbids_extra():
    with pytest.raises(ValidationError):
        AdminOrderTransferUpdate(status="ready")
