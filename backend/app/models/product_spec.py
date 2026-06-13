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

    product: Mapped["Product"] = relationship(back_populates="specs")
