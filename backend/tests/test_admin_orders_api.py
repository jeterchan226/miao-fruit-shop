from datetime import date

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.admin_user import AdminUser
from app.models.order import Order
from app.repositories import admin_repo, order_repo


def _make_order(order_no: str, *, status: str = "pending") -> Order:
    return Order(
        order_no=order_no,
        status=status,
        customer_name="王小明",
        customer_phone="0912345678",
        customer_email=None,
        ship_zipcode="100",
        ship_city="台北市",
        ship_district="中正區",
        ship_street="重慶南路1號",
        preferred_date=date(2026, 10, 1),
        delivery_window="any",
        payment_method="cod",
        note=None,
        subtotal=880,
        shipping_fee=0,
        cod_fee=30,
        total=910,
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
    await order_repo.add(db_session, _make_order("MM-API02", status="pending"))
    await order_repo.add(db_session, _make_order("MM-API03", status="confirmed"))
    await db_session.flush()
    resp = await client.get("/api/admin/orders?status=pending", headers=headers)
    assert resp.status_code == 200
    nos = [item["order_no"] for item in resp.json()["items"]]
    assert "MM-API02" in nos
    assert "MM-API03" not in nos


async def test_get_order_detail(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth_header(db_session)
    await order_repo.add(db_session, _make_order("MM-DT01"))
    await db_session.flush()
    resp = await client.get("/api/admin/orders/MM-DT01", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["order_no"] == "MM-DT01"
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
    await order_repo.add(db_session, _make_order("MM-CH01", status="pending"))
    await db_session.flush()
    resp = await client.patch(
        "/api/admin/orders/MM-CH01/status",
        json={"status": "confirmed"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "confirmed"


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
        json={"status": "confirmed"},
        headers=headers,
    )
    assert resp.status_code == 404
