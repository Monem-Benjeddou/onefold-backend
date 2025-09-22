import pytest
from apps.accounts.user.models import User

data_user = {
    "username": "test_user",
    "email": "test@gmail.com",
    "password": "test_password",
}

other_user_data = {
    "username": "other_user",
    "email": "other_user@other_user.com",
    "password": "other_user_password",
}


@pytest.fixture(scope="class", autouse=True)
def user() -> User:
    user = User.objects.create(**data_user)
    user.set_password(data_user["password"])
    user.save()
    return user


@pytest.fixture(scope="class", autouse=True)
def other_user() -> User:
    user = User.objects.create(**other_user_data)
    user.set_password(other_user_data["password"])
    user.save()
    return user
