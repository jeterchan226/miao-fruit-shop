# 規格照片改「包裝群組」共用 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 讓 `ProductImage` 依 `is_two_pack`（兩粒裝／一層裝）分組，而不是綁定單一 `spec_id`，使同群組底下的所有規格共用同一組照片，後台只需維護兩組相簿。

**Architecture:** `ProductImage` 拿掉 `spec_id` FK，改成 `is_two_pack: bool | None` 欄位（`True`=兩粒裝、`False`=一層裝、`None`=商品層級 fallback，現況不用）。後端 repository/service/routes 從「依 spec_id 查詢」改成「依 (product_id, is_two_pack) 查詢」。`product_service` 組裝規格回應時，改成把整個商品的圖片依 `spec.is_two_pack` 過濾出對應群組。前端後台新增「商品照片管理」區塊管理兩組相簿，規格編輯 Modal 內只留唯讀預覽。

**Tech Stack:** Python 3.13 + FastAPI + SQLAlchemy 2.0 async（backend），React 18 + Vite（frontend），pytest（backend tests），alembic（migration）。

## Global Constraints

- 後端嚴格分層：`api/routes` → `services` → `repositories` → `models`，routes 不可直接碰 repository。
- 所有新 pytest 測試需能在既有 `tests/conftest.py`（`Base.metadata.create_all` 建表，非跑 alembic）下通過。
- 正式部署只能從 `master` 分支（本次先在 feature 分支開發）。
- 不新增 `is_two_pack` 以外的分組值；只有兩種群組（`two_pack` / `single`）。
- 前端沒有元件層級單元測試慣例（僅 `pricing.js`/`notifications.js` 這類純函式有 `*.test.js`），UI 互動一律用瀏覽器手動驗證，不用為 UI 元件硬湊假測試。

---

## Task 1: `ProductImage`/`ProductSpec` model 改為 `is_two_pack` 分組 + repository

**Files:**
- Modify: `backend/app/models/product_image.py`
- Modify: `backend/app/models/product_spec.py`
- Modify: `backend/app/repositories/image_repo.py`
- Test: `backend/tests/test_image_repo.py`

**Interfaces:**
- Consumes: 無（最底層）。
- Produces:
  - `ProductImage.is_two_pack: bool | None`（取代 `spec_id`）
  - `image_repo.list_by_group(session: AsyncSession, product_id: int, is_two_pack: bool) -> list[ProductImage]`
  - `image_repo.list_by_product(session: AsyncSession, product_id: int) -> list[ProductImage]`（語意不變：只回傳 `is_two_pack IS NULL` 的商品層級 fallback 圖片）

- [ ] **Step 1: 寫失敗測試 — `list_by_group` 依旗標過濾**

在 `backend/tests/test_image_repo.py` 尾端新增：

```python
async def test_list_by_group_filters_by_is_two_pack(db_session: AsyncSession):
    p = await _seed_product(db_session)
    await image_repo.add(
        db_session, ProductImage(product_id=p.id, url="two.jpg", is_two_pack=True)
    )
    await image_repo.add(
        db_session, ProductImage(product_id=p.id, url="single.jpg", is_two_pack=False)
    )
    two_pack_imgs = await image_repo.list_by_group(db_session, p.id, True)
    single_imgs = await image_repo.list_by_group(db_session, p.id, False)
    assert [i.url for i in two_pack_imgs] == ["two.jpg"]
    assert [i.url for i in single_imgs] == ["single.jpg"]


async def test_list_by_product_excludes_group_images(db_session: AsyncSession):
    p = await _seed_product(db_session)
    await image_repo.add(db_session, ProductImage(product_id=p.id, url="fallback.jpg"))
    await image_repo.add(
        db_session, ProductImage(product_id=p.id, url="two.jpg", is_two_pack=True)
    )
    imgs = await image_repo.list_by_product(db_session, p.id)
    assert [i.url for i in imgs] == ["fallback.jpg"]
```

- [ ] **Step 2: 執行測試，確認因缺少欄位/函式而失敗**

Run: `cd backend && uv run pytest tests/test_image_repo.py -v`
Expected: FAIL（`TypeError: 'is_two_pack' is an invalid keyword argument` 或 `AttributeError: module 'image_repo' has no attribute 'list_by_group'`）

- [ ] **Step 3: 修改 `ProductImage` model**

把 `backend/app/models/product_image.py` 整份改成：

```python
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.product import Product


class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    is_two_pack: Mapped[bool | None] = mapped_column(default=None)
    url: Mapped[str] = mapped_column()
    sort_order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    product: Mapped["Product"] = relationship(back_populates="images")
```

（拿掉 `spec_id` 欄位與 `spec` relationship；`is_two_pack`：`True`=兩粒裝、`False`=一層裝、`None`=商品層級 fallback。）

- [ ] **Step 4: 修改 `ProductSpec` model，移除 `images` relationship**

把 `backend/app/models/product_spec.py` 整份改成：

```python
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.product import Product


class ProductSpec(Base):
    __tablename__ = "product_specs"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), index=True
    )
    label: Mapped[str] = mapped_column()
    qty_text: Mapped[str] = mapped_column()
    price: Mapped[int] = mapped_column()
    stock_qty: Mapped[int] = mapped_column()
    low_stock_threshold: Mapped[int] = mapped_column(default=3)
    note: Mapped[str | None] = mapped_column(default=None)
    sort_order: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_two_pack: Mapped[bool] = mapped_column(default=False)

    product: Mapped["Product"] = relationship(back_populates="specs")
```

（規格不再直接持有圖片，圖片群組比對改在 service 層做。）

- [ ] **Step 5: 修改 `image_repo.py`**

把 `backend/app/repositories/image_repo.py` 整份改成：

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_image import ProductImage


async def list_by_product(session: AsyncSession, product_id: int) -> list[ProductImage]:
    result = await session.execute(
        select(ProductImage)
        .where(ProductImage.product_id == product_id, ProductImage.is_two_pack.is_(None))
        .order_by(ProductImage.sort_order, ProductImage.id)
    )
    return list(result.scalars().all())


async def list_by_group(
    session: AsyncSession, product_id: int, is_two_pack: bool
) -> list[ProductImage]:
    result = await session.execute(
        select(ProductImage)
        .where(
            ProductImage.product_id == product_id,
            ProductImage.is_two_pack == is_two_pack,
        )
        .order_by(ProductImage.sort_order, ProductImage.id)
    )
    return list(result.scalars().all())


async def get_by_id(session: AsyncSession, image_id: int) -> ProductImage | None:
    return await session.get(ProductImage, image_id)


async def add(session: AsyncSession, image: ProductImage) -> ProductImage:
    session.add(image)
    await session.flush()
    return image


async def delete(session: AsyncSession, image: ProductImage) -> None:
    await session.delete(image)
    await session.flush()
```

- [ ] **Step 6: 執行測試，確認全部通過**

Run: `cd backend && uv run pytest tests/test_image_repo.py -v`
Expected: PASS（全部，含既有的 4 個舊測試）

- [ ] **Step 7: 型別檢查**

Run: `cd backend && uv run mypy app`
Expected: 無新增錯誤

- [ ] **Step 8: Commit**

```bash
git add backend/app/models/product_image.py backend/app/models/product_spec.py \
  backend/app/repositories/image_repo.py backend/tests/test_image_repo.py
git commit -m "feat(images): group ProductImage by is_two_pack instead of spec_id"
```

---

## Task 2: `image_service.py` — 群組圖片 service 函式

**Files:**
- Modify: `backend/app/services/image_service.py`
- Test: `backend/tests/test_image_service.py`

**Interfaces:**
- Consumes: `image_repo.list_by_group`（Task 1）；`app.models.product_image.ProductImage`（`is_two_pack` 欄位，Task 1）
- Produces:
  - `image_service.list_group_images(session, product_id: int, is_two_pack: bool) -> list[AdminImageRead]`
  - `image_service.register_group_image(session, product_id: int, is_two_pack: bool, data: ImageRegister) -> AdminImageRead`
  - `image_service.reorder_group_images(session, product_id: int, is_two_pack: bool, req: ImageReorderRequest) -> list[AdminImageRead]`

- [ ] **Step 1: 寫失敗測試**

在 `backend/tests/test_image_service.py` 尾端新增：

```python
async def test_register_group_image_saves_with_flag(db_session: AsyncSession):
    p = await _seed(db_session)
    img = await image_service.register_group_image(
        db_session, p.id, True, ImageRegister(url="https://gcs/two.jpg", sort_order=0)
    )
    assert img.url == "https://gcs/two.jpg"


async def test_register_group_image_missing_product_raises(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await image_service.register_group_image(
            db_session, 999999, True, ImageRegister(url="https://gcs/x.jpg")
        )


async def test_list_group_images_filters_by_flag(db_session: AsyncSession):
    p = await _seed(db_session)
    await image_service.register_group_image(
        db_session, p.id, True, ImageRegister(url="two.jpg")
    )
    await image_service.register_group_image(
        db_session, p.id, False, ImageRegister(url="single.jpg")
    )
    two_pack = await image_service.list_group_images(db_session, p.id, True)
    assert [i.url for i in two_pack] == ["two.jpg"]


async def test_reorder_group_images_updates_sort_order(db_session: AsyncSession):
    p = await _seed(db_session)
    img_a = await image_service.register_group_image(
        db_session, p.id, True, ImageRegister(url="a.jpg", sort_order=0)
    )
    img_b = await image_service.register_group_image(
        db_session, p.id, True, ImageRegister(url="b.jpg", sort_order=1)
    )
    req = ImageReorderRequest(items=[
        ImageReorderItem(id=img_a.id, sort_order=1),
        ImageReorderItem(id=img_b.id, sort_order=0),
    ])
    result = await image_service.reorder_group_images(db_session, p.id, True, req)
    assert [r.url for r in result] == ["b.jpg", "a.jpg"]
```

（`ImageRegister`／`ImageReorderItem`／`ImageReorderRequest`／`NotFoundError` 這些既有測試已 import 過，不用再加。）

- [ ] **Step 2: 執行測試，確認失敗**

Run: `cd backend && uv run pytest tests/test_image_service.py -v`
Expected: FAIL（`AttributeError: module 'image_service' has no attribute 'register_group_image'`）

- [ ] **Step 3: 實作 service 函式**

移除 `list_spec_images`、`register_spec_image`、`reorder_spec_images` 三個函式，替換成：

```python
async def list_group_images(
    session: AsyncSession, product_id: int, is_two_pack: bool
) -> list[AdminImageRead]:
    imgs = await image_repo.list_by_group(session, product_id, is_two_pack)
    return [AdminImageRead.model_validate(i) for i in imgs]


async def register_group_image(
    session: AsyncSession, product_id: int, is_two_pack: bool, data: ImageRegister
) -> AdminImageRead:
    product = await product_repo.get_by_id(session, product_id)
    if product is None:
        raise NotFoundError("找不到商品")
    img = ProductImage(
        product_id=product_id,
        is_two_pack=is_two_pack,
        url=data.url,
        sort_order=data.sort_order,
    )
    await image_repo.add(session, img)
    await session.commit()
    await session.refresh(img)
    return AdminImageRead.model_validate(img)
```

`reorder_images`（商品層級）維持不動；`reorder_group_images` 放在它後面：

```python
async def reorder_group_images(
    session: AsyncSession, product_id: int, is_two_pack: bool, req: ImageReorderRequest
) -> list[AdminImageRead]:
    for item in req.items:
        img = await image_repo.get_by_id(session, item.id)
        if (
            img is not None
            and img.product_id == product_id
            and img.is_two_pack == is_two_pack
        ):
            img.sort_order = item.sort_order
    await session.commit()
    return await list_group_images(session, product_id, is_two_pack)
```

移除檔案內不再需要的 `spec_repo` import（原本只有 `register_spec_image`/`reorder_spec_images`/`list_spec_images` 用到）。

- [ ] **Step 4: 執行測試，確認通過**

Run: `cd backend && uv run pytest tests/test_image_service.py -v`
Expected: PASS

- [ ] **Step 5: Lint + 型別檢查**

Run: `cd backend && uv run ruff check . && uv run mypy app`
Expected: 無錯誤（尤其確認沒有未使用的 import）

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/image_service.py backend/tests/test_image_service.py
git commit -m "feat(images): replace spec-scoped image service fns with group-scoped ones"
```

---

## Task 3: `admin_images.py` — 群組圖片 API routes

**Files:**
- Modify: `backend/app/api/routes/admin_images.py`
- Test: `backend/tests/test_admin_images_api.py`

**Interfaces:**
- Consumes: `image_service.list_group_images` / `register_group_image` / `reorder_group_images`（Task 2）
- Produces（新 HTTP 端點，`group` 路徑參數字面值 `"two_pack"` / `"single"`）:
  - `GET /api/admin/products/{product_id}/images/group/{group}`
  - `POST /api/admin/products/{product_id}/images/group/{group}`
  - `PATCH /api/admin/products/{product_id}/images/group/{group}/reorder`

- [ ] **Step 1: 寫失敗測試**

在 `backend/tests/test_admin_images_api.py` 尾端新增：

```python
async def test_register_group_image_201(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth(db_session)
    p = await _seed_product(db_session)
    resp = await client.post(
        f"/api/admin/products/{p.id}/images/group/two_pack",
        json={"url": "https://gcs/two.jpg", "sort_order": 0},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["url"] == "https://gcs/two.jpg"


async def test_list_group_images_filters_by_group(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth(db_session)
    p = await _seed_product(db_session)
    await client.post(
        f"/api/admin/products/{p.id}/images/group/two_pack",
        json={"url": "two.jpg", "sort_order": 0}, headers=headers,
    )
    await client.post(
        f"/api/admin/products/{p.id}/images/group/single",
        json={"url": "single.jpg", "sort_order": 0}, headers=headers,
    )
    resp = await client.get(f"/api/admin/products/{p.id}/images/group/two_pack", headers=headers)
    assert resp.status_code == 200
    assert [i["url"] for i in resp.json()] == ["two.jpg"]


async def test_reorder_group_images(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth(db_session)
    p = await _seed_product(db_session)
    r1 = await client.post(
        f"/api/admin/products/{p.id}/images/group/single",
        json={"url": "a.jpg", "sort_order": 0}, headers=headers,
    )
    r2 = await client.post(
        f"/api/admin/products/{p.id}/images/group/single",
        json={"url": "b.jpg", "sort_order": 1}, headers=headers,
    )
    id_a, id_b = r1.json()["id"], r2.json()["id"]
    resp = await client.patch(
        f"/api/admin/products/{p.id}/images/group/single/reorder",
        json={"items": [{"id": id_a, "sort_order": 1}, {"id": id_b, "sort_order": 0}]},
        headers=headers,
    )
    assert resp.status_code == 200
    assert [i["url"] for i in resp.json()] == ["b.jpg", "a.jpg"]


async def test_group_path_rejects_invalid_group_value(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth(db_session)
    p = await _seed_product(db_session)
    resp = await client.get(f"/api/admin/products/{p.id}/images/group/bogus", headers=headers)
    assert resp.status_code == 422
```

- [ ] **Step 2: 執行測試，確認失敗（404，因路由不存在）**

Run: `cd backend && uv run pytest tests/test_admin_images_api.py -v`
Expected: FAIL（新增的 4 個測試回傳 404 而非預期狀態碼）

- [ ] **Step 3: 修改 routes**

把 `backend/app/api/routes/admin_images.py` 的 `/specs/{spec_id}/images...` 三支端點（檔案最後 18 行）整段刪除，改成：

```python
from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.database import get_session
from app.schemas.image import (
    AdminImageRead,
    ImageRegister,
    ImageReorderRequest,
    SignedUrlRequest,
    SignedUrlResponse,
)
from app.services import image_service

router = APIRouter(
    prefix="/api/admin",
    tags=["admin-images"],
    dependencies=[Depends(get_current_admin)],
)

SessionDep = Annotated[AsyncSession, Depends(get_session)]
ImageGroup = Literal["two_pack", "single"]


def _is_two_pack(group: ImageGroup) -> bool:
    return group == "two_pack"


@router.post("/uploads/sign", response_model=SignedUrlResponse)
async def sign_upload(req: SignedUrlRequest, session: SessionDep) -> SignedUrlResponse:
    return image_service.request_sign(product_id=0, req=req)


@router.get("/products/{product_id}/images", response_model=list[AdminImageRead])
async def list_images(product_id: int, session: SessionDep) -> list[AdminImageRead]:
    return await image_service.list_images(session, product_id)


@router.post(
    "/products/{product_id}/images", response_model=AdminImageRead, status_code=201
)
async def register_image(
    product_id: int, data: ImageRegister, session: SessionDep
) -> AdminImageRead:
    return await image_service.register_image(session, product_id, data)


@router.delete("/images/{image_id}", status_code=204)
async def delete_image(image_id: int, session: SessionDep) -> None:
    await image_service.delete_image(session, image_id)


@router.patch("/products/{product_id}/images/reorder", response_model=list[AdminImageRead])
async def reorder_images(
    product_id: int, req: ImageReorderRequest, session: SessionDep
) -> list[AdminImageRead]:
    return await image_service.reorder_images(session, product_id, req)


@router.get(
    "/products/{product_id}/images/group/{group}", response_model=list[AdminImageRead]
)
async def list_group_images(
    product_id: int, group: ImageGroup, session: SessionDep
) -> list[AdminImageRead]:
    return await image_service.list_group_images(session, product_id, _is_two_pack(group))


@router.post(
    "/products/{product_id}/images/group/{group}",
    response_model=AdminImageRead,
    status_code=201,
)
async def register_group_image(
    product_id: int, group: ImageGroup, data: ImageRegister, session: SessionDep
) -> AdminImageRead:
    return await image_service.register_group_image(
        session, product_id, _is_two_pack(group), data
    )


@router.patch(
    "/products/{product_id}/images/group/{group}/reorder",
    response_model=list[AdminImageRead],
)
async def reorder_group_images(
    product_id: int, group: ImageGroup, req: ImageReorderRequest, session: SessionDep
) -> list[AdminImageRead]:
    return await image_service.reorder_group_images(
        session, product_id, _is_two_pack(group), req
    )
```

- [ ] **Step 4: 執行測試，確認通過**

Run: `cd backend && uv run pytest tests/test_admin_images_api.py -v`
Expected: PASS（全部，含既有測試）

- [ ] **Step 5: 全套後端測試 + lint + 型別檢查**

Run: `cd backend && uv run pytest -q && uv run ruff check . && uv run mypy app`
Expected: 全綠

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/routes/admin_images.py backend/tests/test_admin_images_api.py
git commit -m "feat(images): expose group-scoped image endpoints, drop spec-scoped ones"
```

---

## Task 4: `product_service.py` — 規格依群組取圖片

**Files:**
- Modify: `backend/app/services/product_service.py`
- Test: `backend/tests/test_product_service.py`

**Interfaces:**
- Consumes: `ProductImage.is_two_pack`（Task 1）；`product_repo.get_by_id`（既有）
- Produces: `_group_images(images: list[ProductImage], is_two_pack: bool) -> list[str]`（供本檔內部使用，不對外匯出）；`PublicSpecRead.images` / `AdminSpecRead.images` 現在反映「同群組共用」的結果。

- [ ] **Step 1: 寫失敗測試 — 同群組規格共用圖片**

在 `backend/tests/test_product_service.py` 的 import 區塊加入：

```python
from app.models.product_image import ProductImage
```

尾端新增：

```python
async def test_specs_sharing_is_two_pack_share_images(db_session: AsyncSession):
    product = Product(
        slug="kanro", name="甘露梨", description="d", image="i", season="s",
    )
    product.specs = [
        ProductSpec(label="2 粒禮盒", qty_text="q", price=880, stock_qty=20, is_two_pack=True),
        ProductSpec(label="5 台斤", qty_text="q", price=1880, stock_qty=10, is_two_pack=False),
        ProductSpec(label="10 台斤", qty_text="q", price=3580, stock_qty=10, is_two_pack=False),
    ]
    product.images = [
        ProductImage(url="two.jpg", is_two_pack=True, sort_order=0),
        ProductImage(url="single-a.jpg", is_two_pack=False, sort_order=0),
        ProductImage(url="single-b.jpg", is_two_pack=False, sort_order=1),
    ]
    await product_repo.add(db_session, product)

    products = await product_service.list_public_products(db_session)
    specs = {s.label: s for s in products[0].specs}
    assert specs["2 粒禮盒"].images == ["two.jpg"]
    assert specs["5 台斤"].images == ["single-a.jpg", "single-b.jpg"]
    assert specs["10 台斤"].images == specs["5 台斤"].images


async def test_create_spec_returns_matching_group_images(db_session: AsyncSession):
    product = Product(slug="kanro", name="甘露梨", description="d", image="i", season="s")
    product.images = [ProductImage(url="two.jpg", is_two_pack=True, sort_order=0)]
    await product_repo.add(db_session, product)

    created = await product_service.create_spec(
        db_session, product.id,
        SpecCreate(label="2 粒精緻禮盒", qty_text="q", price=880, stock_qty=20, is_two_pack=True),
    )
    assert created.images == ["two.jpg"]


async def test_update_spec_switches_group_images(db_session: AsyncSession):
    product = Product(slug="kanro", name="甘露梨", description="d", image="i", season="s")
    product.specs = [
        ProductSpec(label="A", qty_text="q", price=880, stock_qty=20, is_two_pack=False),
    ]
    product.images = [
        ProductImage(url="single.jpg", is_two_pack=False, sort_order=0),
        ProductImage(url="two.jpg", is_two_pack=True, sort_order=0),
    ]
    await product_repo.add(db_session, product)
    spec = product.specs[0]

    updated = await product_service.update_spec(db_session, spec.id, SpecUpdate(is_two_pack=True))
    assert updated.images == ["two.jpg"]
```

- [ ] **Step 2: 執行測試，確認失敗**

Run: `cd backend && uv run pytest tests/test_product_service.py -v`
Expected: FAIL（`_to_public_spec`/`_to_admin_spec` 目前吃 `s.images`，`ProductSpec` 已無此 relationship，會是 `AttributeError`）

- [ ] **Step 3: 修改 `product_service.py`**

在檔案頂部 import 區塊加入：

```python
from app.models.product_image import ProductImage
```

把 `_get_spec_images` 換成 `_group_images`，並改動 `_to_public_spec`/`_to_admin_spec`/`_to_public_product`/`_to_admin_product` 簽名：

```python
def _group_images(images: list[ProductImage], is_two_pack: bool) -> list[str]:
    return [img.url for img in images if img.is_two_pack == is_two_pack]


def _to_public_spec(s: ProductSpec, product_images: list[ProductImage]) -> PublicSpecRead:
    return PublicSpecRead(
        id=s.id,
        label=s.label,
        qty_text=s.qty_text,
        price=s.price,
        stock_status=derive_stock_status(s.stock_qty, s.low_stock_threshold),
        note=s.note,
        images=_group_images(product_images, s.is_two_pack),
        is_two_pack=s.is_two_pack,
    )


def _to_admin_spec(s: ProductSpec, product_images: list[ProductImage]) -> AdminSpecRead:
    return AdminSpecRead(
        id=s.id,
        label=s.label,
        qty_text=s.qty_text,
        price=s.price,
        stock_status=derive_stock_status(s.stock_qty, s.low_stock_threshold),
        note=s.note,
        stock_qty=s.stock_qty,
        low_stock_threshold=s.low_stock_threshold,
        sort_order=s.sort_order,
        is_active=s.is_active,
        images=_group_images(product_images, s.is_two_pack),
        is_two_pack=s.is_two_pack,
    )
```

`_to_public_product`/`_to_admin_product` 內組裝 specs 的地方改成把 `p.images` 傳進去：

```python
def _to_public_product(p: Product) -> PublicProductRead:
    return PublicProductRead(
        id=p.id,
        slug=p.slug,
        name=p.name,
        description=p.description,
        images=_get_images(p),
        season=p.season,
        tag=p.tag,
        tag_color=p.tag_color,
        specs=[_to_public_spec(s, p.images) for s in p.specs if s.is_active],
    )


def _to_admin_product(p: Product) -> AdminProductRead:
    return AdminProductRead(
        id=p.id,
        slug=p.slug,
        name=p.name,
        description=p.description,
        images=_get_images(p),
        season=p.season,
        tag=p.tag,
        tag_color=p.tag_color,
        is_active=p.is_active,
        specs=[_to_admin_spec(s, p.images) for s in p.specs],
    )
```

`create_spec`/`update_spec` 目前各自呼叫 `_to_admin_spec(spec)`（單一參數）；改成先撈該規格所屬商品（拿到 `product.images`）再組裝：

```python
async def create_spec(
    session: AsyncSession, product_id: int, data: SpecCreate
) -> AdminSpecRead:
    product = await product_repo.get_by_id(session, product_id)
    if product is None:
        raise NotFoundError("找不到商品")
    spec = ProductSpec(product_id=product_id, **data.model_dump())
    await spec_repo.add(session, spec)
    await session.commit()
    await session.refresh(spec)
    return _to_admin_spec(spec, product.images)


async def update_spec(
    session: AsyncSession, spec_id: int, data: SpecUpdate
) -> AdminSpecRead:
    spec = await spec_repo.get_by_id(session, spec_id)
    if spec is None:
        raise NotFoundError("找不到規格")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(spec, field, value)
    await session.commit()
    await session.refresh(spec)
    product = await product_repo.get_by_id(session, spec.product_id)
    return _to_admin_spec(spec, product.images)
```

（`product` 一定存在，因為 `spec.product_id` 是 FK 保證有效，不用另外判斷 `None`。）

- [ ] **Step 4: 執行測試，確認全部通過**

Run: `cd backend && uv run pytest tests/test_product_service.py tests/test_product_images_public.py -v`
Expected: PASS（含既有測試——`test_product_images_public.py` 測的是商品層級 fallback，不受影響）

- [ ] **Step 5: 全套後端測試 + lint + 型別檢查**

Run: `cd backend && uv run pytest -q && uv run ruff check . && uv run mypy app`
Expected: 全綠

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/product_service.py backend/tests/test_product_service.py
git commit -m "feat(products): resolve spec images from shared pack-size group"
```

---

## Task 5: Alembic migration（正式資料庫 schema）

**Files:**
- Create: `backend/alembic/versions/<revision>_group_product_images_by_pack_size.py`

**Interfaces:**
- Consumes: 無（獨立 schema migration，跟 pytest 測試套件無關——測試用 `Base.metadata.create_all` 直接照 model 建表）。
- Produces: 正式/本機 Postgres 的 `product_images` 表結構符合 Task 1 的 model。

- [ ] **Step 1: 產生 migration 骨架**

Run: `cd backend && uv run alembic revision -m "group product images by pack size"`

這會在 `backend/alembic/versions/` 產生一個新檔案，記下產生的 revision id（檔名開頭那串 hash）。

- [ ] **Step 2: 填入 upgrade/downgrade 內容**

打開剛產生的檔案，確認 `down_revision = 'ccae80d8b67e'`（目前 head，`add_is_two_pack_to_product_specs` 那支），把 `upgrade()`/`downgrade()` 改成：

```python
def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('product_images', sa.Column('is_two_pack', sa.Boolean(), nullable=True))
    op.execute(
        """
        UPDATE product_images
        SET is_two_pack = product_specs.is_two_pack
        FROM product_specs
        WHERE product_images.spec_id = product_specs.id
        """
    )
    op.drop_constraint('product_images_spec_id_fkey', 'product_images', type_='foreignkey')
    op.drop_index('ix_product_images_spec_id', table_name='product_images')
    op.drop_column('product_images', 'spec_id')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('product_images', sa.Column('spec_id', sa.Integer(), nullable=True))
    op.create_index(
        'ix_product_images_spec_id', 'product_images', ['spec_id'], unique=False
    )
    op.create_foreign_key(
        'product_images_spec_id_fkey', 'product_images', 'product_specs', ['spec_id'], ['id']
    )
    op.drop_column('product_images', 'is_two_pack')
```

> `downgrade()` 只還原 schema，**不**還原「哪張圖片原本屬於哪個規格」——這在 upgrade 的合併過程中已經是不可逆資訊，只用於緊急回滾 schema。

- [ ] **Step 3: 本機驗證（需要 `docker compose up db` 開著）**

Run: `cd backend && uv run alembic upgrade head`
Expected: 成功套用，無錯誤。

若 `drop_constraint('product_images_spec_id_fkey', ...)` 報錯（constraint 名稱不符，通常是 Postgres 實際生成的名字跟猜測的不同），先用 `psql $DATABASE_URL -c '\d product_images'` 查出真正的 FK/index 名稱，改掉 migration 檔裡的字串常數再重跑。

用一次性 Python 腳本確認 backfill 正確（若本機 DB 內已有 seed 資料/測試資料可直接查）：

```bash
cd backend && uv run python -c "
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as s:
        rows = await s.execute(text('SELECT id, is_two_pack FROM product_images'))
        for r in rows:
            print(r)

asyncio.run(main())
"
```
Expected: 每一列的 `is_two_pack` 與其原本規格的 `is_two_pack` 一致（若本機沒有既有圖片資料，這步驟只需確認指令本身能跑、欄位存在即可）。

- [ ] **Step 4: 驗證 downgrade 可還原 schema**

Run: `cd backend && uv run alembic downgrade -1 && uv run alembic upgrade head`
Expected: 兩個方向都不報錯。

- [ ] **Step 5: Commit**

```bash
git add backend/alembic/versions/
git commit -m "chore(db): migrate product_images from spec_id to is_two_pack grouping"
```

---

## Task 6: `api.js` — 群組圖片 API client

**Files:**
- Modify: `frontend/src/api.js`

**Interfaces:**
- Consumes: Task 3 的三支後端 group 端點。
- Produces:
  - `listGroupImages(token, productId, group)`
  - `registerGroupImage(token, productId, group, url, sortOrder = 0)`
  - `reorderGroupImages(token, productId, group, items)`
  - （`group` 為 `'two_pack' | 'single'` 字串，直接對應後端路徑參數）

- [ ] **Step 1: 修改 `frontend/src/api.js`**

把「Admin spec image APIs」整段（`listSpecImages`/`registerSpecImage`/`reorderSpecImages`）換成：

```js
// ── Admin group image APIs（依包裝群組：two_pack / single）──

export const listGroupImages = (token, productId, group) =>
  adminRequest(token, `/api/admin/products/${productId}/images/group/${group}`);

export const registerGroupImage = (token, productId, group, url, sortOrder = 0) =>
  adminRequest(token, `/api/admin/products/${productId}/images/group/${group}`, {
    method: 'POST',
    body: JSON.stringify({ url, sort_order: sortOrder }),
  });

export const reorderGroupImages = (token, productId, group, items) =>
  adminRequest(token, `/api/admin/products/${productId}/images/group/${group}/reorder`, {
    method: 'PATCH',
    body: JSON.stringify({ items }),
  });
```

`deleteProductImage` 不變（沿用，group 圖片跟商品圖片共用同一個 `DELETE /images/{id}` 端點）。

把檔案尾端 `window.MiaoApi = {...}` 這個匯出物件內的 `listSpecImages`/`registerSpecImage`/`reorderSpecImages` 換成 `listGroupImages`/`registerGroupImage`/`reorderGroupImages`（保持字母序）：

```js
window.MiaoApi = {
  ApiError,
  createOrder,
  createSpec,
  deleteProductImage,
  deleteSpec,
  getAdminOrder,
  getAdminOrderSummary,
  getCurrentAdmin,
  listAdminOrders,
  listAdminProducts,
  listGroupImages,
  listProductImages,
  listProducts,
  loginAdmin,
  registerGroupImage,
  registerProductImage,
  reorderGroupImages,
  reorderProductImages,
  signUpload,
  updateAdminOrderStatus,
  updateAdminProduct,
  updateSpec,
};
```

- [ ] **Step 2: 檢查沒有殘留舊 import**

Run: `cd frontend && grep -rn "listSpecImages\|registerSpecImage\|reorderSpecImages" src/`
Expected: 只剩 `AdminApp.jsx` 裡的用法（Task 7/8 會處理），`api.js` 本身不再出現。

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api.js
git commit -m "feat(admin-api): replace spec-scoped image client fns with group-scoped ones"
```

---

## Task 7: `AdminApp.jsx` — `GroupImageGallery` + `GroupImagePreview` 元件

**Files:**
- Modify: `frontend/src/AdminApp.jsx`

**Interfaces:**
- Consumes: `listGroupImages`/`registerGroupImage`/`reorderGroupImages`（Task 6）、`deleteProductImage`（既有）、`signUpload`（既有）
- Produces:
  - `<GroupImageGallery productId={number} group={'two_pack'|'single'} token={string} />`（可編輯：上傳/刪除/拖曳排序）
  - `<GroupImagePreview productId={number} group={'two_pack'|'single'} token={string} />`（唯讀縮圖）

- [ ] **Step 1: 修改 import 區塊**

把 `frontend/src/AdminApp.jsx` 頂部的：

```js
import {
  createSpec,
  deleteProductImage,
  deleteSpec,
  getAdminOrder,
  getAdminOrderSummary,
  getCurrentAdmin,
  listAdminOrders,
  listAdminProducts,
  listSpecImages,
  loginAdmin,
  registerSpecImage,
  reorderSpecImages,
  signUpload,
  updateAdminOrderStatus,
  updateSpec,
} from './api.js';
```

改成：

```js
import {
  createSpec,
  deleteProductImage,
  deleteSpec,
  getAdminOrder,
  getAdminOrderSummary,
  getCurrentAdmin,
  listAdminOrders,
  listAdminProducts,
  listGroupImages,
  loginAdmin,
  registerGroupImage,
  reorderGroupImages,
  signUpload,
  updateAdminOrderStatus,
  updateSpec,
} from './api.js';
```

- [ ] **Step 2: 把 `SpecImageGallery` 改名並改吃 `(productId, group)`**

把 `SortableImageItem` 後面、`SpecEditModal` 前面那段 `SpecImageGallery`（約 606–697 行）整段換成：

```js
const GROUP_LABEL = { two_pack: '兩粒裝', single: '一層裝' };

/* ── 群組相片相簿（依包裝群組，可編輯）── */
function GroupImageGallery({ productId, group, token }) {
  const [images, setImages] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(TouchSensor, { activationConstraint: { delay: 200, tolerance: 5 } }),
  );

  useEffect(() => {
    listGroupImages(token, productId, group).then(setImages).catch(() => {});
  }, [productId, group, token]);

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    setError('');
    try {
      const { signed_url, public_url } = await signUpload(token, file.name, file.type);
      await fetch(signed_url, {
        method: 'PUT',
        headers: { 'Content-Type': file.type },
        body: file,
      });
      const img = await registerGroupImage(token, productId, group, public_url, images.length);
      setImages((prev) => [...prev, img]);
    } catch (err) {
      setError('上傳失敗：' + (err?.message || '請稍後再試'));
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleDelete = async (imageId) => {
    try {
      await deleteProductImage(token, imageId);
      setImages((prev) => prev.filter((i) => i.id !== imageId));
    } catch {
      setError('刪除失敗，請稍後再試');
    }
  };

  const handleDragEnd = async (event) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const oldIndex = images.findIndex((i) => i.id === active.id);
    const newIndex = images.findIndex((i) => i.id === over.id);
    setError('');
    const prevImages = images;
    const newImages = arrayMove(images, oldIndex, newIndex);
    setImages(newImages);
    try {
      await reorderGroupImages(
        token,
        productId,
        group,
        newImages.map((img, idx) => ({ id: img.id, sort_order: idx })),
      );
    } catch {
      setImages(prevImages);
      setError('排序儲存失敗，請稍後再試');
    }
  };

  return (
    <div className="img-gallery">
      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={images.map((i) => i.id)} strategy={rectSortingStrategy}>
          <div className="img-gallery__grid">
            {images.map((img) => (
              <SortableImageItem key={img.id} image={img} onDelete={handleDelete} />
            ))}
            <label className={`img-gallery__upload-btn${uploading ? ' is-uploading' : ''}`}>
              {uploading ? '上傳中…' : '＋'}
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                style={{ display: 'none' }}
                onChange={handleFileChange}
                disabled={uploading}
              />
            </label>
          </div>
        </SortableContext>
      </DndContext>
      {error && <div className="adm-alert" style={{ marginTop: 8 }}>{error}</div>}
    </div>
  );
}

/* ── 群組相片唯讀預覽（規格 Modal 內用）── */
function GroupImagePreview({ productId, group, token }) {
  const [images, setImages] = useState([]);

  useEffect(() => {
    listGroupImages(token, productId, group).then(setImages).catch(() => {});
  }, [productId, group, token]);

  return (
    <div className="img-gallery img-gallery--preview">
      <div className="img-gallery__grid">
        {images.map((img) => (
          <img key={img.id} src={img.url} alt="" className="img-gallery__thumb" />
        ))}
        {images.length === 0 && <span className="adm-muted">此群組尚無照片</span>}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: 啟動前端 dev server，確認沒有編譯錯誤**

Run: `cd frontend && npm run dev`（背景執行即可，看 terminal 輸出）
Expected: Vite 編譯成功，無 `GroupImageGallery`/`GroupImagePreview` 相關錯誤（此階段還沒有任何地方呼叫它們，正常）

- [ ] **Step 4: Commit**

```bash
git add frontend/src/AdminApp.jsx
git commit -m "feat(admin-ui): add GroupImageGallery/GroupImagePreview components"
```

---

## Task 8: `AdminApp.jsx` — 接上「商品照片管理」區塊 + 規格 Modal 唯讀預覽

**Files:**
- Modify: `frontend/src/AdminApp.jsx`
- Modify: `frontend/assets/admin.css`

**Interfaces:**
- Consumes: `GroupImageGallery`/`GroupImagePreview`（Task 7）
- Produces: 無新函式匯出——這是最終的 UI 接線，完成後即可手動瀏覽器驗證整條路徑。

- [x] **Step 1: `SpecEditModal` 改用 `GroupImagePreview`**

把 `SpecEditModal` 裡：

```js
          {/* 圖片 */}
          <div className="adm-modal__section">
            <div className="adm-modal__section-title">規格圖片</div>
            <SpecImageGallery specId={spec.id} token={token} />
          </div>
```

改成：

```js
          {/* 圖片 */}
          <div className="adm-modal__section">
            <div className="adm-modal__section-title">
              規格圖片（{GROUP_LABEL[form.is_two_pack ? 'two_pack' : 'single']}相片組）
            </div>
            <p className="adm-field__hint">
              此規格使用「{GROUP_LABEL[form.is_two_pack ? 'two_pack' : 'single']}」相片組，
              請至上方「商品照片管理」編輯，這裡僅供預覽。
            </p>
            <GroupImagePreview
              productId={spec.product_id}
              group={form.is_two_pack ? 'two_pack' : 'single'}
              token={token}
            />
          </div>
```

- [x] **Step 2: `CreateSpecModal` 建立完成後的預覽也改用 `GroupImagePreview`**

```js
          <div className="adm-modal__product-body">
            <div className="adm-modal__section">
              <div className="adm-modal__section-title">
                規格圖片（{GROUP_LABEL[form.is_two_pack ? 'two_pack' : 'single']}相片組）
              </div>
              <p className="adm-field__hint">
                此規格使用「{GROUP_LABEL[form.is_two_pack ? 'two_pack' : 'single']}」相片組，
                請至上方「商品照片管理」編輯，這裡僅供預覽。
              </p>
              <GroupImagePreview
                productId={productId}
                group={form.is_two_pack ? 'two_pack' : 'single'}
                token={token}
              />
            </div>
          </div>
```

（`CreateSpecModal` 本來就有 `productId` prop，不用額外傳遞。）

- [x] **Step 3: `SpecEditModal` 呼叫端要帶上 `product_id`**

`AdminSpecRead` 沒有 `product_id` 欄位，`ProductsTab` 裡的 `p.specs` 陣列元素也沒有，所以在開啟編輯 Modal 時手動附掛。把 `ProductsTab` 內：

```js
                          <button
                            className="adm-btn adm-btn--secondary"
                            style={{ fontSize: 13.5 }}
                            onClick={() => setEditSpec(s)}
                          >編輯</button>
```

改成：

```js
                          <button
                            className="adm-btn adm-btn--secondary"
                            style={{ fontSize: 13.5 }}
                            onClick={() => setEditSpec({ ...s, product_id: p.id })}
                          >編輯</button>
```

- [x] **Step 4: 在 `ProductsTab` 商品卡片內加入「商品照片管理」區塊**

在 `adm-product-header` 之後、規格表格（`adm-spec-scroll`）之前插入：

```js
          {expanded[p.id] && (
            <>
              <div className="adm-photo-groups">
                <div className="adm-photo-groups__group">
                  <div className="adm-modal__section-title">兩粒裝相片</div>
                  <GroupImageGallery productId={p.id} group="two_pack" token={token} />
                </div>
                <div className="adm-photo-groups__group">
                  <div className="adm-modal__section-title">一層裝相片</div>
                  <GroupImageGallery productId={p.id} group="single" token={token} />
                </div>
              </div>
              <div className="adm-spec-scroll">
```

（原本 `<>` 後面直接接的就是 `<div className="adm-spec-scroll">`，只需要在它前面插入新的 `adm-photo-groups` 區塊，其餘 JSX 結構不變。）

- [x] **Step 5: 補上 `.adm-photo-groups` CSS**

在 `frontend/assets/admin.css` 找到 `.img-gallery__grid` 定義前後，新增：

```css
.adm-photo-groups {
  display: flex;
  gap: 20px;
  padding: 14px 16px 0;
  flex-wrap: wrap;
}
.adm-photo-groups__group {
  flex: 1 1 280px;
  min-width: 240px;
}
```

- [x] **Step 6: 手動瀏覽器驗證**

Run: `cd backend && uv run uvicorn app.main:app --reload --port 8000`（背景）
Run: `cd frontend && npm run dev`（背景）

用瀏覽器打開後台商品管理頁，操作並確認：
1. 展開商品卡片可看到「兩粒裝相片」「一層裝相片」兩個相簿，各自可上傳/刪除/拖曳排序。
2. 上傳到「兩粒裝相片」後，編輯任一個 `is_two_pack=true` 的規格（例：2 粒精緻禮盒），Modal 內預覽顯示同一組照片。
3. 新增規格時勾選/取消「2 粒裝」checkbox，Modal 內預覽即時切換成對應群組的照片（不用存檔）。
4. 前台商店頁（`npm run dev` 的 storefront 或 `AdminApp` 之外的主站）各規格 `SpecCard` 輪播顯示正確的群組照片，且同群組的不同規格顯示相同照片。

- [x] **Step 7: 前端建置檢查**

Run: `cd frontend && npm run build`
Expected: 建置成功，無錯誤。

- [x] **Step 8: Commit**

```bash
git add frontend/src/AdminApp.jsx frontend/assets/admin.css
git commit -m "feat(admin-ui): manage two-pack/single photo groups at product level"
```

---

## 完成後檢查清單（對照 spec）

- [x] Task 1–4：`ProductImage` 以 `is_two_pack` 分組取代 `spec_id`，`product_service` 依群組共用圖片。
- [x] Task 5：正式 DB migration + backfill + downgrade。
- [x] Task 6–8：後台 API client、群組相簿元件、商品層級管理區塊、規格 Modal 唯讀預覽。
- [x] 前台 `SpecCard.jsx` 不需改動（spec 已確認）。
- [ ] 部署前確認：這是設計文件標記的「合併效應」——正式環境資料庫的 5 台斤/10 台斤兩個規格若先前各自有獨立照片，migration 後會合併成一個「一層裝」相簿，需人工檢查排序（對照 spec「合併效應」段落）。
