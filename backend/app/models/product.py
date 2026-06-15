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
    image: Mapped[str | None] = mapped_column(default=None)  # nullable — GCS 上線後逐步淘汰
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
