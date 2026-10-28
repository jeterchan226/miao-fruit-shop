from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DuplicateSpecError,
    EvenQtyRequiredError,
    InsufficientStockError,
    ItemQtyLockedError,
    NotFoundError,
    PriceChangedError,
)
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.product_spec import ProductSpec
from app.repositories import product_repo
from app.services.order_items import (
    Amounts,
    ItemRequest,
    ItemsResult,
    apply_items,
    release_items,
)


async def _seed_specs(db_session: AsyncSession, *specs: ProductSpec) -> list[ProductSpec]:
    product = Product(slug="kanro", name="甘露梨", description="d", image="i", season="s")
    product.specs = list(specs)
    await product_repo.add(db_session, product)
    await db_session.flush()
    return product.specs


def _spec(label: str, *, price: int, stock: int, two_pack: bool = False,
          active: bool = True) -> ProductSpec:
    return ProductSpec(label=label, qty_text="q", price=price, stock_qty=stock,
                       sort_order=1, is_two_pack=two_pack, is_active=active)


async def test_new_order_snapshots_current_price_and_deducts_stock(db_session: AsyncSession):
    box, pair = await _seed_specs(
        db_session,
        _spec("5 台斤家庭箱", price=1200, stock=10),
        _spec("2 粒裝", price=300, stock=8, two_pack=True),
    )

    result = await apply_items(
        db_session, [], [ItemRequest(box.id, 1), ItemRequest(pair.id, 2)],
        expected_total=1950,
    )

    assert [(i.spec_id, i.unit_price, i.qty, i.line_total) for i in result.items] == [
        (box.id, 1200, 1, 1200),
        (pair.id, 300, 2, 600),
    ]
    assert [(i.product_name, i.spec_label) for i in result.items] == [
        ("甘露梨", "5 台斤家庭箱"),
        ("甘露梨", "2 粒裝"),
    ]
    # 1 箱 + 2 粒裝×2 = 2 層 → 運費 150
    assert (result.amounts.subtotal, result.amounts.shipping_fee, result.amounts.total) == (
        1800, 150, 1950,
    )
    assert box.stock_qty == 9
    assert pair.stock_qty == 6


async def _existing_order(db_session: AsyncSession, *lines: tuple[ProductSpec, int, int]) -> Order:
    """建立含訂單品項的訂單;line = (規格, 數量, 下單價)。庫存視為已扣過。"""
    order = Order(
        order_no="MM-ITEMS1", status="pending_payment", customer_name="王小明",
        customer_phone="0912345678", ship_zipcode="100", ship_city="台北市",
        ship_district="中正區", ship_street="x", preferred_date=date(2026, 10, 1),
        delivery_window="any", payment_method="transfer",
        subtotal=0, shipping_fee=0, cod_fee=0, total=0,
    )
    order.items = [
        OrderItem(product_id=spec.product_id, spec_id=spec.id, product_name="甘露梨",
                  spec_label=spec.label, unit_price=unit_price, qty=qty,
                  line_total=unit_price * qty)
        for spec, qty, unit_price in lines
    ]
    db_session.add(order)
    await db_session.flush()
    return order


async def test_unchanged_item_keeps_unit_price_and_stock(db_session: AsyncSession):
    (box,) = await _seed_specs(db_session, _spec("A", price=1500, stock=5))
    order = await _existing_order(db_session, (box, 2, 1200))

    result = await apply_items(
        db_session, order.items, [ItemRequest(box.id, 2)], expected_total=2550,
    )

    assert result.items == [order.items[0]]
    assert (result.items[0].unit_price, result.items[0].qty) == (1200, 2)
    assert box.stock_qty == 5


async def test_increase_after_price_change_keeps_unit_price_and_deducts_difference(
    db_session: AsyncSession,
):
    (box,) = await _seed_specs(db_session, _spec("A", price=1500, stock=5))
    order = await _existing_order(db_session, (box, 1, 1200))

    result = await apply_items(
        db_session, order.items, [ItemRequest(box.id, 3)], expected_total=3600,
    )

    (item,) = result.items
    assert item is order.items[0]
    assert (item.unit_price, item.qty, item.line_total) == (1200, 3, 3600)
    assert box.stock_qty == 3


async def test_decrease_restores_difference(db_session: AsyncSession):
    (box,) = await _seed_specs(db_session, _spec("A", price=1200, stock=5))
    order = await _existing_order(db_session, (box, 3, 1200))

    result = await apply_items(
        db_session, order.items, [ItemRequest(box.id, 1)], expected_total=1300,
    )

    assert (result.items[0].qty, result.items[0].line_total) == (1, 1200)
    assert box.stock_qty == 7


async def test_added_spec_uses_current_price(db_session: AsyncSession):
    box, other = await _seed_specs(
        db_session, _spec("A", price=1500, stock=5), _spec("B", price=900, stock=5),
    )
    order = await _existing_order(db_session, (box, 1, 1200))

    result = await apply_items(
        db_session, order.items, [ItemRequest(box.id, 1), ItemRequest(other.id, 1)],
        expected_total=2250,
    )

    assert [(i.spec_id, i.unit_price) for i in result.items] == [
        (box.id, 1200), (other.id, 900),
    ]
    assert (box.stock_qty, other.stock_qty) == (5, 4)


async def test_removed_items_restore_stock_including_inactive_spec(db_session: AsyncSession):
    box, gone, keep = await _seed_specs(
        db_session,
        _spec("A", price=1200, stock=5),
        _spec("下架", price=800, stock=0, active=False),
        _spec("C", price=1000, stock=5),
    )
    order = await _existing_order(db_session, (box, 2, 1200), (gone, 1, 800), (keep, 1, 1000))

    result = await apply_items(
        db_session, order.items, [ItemRequest(keep.id, 1)], expected_total=1100,
    )

    assert [i.spec_id for i in result.items] == [keep.id]
    assert (box.stock_qty, gone.stock_qty, keep.stock_qty) == (7, 1, 5)


async def test_inactive_spec_kept_unchanged_succeeds(db_session: AsyncSession):
    gone, box = await _seed_specs(
        db_session,
        _spec("下架", price=800, stock=0, active=False),
        _spec("A", price=1200, stock=5),
    )
    order = await _existing_order(db_session, (gone, 1, 800), (box, 1, 1200))

    result = await apply_items(
        db_session, order.items, [ItemRequest(gone.id, 1), ItemRequest(box.id, 2)],
        expected_total=3200,
    )

    assert [(i.spec_id, i.qty, i.unit_price) for i in result.items] == [
        (gone.id, 1, 800), (box.id, 2, 1200),
    ]
    assert (gone.stock_qty, box.stock_qty) == (0, 4)


async def test_changing_qty_of_inactive_spec_raises_item_qty_locked(db_session: AsyncSession):
    (gone,) = await _seed_specs(db_session, _spec("下架箱", price=800, stock=3, active=False))
    order = await _existing_order(db_session, (gone, 1, 800))

    with pytest.raises(ItemQtyLockedError) as exc:
        await apply_items(db_session, order.items, [ItemRequest(gone.id, 2)], expected_total=1750)

    assert exc.value.detail == "下架箱 已下架，數量不可修改"
    assert (exc.value.code, exc.value.status_code) == ("ITEM_QTY_LOCKED", 409)
    assert gone.stock_qty == 3
    assert order.items[0].qty == 1


async def test_adding_inactive_spec_raises_not_found(db_session: AsyncSession):
    (gone,) = await _seed_specs(db_session, _spec("下架", price=800, stock=3, active=False))

    with pytest.raises(NotFoundError):
        await apply_items(db_session, [], [ItemRequest(gone.id, 1)], expected_total=900)


async def test_adding_unknown_spec_raises_not_found(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await apply_items(db_session, [], [ItemRequest(999999, 1)], expected_total=0)


async def test_duplicate_spec_in_request_raises(db_session: AsyncSession):
    (box,) = await _seed_specs(db_session, _spec("A", price=1200, stock=5))

    with pytest.raises(DuplicateSpecError) as exc:
        await apply_items(
            db_session, [], [ItemRequest(box.id, 1), ItemRequest(box.id, 2)],
            expected_total=3600,
        )

    assert (exc.value.code, exc.value.status_code) == ("DUPLICATE_SPEC", 422)
    assert box.stock_qty == 5


async def test_two_pack_odd_qty_raises_even_qty_required(db_session: AsyncSession):
    (pair,) = await _seed_specs(db_session, _spec("2 粒裝", price=300, stock=9, two_pack=True))

    with pytest.raises(EvenQtyRequiredError):
        await apply_items(db_session, [], [ItemRequest(pair.id, 3)], expected_total=1000)

    assert pair.stock_qty == 9


async def test_insufficient_stock_raises_and_leaves_all_stock_unchanged(
    db_session: AsyncSession,
):
    box, other = await _seed_specs(
        db_session, _spec("A", price=1200, stock=5), _spec("B", price=900, stock=1),
    )
    order = await _existing_order(db_session, (box, 2, 1200))

    with pytest.raises(InsufficientStockError):
        await apply_items(
            db_session, order.items, [ItemRequest(box.id, 1), ItemRequest(other.id, 2)],
            expected_total=3000,
        )

    assert (box.stock_qty, other.stock_qty) == (5, 1)
    assert order.items[0].qty == 2


async def test_expected_total_mismatch_raises_price_changed_without_writing(
    db_session: AsyncSession,
):
    box, other = await _seed_specs(
        db_session, _spec("A", price=1500, stock=5), _spec("B", price=900, stock=5),
    )
    order = await _existing_order(db_session, (box, 1, 1200))

    with pytest.raises(PriceChangedError) as exc:
        await apply_items(
            db_session, order.items, [ItemRequest(box.id, 2), ItemRequest(other.id, 1)],
            expected_total=3000,
        )

    # 1200×2 + 900 = 3300,達免運
    assert (exc.value.subtotal, exc.value.shipping_fee, exc.value.total) == (3300, 0, 3300)
    assert (box.stock_qty, other.stock_qty) == (5, 5)
    assert [(i.qty, i.line_total) for i in order.items] == [(1, 1200)]


async def test_release_items_restores_all_stock_including_inactive_and_skips_deleted(
    db_session: AsyncSession,
):
    box, gone = await _seed_specs(
        db_session,
        _spec("A", price=1200, stock=5),
        _spec("下架", price=800, stock=0, active=False),
    )
    order = await _existing_order(db_session, (box, 2, 1200), (gone, 1, 800))
    deleted = OrderItem(product_id=box.product_id, spec_id=999999, product_name="甘露梨",
                        spec_label="已刪除", unit_price=500, qty=1, line_total=500)
    orphan = OrderItem(product_id=box.product_id, spec_id=None, product_name="甘露梨",
                       spec_label="無規格", unit_price=500, qty=1, line_total=500)

    await release_items(db_session, [*order.items, deleted, orphan])

    assert (box.stock_qty, gone.stock_qty) == (7, 1)


def test_items_result_apply_to_sets_items_and_amounts():
    order = Order()
    item = OrderItem(product_id=1, spec_id=1, product_name="甘露梨", spec_label="A",
                     unit_price=880, qty=2, line_total=1760)
    result = ItemsResult(items=[item], amounts=Amounts(subtotal=1760, shipping_fee=150,
                                                       cod_fee=0, total=1910))

    result.apply_to(order)

    assert order.items == [item]
    assert (order.subtotal, order.shipping_fee, order.cod_fee, order.total) == (1760, 150, 0, 1910)
