import re
import uuid
from django.utils.text import slugify as django_slugify


class SlugUtil:
    """
    A utility to convert a string into a slug.
    """

    @staticmethod
    def slugify(
        value, allow_unicode=False, unique=False, model_class=None, instance_pk=None
    ):
        """
        Convert a string into a slug.

        Args:
            value: The value to slugify
            allow_unicode: Whether to allow unicode characters
            unique: Whether to ensure uniqueness (requires model_class)
            model_class: The model class to check for uniqueness against
            instance_pk: The primary key of the current instance (for updates)
        """
        if allow_unicode:

            base_slug = django_slugify(value, allow_unicode=True)
        else:

            value = str(value).lower()
            value = (
                re.sub(r"[^\w\s-]", "", value).encode("ascii", "ignore").decode("utf-8")
            )
            base_slug = re.sub(r"[-\s]+", "-", value).strip("-")

        if not unique or not model_class:
            if unique and not model_class:

                base_slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
            return base_slug

        slug = base_slug
        counter = 1

        while True:

            queryset = model_class.objects.filter(slug=slug)

            if instance_pk:
                queryset = queryset.exclude(pk=instance_pk)

            if not queryset.exists():
                return slug

            slug = f"{base_slug}-{counter}"
            counter += 1

            if counter > 1000:

                return f"{base_slug}-{uuid.uuid4().hex[:8]}"
