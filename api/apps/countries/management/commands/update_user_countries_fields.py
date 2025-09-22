import re
import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from apps.accounts.user.models import User
from apps.countries.models import Country

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Update user country fields based on their phone numbers"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run the command without making actual changes",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)

        if dry_run:
            self.stdout.write(
                self.style.WARNING("Running in dry-run mode. No changes will be made.")
            )

        users = User.objects.filter(
            Q(country__isnull=True)
            & ~Q(phone_number__isnull=True)
            & ~Q(phone_number="")
        )

        total_users = users.count()
        success_count = 0
        failure_count = 0

        self.stdout.write(
            f"Found {total_users} users with phone numbers but no country"
        )

        countries = Country.objects.exclude(
            Q(phone_code__isnull=True) | Q(phone_code="")
        )

        phone_code_map = {}
        for country in countries:
            phone_code_map[country.phone_code] = country

        for user in users:
            try:
                phone_number = user.phone_number.strip()

                country = self._guess_country_from_phone(phone_number, phone_code_map)

                if country:
                    if not dry_run:
                        with transaction.atomic():
                            user.country = country
                            user.save(update_fields=["country"])

                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Updated user {user.id} ({user.username}) with country {country.name} based on phone number {phone_number}"
                        )
                    )
                else:
                    failure_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"Could not determine country for user {user.id} ({user.username}) with phone number {phone_number}"
                        )
                    )
            except Exception as e:
                failure_count += 1
                logger.error(f"Error updating user {user.id}: {str(e)}")
                self.stdout.write(
                    self.style.ERROR(
                        f"Error updating user {user.id} ({user.username}): {str(e)}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Completed updating user countries. "
                f"Success: {success_count}, Failures: {failure_count}, Total: {total_users}"
            )
        )

    def _guess_country_from_phone(self, phone_number, phone_code_map):
        clean_number = re.sub(r"\D", "", phone_number)

        for i in range(min(4, len(clean_number)), 0, -1):
            prefix = clean_number[:i]

            if prefix in phone_code_map:
                return phone_code_map[prefix]

            if "+" + prefix in phone_code_map:
                return phone_code_map["+" + prefix]

        if clean_number.startswith("0") and len(clean_number) > 1:
            return self._guess_country_from_phone(clean_number[1:], phone_code_map)

        if phone_number.startswith("+"):
            pass

        return None
