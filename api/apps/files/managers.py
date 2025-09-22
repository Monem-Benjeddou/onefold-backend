from django.db import models


class FileManager(models.Manager):
    def create_file(self, name, path):
        if not name:
            name = self.get_name_by_path(path)

        name = name.title()
        file = self.model(name=name, path=path)
        file.save(using=self._db)

        return file

    def get_name_by_path(self, path):
        return self.get(path=path).name
