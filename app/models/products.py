from sqlalchemy import String, Boolean, Float, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from categories import Category
    from reviews import Review

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(200), nullable=True)
    stock: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    category: Mapped["Category"] = relationship("Category", back_populates="products")
    seller = relationship("User", back_populates="products")
    reviews: Mapped[list["Review"]] = relationship("Review", uselist=True, back_populates="product")
    rating: Mapped[float] = mapped_column(default=0.0)
    
    async def recalculating_rating(self, db: AsyncSession) -> None:
        from app.models.reviews import Review
        avg_rating = await db.scalar(select(func.avg(Review.grade)).where(Review.product_id == self.id, Review.is_active))
        self.rating = avg_rating or 0.0