from rest_framework import serializers

from ..models import File
from ..utils import guess_file_type_by_extension


class FileSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving file information.
    Used for basic file info without extended fields.
    """

    type = serializers.SerializerMethodField()
    file = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = ["id", "_id", "file", "type"]
        read_only_fields = ["id", "_id", "file", "type"]

    def get_type(self, obj):
        """Get file type based on extension."""
        return guess_file_type_by_extension(obj.file.name)

    def get_file(self, obj):
        """Get complete file URL."""
        request = self.context.get("request")
        if obj.file and hasattr(obj.file, "url"):
            if request:
                return request.build_absolute_uri(obj.file.url)

            return obj.file.url
        return None


class ExtendedFileSerializer(serializers.ModelSerializer):
    """
    Extended serializer for file listing and creation views.
    Standardized to return only: id, file, type
    """

    type = serializers.SerializerMethodField()
    file = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = ["id", "_id", "file", "type"]
        read_only_fields = ["id", "_id", "file", "type"]

    def get_type(self, obj):
        """Get file type based on extension."""
        return guess_file_type_by_extension(obj.file.name)

    def get_file(self, obj):
        """Get complete file URL."""
        request = self.context.get("request")
        if obj.file and hasattr(obj.file, "url"):
            if request:
                return request.build_absolute_uri(obj.file.url)

            return obj.file.url
        return None
