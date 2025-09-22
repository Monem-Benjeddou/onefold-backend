import pytest
from django.core.files import File as DjangoFile

from apps.products.models import Category, Product
from apps.files.models import File
from apps.accounts.user.models import User
from .user import user


@pytest.fixture(scope="class", autouse=True)
def category():
    return Category.objects.create(name="TestCategory")


@pytest.fixture(scope="class", autouse=True)
def product():
    with open("apps/products/tests/static/image.png", "rb") as image:
        image = File.objects.create(name="TestImage", file=DjangoFile(image))
        product = Product.objects.create(
            name="TestProduct",
            seller=User.objects.create(
                username="TestSeller",
                email="testseller@gmail.com",
                password="testpassword",
            ),
            category=Category.objects.create(name="TestCategory2"),
            serial_number="12345",
            total_pages=45,
            publication_date="2021-01-01",
            book_cover="paperback",
            description="Test description",
            price=100.00,
            weight=1.5,
            quantity=10,
        )
        product.images.add(image)
    return product
