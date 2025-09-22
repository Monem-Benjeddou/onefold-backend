"""
Factory classes for File model testing.
"""

import factory
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.files.models import File


class FileFactory(factory.django.DjangoModelFactory):
    """Factory for creating File instances."""

    class Meta:
        model = File

    name = factory.Sequence(lambda n: f"test_file_{n}")
    file = factory.LazyAttribute(
        lambda obj: SimpleUploadedFile(
            name=f"{obj.name}.txt",
            content=b"test file content",
            content_type="text/plain",
        )
    )
