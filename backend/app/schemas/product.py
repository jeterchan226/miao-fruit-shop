from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from app.schemas.validators import reject_null_required_fields


class PublicSpecRead(BaseModel):
    id: int
    label: str
    qty_text: str
    price: int
    stock_status: str
    note: str | None = None
    images: list[str] = []
    is_two_pack: bool


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
    images: list[str] = []
    is_two_pack: bool


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


PRODUCT_REQUIRED_FIELDS = ("name", "description", "season", "is_active")


class ProductUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None
    image: str | None = None
    season: str | None = None
    tag: str | None = None
    tag_color: str | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def _required_fields_not_null(self) -> Self:
        reject_null_required_fields(self, PRODUCT_REQUIRED_FIELDS)
        return self


class SpecCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    qty_text: str
    price: int
    stock_qty: int
    low_stock_threshold: int = 3
    note: str | None = None
    sort_order: int = 0
    is_two_pack: bool = False


SPEC_REQUIRED_FIELDS = (
    "label",
    "qty_text",
    "price",
    "stock_qty",
    "low_stock_threshold",
    "sort_order",
    "is_active",
    "is_two_pack",
)


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
    is_two_pack: bool | None = None

    @model_validator(mode="after")
    def _required_fields_not_null(self) -> Self:
        reject_null_required_fields(self, SPEC_REQUIRED_FIELDS)
        return self
