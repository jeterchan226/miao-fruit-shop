from httpx import AsyncClient
from pytest import MonkeyPatch
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.admin_user import AdminUser
from app.models.order import Order
from app.models.product import Product
from app.models.product_spec import ProductSpec
from app.repositories import admin_repo, order_repo, product_repo
from app.services import line_service


async def _auth_header(session: AsyncSession) -> dict[str, str]:
    admin = await admin_repo.add(
        session,
        AdminUser(
            username="miaomama", hashed_password=hash_password("pw"), is_active=True
        ),
    )
    return {"Authorization": f"Bearer {create_access_token(subject=admin.id)}"}


async def _seed_specs(db_session: AsyncSession, *specs: ProductSpec) -> list[ProductSpec]:
    product = Product(slug="kanro", name="甘露梨", description="d", image="i", season="s")
    product.specs = list(specs)
    await product_repo.add(db_session, product)
    await db_session.flush()
    return product.specs


def _spec(label: str = "5 台斤家庭箱", *, price: int = 1880, stock: int = 10,
          two_pack: bool = False) -> ProductSpec:
    return ProductSpec(label=label, qty_text="q", price=price, stock_qty=stock,
                       sort_order=1, is_two_pack=two_pack)


def _body(items: list[dict[str, int]], *, expected_total: int) -> dict[str, object]:
    return {
        "customer_name": "王小明",
        "customer_phone": "0912345678",
        "customer_email": None,
        "shipping": {
            "zipcode": "100", "city": "台北市", "district": "中正區",
            "street": "重慶南路1號", "preferred_date": "2026-11-12",
            "delivery_window": "am",
        },
        "items": items,
        "note": "電話訂購",
        "expected_total": expected_total,
    }


async def test_admin_create_order_requires_auth(client: AsyncClient):
    resp = await client.post(
        "/api/admin/orders", json=_body([{"spec_id": 1, "qty": 1}], expected_total=0)
    )
    assert resp.status_code == 401


async def test_admin_create_order_201(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth_header(db_session)
    (spec,) = await _seed_specs(db_session, _spec(price=1880, stock=10))

    resp = await client.post(
        "/api/admin/orders",
        json=_body([{"spec_id": spec.id, "qty": 1}], expected_total=1980),
        headers=headers,
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["order_no"].startswith("MM-")
    assert body["status"] == "pending_payment"
    assert body["payment_method"] == "transfer"
    assert body["source"] == "admin"
    assert body["customer_name"] == "王小明"
    assert body["ship_street"] == "重慶南路1號"
    assert body["delivery_window"] == "am"
    assert body["note"] == "電話訂購"
    assert body["total"] == 1980
    assert body["items"][0]["unit_price"] == 1880
    assert body["line_user_id"] is None
    assert body["line_display_name"] is None
    assert body["line_picture_url"] is None
    assert body["line_friendship_status"] is None
    assert body["line_notification_consent"] is False
    await db_session.refresh(spec)
    assert spec.stock_qty == 9


async def test_admin_create_order_does_not_notify_line(
    client: AsyncClient, db_session: AsyncSession, monkeypatch: MonkeyPatch
):
    calls: list[Order] = []

    async def _record(order: Order) -> bool:
        calls.append(order)
        return True

    monkeypatch.setattr(line_service, "send_order_created", _record)
    headers = await _auth_header(db_session)
    (spec,) = await _seed_specs(db_session, _spec(price=1880, stock=10))

    resp = await client.post(
        "/api/admin/orders",
        json=_body([{"spec_id": spec.id, "qty": 1}], expected_total=1980),
        headers=headers,
    )

    assert resp.status_code == 201
    assert calls == []


async def test_admin_create_order_rejects_line_fields(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    (spec,) = await _seed_specs(db_session, _spec())
    payload = _body([{"spec_id": spec.id, "qty": 1}], expected_total=1980)
    payload["line_user_id"] = "U123"

    resp = await client.post("/api/admin/orders", json=payload, headers=headers)

    assert resp.status_code == 422


async def test_admin_create_order_unknown_spec_404(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    resp = await client.post(
        "/api/admin/orders",
        json=_body([{"spec_id": 999999, "qty": 1}], expected_total=0),
        headers=headers,
    )
    assert resp.status_code == 404
    assert resp.json()["code"] == "NOT_FOUND"


async def test_admin_create_order_duplicate_spec_422(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    (spec,) = await _seed_specs(db_session, _spec())
    resp = await client.post(
        "/api/admin/orders",
        json=_body(
            [{"spec_id": spec.id, "qty": 1}, {"spec_id": spec.id, "qty": 2}],
            expected_total=0,
        ),
        headers=headers,
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == "DUPLICATE_SPEC"


async def test_admin_create_order_two_pack_odd_qty_409(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    (pair,) = await _seed_specs(db_session, _spec("2 粒裝", price=300, two_pack=True))
    resp = await client.post(
        "/api/admin/orders",
        json=_body([{"spec_id": pair.id, "qty": 3}], expected_total=0),
        headers=headers,
    )
    assert resp.status_code == 409
    assert resp.json()["code"] == "EVEN_QTY_REQUIRED"


async def test_admin_create_order_insufficient_stock_409(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    (spec,) = await _seed_specs(db_session, _spec(stock=2))
    resp = await client.post(
        "/api/admin/orders",
        json=_body([{"spec_id": spec.id, "qty": 5}], expected_total=9400),
        headers=headers,
    )
    assert resp.status_code == 409
    assert resp.json()["code"] == "INSUFFICIENT_STOCK"


async def test_admin_create_order_price_changed_409_writes_nothing(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    (spec,) = await _seed_specs(db_session, _spec(price=1880, stock=10))

    resp = await client.post(
        "/api/admin/orders",
        json=_body([{"spec_id": spec.id, "qty": 1}], expected_total=1880),
        headers=headers,
    )

    assert resp.status_code == 409
    body = resp.json()
    assert body["code"] == "PRICE_CHANGED"
    assert body["total"] == 1980
    total, _ = await order_repo.list_filtered(db_session, source="admin")
    assert total == 0
    await db_session.refresh(spec)
    assert spec.stock_qty == 10


async def test_admin_create_order_validation_422(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    resp = await client.post(
        "/api/admin/orders", json=_body([], expected_total=0), headers=headers
    )
    assert resp.status_code == 422


async def test_admin_create_order_inactive_spec_404(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    (spec,) = await _seed_specs(db_session, _spec())
    spec.is_active = False
    await db_session.flush()

    resp = await client.post(
        "/api/admin/orders",
        json=_body([{"spec_id": spec.id, "qty": 1}], expected_total=1980),
        headers=headers,
    )

    assert resp.status_code == 404
    assert resp.json()["code"] == "NOT_FOUND"


async def test_admin_create_order_snapshots_pack_type(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    (pair,) = await _seed_specs(db_session, _spec("2 粒裝", price=300, two_pack=True))

    resp = await client.post(
        "/api/admin/orders",
        json=_body([{"spec_id": pair.id, "qty": 2}], expected_total=700),
        headers=headers,
    )

    assert resp.status_code == 201
    assert resp.json()["items"][0]["is_two_pack"] is True
