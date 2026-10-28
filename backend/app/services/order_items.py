"""訂單品項 module:建立或改動訂單品項的規則(上架、兩粒裝雙數、庫存、下單價、金額)集中於此。"""

from collections.abc import Sequence
from typing import NamedTuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import FREE_SHIPPING_THRESHOLD, SHIPPING_BY_LAYER
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
from app.models.product_spec import ProductSpec
from app.repositories import spec_repo


class Amounts(NamedTuple):
    subtotal: int
    shipping_fee: int
    cod_fee: int
    total: int


class ItemRequest(NamedTuple):
    spec_id: int
    qty: int


class ItemsResult(NamedTuple):
    items: list[OrderItem]  # 新的完整訂單品項清單(既有的沿用原物件)
    amounts: Amounts

    def apply_to(self, order: Order) -> None:
        """把訂單品項與金額寫回訂單。"""
        order.items = self.items
        order.subtotal = self.amounts.subtotal
        order.shipping_fee = self.amounts.shipping_fee
        order.cod_fee = self.amounts.cod_fee
        order.total = self.amounts.total


def compute_layers(items: list[tuple[int, int, bool]]) -> int:
    # item = (unit_price, qty, is_two_pack);非2粒每箱1層,2粒每2箱1層。
    layers = 0
    for _price, qty, is_two_pack in items:
        layers += qty // 2 if is_two_pack else qty
    return layers


def compute_shipping(subtotal: int, layers: int) -> int:
    if subtotal >= FREE_SHIPPING_THRESHOLD:
        return 0
    if layers <= 0:
        return 0
    return SHIPPING_BY_LAYER[min(layers, 3)]


def compute_amounts(items: list[tuple[int, int, bool]]) -> Amounts:
    # item = (unit_price, qty, is_two_pack)。cod_fee 永遠 0(僅剩轉帳)。
    subtotal = sum(price * qty for price, qty, _ in items)
    layers = compute_layers(items)
    shipping_fee = compute_shipping(subtotal, layers)
    return Amounts(
        subtotal=subtotal,
        shipping_fee=shipping_fee,
        cod_fee=0,
        total=subtotal + shipping_fee,
    )


async def apply_items(
    session: AsyncSession,
    current: Sequence[OrderItem],
    requested: Sequence[ItemRequest],
    *,
    expected_total: int,
) -> ItemsResult:
    """以「期望的完整清單」對照「目前清單」依規格比對差異;不 commit,由呼叫端 commit。"""
    requested_qty: dict[int, int] = {}
    for r in requested:
        if r.spec_id in requested_qty:
            raise DuplicateSpecError(f"規格 {r.spec_id} 重複")
        requested_qty[r.spec_id] = r.qty
    current_by_spec = {i.spec_id: i for i in current if i.spec_id is not None}

    # 1) 只有數量變動(新增、移除、改數量)的規格要鎖定、異動庫存;依 spec_id 排序鎖定避免死結
    changed = sorted(
        spec_id
        for spec_id in requested_qty.keys() | current_by_spec.keys()
        if _current_qty(current_by_spec, spec_id) != requested_qty.get(spec_id, 0)
    )
    locked: dict[int, ProductSpec | None] = {}
    for spec_id in changed:
        locked[spec_id] = await spec_repo.get_for_update(session, spec_id)

    # 2) 新增須存在且上架中;已下架不可改數量(移除則任何規格皆可)
    active: dict[int, ProductSpec] = {}
    for spec_id in changed:
        if spec_id not in requested_qty:
            continue
        spec = locked[spec_id]
        if spec is None or not spec.is_active:
            existing = current_by_spec.get(spec_id)
            if existing is None:
                raise NotFoundError(f"找不到規格 {spec_id}")
            raise ItemQtyLockedError(f"{existing.spec_label} 已下架，數量不可修改")
        active[spec_id] = spec

    # 3) 兩粒裝須以雙數購買
    for spec_id, spec in active.items():
        if spec.is_two_pack and requested_qty[spec_id] % 2 != 0:
            raise EvenQtyRequiredError(f"{spec.label} 為 2 粒裝，請以雙數（2、4、6…）購買")

    # 4) 先補回再扣除,檢查庫存不為負(規格已刪除則略過補回)
    new_stock: list[tuple[ProductSpec, int]] = []
    for spec_id in changed:
        spec = locked[spec_id]
        if spec is None:
            continue
        stock = (
            spec.stock_qty
            + _current_qty(current_by_spec, spec_id)
            - requested_qty.get(spec_id, 0)
        )
        if stock < 0:
            raise InsufficientStockError(f"庫存不足:{spec.label}")
        new_stock.append((spec, stock))

    # 5) 以下單價計算金額(既有沿用原下單價、新增用規格目前價格)並比對 expected_total
    is_two_pack: dict[int, bool] = {}
    for r in requested:
        spec = locked[r.spec_id] if r.spec_id in locked else await spec_repo.get_by_id(
            session, r.spec_id
        )
        is_two_pack[r.spec_id] = spec is not None and spec.is_two_pack
    amounts = compute_amounts(
        [
            (_unit_price(current_by_spec, active, r.spec_id), r.qty, is_two_pack[r.spec_id])
            for r in requested
        ]
    )
    if amounts.total != expected_total:
        raise PriceChangedError(
            "商品價格已更新,請重新確認",
            subtotal=amounts.subtotal,
            shipping_fee=amounts.shipping_fee,
            cod_fee=amounts.cod_fee,
            total=amounts.total,
        )

    # 6) 檢查都通過才寫入
    for spec, stock in new_stock:
        spec.stock_qty = stock
    items: list[OrderItem] = []
    for r in requested:
        existing = current_by_spec.get(r.spec_id)
        if existing is not None:
            existing.qty = r.qty
            existing.line_total = existing.unit_price * r.qty
            items.append(existing)
            continue
        spec = active[r.spec_id]
        items.append(
            OrderItem(
                product_id=spec.product_id,
                spec_id=spec.id,
                product_name=spec.product.name,
                spec_label=spec.label,
                unit_price=spec.price,
                qty=r.qty,
                line_total=spec.price * r.qty,
            )
        )
    return ItemsResult(items=items, amounts=amounts)


async def release_items(session: AsyncSession, items: Sequence[OrderItem]) -> None:
    """鎖定並補回每個訂單品項的庫存(含已下架規格);規格已刪除則略過。不 commit。"""
    # 依 spec_id 排序鎖定,避免死結
    for item in sorted(items, key=lambda i: i.spec_id or 0):
        if item.spec_id is None:
            continue
        spec = await spec_repo.get_for_update(session, item.spec_id)
        if spec is not None:
            spec.stock_qty += item.qty


def _current_qty(current_by_spec: dict[int, OrderItem], spec_id: int) -> int:
    existing = current_by_spec.get(spec_id)
    return existing.qty if existing is not None else 0


def _unit_price(
    current_by_spec: dict[int, OrderItem], active: dict[int, ProductSpec], spec_id: int
) -> int:
    # 既有訂單品項沿用原下單價(R6);新增的以規格目前價格為下單價(R5)
    existing = current_by_spec.get(spec_id)
    return existing.unit_price if existing is not None else active[spec_id].price
