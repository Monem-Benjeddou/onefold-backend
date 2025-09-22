from django.db import models
import os

from core.abstract.models import AbstractAutoIncrementModel


class Image(AbstractAutoIncrementModel):
    image = models.ImageField(upload_to="images/")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Image"
        verbose_name_plural = "Images"
        app_label = "core"

    def __str__(self):
        return self.image.url

    @property
    def get_image_absolute_url(self):
        return os.environ.get("MEDIA_URL", "") + self.image.url if self.image else None
