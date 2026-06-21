from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.product_spec import ProductSpec
from app.repositories import product_repo


async def _seed_spec(db_session, *, price=1880, stock=10):
    product = Product(slug="kanro", name="甘露梨", description="d", image="i", season="s")
    product.specs = [
        ProductSpec(label="5 台斤家庭箱", qty_text="q", price=price,
                    stock_qty=stock, sort_order=1)
    ]
    await product_repo.add(db_session, product)
    await db_session.flush()
    return product.specs[0]


def _body(spec_id, qty, *, payment="transfer", expected_total):
    return {
        "customer": {
            "name": "王小明",
            "phone": "0912345678",
            "email": None,
            "line_user_id": "U123",
            "line_display_name": "小明",
            "line_picture_url": "https://example.com/line.jpg",
            "line_friendship_status": "friend",
            "line_notification_consent": True,
        },
        "shipping": {
            "zipcode": "100", "city": "台北市", "district": "中正區",
            "street": "x", "preferred_date": "2026-10-12", "delivery_window": "any",
        },
        "items": [{"spec_id": spec_id, "qty": qty}],
        "payment_method": payment,
        "note": None,
        "expected_total": expected_total,
    }


async def test_create_order_201(client: AsyncClient, db_session: AsyncSession):
    spec = await _seed_spec(db_session, price=1880, stock=10)
    resp = await client.post("/api/orders", json=_body(spec.id, 1, expected_total=2030))
    assert resp.status_code == 201
    data = resp.json()
    assert data["order_no"].startswith("MM-")
    assert data["status"] == "pending_payment"
    assert data["total"] == 2030
    assert data["items"][0]["unit_price"] == 1880
    assert "stock_qty" not in str(data)


async def test_create_order_price_changed_409(client: AsyncClient, db_session: AsyncSession):
    spec = await _seed_spec(db_session, price=1880, stock=10)
    resp = await client.post("/api/orders", json=_body(spec.id, 1, expected_total=9999))
    assert resp.status_code == 409
    data = resp.json()
    assert data["code"] == "PRICE_CHANGED"
    assert data["total"] == 2030


async def test_create_order_insufficient_stock_409(client: AsyncClient, db_session: AsyncSession):
    spec = await _seed_spec(db_session, price=1880, stock=2)
    resp = await client.post("/api/orders", json=_body(spec.id, 5, expected_total=9400))
    assert resp.status_code == 409
    assert resp.json()["code"] == "INSUFFICIENT_STOCK"


async def test_create_order_unknown_spec_404(client: AsyncClient, db_session: AsyncSession):
    resp = await client.post("/api/orders", json=_body(999999, 1, expected_total=0))
    assert resp.status_code == 404
    assert resp.json()["code"] == "NOT_FOUND"


async def test_create_order_validation_422(client: AsyncClient, db_session: AsyncSession):
    resp = await client.post("/api/orders", json=_body(1, 1, expected_total=0) | {"items": []})
    assert resp.status_code == 422
