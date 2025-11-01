from sqlalchemy import ForeignKey
from sqlalchemy import Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from datetime import datetime
from app.database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from users import User
    from products import Product
    
class Review(Base):
    __tablename__ = "reviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    user: Mapped["User"] = relationship("User", uselist=False, back_populates="reviews")
    product: Mapped["Product"] = relationship("Product", uselist=False, back_populates="reviews")
    comment: Mapped[Optional[str]] = mapped_column(Text)
    comment_date: Mapped[datetime] = mapped_column(server_default=func.now())
    grade: Mapped[int] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)