import pytest
from apps.accounts.user.models import User

data_admin = {
    "username": "test_admin",
    "email": "test@gmail.com",
    "password": "test_password",
}


@pytest.fixture(scope="class", autouse=True)
def admin() -> User:
    admin = User.objects.create_superuser(**data_admin)
    admin.set_password(data_admin["password"])
    admin.save()
    return admin
