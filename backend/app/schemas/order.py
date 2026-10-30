from datetime import date, datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CustomerCreate(BaseModel):
    name: str
    phone: str
    email: str | None = None
    line_user_id: str | None = None
    line_display_name: str | None = None
    line_picture_url: str | None = None
    line_friendship_status: str | None = None
    line_notification_consent: bool = False


class ShippingCreate(BaseModel):
    zipcode: str
    city: str
    district: str
    street: str
    preferred_date: date
    delivery_window: Literal["any", "am", "pm"]


class OrderItemCreate(BaseModel):
    spec_id: int
    qty: int = Field(ge=1)


class OrderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer: CustomerCreate
    shipping: ShippingCreate
    items: list[OrderItemCreate] = Field(min_length=1)
    payment_method: Literal["transfer"] = "transfer"
    note: str | None = None
    expected_total: int = Field(ge=0)


class OrderItemRead(BaseModel):
    spec_id: int | None = None
    product_name: str
    spec_label: str
    unit_price: int
    qty: int
    line_total: int


class OrderRead(BaseModel):
    order_no: str
    status: str
    items: list[OrderItemRead]
    subtotal: int
    shipping_fee: int
    cod_fee: int
    total: int
    created_at: datetime


class PriceChangedResponse(BaseModel):
    """409 PRICE_CHANGED 的回應體(供文件/前端參考)。"""

    detail: str
    code: str = "PRICE_CHANGED"
    subtotal: int
    shipping_fee: int
    cod_fee: int
    total: int


class AdminOrderCreate(BaseModel):
    """代客下單:無 LINE 身份欄位,付款方式固定轉帳。"""

    model_config = ConfigDict(extra="forbid")

    customer_name: str
    customer_phone: str
    customer_email: str | None = None
    shipping: ShippingCreate
    items: list[OrderItemCreate] = Field(min_length=1)
    note: str | None = None
    expected_total: int = Field(ge=0)


class AdminOrderListItem(BaseModel):
    order_no: str
    status: str
    source: str
    customer_name: str
    customer_phone: str
    total: int
    created_at: datetime
    # 商品摘要:首項商品名 + 品項數(供列表 / 新訂單通知卡顯示「甘露梨 禮盒 等 N 項」)
    first_item_name: str | None = None
    item_count: int = 0


class AdminOrderListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AdminOrderListItem]
    status_counts: dict[str, int] = {}


class AdminOrderSummary(BaseModel):
    pending_shipment: int
    total_orders: int
    total_revenue: int


class AdminOrderRead(BaseModel):
    id: int
    order_no: str
    status: str
    source: str
    customer_name: str
    customer_phone: str
    customer_email: str | None
    line_user_id: str | None
    line_display_name: str | None
    line_picture_url: str | None
    line_friendship_status: str | None
    line_notification_consent: bool
    ship_zipcode: str
    ship_city: str
    ship_district: str
    ship_street: str
    preferred_date: date
    delivery_window: str
    payment_method: str
    note: str | None
    transfer_last5: str | None
    transfer_payer_name: str | None
    transfer_note: str | None
    subtotal: int
    shipping_fee: int
    cod_fee: int
    total: int
    items: list[OrderItemRead]
    created_at: datetime
    updated_at: datetime


class OrderStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["pending_payment", "ready", "shipping", "cancelled"]


class AdminOrderItemUpdate(BaseModel):
    spec_id: int
    qty: int = Field(ge=1)


class AdminOrderUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_name: str | None = None
    customer_phone: str | None = None
    customer_email: str | None = None
    ship_zipcode: str | None = None
    ship_city: str | None = None
    ship_district: str | None = None
    ship_street: str | None = None
    preferred_date: date | None = None
    delivery_window: Literal["any", "am", "pm"] | None = None
    note: str | None = None
    # 期望的完整訂單品項清單;只改顧客/收件資訊時不送(R13)
    items: list[AdminOrderItemUpdate] | None = Field(default=None, min_length=1)
    expected_total: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _items_require_expected_total(self) -> Self:
        if self.items is not None and self.expected_total is None:
            raise ValueError("送出訂單品項時須附 expected_total")
        return self


class AdminOrderTransferUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transfer_last5: str | None = None
    transfer_payer_name: str | None = None
    transfer_note: str | None = None
