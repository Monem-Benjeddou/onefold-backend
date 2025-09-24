from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from core.abstract.models import AbstractAutoIncrementModel

class StartupServiceProduct(AbstractAutoIncrementModel):
    """
    Discrete service/product offered by a startup.
    One-to-many: each service/product belongs to one StartupProfile.
    """

    startup = models.ForeignKey(
        "company.StartupProfile",
        on_delete=models.CASCADE,
        related_name="services_and_products",
        help_text=_("Related startup profile"),
    )
    name = models.CharField(max_length=255, help_text=_("Service/Product name"))
    description = models.TextField(blank=True, help_text=_("Optional description"))
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "company"
        verbose_name = _("Startup Service/Product")
        verbose_name_plural = _("Startup Services/Products")
        db_table = "startup_service_product"

        ordering = ["created", "_id"]
        indexes = [
            models.Index(fields=["startup", "is_active"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.startup.startup_name})"