from fastapi import APIRouter, status, Depends, HTTPException
from app.schemas import Review, ReviewCreate
from app.models.reviews import Review as ReviewModel
from app.models.users import User as UserModel
from app.models.products import Product as ProductModel
from app.auth import get_current_buyer, get_current_admin
from app.db_depends import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func
from typing import List

router = APIRouter(
    prefix="/reviews",
    tags=["reviews"]
)

@router.get("/", response_model=List[Review], status_code=status.HTTP_200_OK)
async def get_reviews(db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список всех активных отзывов товаров
    """
    temp = await db.scalars(select(ReviewModel).where(ReviewModel.is_active))
    return temp.all()

@router.get("/products/{product_id}/reviews", response_model=List[Review], status_code=status.HTTP_200_OK)
async def get_product_reviews(product_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает активные отзывы товара
    """
    product = await db.scalar(select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active))
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    temp = await db.scalars(select(ReviewModel).where(ReviewModel.product_id == product_id, ReviewModel.is_active))
    return temp.all()

@router.post("/", status_code=status.HTTP_201_CREATED, response_model = Review)
async def create_review(review: ReviewCreate,
                        db: AsyncSession = Depends(get_async_db), 
                        user: UserModel = Depends(get_current_buyer)):
    """
    Создаёт новый отзыв для определённого товара (только для buyer)
    """
    product = await db.scalar(select(ProductModel).where(ProductModel.id == review.product_id, ProductModel.is_active))
    if product is None:
        raise HTTPException(status_code = 404, detail="Product not found")
    user_review = await db.scalar(select(ReviewModel).where(ReviewModel.user_id == user.id, ReviewModel.is_active))
    if user_review:
        raise HTTPException(status_code=409, detail="You have already written a review")
    review_db = ReviewModel(user_id = user.id, **review.model_dump())
    db.add(review_db)
    await db.flush()
    await product.recalculating_rating(db)
    await db.commit()    
    await db.refresh(review_db)
    return review_db

@router.delete("/{review_id}", status_code=status.HTTP_200_OK)
async def delete_review(review_id: int, 
                        db: AsyncSession = Depends(get_async_db), 
                        user: UserModel = Depends(get_current_admin)):
    """
    Выполняет мягкое удаление отзыва по его id, устанавливая is_active = false (только для admin)
    """
    review_db = await db.scalar(select(ReviewModel)
                                .where(ReviewModel.id == review_id, ReviewModel.is_active)
                                .options(selectinload(ReviewModel.product)))
    if review_db is None:
        raise HTTPException(status_code=404, detail="review not found")
    review_db.is_active = False
    await db.flush()
    await review_db.product.recalculating_rating(db)
    await db.commit()
    return {"message": "Review deleted"}
