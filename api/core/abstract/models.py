from django.db import models
from django.utils import timezone
import uuid

from .managers import (
    AbstractManager,
    AbstractSlugManager,
    AbstractTimestampManager,
)
from core.utilities.slugify import SlugUtil


class AbstractModelTimeStamp(models.Model):
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    objects = AbstractTimestampManager()

    class Meta:
        abstract = True


class AbstractModel(AbstractModelTimeStamp):
    """
    An abstract model with a id field.
    """

    id = models.UUIDField(
        db_index=True,
        unique=True,
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
    )

    objects = AbstractManager()

    class Meta:
        abstract = True


class AbstractAutoIncrementModel(AbstractModel):
    """
    Abstract model that adds an auto-incrementing _id field.
    This field will increment independently for each table that inherits from this model.
    """

    _id = models.IntegerField(
        db_index=True,
        unique=True,
        editable=False,
        null=True,
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self._id is None:
            from django.db import IntegrityError, connection
            import logging
            import time
            import random

            logger = logging.getLogger(__name__)

            max_retries = 10
            for attempt in range(max_retries):
                try:

                    self._id = self._generate_next_id()

                    super().save(*args, **kwargs)
                    return

                except IntegrityError as e:
                    error_msg = str(e)

                    is_unique_constraint = (
                        "UNIQUE constraint failed" in error_msg
                        or "duplicate key" in error_msg
                        or "violates unique constraint" in error_msg
                    )

                    table_name = self._meta.db_table
                    is_actual_id_column = (
                        f"{table_name}._id" in error_msg
                        or "_id UNIQUE constraint failed" in error_msg
                    )

                    if (
                        is_unique_constraint
                        and is_actual_id_column
                        and attempt < max_retries - 1
                    ):
                        logger.warning(
                            f"_id collision detected for {self.__class__.__name__}, attempt {attempt + 1}/{max_retries}, retrying..."
                        )

                        self._id = None

                        base_delay = 0.01 * (2**attempt)
                        jitter = random.uniform(0, 0.01)
                        delay = base_delay + jitter
                        time.sleep(delay)
                        continue
                    else:

                        raise

            timestamp_id = int(time.time() * 1000000) % 2147483647
            self._id = timestamp_id
            try:
                super().save(*args, **kwargs)
                logger.warning(
                    f"Used timestamp-based fallback _id {self._id} for {self.__class__.__name__}"
                )
                return
            except IntegrityError:
                raise IntegrityError(
                    f"Failed to generate unique _id for {self.__class__.__name__} after {max_retries} attempts"
                )
        else:

            super().save(*args, **kwargs)

    def _generate_next_id(self):
        """
        Generate the next available _id for this model.
        Uses raw SQL to get the maximum ID without nested transactions.
        """
        from django.db import connection, OperationalError, transaction
        from django.db.transaction import TransactionManagementError
        import logging
        import time

        logger = logging.getLogger(__name__)
        table_name = self._meta.db_table

        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT COALESCE(MAX(_id), 0) FROM {table_name}")
                max_id = cursor.fetchone()[0] or 0

                base_id = max_id + 1

                if hasattr(self, "bulk_task") and self.bulk_task:
                    timestamp_component = int(time.time() * 1000) % 1000
                    base_id += timestamp_component

                return base_id
        except (TransactionManagementError, OperationalError) as e:

            timestamp_id = int(time.time() * 1000000) % 2147483647
            logger.info(
                f"Using timestamp-based _id for {self.__class__.__name__}: {timestamp_id} (reason: transaction issues)"
            )
            return timestamp_id
        except Exception as e:
            error_msg = str(e)
            if (
                "no such table" in error_msg
                or "does not exist" in error_msg
                or "transaction is aborted" in error_msg
                or "current transaction is aborted" in error_msg
            ):

                timestamp_id = int(time.time() * 1000000) % 2147483647
                logger.info(
                    f"Using timestamp-based _id for {self.__class__.__name__}: {timestamp_id} (reason: {error_msg[:100]})"
                )
                return timestamp_id
            else:
                raise


class AbstractSlugModel(AbstractAutoIncrementModel):
    """
    Abstract model with a slug field.
    Auto generate and save a slug based on the 'name' field.
    """

    name = models.CharField(max_length=250)
    slug = models.SlugField(
        max_length=200,
        unique=True,
        db_index=True,
        allow_unicode=True,
        blank=True,
    )

    objects = AbstractSlugManager()

    class Meta:
        abstract = True

    def _generate_slug(self):
        """
        Generate a slug based on the 'name' field.
        """
        value = self.name
        self.slug = SlugUtil.slugify(
            value,
            allow_unicode=True,
            unique=True,
            model_class=self.__class__,
            instance_pk=self.pk,
        )

    def save(self, *args, **kwargs):
        self._generate_slug()
        super().save(*args, **kwargs)
