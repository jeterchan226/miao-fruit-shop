# Phase 5: GCS 圖片管理（多圖上傳 + 前台輪播）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. When a task is fully done, also tick its checkboxes here.

**Goal:** 讓管理員從後台直接上傳商品圖片到 Google Cloud Storage，商品支援多張圖片並記錄排序；前台 SpecCard 以輪播方式呈現多張圖片。

**Architecture:**
- 後端簽發 GCS v4 Signed URL（15 分鐘效期）→ 前端直接 PUT 到 GCS，不經過後端傳輸檔案
- 上傳完成後前端呼叫後端 API 登記 URL 至 `product_images` 表
- `Product.image`（舊單圖欄位）保留但改為 nullable，作為過渡期 fallback；公開 API 優先回傳 `product_images`，若無則包裝 `[product.image]`
- 前台輪播以原生 CSS scroll-snap 實作，不引入外部 library

**Tech Stack:** Python 3.13, FastAPI 0.136.3, SQLAlchemy 2.0.50 async, `google-cloud-storage 2.x`, Alembic; React 18, Vite, CSS scroll-snap。

**Spec:** `docs/superpowers/specs/2026-06-15-phase5-gcs-images-design.md`（本計畫附帶）

**Branch:** `feat/phase5-gcs-images`（built on Phase 4b）

**Prerequisites:**
- Phase 1–4b 全部完成、測試全綠
- GCP 專案已建立，`gsutil` / `gcloud` CLI 可用（Task 1 手動操作）
- 所有 backend 指令從 `backend/` 執行

---

## 上傳流程

```
前端 AdminApp          後端 FastAPI              GCS Bucket
     │                       │                        │
     │─ POST /api/admin/     │                        │
     │  uploads/sign ───────▶│                        │
     │  { filename,          │── generate_signed_url ─▶│
     │    content_type }     │◀── signed_url ─────────│
     │◀─ { signed_url,       │                        │
     │     public_url } ─────│                        │
     │                       │                        │
     │─ PUT signed_url ───────────────────────────────▶│
     │  (直接上傳，不過後端)  │                 存檔案 │
     │◀─ 200 ────────────────────────────────────────│
     │                       │                        │
     │─ POST /api/admin/     │                        │
     │  products/{id}/images▶│                        │
     │  { url, sort_order }  │── INSERT product_images│
     │◀─ 201 { image } ──────│                        │
```

---

## 檔案結構

**新增（後端）：**
- `app/models/product_image.py` — `ProductImage` ORM
- `app/schemas/image.py` — 圖片相關 schemas
- `app/repositories/image_repo.py` — image CRUD
- `app/services/gcs_service.py` — signed URL、GCS 刪除
- `app/services/image_service.py` — 業務邏輯（sign / register / delete / reorder）
- `app/api/routes/admin_images.py` — 5 個 endpoints
- `alembic/versions/<rev>_add_product_images.py` — migration

**修改（後端）：**
- `app/core/config.py` — 新增 `gcs_bucket_name`, `gcs_credentials_b64`
- `app/models/__init__.py` — 匯出 `ProductImage`
- `app/models/product.py` — `image` 改 nullable、加 `images` selectin relationship
- `app/schemas/product.py` — `PublicProductRead.image` → `images: list[str]`、`AdminProductRead` 同步
- `app/services/product_service.py` — `_to_public_product` / `_to_admin_product` 加入 images
- `app/main.py` — include `admin_images` router
- `backend/pyproject.toml` — 加 `google-cloud-storage`
- `backend/.env.example` — 加 GCS 設定說明

**新增測試：**
- `tests/test_gcs_service.py`
- `tests/test_image_repo.py`
- `tests/test_image_service.py`
- `tests/test_admin_images_api.py`
- `tests/test_product_images_public.py`

**修改（前端）：**
- `frontend/src/api.js` — 新增圖片相關 API 函式
- `frontend/src/AdminApp.jsx` — 商品編輯 Modal 圖片 gallery
- `frontend/src/SpecCard.jsx` — 單圖 → 輪播
- `frontend/assets/site.css` — 輪播樣式
- `frontend/assets/admin.css` — 圖片 gallery 樣式

---

## Task 1：GCP 環境設定（手動，非程式碼）

> **此 Task 需要人工操作**，無 checkbox 可自動執行。完成後在下方打勾。

- [ ] **Step 1：建立 GCS Bucket**

```bash
# 替換為你的 project ID 和偏好的 bucket 名稱
PROJECT_ID="your-project-id"
BUCKET_NAME="miao-fruit-shop-images"

gcloud storage buckets create gs://$BUCKET_NAME \
  --project=$PROJECT_ID \
  --location=asia-east1 \
  --uniform-bucket-level-access
```

- [ ] **Step 2：設定 Bucket 公開讀取（圖片可被前台直接存取）**

```bash
gcloud storage buckets add-iam-policy-binding gs://$BUCKET_NAME \
  --member="allUsers" \
  --role="roles/storage.objectViewer"
```

- [ ] **Step 3：設定 CORS（允許瀏覽器直接 PUT）**

建立 `backend/gcs-cors.json`：
```json
[
  {
    "origin": ["http://localhost:8080", "https://your-production-domain.com"],
    "method": ["PUT", "GET"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
```

套用：
```bash
gcloud storage buckets update gs://$BUCKET_NAME \
  --cors-file=backend/gcs-cors.json
```

- [ ] **Step 4：建立 Service Account**

```bash
SA_NAME="miao-gcs-uploader"

gcloud iam service-accounts create $SA_NAME \
  --display-name="Miao Fruit Shop GCS Uploader" \
  --project=$PROJECT_ID

# 授予 Object Creator（上傳）+ Object Viewer（生成 signed URL）
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.objectCreator"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"
```

- [ ] **Step 5：下載 JSON Key 並轉為 base64**

```bash
gcloud iam service-accounts keys create backend/gcs-key.json \
  --iam-account="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# 轉 base64（貼入 .env）
cat backend/gcs-key.json | base64 | tr -d '\n'
```

將輸出值存入 `backend/.env`：
```dotenv
GCS_BUCKET_NAME=miao-fruit-shop-images
GCS_CREDENTIALS_B64=<上面 base64 輸出>
```

> ⚠️ `gcs-key.json` 已在 `.gitignore` 中（Task 2 Step 1 確認），**絕對不可 commit**。

- [ ] **Step 6：確認 `.gitignore` 包含 key 檔**

`backend/.gitignore` 確認含有：
```
gcs-key.json
gcs-cors.json
```

---

## Task 2：更新 Settings、安裝 library

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/app/core/config.py`
- Modify: `backend/.env.example`
- Modify: `backend/.gitignore`

- [x] **Step 1：確認 `.gitignore`**

確認 `backend/.gitignore` 含：
```
gcs-key.json
gcs-cors.json
```

- [x] **Step 2：加入 `google-cloud-storage` 依賴**

`backend/pyproject.toml` 的 `dependencies` 加入：
```toml
"google-cloud-storage==2.19.0",
```

Run: `uv sync`
Expected: 安裝 `google-cloud-storage` 及其依賴，無 error。

- [x] **Step 3：更新 `backend/app/core/config.py`**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    cors_origins: str = "http://localhost:8080"

    # GCS
    gcs_bucket_name: str = ""
    gcs_credentials_b64: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def gcs_enabled(self) -> bool:
        return bool(self.gcs_bucket_name and self.gcs_credentials_b64)


settings = Settings()  # type: ignore[call-arg]
```

> `gcs_bucket_name` 和 `gcs_credentials_b64` 預設為空字串而非 required，讓缺少 GCS 設定時後端仍可啟動（僅 GCS 功能降級）。`gcs_enabled` property 用於 service 層決定是否可用。

- [x] **Step 4：更新 `backend/.env.example`**

加入區塊：
```dotenv
# GCS 圖片儲存（選填，未設定時圖片 API 回傳 503）
GCS_BUCKET_NAME=miao-fruit-shop-images
GCS_CREDENTIALS_B64=<base64 encoded service account JSON>
```

- [x] **Step 5：驗證 import**

Run: `uv run python -c "from google.cloud import storage; print('ok')"`
Expected: `ok`

- [x] **Step 6：Run 全套測試確認不壞**

Run: `uv run pytest -q`
Expected: all pass（129 既有）。

- [x] **Step 7：Commit**

```bash
git add pyproject.toml uv.lock app/core/config.py .env.example .gitignore
git commit -m "feat(backend): add GCS settings + google-cloud-storage dep"
```

---

## Task 3：`ProductImage` model + Alembic migration

**Files:**
- Create: `app/models/product_image.py`
- Modify: `app/models/__init__.py`
- Modify: `app/models/product.py`
- Create: `alembic/versions/<rev>_add_product_images.py`

- [x] **Step 1：建立 `app/models/product_image.py`**

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
    url: Mapped[str] = mapped_column()
    sort_order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    product: Mapped["Product"] = relationship(back_populates="images")
```

- [x] **Step 2：修改 `app/models/product.py`**

加入 `images` relationship，並將 `image` 欄位改為 nullable：

```python
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.product_image import ProductImage
    from app.models.product_spec import ProductSpec


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(unique=True, index=True)
    name: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column(Text)
    image: Mapped[str | None] = mapped_column(default=None)   # nullable — GCS 上線後逐步淘汰
    season: Mapped[str] = mapped_column()
    tag: Mapped[str | None] = mapped_column(default=None)
    tag_color: Mapped[str | None] = mapped_column(default=None)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    specs: Mapped[list["ProductSpec"]] = relationship(
        back_populates="product",
        lazy="selectin",
        order_by="ProductSpec.sort_order, ProductSpec.id",
        cascade="all, delete-orphan",
    )
    images: Mapped[list["ProductImage"]] = relationship(
        back_populates="product",
        lazy="selectin",
        order_by="ProductImage.sort_order, ProductImage.id",
        cascade="all, delete-orphan",
    )
```

- [x] **Step 3：更新 `app/models/__init__.py`**

```python
from app.models.admin_user import AdminUser
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.product_spec import ProductSpec

__all__ = ["AdminUser", "Order", "OrderItem", "Product", "ProductImage", "ProductSpec"]
```

- [x] **Step 4：驗證表格註冊**

Run: `uv run python -c "import app.models; from app.core.database import Base; print(sorted(Base.metadata.tables))"`
Expected: 包含 `'product_images'`。

- [x] **Step 5：Autogenerate migration**

Run: `uv run alembic revision --autogenerate -m "add product_images"`
Expected: 產生 `<rev>_add_product_images.py`，`upgrade()` 含：
- `op.create_table("product_images", ...)` 含 FK → products.id、index on product_id
- `op.alter_column("products", "image", nullable=True)`
- `downgrade()` 反向操作

- [x] **Step 6：Sanity-check 並套用**

Run: `sed -n '1,60p' alembic/versions/*_add_product_images.py`
確認 `create_table` + `alter_column` 均在 upgrade() 內，無空 body。

Run: `uv run alembic upgrade head`
Expected: 無 traceback，exit 0。

- [x] **Step 7：Run suite**

Run: `uv run pytest -q`
Expected: all pass（既有 129 tests）。

- [x] **Step 8：Commit**

```bash
git add app/models/product_image.py app/models/product.py app/models/__init__.py alembic/versions/
git commit -m "feat(backend): ProductImage model + migration"
```

---

## Task 4：GCS Service

**Files:**
- Create: `app/services/gcs_service.py`
- Test: `tests/test_gcs_service.py`

- [x] **Step 1：寫 failing test** — `tests/test_gcs_service.py`

```python
import base64
import json
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.services.gcs_service import GcsService


def _fake_credentials_b64() -> str:
    info = {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "key-id",
        "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA\n-----END RSA PRIVATE KEY-----\n",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    return base64.b64encode(json.dumps(info).encode()).decode()


def _make_service(bucket: str = "test-bucket", b64: str | None = None) -> GcsService:
    return GcsService(bucket_name=bucket, credentials_b64=b64 or _fake_credentials_b64())


def test_gcs_service_disabled_when_no_credentials():
    svc = GcsService(bucket_name="", credentials_b64="")
    assert not svc.enabled


def test_gcs_service_enabled_with_credentials():
    svc = _make_service()
    assert svc.enabled


def test_make_blob_name_format():
    svc = _make_service()
    name = svc._make_blob_name(product_id=3, filename="photo.jpg")
    assert name.startswith("products/3/")
    assert name.endswith(".jpg")


def test_public_url_format():
    svc = _make_service(bucket="my-bucket")
    assert svc.public_url("products/3/abc.jpg") == (
        "https://storage.googleapis.com/my-bucket/products/3/abc.jpg"
    )


@patch("app.services.gcs_service.storage.Client")
@patch("app.services.gcs_service.service_account.Credentials.from_service_account_info")
def test_sign_returns_signed_url_and_public_url(mock_creds, mock_client_cls):
    mock_blob = MagicMock()
    mock_blob.generate_signed_url.return_value = "https://storage.googleapis.com/signed"
    mock_bucket = MagicMock()
    mock_bucket.blob.return_value = mock_blob
    mock_client_cls.return_value.bucket.return_value = mock_bucket

    svc = _make_service()
    result = svc.sign_upload(product_id=1, filename="img.jpg", content_type="image/jpeg")

    assert result["signed_url"] == "https://storage.googleapis.com/signed"
    assert result["public_url"].startswith("https://storage.googleapis.com/test-bucket/products/1/")
    mock_blob.generate_signed_url.assert_called_once()


@patch("app.services.gcs_service.storage.Client")
@patch("app.services.gcs_service.service_account.Credentials.from_service_account_info")
def test_delete_calls_blob_delete(mock_creds, mock_client_cls):
    mock_blob = MagicMock()
    mock_bucket = MagicMock()
    mock_bucket.blob.return_value = mock_blob
    mock_client_cls.return_value.bucket.return_value = mock_bucket

    svc = _make_service(bucket="my-bucket")
    svc.delete_object("https://storage.googleapis.com/my-bucket/products/1/abc.jpg")

    mock_blob.delete.assert_called_once()
```

- [x] **Step 2：Run test 確認 fail**

Run: `uv run pytest tests/test_gcs_service.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.gcs_service'`

- [x] **Step 3：實作 `app/services/gcs_service.py`**

```python
import base64
import json
import uuid
from datetime import timedelta

from google.cloud import storage
from google.oauth2 import service_account

from app.core.config import settings

_GCS_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]
_SIGNED_URL_TTL = timedelta(minutes=15)


class GcsService:
    def __init__(self, bucket_name: str, credentials_b64: str) -> None:
        self._bucket_name = bucket_name
        self._credentials_b64 = credentials_b64
        self._credentials: service_account.Credentials | None = None
        self._client: storage.Client | None = None

    @property
    def enabled(self) -> bool:
        return bool(self._bucket_name and self._credentials_b64)

    def _get_credentials(self) -> service_account.Credentials:
        if self._credentials is None:
            info = json.loads(base64.b64decode(self._credentials_b64))
            self._credentials = service_account.Credentials.from_service_account_info(
                info, scopes=_GCS_SCOPES
            )
        return self._credentials

    def _get_client(self) -> storage.Client:
        if self._client is None:
            creds = self._get_credentials()
            info = json.loads(base64.b64decode(self._credentials_b64))
            self._client = storage.Client(credentials=creds, project=info["project_id"])
        return self._client

    def _make_blob_name(self, product_id: int, filename: str) -> str:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
        return f"products/{product_id}/{uuid.uuid4().hex}.{ext}"

    def public_url(self, blob_name: str) -> str:
        return f"https://storage.googleapis.com/{self._bucket_name}/{blob_name}"

    def sign_upload(
        self, product_id: int, filename: str, content_type: str
    ) -> dict[str, str]:
        blob_name = self._make_blob_name(product_id, filename)
        client = self._get_client()
        bucket = client.bucket(self._bucket_name)
        blob = bucket.blob(blob_name)
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=_SIGNED_URL_TTL,
            method="PUT",
            content_type=content_type,
            credentials=self._get_credentials(),
        )
        return {"signed_url": signed_url, "public_url": self.public_url(blob_name)}

    def delete_object(self, public_url: str) -> None:
        prefix = f"https://storage.googleapis.com/{self._bucket_name}/"
        if not public_url.startswith(prefix):
            return
        blob_name = public_url[len(prefix):]
        client = self._get_client()
        bucket = client.bucket(self._bucket_name)
        blob = bucket.blob(blob_name)
        blob.delete()


gcs_service = GcsService(
    bucket_name=settings.gcs_bucket_name,
    credentials_b64=settings.gcs_credentials_b64,
)
```

- [x] **Step 4：Run test 確認通過**

Run: `uv run pytest tests/test_gcs_service.py -v`
Expected: PASS（6 passed）。

- [x] **Step 5：Commit**

```bash
git add app/services/gcs_service.py tests/test_gcs_service.py
git commit -m "feat(backend): GCS service (sign upload, delete object)"
```

---

## Task 5：Image Schemas

**Files:**
- Create: `app/schemas/image.py`
- Test: `tests/test_schemas_image.py`

- [x] **Step 1：寫 failing test** — `tests/test_schemas_image.py`

```python
import pytest
from pydantic import ValidationError

from app.schemas.image import ImageRegister, ImageReorderItem, SignedUrlRequest


def test_signed_url_request_requires_filename_and_content_type():
    s = SignedUrlRequest(filename="photo.jpg", content_type="image/jpeg")
    assert s.filename == "photo.jpg"


def test_signed_url_request_rejects_unknown_content_type():
    with pytest.raises(ValidationError):
        SignedUrlRequest(filename="photo.pdf", content_type="application/pdf")


def test_image_register_default_sort_order():
    r = ImageRegister(url="https://storage.googleapis.com/bucket/img.jpg")
    assert r.sort_order == 0


def test_reorder_item_has_id_and_sort_order():
    item = ImageReorderItem(id=3, sort_order=1)
    assert item.id == 3
```

- [x] **Step 2：Run test 確認 fail**

Run: `uv run pytest tests/test_schemas_image.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [x] **Step 3：實作 `app/schemas/image.py`**

```python
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


class SignedUrlRequest(BaseModel):
    filename: str
    content_type: str

    @field_validator("content_type")
    @classmethod
    def check_content_type(cls, v: str) -> str:
        if v not in _ALLOWED_CONTENT_TYPES:
            raise ValueError(f"不支援的圖片格式，允許：{_ALLOWED_CONTENT_TYPES}")
        return v


class SignedUrlResponse(BaseModel):
    signed_url: str
    public_url: str


class ImageRegister(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str
    sort_order: int = 0


class AdminImageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    url: str
    sort_order: int


class ImageReorderItem(BaseModel):
    id: int
    sort_order: int


class ImageReorderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[ImageReorderItem]
```

- [x] **Step 4：Run test 確認通過**

Run: `uv run pytest tests/test_schemas_image.py -v`
Expected: PASS（4 passed）。

- [x] **Step 5：Commit**

```bash
git add app/schemas/image.py tests/test_schemas_image.py
git commit -m "feat(backend): image schemas"
```

---

## Task 6：Image Repository

**Files:**
- Create: `app/repositories/image_repo.py`
- Test: `tests/test_image_repo.py`

- [x] **Step 1：寫 failing test** — `tests/test_image_repo.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.product_image import ProductImage
from app.repositories import image_repo, product_repo


async def _seed_product(session: AsyncSession) -> Product:
    p = Product(slug="kanro", name="甘露梨", description="d", season="s")
    return await product_repo.add(session, p)


async def test_add_and_list_by_product(db_session: AsyncSession):
    p = await _seed_product(db_session)
    img = ProductImage(product_id=p.id, url="https://example.com/1.jpg", sort_order=0)
    saved = await image_repo.add(db_session, img)
    assert saved.id is not None

    imgs = await image_repo.list_by_product(db_session, p.id)
    assert len(imgs) == 1
    assert imgs[0].url == "https://example.com/1.jpg"


async def test_get_by_id_returns_none_for_missing(db_session: AsyncSession):
    assert await image_repo.get_by_id(db_session, 999999) is None


async def test_delete_removes_record(db_session: AsyncSession):
    p = await _seed_product(db_session)
    img = await image_repo.add(
        db_session, ProductImage(product_id=p.id, url="https://example.com/2.jpg")
    )
    await image_repo.delete(db_session, img)
    assert await image_repo.get_by_id(db_session, img.id) is None


async def test_list_ordered_by_sort_order(db_session: AsyncSession):
    p = await _seed_product(db_session)
    await image_repo.add(db_session, ProductImage(product_id=p.id, url="b.jpg", sort_order=2))
    await image_repo.add(db_session, ProductImage(product_id=p.id, url="a.jpg", sort_order=1))
    imgs = await image_repo.list_by_product(db_session, p.id)
    assert [i.url for i in imgs] == ["a.jpg", "b.jpg"]
```

- [x] **Step 2：Run test 確認 fail**

Run: `uv run pytest tests/test_image_repo.py -v`

- [x] **Step 3：實作 `app/repositories/image_repo.py`**

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_image import ProductImage


async def list_by_product(session: AsyncSession, product_id: int) -> list[ProductImage]:
    result = await session.execute(
        select(ProductImage)
        .where(ProductImage.product_id == product_id)
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

- [x] **Step 4：Run test 確認通過**

Run: `uv run pytest tests/test_image_repo.py -v`
Expected: PASS（4 passed）。

- [x] **Step 5：Commit**

```bash
git add app/repositories/image_repo.py tests/test_image_repo.py
git commit -m "feat(backend): image repository"
```

---

## Task 7：Image Service

**Files:**
- Create: `app/services/image_service.py`
- Test: `tests/test_image_service.py`

- [x] **Step 1：寫 failing test** — `tests/test_image_service.py`

```python
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.product import Product
from app.repositories import product_repo
from app.schemas.image import ImageRegister, ImageReorderRequest, ImageReorderItem, SignedUrlRequest
from app.services import image_service


async def _seed(session: AsyncSession) -> Product:
    p = Product(slug="kanro", name="甘露梨", description="d", season="s")
    return await product_repo.add(session, p)


@patch("app.services.image_service.gcs_service")
def test_request_sign_returns_signed_url(mock_gcs):
    mock_gcs.enabled = True
    mock_gcs.sign_upload.return_value = {
        "signed_url": "https://signed", "public_url": "https://public/img.jpg"
    }
    result = image_service.request_sign(
        product_id=1, req=SignedUrlRequest(filename="img.jpg", content_type="image/jpeg")
    )
    assert result.signed_url == "https://signed"
    assert result.public_url == "https://public/img.jpg"


@patch("app.services.image_service.gcs_service")
def test_request_sign_raises_when_gcs_disabled(mock_gcs):
    from app.core.exceptions import AppError
    mock_gcs.enabled = False
    with pytest.raises(AppError):
        image_service.request_sign(
            product_id=1, req=SignedUrlRequest(filename="img.jpg", content_type="image/jpeg")
        )


async def test_register_image_saves_to_db(db_session: AsyncSession):
    p = await _seed(db_session)
    img = await image_service.register_image(
        db_session, p.id, ImageRegister(url="https://gcs/img.jpg", sort_order=0)
    )
    assert img.id is not None
    assert img.url == "https://gcs/img.jpg"


async def test_register_image_missing_product_raises(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await image_service.register_image(
            db_session, 999999, ImageRegister(url="https://gcs/img.jpg")
        )


@patch("app.services.image_service.gcs_service")
async def test_delete_image_removes_db_and_calls_gcs(mock_gcs, db_session: AsyncSession):
    mock_gcs.enabled = True
    p = await _seed(db_session)
    img = await image_service.register_image(
        db_session, p.id, ImageRegister(url="https://storage.googleapis.com/b/img.jpg")
    )
    await image_service.delete_image(db_session, img.id)
    mock_gcs.delete_object.assert_called_once_with(
        "https://storage.googleapis.com/b/img.jpg"
    )


async def test_delete_image_missing_raises(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await image_service.delete_image(db_session, 999999)


async def test_reorder_updates_sort_order(db_session: AsyncSession):
    p = await _seed(db_session)
    img_a = await image_service.register_image(
        db_session, p.id, ImageRegister(url="https://gcs/a.jpg", sort_order=0)
    )
    img_b = await image_service.register_image(
        db_session, p.id, ImageRegister(url="https://gcs/b.jpg", sort_order=1)
    )
    req = ImageReorderRequest(items=[
        ImageReorderItem(id=img_a.id, sort_order=1),
        ImageReorderItem(id=img_b.id, sort_order=0),
    ])
    result = await image_service.reorder_images(db_session, p.id, req)
    urls_in_order = [r.url for r in result]
    assert urls_in_order == ["https://gcs/b.jpg", "https://gcs/a.jpg"]
```

- [x] **Step 2：Run test 確認 fail**

Run: `uv run pytest tests/test_image_service.py -v`

- [x] **Step 3：實作 `app/services/image_service.py`**

```python
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, NotFoundError
from app.models.product_image import ProductImage
from app.repositories import image_repo, product_repo
from app.schemas.image import (
    AdminImageRead,
    ImageRegister,
    ImageReorderRequest,
    SignedUrlRequest,
    SignedUrlResponse,
)
from app.services.gcs_service import gcs_service


def request_sign(product_id: int, req: SignedUrlRequest) -> SignedUrlResponse:
    if not gcs_service.enabled:
        raise AppError("GCS 未設定，無法上傳圖片")
    result = gcs_service.sign_upload(product_id, req.filename, req.content_type)
    return SignedUrlResponse(**result)


async def list_images(session: AsyncSession, product_id: int) -> list[AdminImageRead]:
    imgs = await image_repo.list_by_product(session, product_id)
    return [AdminImageRead.model_validate(i) for i in imgs]


async def register_image(
    session: AsyncSession, product_id: int, data: ImageRegister
) -> AdminImageRead:
    product = await product_repo.get_by_id(session, product_id)
    if product is None:
        raise NotFoundError("找不到商品")
    img = ProductImage(product_id=product_id, url=data.url, sort_order=data.sort_order)
    await image_repo.add(session, img)
    await session.commit()
    await session.refresh(img)
    return AdminImageRead.model_validate(img)


async def delete_image(session: AsyncSession, image_id: int) -> None:
    img = await image_repo.get_by_id(session, image_id)
    if img is None:
        raise NotFoundError("找不到圖片")
    url = img.url
    await image_repo.delete(session, img)
    await session.commit()
    if gcs_service.enabled:
        gcs_service.delete_object(url)


async def reorder_images(
    session: AsyncSession, product_id: int, req: ImageReorderRequest
) -> list[AdminImageRead]:
    for item in req.items:
        img = await image_repo.get_by_id(session, item.id)
        if img is not None and img.product_id == product_id:
            img.sort_order = item.sort_order
    await session.commit()
    return await list_images(session, product_id)
```

- [x] **Step 4：Run test 確認通過**

Run: `uv run pytest tests/test_image_service.py -v`
Expected: PASS（8 passed）。

- [x] **Step 5：Commit**

```bash
git add app/services/image_service.py tests/test_image_service.py
git commit -m "feat(backend): image service (sign/register/delete/reorder)"
```

---

## Task 8：Admin Image Routes

**Files:**
- Create: `app/api/routes/admin_images.py`
- Modify: `app/main.py`
- Test: `tests/test_admin_images_api.py`

- [x] **Step 1：寫 failing test** — `tests/test_admin_images_api.py`

```python
from unittest.mock import patch

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.admin_user import AdminUser
from app.models.product import Product
from app.repositories import admin_repo, product_repo


async def _auth(session: AsyncSession) -> dict[str, str]:
    admin = await admin_repo.add(
        session,
        AdminUser(username="miao", hashed_password=hash_password("pw"), is_active=True),
    )
    return {"Authorization": f"Bearer {create_access_token(subject=admin.id)}"}


async def _seed_product(session: AsyncSession) -> Product:
    p = Product(slug="kanro", name="甘露梨", description="d", season="s")
    return await product_repo.add(session, p)


async def test_sign_requires_auth(client: AsyncClient):
    resp = await client.post(
        "/api/admin/uploads/sign",
        json={"filename": "img.jpg", "content_type": "image/jpeg"},
    )
    assert resp.status_code == 401


@patch("app.services.image_service.gcs_service")
async def test_sign_returns_signed_url(mock_gcs, client: AsyncClient, db_session: AsyncSession):
    mock_gcs.enabled = True
    mock_gcs.sign_upload.return_value = {
        "signed_url": "https://signed", "public_url": "https://public/img.jpg"
    }
    headers = await _auth(db_session)
    resp = await client.post(
        "/api/admin/uploads/sign",
        json={"filename": "img.jpg", "content_type": "image/jpeg"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["signed_url"] == "https://signed"


async def test_register_image_201(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth(db_session)
    p = await _seed_product(db_session)
    resp = await client.post(
        f"/api/admin/products/{p.id}/images",
        json={"url": "https://storage.googleapis.com/b/img.jpg", "sort_order": 0},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["url"] == "https://storage.googleapis.com/b/img.jpg"


async def test_list_images(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth(db_session)
    p = await _seed_product(db_session)
    await client.post(
        f"/api/admin/products/{p.id}/images",
        json={"url": "https://gcs/img.jpg", "sort_order": 0},
        headers=headers,
    )
    resp = await client.get(f"/api/admin/products/{p.id}/images", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@patch("app.services.image_service.gcs_service")
async def test_delete_image_204(mock_gcs, client: AsyncClient, db_session: AsyncSession):
    mock_gcs.enabled = True
    mock_gcs.delete_object = lambda url: None
    headers = await _auth(db_session)
    p = await _seed_product(db_session)
    reg = await client.post(
        f"/api/admin/products/{p.id}/images",
        json={"url": "https://gcs/img.jpg", "sort_order": 0},
        headers=headers,
    )
    image_id = reg.json()["id"]
    resp = await client.delete(f"/api/admin/images/{image_id}", headers=headers)
    assert resp.status_code == 204


async def test_reorder_images(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth(db_session)
    p = await _seed_product(db_session)
    r1 = await client.post(
        f"/api/admin/products/{p.id}/images",
        json={"url": "https://gcs/a.jpg", "sort_order": 0},
        headers=headers,
    )
    r2 = await client.post(
        f"/api/admin/products/{p.id}/images",
        json={"url": "https://gcs/b.jpg", "sort_order": 1},
        headers=headers,
    )
    id_a, id_b = r1.json()["id"], r2.json()["id"]
    resp = await client.patch(
        f"/api/admin/products/{p.id}/images/reorder",
        json={"items": [{"id": id_a, "sort_order": 1}, {"id": id_b, "sort_order": 0}]},
        headers=headers,
    )
    assert resp.status_code == 200
    urls = [i["url"] for i in resp.json()]
    assert urls == ["https://gcs/b.jpg", "https://gcs/a.jpg"]
```

- [x] **Step 2：Run test 確認 fail**

Run: `uv run pytest tests/test_admin_images_api.py -v`

- [x] **Step 3：建立 `app/api/routes/admin_images.py`**

```python
from typing import Annotated

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
```

> `sign_upload` 目前傳 `product_id=0` 至 service，因簽發 URL 時 product_id 只影響 blob 路徑的命名，與 DB 無關；若要在 URL 路徑中帶入正確 product_id，可改為路由參數 `POST /products/{product_id}/uploads/sign`——此為設計取捨，目前保持簡單。

- [x] **Step 4：加入 router 至 `app/main.py`**

```python
from app.api.routes import admin_auth, admin_images, admin_orders, admin_products, orders, products
```
```python
    app.include_router(admin_images.router)
```

- [x] **Step 5：Run test + 全套**

Run: `uv run pytest tests/test_admin_images_api.py -v`
Expected: PASS（7 passed）。

Run: `uv run pytest -q && uv run ruff check . && uv run mypy app`
Expected: all green。

- [x] **Step 6：Commit**

```bash
git add app/api/routes/admin_images.py app/main.py tests/test_admin_images_api.py
git commit -m "feat(backend): admin image routes (sign/register/list/delete/reorder)"
```

---

## Task 9：更新公開 Product Schema 與 Service

**Goal:** `PublicProductRead` 和 `AdminProductRead` 的 `image: str` 換成 `images: list[str]`；service mapping 函式改為從 `product.images` 讀取 URL，fallback 至舊的 `product.image`。

**Files:**
- Modify: `app/schemas/product.py`
- Modify: `app/services/product_service.py`
- Modify: `tests/test_product_service.py`（更新 assertions）
- Modify: `tests/test_products_api.py`（更新 assertions）
- Modify: `tests/test_admin_products_api.py`（更新 assertions）
- Test: `tests/test_product_images_public.py`（新增）

- [x] **Step 1：更新 `app/schemas/product.py`**

`PublicProductRead` 和 `AdminProductRead` 中將 `image: str` 改為 `images: list[str]`：

```python
class PublicProductRead(BaseModel):
    id: int
    slug: str
    name: str
    description: str
    images: list[str]          # GCS URLs（或 fallback 單張）
    season: str
    tag: str | None = None
    tag_color: str | None = None
    specs: list[PublicSpecRead]


class AdminProductRead(BaseModel):
    id: int
    slug: str
    name: str
    description: str
    images: list[str]
    season: str
    tag: str | None = None
    tag_color: str | None = None
    is_active: bool
    specs: list[AdminSpecRead]
```

- [x] **Step 2：更新 `app/services/product_service.py` 的 mapping 函式**

修改 `_to_public_product` 和 `_to_admin_product`，加入 images fallback 邏輯：

```python
def _get_images(p: Product) -> list[str]:
    if p.images:
        return [img.url for img in p.images]
    if p.image:
        return [p.image]
    return []
```

在 `_to_public_product` 和 `_to_admin_product` 中將 `image=p.image` 替換為 `images=_get_images(p)`。

- [x] **Step 3：新增 `tests/test_product_images_public.py`**

```python
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.product_image import ProductImage
from app.repositories import product_repo


async def _seed(session: AsyncSession) -> Product:
    p = Product(slug="kanro", name="甘露梨", description="d", season="s")
    p.images = [
        ProductImage(url="https://gcs/1.jpg", sort_order=0),
        ProductImage(url="https://gcs/2.jpg", sort_order=1),
    ]
    return await product_repo.add(session, p)


async def test_public_api_returns_images_list(client: AsyncClient, db_session: AsyncSession):
    await _seed(db_session)
    resp = await client.get("/api/products")
    assert resp.status_code == 200
    product = resp.json()[0]
    assert product["images"] == ["https://gcs/1.jpg", "https://gcs/2.jpg"]


async def test_public_api_fallback_to_legacy_image(client: AsyncClient, db_session: AsyncSession):
    p = Product(
        slug="kanro", name="甘露梨", description="d", season="s",
        image="assets/product_5.jpg",
    )
    await product_repo.add(db_session, p)
    resp = await client.get("/api/products")
    product = resp.json()[0]
    assert product["images"] == ["assets/product_5.jpg"]


async def test_public_api_empty_images_when_no_image(client: AsyncClient, db_session: AsyncSession):
    p = Product(slug="kanro", name="甘露梨", description="d", season="s")
    await product_repo.add(db_session, p)
    resp = await client.get("/api/products")
    product = resp.json()[0]
    assert product["images"] == []
```

- [x] **Step 4：修復既有測試中的 `image` 欄位 assertions**

搜尋所有測試中 `"image"` key 的斷言並改為 `"images"`：

Run: `grep -rn '"image"' tests/`
逐一確認並更新（大多數只是 seeding 不涉及 assert）。

- [x] **Step 5：Run 全套測試**

Run: `uv run pytest -q`
Expected: all pass。

- [x] **Step 6：Commit**

```bash
git add app/schemas/product.py app/services/product_service.py tests/
git commit -m "feat(backend): product images list in public/admin schema (fallback to legacy image)"
```

---

## Task 10：前端後台 — 商品編輯 Modal 圖片 Gallery

**Goal:** 商品編輯 Modal 的圖片欄位改為：顯示已上傳圖片（含刪除）+ 上傳新圖片按鈕（觸發 signed URL 流程）+ 拖曳排序。

**Files:**
- Modify: `frontend/src/api.js`
- Modify: `frontend/src/AdminApp.jsx`
- Modify: `frontend/assets/admin.css`

- [x] **Step 1：`api.js` 加入圖片 API 函式**

```js
// ── Image APIs (admin) ──

export const signUpload = (token, filename, contentType) =>
  adminRequest(token, '/api/admin/uploads/sign', {
    method: 'POST',
    body: JSON.stringify({ filename, content_type: contentType }),
  });

export const listProductImages = (token, productId) =>
  adminRequest(token, `/api/admin/products/${productId}/images`);

export const registerProductImage = (token, productId, url, sortOrder = 0) =>
  adminRequest(token, `/api/admin/products/${productId}/images`, {
    method: 'POST',
    body: JSON.stringify({ url, sort_order: sortOrder }),
  });

export const deleteProductImage = (token, imageId) =>
  adminRequest(token, `/api/admin/images/${imageId}`, { method: 'DELETE' });

export const reorderProductImages = (token, productId, items) =>
  adminRequest(token, `/api/admin/products/${productId}/images/reorder`, {
    method: 'PATCH',
    body: JSON.stringify({ items }),
  });
```

> `adminRequest` 為帶 Authorization header 的 request helper，參照現有 `AdminApp.jsx` 的 API 呼叫模式提取或 inline。

- [x] **Step 2：`AdminApp.jsx` — 新增 `ImageGallery` 元件**

在 `ProductEditModal` 內（或獨立元件）實作：

```jsx
function ImageGallery({ productId, token }) {
  const [images, setImages] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  // 載入圖片列表
  useEffect(() => {
    listProductImages(token, productId).then(setImages).catch(() => {});
  }, [productId, token]);

  // 上傳流程
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
      const newSortOrder = images.length;
      const img = await registerProductImage(token, productId, public_url, newSortOrder);
      setImages(prev => [...prev, img]);
    } catch (err) {
      setError('上傳失敗：' + err.message);
    } finally {
      setUploading(false);
    }
  };

  // 刪除
  const handleDelete = async (imageId) => {
    await deleteProductImage(token, imageId);
    setImages(prev => prev.filter(i => i.id !== imageId));
  };

  return (
    <div className="img-gallery">
      <div className="img-gallery__grid">
        {images.map((img) => (
          <div key={img.id} className="img-gallery__item">
            <img src={img.url} alt="" className="img-gallery__thumb" />
            <button
              className="img-gallery__delete"
              onClick={() => handleDelete(img.id)}
              title="移除"
            >✕</button>
          </div>
        ))}
        {/* 上傳按鈕 */}
        <label className="img-gallery__upload-btn">
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
      {error && <div className="adm-alert">{error}</div>}
    </div>
  );
}
```

- [x] **Step 3：`admin.css` 加入 gallery 樣式**

```css
/* ── Image gallery（商品圖片管理）── */
.img-gallery__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 8px;
}
.img-gallery__item {
  position: relative;
  aspect-ratio: 4/3;
  border-radius: var(--r-sm);
  overflow: hidden;
  border: 1px solid var(--sage-200);
}
.img-gallery__thumb {
  width: 100%; height: 100%;
  object-fit: cover;
}
.img-gallery__delete {
  position: absolute; top: 4px; right: 4px;
  background: rgba(58,45,31,.65); color: #fff;
  border: none; border-radius: 50%;
  width: 22px; height: 22px; font-size: 11px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; opacity: 0; transition: opacity var(--dur-micro);
}
.img-gallery__item:hover .img-gallery__delete { opacity: 1; }
.img-gallery__upload-btn {
  aspect-ratio: 4/3;
  border: 2px dashed var(--sage-300);
  border-radius: var(--r-sm);
  display: flex; align-items: center; justify-content: center;
  font-size: 24px; color: var(--sage-500);
  cursor: pointer; transition: all var(--dur-micro);
}
.img-gallery__upload-btn:hover {
  border-color: var(--sage-600); color: var(--sage-700);
  background: var(--sage-100);
}
```

- [x] **Step 4：整合進商品編輯 Modal**

在 `ProductEditModal`（或現有編輯邏輯）中，於「季節」欄位後加入：
```jsx
<div className="field">
  <label>商品圖片</label>
  <ImageGallery productId={productId} token={token} />
</div>
```

- [x] **Step 5：瀏覽器驗證**

啟動 dev server：`cd frontend && npm run dev`
啟動 backend：`cd backend && uv run uvicorn app.main:app --reload --port 8000`

驗證：
- [x] 開啟後台 `http://localhost:8080/admin`，登入
- [x] 切換到「商品管理」，點「編輯商品」
- [x] 圖片 gallery 正確顯示空狀態（＋ 上傳按鈕）
- [x] 點「＋」選取一張圖片，進度顯示「上傳中…」，完成後縮圖出現在 grid
- [x] hover 縮圖出現 ✕，點擊後縮圖消失
- [x] 重新開啟 Modal，已上傳的圖片仍顯示（DB 持久化確認）

- [x] **Step 6：Commit**

```bash
git add frontend/src/api.js frontend/src/AdminApp.jsx frontend/assets/admin.css
git commit -m "feat(admin): image gallery with GCS upload/delete"
```

---

## Task 11：前台 SpecCard 輪播

**Goal:** `SpecCard` 的單張背景圖改為支援多張圖片的輪播（CSS scroll-snap，無外部 library）。

**Files:**
- Modify: `frontend/src/SpecCard.jsx`
- Modify: `frontend/assets/site.css`

- [x] **Step 1：修改 `SpecCard.jsx`**

```jsx
export const SpecCard = ({ p, spec, onAdd }) => {
  const [qty, setQty] = useState(1);
  const [imgIdx, setImgIdx] = useState(0);
  const disabled = spec.stock === 'out';
  const productSub = p.sub ? p.sub.split(' · ')[1] : p.slug;
  const images = p.images || [];

  return (
    <article className="pcard speccard">
      <div className="pcard__carousel">
        <div className="pcard__slides">
          {images.length > 0 ? images.map((url, i) => (
            <div
              key={i}
              className="pcard__slide"
              style={{ backgroundImage: `url(${url})` }}
            />
          )) : (
            <div className="pcard__slide pcard__slide--empty" />
          )}
        </div>
        <span className="pcard__season">產季 {p.season}</span>
        {images.length > 1 && (
          <div className="pcard__dots">
            {images.map((_, i) => (
              <button
                key={i}
                className={'pcard__dot' + (i === imgIdx ? ' is-active' : '')}
                onClick={() => {
                  setImgIdx(i);
                  document.getElementById(`slide-${spec.id}-${i}`)?.scrollIntoView(
                    { behavior: 'smooth', block: 'nearest', inline: 'center' }
                  );
                }}
              />
            ))}
          </div>
        )}
      </div>
      {/* body 以下保持不變 */}
      <div className="pcard__body">
        {/* ... 原有 body 內容 ... */}
      </div>
    </article>
  );
};
```

> 若使用 scroll-snap 方式，需在 `.pcard__slides` 設 `overflow-x: scroll; scroll-snap-type: x mandatory`，每個 `.pcard__slide` 設 `scroll-snap-align: start`。

- [x] **Step 2：`site.css` 加入輪播樣式**

```css
/* ── SpecCard carousel ── */
.pcard__carousel {
  position: relative;
  overflow: hidden;
  border-radius: var(--r-lg) var(--r-lg) 0 0;
}
.pcard__slides {
  display: flex;
  overflow-x: scroll;
  scroll-snap-type: x mandatory;
  scrollbar-width: none;
}
.pcard__slides::-webkit-scrollbar { display: none; }
.pcard__slide {
  flex: 0 0 100%;
  scroll-snap-align: start;
  aspect-ratio: 4/3;
  background-size: cover;
  background-position: center;
}
.pcard__slide--empty {
  background: var(--sage-100);
}
.pcard__dots {
  position: absolute; bottom: 8px; left: 50%; transform: translateX(-50%);
  display: flex; gap: 5px;
}
.pcard__dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: rgba(255,255,255,.55); border: none; padding: 0; cursor: pointer;
  transition: background var(--dur-micro);
}
.pcard__dot.is-active { background: #fff; }
```

- [x] **Step 3：更新 `api.js` normalizeProduct**

`image` → `images`，配合後端新 schema：

```js
const normalizeProduct = (product) => ({
  id: product.id,
  slug: product.slug,
  name: product.name,
  sub: product.sub || 'Kanro · 蜜糖之味',
  desc: product.description,
  images: product.images || [],
  season: product.season,
  specs: (product.specs || []).map((spec) => ({
    id: spec.id,
    label: spec.label,
    qty: spec.qty_text,
    price: spec.price,
    stock: spec.stock_status,
    stockText: stockText[spec.stock_status] || '狀態確認中',
    note: spec.note,
  })),
});
```

- [x] **Step 4：瀏覽器驗證**

- [x] 前台 `http://localhost:8080/` 載入，單張圖片時輪播正常顯示，無 dot
- [x] 在後台上傳第二張圖片後，重新整理前台，dot 出現，可切換圖片
- [x] 無圖片時 `.pcard__slide--empty`（sage 底色）正確 fallback

- [x] **Step 5：Commit**

```bash
git add frontend/src/SpecCard.jsx frontend/assets/site.css frontend/src/api.js
git commit -m "feat(frontend): product image carousel with CSS scroll-snap"
```

---

## Definition of Done（Phase 5）

- [x] `cd backend && uv run pytest -q` → all pass（既有 129 + 新增：gcs 6、schemas_image 4、image_repo 4、image_service 8、admin_images_api 7、product_images_public 3 = 161 total）
- [x] `cd backend && uv run ruff check .` → clean
- [x] `cd backend && uv run mypy app` → Success
- [x] GCS Bucket 已建立、CORS 已設定、Service Account 已建立
- [x] `POST /api/admin/uploads/sign` 回傳 signed URL；前端可直接 PUT 到 GCS
- [x] 後台 Modal 可上傳多張圖片、刪除、看到縮圖
- [x] 前台輪播正確顯示多張圖片，dot 可切換；單張/無圖片正常 fallback
- [x] `GET /api/products` 回傳 `images: list[str]`（多張或 fallback 舊 `image`）
- [x] `gcs-key.json` 未被 commit
- [x] 所有任務已 commit；plan checkboxes 已勾選

## Next Phase

Phase 6（待定）：前台訂單成立後的狀態追蹤頁面（`GET /api/orders/{order_no}`）+ 後台商品圖片拖曳排序。
