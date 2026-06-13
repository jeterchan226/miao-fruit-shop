from app.schemas.product import (
    AdminSpecRead,
    ProductUpdate,
    PublicSpecRead,
    SpecCreate,
)


def test_public_spec_has_no_stock_qty_field():
    fields = set(PublicSpecRead.model_fields)
    assert "stock_status" in fields
    assert "stock_qty" not in fields  # public must not expose exact stock


def test_admin_spec_exposes_stock_qty():
    fields = set(AdminSpecRead.model_fields)
    assert {"stock_qty", "low_stock_threshold", "is_active"} <= fields


def test_product_update_all_optional():
    u = ProductUpdate()
    assert u.model_dump(exclude_unset=True) == {}


def test_spec_create_defaults():
    s = SpecCreate(label="x", qty_text="y", price=100, stock_qty=5)
    assert s.low_stock_threshold == 3
    assert s.sort_order == 0
