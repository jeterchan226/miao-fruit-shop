from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CustomerCreate(BaseModel):
    name: str
    phone: str
    email: str | None = None


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
    payment_method: Literal["linepay", "card", "atm", "cod"]
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
