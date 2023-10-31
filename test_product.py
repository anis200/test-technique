from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from products import app, get_session, ProductCategory
import models
import pytest


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///./testing.db", connect_args={"check_same_thread": False}
    )
    models.Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_list_products(session: Session, client: TestClient):

    # Adding three rows :
    session.query(models.Product).delete()
    products = [
        models.Product(
            name="mouse",
            description="It's a mouse",
            category=ProductCategory.category1,
            quantity=12,
        ),
        models.Product(
            name="keyboard",
            description="It's a keyboard",
            category=ProductCategory.category2,
            quantity=13,
        ),
        models.Product(
            name="phone",
            description="It's a phone",
            category=ProductCategory.category3,
            quantity=14,
        ),
    ]

    session.add_all(products)
    session.commit()

    response = client.get("/products/")
    assert response.status_code == 200
    assert len(response.json()) == len(products)
    session.query(models.Product).delete()


def test_create_product(session: Session, client: TestClient):

    response = client.post(
        "/products/",
        json={
            "quantity": 13,
            "description": "this is a keyboard",
            "category": "category3",
            "name": "keyboard",
        },
    )

    data = response.json()

    # Try to get the added product
    db_product = (
        session.query(models.Product)
        .filter(
            models.Product.name == data["name"],
            models.Product.category == data["category"],
        )
        .first()
    )

    assert db_product.name == "keyboard"
    assert db_product.category == "category3"
    assert db_product.description == "this is a keyboard"
    assert db_product.quantity == 13
    assert response.status_code == 200

    # Clear Product Table
    session.query(models.Product).delete()


def test_create_product_negative_quantity(session: Session, client: TestClient):

    response = client.post(
        "/products/",
        json={
            "quantity": -10,
            "description": "this is a keyboard",
            "category": "category3",
            "name": "keyboard",
        },
    )

    data = response.json()

    assert response.status_code == 422
    assert data["detail"][0]["msg"] == "Input should be greater than or equal to 0"


def test_create_product_unsupported_category(session: Session, client: TestClient):

    response = client.post(
        "/products/",
        json={
            "quantity": 10,
            "description": "this is a keyboard",
            "category": "category7",
            "name": "keyboard",
        },
    )

    data = response.json()
    print(data)

    assert response.status_code == 422
    assert (
        data["detail"][0]["msg"]
        == "Input should be 'category1', 'category2' or 'category3'"
    )


def test_update_product(session: Session, client: TestClient):

    session.query(models.Product).delete()
    product = models.Product(
        name="phone",
        description="It's a phone",
        category=ProductCategory.category3,
        quantity=14,
    )

    session.add(product)
    session.commit()

    # For example we update it's name to : "my_phone"
    response = client.patch(
        f"/products/{product.id}/",
        json={"name": "zaki"},
    )

    db_product = (
        session.query(models.Product).filter(models.Product.id == product.id).first()
    )

    assert response.status_code == 200
    assert db_product.name == "zaki"
    # assert if the unupdated fields are in the old status
    assert db_product.description == "It's a phone"
    assert db_product.category == "category3"
    assert db_product.quantity == 14


def test_update_product_negative_quantity(session: Session, client: TestClient):

    session.query(models.Product).delete()
    product = models.Product(
        name="phone",
        description="It's a phone",
        category=ProductCategory.category3,
        quantity=14,
    )

    session.add(product)
    session.commit()

    # For example we update it's name to : "my_phone"
    response = client.patch(
        f"/products/{product.id}/",
        json={"quantity": -10},
    )
    data = response.json()

    assert response.status_code == 422
    assert data["detail"][0]["msg"] == "Input should be greater than or equal to 0"


def test_update_product_unsuppoted_category(session: Session, client: TestClient):

    session.query(models.Product).delete()
    product = models.Product(
        name="phone",
        description="It's a phone",
        category=ProductCategory.category3,
        quantity=14,
    )

    session.add(product)
    session.commit()

    # For example we update it's name to : "my_phone"
    response = client.patch(
        f"/products/{product.id}/",
        json={"category": "catee"},
    )
    data = response.json()

    assert response.status_code == 422
    assert (
        data["detail"][0]["msg"]
        == "Input should be 'category1', 'category2' or 'category3'"
    )


def test_delete_product(session: Session, client: TestClient):
    session.query(models.Product).delete()

    product = models.Product(
        name="mouse",
        description="It's a phone",
        category=ProductCategory.category3,
        quantity=14,
    )

    session.add(product)
    session.commit()

    response = client.delete(f"/products/{product.id}")

    db_products = session.query(models.Product).all()

    assert response.status_code == 200
    assert len(db_products) == 0
