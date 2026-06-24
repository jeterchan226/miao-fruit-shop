from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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


class AdminOrderListItem(BaseModel):
    order_no: str
    status: str
    customer_name: str
    customer_phone: str
    total: int
    created_at: datetime


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
