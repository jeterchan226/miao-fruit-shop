from datetime import UTC, date, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.admin_user import AdminUser
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.product_spec import ProductSpec
from app.repositories import admin_repo, order_repo


def _make_order(
    order_no: str, *, status: str = "pending_payment", source: str = "storefront"
) -> Order:
    return Order(
        order_no=order_no,
        status=status,
        source=source,
        customer_name="王小明",
        customer_phone="0912345678",
        customer_email=None,
        ship_zipcode="100",
        ship_city="台北市",
        ship_district="中正區",
        ship_street="重慶南路1號",
        preferred_date=date(2026, 10, 1),
        delivery_window="any",
        payment_method="transfer",
        note=None,
        subtotal=880,
        shipping_fee=0,
        cod_fee=0,
        total=880,
    )


async def _auth_header(session: AsyncSession) -> dict[str, str]:
    admin = await admin_repo.add(
        session,
        AdminUser(
            username="miaomama", hashed_password=hash_password("pw"), is_active=True
        ),
    )
    return {"Authorization": f"Bearer {create_access_token(subject=admin.id)}"}


async def test_admin_orders_require_auth(client: AsyncClient):
    assert (await client.get("/api/admin/orders")).status_code == 401


async def test_list_orders_returns_response_structure(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    await order_repo.add(db_session, _make_order("MM-API01"))
    await db_session.flush()
    resp = await client.get("/api/admin/orders", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert {"total", "page", "page_size", "items"} <= set(body)
    assert body["total"] >= 1
    assert body["items"][0]["order_no"] == "MM-API01"


async def test_list_orders_filter_by_status(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    await order_repo.add(db_session, _make_order("MM-API02", status="pending_payment"))
    await order_repo.add(db_session, _make_order("MM-API03", status="shipping"))
    await db_session.flush()
    resp = await client.get("/api/admin/orders?status=pending_payment", headers=headers)
    assert resp.status_code == 200
    nos = [item["order_no"] for item in resp.json()["items"]]
    assert "MM-API02" in nos
    assert "MM-API03" not in nos


async def test_list_orders_items_include_source(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    await order_repo.add(db_session, _make_order("MM-SRC01", source="admin"))
    await db_session.flush()
    resp = await client.get("/api/admin/orders?order_no=MM-SRC01", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["items"][0]["source"] == "admin"


async def test_list_orders_filter_by_source(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    await order_repo.add(db_session, _make_order("MM-SRC02", source="storefront"))
    await order_repo.add(db_session, _make_order("MM-SRC03", source="admin"))
    await db_session.flush()

    resp = await client.get("/api/admin/orders?source=admin", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    nos = [item["order_no"] for item in body["items"]]
    assert "MM-SRC03" in nos
    assert "MM-SRC02" not in nos
    assert body["total"] == len(nos)

    resp = await client.get("/api/admin/orders?source=storefront", headers=headers)
    nos = [item["order_no"] for item in resp.json()["items"]]
    assert "MM-SRC02" in nos
    assert "MM-SRC03" not in nos


async def test_list_orders_invalid_source_422(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    resp = await client.get("/api/admin/orders?source=line", headers=headers)
    assert resp.status_code == 422


async def test_list_orders_filter_by_phone_fragment(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    hit = _make_order("MM-Q01")
    hit.customer_phone = "0987654321"
    await order_repo.add(db_session, hit)
    await order_repo.add(db_session, _make_order("MM-Q02"))
    await db_session.flush()

    resp = await client.get(
        "/api/admin/orders", params={"q": "87654"}, headers=headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert [item["order_no"] for item in body["items"]] == ["MM-Q01"]
    assert body["total"] == 1


async def test_list_orders_multiple_filters_all_apply(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    await order_repo.add(
        db_session, _make_order("MM-AND01", status="shipping", source="admin")
    )
    await order_repo.add(
        db_session, _make_order("MM-AND02", status="shipping", source="storefront")
    )
    await order_repo.add(
        db_session, _make_order("MM-AND03", status="pending_payment", source="admin")
    )
    await db_session.flush()

    resp = await client.get(
        "/api/admin/orders",
        params={"status": "shipping", "source": "admin"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert [item["order_no"] for item in body["items"]] == ["MM-AND01"]
    assert body["total"] == 1


@pytest.mark.parametrize(
    ("params", "expected_total"),
    [
        ({"status": "shipping"}, 2),
        ({"source": "admin"}, 2),
        ({"created_from": "2026-10-29T00:00:00Z"}, 3),
        ({"created_before": "2026-10-30T00:00:00Z"}, 3),
        ({"q": "林美麗"}, 2),
        ({"order_no": "MM-TOT01"}, 1),
    ],
)
async def test_list_orders_total_counts_all_matches_across_pages(
    client: AsyncClient,
    db_session: AsyncSession,
    params: dict[str, str],
    expected_total: int,
):
    headers = await _auth_header(db_session)
    matching = [
        _make_order("MM-TOT01", status="shipping", source="admin"),
        _make_order("MM-TOT02", status="shipping", source="admin"),
    ]
    for order in matching:
        order.customer_name = "林美麗"
        order.created_at = datetime(2026, 10, 29, 12, 0, tzinfo=UTC)
    earlier = _make_order("MM-TOT03")
    earlier.created_at = datetime(2026, 10, 28, 12, 0, tzinfo=UTC)
    later = _make_order("MM-TOT04")
    later.created_at = datetime(2026, 10, 30, 12, 0, tzinfo=UTC)
    for order in (*matching, earlier, later):
        await order_repo.add(db_session, order)
    await db_session.flush()

    resp = await client.get(
        "/api/admin/orders", params={**params, "page_size": 1}, headers=headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == expected_total
    assert len(body["items"]) == 1


# 台北 2026-10-30 = UTC [2026-10-29T16:00Z, 2026-10-30T16:00Z)
TAIPEI_OCT_30 = {
    "created_from": "2026-10-29T16:00:00.000Z",
    "created_before": "2026-10-30T16:00:00.000Z",
}
TAIPEI_OCT_29 = {
    "created_from": "2026-10-28T16:00:00+00:00",
    "created_before": "2026-10-29T16:00:00+00:00",
}


async def test_list_orders_created_range_uses_utc_instants(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    # 台北 10/30 03:00 = UTC 10/29 19:00:UTC 切日會錯分到 10/29
    early = _make_order("MM-TZ01")
    early.created_at = datetime(2026, 10, 29, 19, 0, tzinfo=UTC)
    # 台北 10/30 00:00 整:起點包含
    midnight = _make_order("MM-TZ02")
    midnight.created_at = datetime(2026, 10, 29, 16, 0, tzinfo=UTC)
    # 台北 10/31 00:00 整:終點不包含
    next_day = _make_order("MM-TZ03")
    next_day.created_at = datetime(2026, 10, 30, 16, 0, tzinfo=UTC)
    for order in (early, midnight, next_day):
        await order_repo.add(db_session, order)
    await db_session.flush()

    resp = await client.get("/api/admin/orders", params=TAIPEI_OCT_30, headers=headers)
    assert resp.status_code == 200
    nos = {item["order_no"] for item in resp.json()["items"]}
    assert {"MM-TZ01", "MM-TZ02"} <= nos
    assert "MM-TZ03" not in nos

    resp = await client.get("/api/admin/orders", params=TAIPEI_OCT_29, headers=headers)
    assert resp.status_code == 200
    nos = {item["order_no"] for item in resp.json()["items"]}
    assert not nos & {"MM-TZ01", "MM-TZ02", "MM-TZ03"}


async def test_list_orders_accepts_offset_datetime(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    order = _make_order("MM-TZ04")
    order.created_at = datetime(2026, 10, 29, 19, 0, tzinfo=UTC)
    await order_repo.add(db_session, order)
    await db_session.flush()
    resp = await client.get(
        "/api/admin/orders",
        params={"created_from": "2026-10-30T00:00:00+08:00"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert "MM-TZ04" in {item["order_no"] for item in resp.json()["items"]}


async def test_list_orders_rejects_naive_datetime_422(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    for value in ("2026-10-30T00:00:00", "2026-10-30"):
        resp = await client.get(
            "/api/admin/orders", params={"created_from": value}, headers=headers
        )
        assert resp.status_code == 422, value
        resp = await client.get(
            "/api/admin/orders", params={"created_before": value}, headers=headers
        )
        assert resp.status_code == 422, value


async def test_orders_summary_requires_auth(client: AsyncClient):
    assert (await client.get("/api/admin/orders/summary")).status_code == 401


async def test_orders_summary(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth_header(db_session)
    await order_repo.add(db_session, _make_order("MM-SM01", status="ready"))
    await order_repo.add(db_session, _make_order("MM-SM02", status="shipping"))
    await order_repo.add(db_session, _make_order("MM-SM03", status="cancelled"))
    await db_session.flush()
    resp = await client.get("/api/admin/orders/summary", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_orders"] == 3
    assert body["pending_shipment"] == 1  # 只有 ready 狀態計入待出貨
    assert body["total_revenue"] == 1760  # 880 × 2,已取消不計營收


async def test_get_order_detail(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth_header(db_session)
    await order_repo.add(db_session, _make_order("MM-DT01", source="admin"))
    await db_session.flush()
    resp = await client.get("/api/admin/orders/MM-DT01", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["order_no"] == "MM-DT01"
    assert body["source"] == "admin"
    assert "ship_city" in body
    assert "items" in body


async def test_get_order_detail_not_found(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth_header(db_session)
    resp = await client.get("/api/admin/orders/MM-GHOST", headers=headers)
    assert resp.status_code == 404


async def test_change_status_valid_transition(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    await order_repo.add(db_session, _make_order("MM-CH01", status="pending_payment"))
    await db_session.flush()
    resp = await client.patch(
        "/api/admin/orders/MM-CH01/status",
        json={"status": "ready"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


async def test_change_status_invalid_transition(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    await order_repo.add(db_session, _make_order("MM-CH02", status="shipping"))
    await db_session.flush()
    resp = await client.patch(
        "/api/admin/orders/MM-CH02/status",
        json={"status": "cancelled"},
        headers=headers,
    )
    assert resp.status_code == 409
    assert resp.json()["code"] == "INVALID_STATUS_TRANSITION"


async def test_change_status_order_not_found(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    resp = await client.patch(
        "/api/admin/orders/MM-GHOST/status",
        json={"status": "shipping"},
        headers=headers,
    )
    assert resp.status_code == 404


async def test_update_order_requires_auth(client: AsyncClient):
    resp = await client.patch(
        "/api/admin/orders/MM-XX01", json={"note": "改備註"}
    )
    assert resp.status_code == 401


async def test_update_order_simple_fields(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    await order_repo.add(db_session, _make_order("MM-UP01"))
    await db_session.flush()
    resp = await client.patch(
        "/api/admin/orders/MM-UP01",
        json={"customer_name": "陳大文", "note": "客戶臨時改地址"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["customer_name"] == "陳大文"
    assert body["note"] == "客戶臨時改地址"
    assert body["ship_city"] == "台北市"  # 未送的欄位不變


async def test_update_order_explicit_null_clears_optional_fields(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    order = _make_order("MM-UP02")
    order.customer_email = "a@example.com"
    order.note = "舊備註"
    await order_repo.add(db_session, order)
    await db_session.flush()
    resp = await client.patch(
        "/api/admin/orders/MM-UP02",
        json={"customer_email": None, "note": None},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["customer_email"] is None
    assert body["note"] is None


async def test_update_order_omitted_optional_fields_unchanged(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    order = _make_order("MM-UP03")
    order.customer_email = "a@example.com"
    order.note = "舊備註"
    await order_repo.add(db_session, order)
    await db_session.flush()
    resp = await client.patch(
        "/api/admin/orders/MM-UP03",
        json={"ship_city": "新北市"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ship_city"] == "新北市"
    assert body["customer_email"] == "a@example.com"
    assert body["note"] == "舊備註"
    assert body["customer_name"] == "王小明"


@pytest.mark.parametrize(
    "field",
    [
        "customer_name",
        "customer_phone",
        "ship_zipcode",
        "ship_city",
        "ship_district",
        "ship_street",
        "preferred_date",
        "delivery_window",
    ],
)
async def test_update_order_required_field_null_is_422(
    client: AsyncClient, db_session: AsyncSession, field: str
):
    headers = await _auth_header(db_session)
    await order_repo.add(db_session, _make_order("MM-UP04"))
    await db_session.flush()
    # 同一請求帶合法欄位,整筆 PATCH 仍應被拒、不部分寫入
    resp = await client.patch(
        "/api/admin/orders/MM-UP04",
        json={"note": "不該寫入", field: None},
        headers=headers,
    )
    assert resp.status_code == 422
    detail = (await client.get("/api/admin/orders/MM-UP04", headers=headers)).json()
    assert detail["customer_name"] == "王小明"
    assert detail["note"] is None


async def test_update_order_not_editable_when_shipping(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    await order_repo.add(db_session, _make_order("MM-UP02", status="shipping"))
    await db_session.flush()
    resp = await client.patch(
        "/api/admin/orders/MM-UP02",
        json={"note": "不該成功"},
        headers=headers,
    )
    assert resp.status_code == 409
    assert resp.json()["code"] == "ORDER_NOT_EDITABLE"


async def test_update_order_not_found(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth_header(db_session)
    resp = await client.patch(
        "/api/admin/orders/MM-GHOST",
        json={"note": "x"},
        headers=headers,
    )
    assert resp.status_code == 404


async def test_update_order_rejects_unknown_field(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    await order_repo.add(db_session, _make_order("MM-UP03"))
    await db_session.flush()
    resp = await client.patch(
        "/api/admin/orders/MM-UP03",
        json={"status": "ready"},
        headers=headers,
    )
    assert resp.status_code == 422


async def test_update_order_items_without_expected_total_is_422(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    await order_repo.add(db_session, _make_order("MM-UP04"))
    await db_session.flush()
    resp = await client.patch(
        "/api/admin/orders/MM-UP04",
        json={"items": [{"spec_id": 1, "qty": 1}]},
        headers=headers,
    )
    assert resp.status_code == 422


async def _make_order_with_spec(
    session: AsyncSession, order_no: str, *, slug: str
) -> ProductSpec:
    product = Product(slug=slug, name="甘露梨", description="d", image="i", season="s")
    session.add(product)
    await session.flush()
    spec = ProductSpec(product_id=product.id, label="A", qty_text="q", price=880,
                       stock_qty=5, sort_order=1)
    session.add(spec)
    await session.flush()
    order = _make_order(order_no)
    order.subtotal, order.shipping_fee, order.total = 1760, 0, 1760
    session.add(order)
    await session.flush()
    session.add(OrderItem(order_id=order.id, product_id=product.id, spec_id=spec.id,
                          product_name="甘露梨", spec_label="A", unit_price=880,
                          qty=2, line_total=1760))
    await session.flush()
    return spec


async def test_update_order_address_only_after_price_change_keeps_order_price(
    client: AsyncClient, db_session: AsyncSession
):
    # 回歸:規格調價後只改地址,下單價、金額、庫存不變(ADR 0004)
    headers = await _auth_header(db_session)
    spec = await _make_order_with_spec(db_session, "MM-UP05", slug="api-reprice")
    spec.price = 1000
    await db_session.flush()

    resp = await client.patch(
        "/api/admin/orders/MM-UP05", json={"ship_street": "中山北路2號"}, headers=headers
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["ship_street"] == "中山北路2號"
    assert body["items"][0]["unit_price"] == 880
    assert (body["subtotal"], body["shipping_fee"], body["total"]) == (1760, 0, 1760)
    await db_session.refresh(spec)
    assert spec.stock_qty == 5


async def test_update_order_address_only_with_inactive_spec(
    client: AsyncClient, db_session: AsyncSession
):
    # 回歸:訂單含已下架規格時仍可只改地址
    headers = await _auth_header(db_session)
    spec = await _make_order_with_spec(db_session, "MM-UP06", slug="api-retired")
    spec.is_active = False
    await db_session.flush()

    resp = await client.patch(
        "/api/admin/orders/MM-UP06", json={"ship_street": "中山北路2號"}, headers=headers
    )

    assert resp.status_code == 200
    assert resp.json()["ship_street"] == "中山北路2號"
    await db_session.refresh(spec)
    assert spec.stock_qty == 5


async def test_update_transfer_info_requires_auth(client: AsyncClient):
    resp = await client.patch(
        "/api/admin/orders/MM-TX01/transfer", json={"transfer_last5": "12345"}
    )
    assert resp.status_code == 401


async def test_update_transfer_info(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth_header(db_session)
    await order_repo.add(db_session, _make_order("MM-TX02"))
    await db_session.flush()
    resp = await client.patch(
        "/api/admin/orders/MM-TX02/transfer",
        json={
            "transfer_last5": "88888",
            "transfer_payer_name": "王小明",
            "transfer_note": "已核對",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["transfer_last5"] == "88888"
    assert body["transfer_payer_name"] == "王小明"
    assert body["transfer_note"] == "已核對"
    assert body["status"] == "pending_payment"  # 不影響狀態


async def test_update_transfer_info_explicit_null_clears_fields(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    order = _make_order("MM-TX04")
    order.transfer_last5 = "12345"
    order.transfer_payer_name = "填錯的人"
    order.transfer_note = "填錯"
    await order_repo.add(db_session, order)
    await db_session.flush()
    resp = await client.patch(
        "/api/admin/orders/MM-TX04/transfer",
        json={
            "transfer_last5": None,
            "transfer_payer_name": None,
            "transfer_note": None,
        },
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["transfer_last5"] is None
    assert body["transfer_payer_name"] is None
    assert body["transfer_note"] is None


async def test_update_transfer_info_omitted_fields_unchanged(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    order = _make_order("MM-TX05")
    order.transfer_payer_name = "王小明"
    order.transfer_note = "已核對"
    await order_repo.add(db_session, order)
    await db_session.flush()
    resp = await client.patch(
        "/api/admin/orders/MM-TX05/transfer",
        json={"transfer_last5": "54321"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["transfer_last5"] == "54321"
    assert body["transfer_payer_name"] == "王小明"
    assert body["transfer_note"] == "已核對"


async def test_update_transfer_info_allowed_even_when_shipping(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    await order_repo.add(db_session, _make_order("MM-TX03", status="shipping"))
    await db_session.flush()
    resp = await client.patch(
        "/api/admin/orders/MM-TX03/transfer",
        json={"transfer_last5": "00000"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["transfer_last5"] == "00000"


async def test_update_transfer_info_not_found(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    resp = await client.patch(
        "/api/admin/orders/MM-GHOST/transfer",
        json={"transfer_last5": "00000"},
        headers=headers,
    )
    assert resp.status_code == 404


async def _make_pack_order(
    session: AsyncSession, order_no: str, *, slug: str
) -> tuple[ProductSpec, ProductSpec]:
    """訂單含兩粒裝 ×4(300)與箱裝 ×1(500),回傳 (兩粒裝規格, 箱裝規格)。"""
    product = Product(slug=slug, name="甘露梨", description="d", image="i", season="s")
    session.add(product)
    await session.flush()
    pair = ProductSpec(product_id=product.id, label="2 粒裝", qty_text="q", price=300,
                       stock_qty=10, sort_order=1, is_two_pack=True)
    box = ProductSpec(product_id=product.id, label="箱裝", qty_text="q", price=500,
                      stock_qty=10, sort_order=2)
    session.add_all([pair, box])
    await session.flush()
    order = _make_order(order_no)
    # 2 + 1 = 3 層 → 運費 180
    order.subtotal, order.shipping_fee, order.total = 1700, 180, 1880
    session.add(order)
    await session.flush()
    session.add_all([
        OrderItem(order_id=order.id, product_id=product.id, spec_id=pair.id,
                  product_name="甘露梨", spec_label="2 粒裝", is_two_pack=True,
                  unit_price=300, qty=4, line_total=1200),
        OrderItem(order_id=order.id, product_id=product.id, spec_id=box.id,
                  product_name="甘露梨", spec_label="箱裝", is_two_pack=False,
                  unit_price=500, qty=1, line_total=500),
    ])
    await session.flush()
    return pair, box


async def test_order_detail_includes_pack_type(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    await _make_pack_order(db_session, "MM-PACK01", slug="pack01")

    resp = await client.get("/api/admin/orders/MM-PACK01", headers=headers)

    assert resp.status_code == 200
    assert [i["is_two_pack"] for i in resp.json()["items"]] == [True, False]


async def test_order_detail_keeps_pack_type_after_spec_deleted(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    pair, _ = await _make_pack_order(db_session, "MM-PACK02", slug="pack02")

    deleted = await client.delete(f"/api/admin/specs/{pair.id}", headers=headers)
    assert deleted.status_code == 204

    resp = await client.get("/api/admin/orders/MM-PACK02", headers=headers)
    assert resp.json()["items"][0]["is_two_pack"] is True


async def test_update_items_after_two_pack_spec_deleted_keeps_layers(
    client: AsyncClient, db_session: AsyncSession
):
    """規格硬刪除後改同訂單其他訂單品項:兩粒裝 ×4 仍為 2 層(運費 150),不是 4 層(180)。"""
    headers = await _auth_header(db_session)
    pair, _ = await _make_pack_order(db_session, "MM-PACK03", slug="pack03")
    pair_id = pair.id
    await client.delete(f"/api/admin/specs/{pair_id}", headers=headers)

    resp = await client.patch(
        "/api/admin/orders/MM-PACK03",
        json={"items": [{"spec_id": pair_id, "qty": 4}], "expected_total": 1350},
        headers=headers,
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["shipping_fee"] == 150
    assert [i["is_two_pack"] for i in body["items"]] == [True]


async def test_spec_pack_change_keeps_item_snapshot_and_layers(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    pair, box = await _make_pack_order(db_session, "MM-PACK04", slug="pack04")
    pair_id, box_id = pair.id, box.id

    changed = await client.patch(
        f"/api/admin/specs/{pair_id}", json={"is_two_pack": False}, headers=headers
    )
    assert changed.status_code == 200
    detail = await client.get("/api/admin/orders/MM-PACK04", headers=headers)
    assert [i["is_two_pack"] for i in detail.json()["items"]] == [True, False]

    resp = await client.patch(
        "/api/admin/orders/MM-PACK04",
        json={"items": [{"spec_id": pair_id, "qty": 4}], "expected_total": 1350},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["shipping_fee"] == 150
    assert box_id not in [i["spec_id"] for i in resp.json()["items"]]


async def test_box_snapshot_allows_odd_qty_after_spec_became_two_pack(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    pair, box = await _make_pack_order(db_session, "MM-PACK05", slug="pack05")
    pair_id, box_id = pair.id, box.id
    await client.patch(
        f"/api/admin/specs/{box_id}", json={"is_two_pack": True}, headers=headers
    )

    # 1200 + 500×3 = 2700;2 + 3 = 5 層 → 運費 180
    resp = await client.patch(
        "/api/admin/orders/MM-PACK05",
        json={
            "items": [{"spec_id": pair_id, "qty": 4}, {"spec_id": box_id, "qty": 3}],
            "expected_total": 2880,
        },
        headers=headers,
    )

    assert resp.status_code == 200
    assert [i["is_two_pack"] for i in resp.json()["items"]] == [True, False]


async def test_added_item_snapshots_current_pack_type(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    _, box = await _make_pack_order(db_session, "MM-PACK06", slug="pack06")
    box_id = box.id
    addable = ProductSpec(product_id=box.product_id, label="加訂兩粒裝", qty_text="q",
                          price=300, stock_qty=10, sort_order=3, is_two_pack=True)
    db_session.add(addable)
    await db_session.flush()
    addable_id = addable.id

    # 500 + 600 = 1100;1 + 1 = 2 層 → 運費 150
    resp = await client.patch(
        "/api/admin/orders/MM-PACK06",
        json={
            "items": [{"spec_id": box_id, "qty": 1}, {"spec_id": addable_id, "qty": 2}],
            "expected_total": 1250,
        },
        headers=headers,
    )

    assert resp.status_code == 200
    assert resp.json()["shipping_fee"] == 150
    assert [i["is_two_pack"] for i in resp.json()["items"]] == [False, True]
