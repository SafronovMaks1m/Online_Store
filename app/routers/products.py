from fastapi import APIRouter
from fastapi import status, Depends
from app.schemas import Product as ProductSchema, ProductCreate
from app.models import Product as ProductModel, Category as CategoryModel
from sqlalchemy.orm import selectinload
from app.db_depends import get_db
from sqlalchemy import select, update
from fastapi import HTTPException
from typing import List
from app.models.users import User as UserModel
from app.auth import get_current_seller

from app.db_depends import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
# Создаём маршрутизатор для товаров
router = APIRouter(
    prefix="/products",
    tags=["products"],
)

@router.post("/", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_seller)
):
    """
    Создаёт новый товар, привязанный к текущему продавцу (только для 'seller').
    """
    category_result = await db.scalars(
        select(CategoryModel).where(CategoryModel.id == product.category_id, CategoryModel.is_active == True)
    )
    if not category_result.first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found or inactive")
    db_product = ProductModel(**product.model_dump(), seller_id=current_user.id)
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)  # Для получения id и is_active из базы
    return db_product


@router.get("/", status_code=status.HTTP_200_OK, response_model=List[ProductSchema])
async def get_products(db: AsyncSession = Depends(get_async_db)) -> List[ProductSchema]:
    stmt = select(ProductModel).where(ProductModel.is_active == True)
    products = await db.scalars(stmt)
    result = products.all()
    return result

@router.get("category/{category_id}", status_code=status.HTTP_200_OK, response_model=List[ProductSchema])
async def get_category_products(category_id: int, db: AsyncSession = Depends(get_async_db)) -> List[ProductSchema]:
    stmt = select(CategoryModel.id).where(CategoryModel.id == category_id, CategoryModel.is_active == True)
    category = await db.scalar(stmt)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    stmt = select(ProductModel).where(ProductModel.category_id == category_id, ProductModel.is_active == True)
    products = await db.scalars(stmt)
    result = products.all()
    return result

@router.get("/{product_id}", status_code=status.HTTP_200_OK, response_model=ProductSchema)
async def get_product(product_id: int, db: AsyncSession = Depends(get_async_db)):
    stmt = select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True).options(selectinload(ProductModel.category))
    temp = await db.scalars(stmt)
    product = temp.first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.category.is_active == False:
        raise HTTPException(status_code=400, detail="Category not found")
    return product
    

@router.put("/{product_id}", response_model=ProductSchema)
async def update_product(
    product_id: int,
    product: ProductCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_seller)
):
    """
    Обновляет товар, если он принадлежит текущему продавцу (только для 'seller').
    """
    result = await db.scalars(select(ProductModel).where(ProductModel.id == product_id))
    db_product = result.first()
    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    if db_product.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only update your own products")
    category_result = await db.scalars(
        select(CategoryModel).where(CategoryModel.id == product.category_id, CategoryModel.is_active == True)
    )
    if not category_result.first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found or inactive")
    await db.execute(
        update(ProductModel).where(ProductModel.id == product_id).values(**product.model_dump())
    )
    await db.commit()
    await db.refresh(db_product)  # Для консистентности данных
    return db_product

@router.delete("/{product_id}", response_model=ProductSchema)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_seller)
):
    """
    Выполняет мягкое удаление товара, если он принадлежит текущему продавцу (только для 'seller').
    """
    result = await db.scalars(
        select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    )
    product = result.first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found or inactive")
    if product.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own products")
    await db.execute(
        update(ProductModel).where(ProductModel.id == product_id).values(is_active=False)
    )
    await db.commit()
    await db.refresh(product)  # Для возврата is_active = False
    return product