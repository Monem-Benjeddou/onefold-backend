from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from PIL import Image
import os

from core.abstract.models import AbstractAutoIncrementModel
from .managers import FileManager


class File(AbstractAutoIncrementModel):
    name = models.CharField(max_length=200, unique=True)
    file = models.FileField(upload_to="files", max_length=1000)

    objects = FileManager()

    def __str__(self):
        return self.name

    def get_short_name(self):
        return self.name

    class Meta:
        verbose_name_plural = "files"
        ordering = ["name"]

    @property
    def get_file_url(self):
        return self.file.url
