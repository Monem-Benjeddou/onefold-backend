import json
from django.core.management.base import BaseCommand
import os
from django.conf import settings

from apps.privacy.models import PrivacyPolicyPoint


class Command(BaseCommand):
    help = "Seeds the privacy policy points to the database"

    def handle(self, *args, **kwargs):
        if not PrivacyPolicyPoint.objects.exists():
            file_path = "apps/privacy/static/privacies.json"

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                    for item in data:
                        title = item["title"]
                        content = item["content"]
                        order = item["order"]

                        PrivacyPolicyPoint.objects.get_or_create(
                            title=title,
                            defaults={"content": content, "order": order},
                        )

                self.stdout.write(
                    self.style.SUCCESS("Privacy policy points seeded successfully")
                )

            except FileNotFoundError:
                self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            except json.JSONDecodeError:
                self.stdout.write(self.style.ERROR("Error decoding JSON."))
        else:
            self.stdout.write(
                self.style.SUCCESS("Privacy policy points already seeded")
            )
