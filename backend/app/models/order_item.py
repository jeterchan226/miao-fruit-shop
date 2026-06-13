from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.order import Order


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[int] = mapped_column()
    spec_id: Mapped[int | None] = mapped_column(default=None)
    product_name: Mapped[str] = mapped_column()
    spec_label: Mapped[str] = mapped_column()
    unit_price: Mapped[int] = mapped_column()
    qty: Mapped[int] = mapped_column()
    line_total: Mapped[int] = mapped_column()

    order: Mapped["Order"] = relationship(back_populates="items")
