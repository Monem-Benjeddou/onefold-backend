from django.urls import reverse

CREATE_USER_URL = reverse("create-user")
UPDATE_USER_URL = lambda pk: reverse("update-user", kwargs={"pk": pk})
DELETE_USER_URL = lambda pk: reverse("delete-user", kwargs={"pk": pk})
LIST_USER_URL = reverse("list-user")
EXPORT_USERS_URL = reverse("export-users")

USER_EMAIL = "testuser@example.com"
USER_USERNAME = "testuser"
USER_PASSWORD = "testpassword123"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "adminpassword123"
ADMIN_USERNAME = "adminuser"
