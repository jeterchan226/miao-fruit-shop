from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.order_item import OrderItem


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_no: Mapped[str] = mapped_column(unique=True, index=True)
    status: Mapped[str] = mapped_column()
    customer_name: Mapped[str] = mapped_column()
    customer_phone: Mapped[str] = mapped_column()
    customer_email: Mapped[str | None] = mapped_column(default=None)
    line_user_id: Mapped[str | None] = mapped_column(index=True, default=None)
    line_display_name: Mapped[str | None] = mapped_column(default=None)
    line_picture_url: Mapped[str | None] = mapped_column(Text, default=None)
    line_friendship_status: Mapped[str | None] = mapped_column(default=None)
    line_notification_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    ship_zipcode: Mapped[str] = mapped_column()
    ship_city: Mapped[str] = mapped_column()
    ship_district: Mapped[str] = mapped_column()
    ship_street: Mapped[str] = mapped_column()
    preferred_date: Mapped[date] = mapped_column()
    delivery_window: Mapped[str] = mapped_column()
    payment_method: Mapped[str] = mapped_column()
    note: Mapped[str | None] = mapped_column(Text, default=None)
    subtotal: Mapped[int] = mapped_column()
    shipping_fee: Mapped[int] = mapped_column()
    cod_fee: Mapped[int] = mapped_column()
    total: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        lazy="selectin",
        order_by="OrderItem.id",
        cascade="all, delete-orphan",
    )
