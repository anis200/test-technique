from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, conint, constr
import models
from enum import Enum
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


engine = create_engine(
    "sqlite:///./product.db", connect_args={"check_same_thread": False}
)

models.Base.metadata.create_all(bind=engine)


def get_session():
    with Session(engine) as db:
        yield db


app = FastAPI()


class ProductCategory(str, Enum):
    category1 = "category1"
    category2 = "category2"
    category3 = "category3"


class Product(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: str = Field(min_length=3)
    category: ProductCategory
    quantity: int = Field(ge=0)


class ProductUpdate(BaseModel):
    name: constr(min_length=3, max_length=100) = None
    description: constr(min_length=3) = None
    category: ProductCategory = None
    quantity: conint(ge=0) = None


@app.get("/products/")
async def list_products(db: Session = Depends(get_session)):
    return db.query(models.Product).all()


@app.post("/products/")
async def add_product(product: Product, db: Session = Depends(get_session)):
    # db_product = (
    #     db.query(models.Product).filter(models.Product.name == product.name).first()
    # )
    # if db_product is not None:
    #     raise HTTPException(status_code=500, detail="Product already exists")

    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    return product


@app.patch("/products/{product_id}/")
async def update_product(
    product_id: int, product: ProductUpdate, db: Session = Depends(get_session)
):
    db_product = (
        db.query(models.Product).filter(models.Product.id == product_id).first()
    )

    if db_product is None:
        raise HTTPException(status_code=404, detail="Product doesn't exist")

    # Permit Partial Update
    updated_data = product.model_dump(exclude_unset=True)
    for field, value in updated_data.items():
        setattr(db_product, field, value)

    db.commit()
    db.refresh(db_product)

    return db_product


@app.delete("/products/{product_id}/")
async def delete_product(product_id: int, db: Session = Depends(get_session)):

    db_product = (
        db.query(models.Product).filter(models.Product.id == product_id).first()
    )

    if db_product is None:
        raise HTTPException(status_code=404, detail="Product doesn't exist")

    db.delete(db_product)
    db.commit()

    return db_product
