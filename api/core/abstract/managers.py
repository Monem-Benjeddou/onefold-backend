from django.db import models
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.http import Http404


class AbstractTimestampManager(models.Manager):
    """
    Abstract manager for models with timestamp fields.
    """

    def get_latest(self):
        try:
            instance = self.latest("created")
            return instance
        except (ObjectDoesNotExist, ValueError, TypeError, ValidationError):
            return Http404

    def get_oldest(self):
        try:
            instance = self.earliest("created")
            return instance
        except (ObjectDoesNotExist, ValueError, TypeError, ValidationError):
            return Http404


class AbstractManager(AbstractTimestampManager):
    """
    Abstract manager for models.
    Inherited from AbstractTimestampManager.
    """

    def get_object_by_id(self, id):
        try:
            instance = self.get(id=id)
            return instance
        except (ObjectDoesNotExist, ValueError, TypeError, ValidationError):
            return Http404


class AbstractSlugManager(AbstractManager):
    """
    Manager for models with a slug field.
    Enherited from AbstractManager.
    """

    def get_object_by_slug(self, slug):
        try:
            instance = self.get(slug=slug)
            return instance
        except (ObjectDoesNotExist, ValueError, TypeError, ValidationError):
            return Http404
