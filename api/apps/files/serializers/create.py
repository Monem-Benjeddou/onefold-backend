import uuid
from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable
from django.utils.translation import gettext as _

from ..models import File
from ..utils import guess_file_type_by_extension


class CreateFileSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new files.
    Handles file validation and type detection.
    """

    file = serializers.FileField(required=True)

    class Meta:
        model = File
        fields = ["file"]

    def validate_file(self, value):
        """Validate file extension and type."""
        if not value:
            raise serializers.ValidationError(_("File is required."))

        file_extension = value.name.split(".")[-1].lower()
        allowed_extensions = [
            "pdf",
            "docx",
            "doc",
            "xls",
            "xlsx",
            "csv",
            "txt",
            "png",
            "jpg",
            "jpeg",
            "mp4",
            "mp3",
        ]

        if file_extension not in allowed_extensions:
            raise NotAcceptable(
                detail=_("Only %s files are allowed" % ", ".join(allowed_extensions))
            )

        return value

    def create(self, validated_data):
        """Create a new file instance with generated name."""
        file = validated_data["file"]
        file_extension = file.name.split(".")[-1].lower()
        file_name = f"{uuid.uuid4()}.{file_extension}"
        return File.objects.create(file=file, name=file_name)
