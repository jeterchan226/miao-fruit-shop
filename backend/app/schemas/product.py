from pydantic import BaseModel, ConfigDict


class PublicSpecRead(BaseModel):
    id: int
    label: str
    qty_text: str
    price: int
    stock_status: str
    note: str | None = None


class PublicProductRead(BaseModel):
    id: int
    slug: str
    name: str
    description: str
    images: list[str]
    season: str
    tag: str | None = None
    tag_color: str | None = None
    specs: list[PublicSpecRead]


class AdminSpecRead(BaseModel):
    id: int
    label: str
    qty_text: str
    price: int
    stock_status: str
    note: str | None = None
    stock_qty: int
    low_stock_threshold: int
    sort_order: int
    is_active: bool


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


class ProductUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None
    image: str | None = None
    season: str | None = None
    tag: str | None = None
    tag_color: str | None = None
    is_active: bool | None = None


class SpecCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    qty_text: str
    price: int
    stock_qty: int
    low_stock_threshold: int = 3
    note: str | None = None
    sort_order: int = 0


class SpecUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str | None = None
    qty_text: str | None = None
    price: int | None = None
    stock_qty: int | None = None
    low_stock_threshold: int | None = None
    note: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None
