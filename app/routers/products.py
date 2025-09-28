from fastapi import APIRouter
from fastapi import status, Depends
from app.schemas import Product as ProductSchem, ProductCreate
from app.models import Product, Category
from sqlalchemy.orm import Session
from app.db_depends import get_db
from sqlalchemy import select, update
from fastapi import HTTPException
from typing import List
# Создаём маршрутизатор для товаров
router = APIRouter(
    prefix="/products",
    tags=["products"],
)

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ProductSchem)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)) -> ProductSchem:
    stmt = select(Category.id).where(Category.id == product.category_id, Category.is_active == True)
    category = db.scalar(stmt)
    if category is None:
        raise HTTPException(status_code=400, detail="Category not found")
    new_product = Product(**product.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


@router.get("/", status_code=status.HTTP_200_OK, response_model=List[ProductSchem])
async def get_products(db: Session = Depends(get_db)) -> List[ProductSchem]:
    stmt = select(Product).where(Product.is_active == True)
    products = db.scalars(stmt).all()
    return products

@router.get("category/{category_id}", status_code=status.HTTP_200_OK, response_model=List[ProductSchem])
async def get_category_products(category_id: int, db: Session = Depends(get_db)) -> List[ProductSchem]:
    stmt = select(Category.id).where(Category.id == category_id, Category.is_active == True)
    category = db.scalar(stmt)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    stmt = select(Product).where(Product.category_id == category_id, Product.is_active == True)
    products = db.scalars(stmt).all()
    return products

@router.get("/{product_id}", status_code=status.HTTP_200_OK, response_model=ProductSchem)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    stmt = select(Product).where(Product.id == product_id, Product.is_active == True)
    product = db.scalars(stmt).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.category.is_active == False:
        raise HTTPException(status_code=400, detail="Category not found")
    return product
    
@router.put("/{product_id}", status_code=status.HTTP_200_OK, response_model = ProductSchem)
async def update_product(product_id: int, product: ProductCreate, db: Session = Depends(get_db)):
    stmt = select(Product).where(Product.id == product_id, Product.is_active == True)
    db_product = db.scalars(stmt).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    category = db.scalar(select(Category.id).where(Category.id == product.category_id, Category.is_active == True))
    if category is None:
        raise HTTPException(status_code=400, detail="Category not found")
    db.execute(
        update(Product)
        .where(Product.id == product_id)
        .values(**product.model_dump())
    )
    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete('/{product_id}', status_code=status.HTTP_200_OK)
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    stmt = select(Product).where(Product.id == product_id, Product.is_active == True)
    product = db.scalars(stmt).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    product.is_active = False
    db.commit()
    return {"status": "success", "message": "Product marked as inactive"}