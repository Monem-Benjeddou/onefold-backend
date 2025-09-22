import csv
import os
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.db.models import Field, Q
from apps.accounts.user.models import User


class Command(BaseCommand):
    help = "Export all users to a CSV file with all fields"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=str,
            help="Output file path (default: users_export_YYYY-MM-DD.csv in current directory)",
        )
        parser.add_argument(
            "--roles",
            nargs="+",
            type=str,
            help="Filter by user roles (e.g. --roles admin jury_member)",
        )
        parser.add_argument(
            "--active-only",
            action="store_true",
            help="Export only active users (is_active=True)",
        )
        parser.add_argument(
            "--verified-only",
            action="store_true",
            help="Export only email verified users",
        )
        parser.add_argument(
            "--query",
            type=str,
            help="Filter by username, email, or fullname contains",
        )
        parser.add_argument(
            "--exclude-fields",
            nargs="+",
            type=str,
            help="Exclude specific fields (e.g. --exclude-fields password last_login)",
            default=["password"],
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Limit the number of users exported",
        )

    def handle(self, *args, **options):
        output_file = options.get("output")
        roles = options.get("roles")
        active_only = options.get("active_only")
        verified_only = options.get("verified_only")
        query = options.get("query")
        exclude_fields = options.get("exclude_fields", ["password"])
        limit = options.get("limit")

        if not output_file:
            current_date = datetime.now().strftime("%Y-%m-%d")
            output_file = f"users_export_{current_date}.csv"

        users_query = User.objects.all()

        if roles:
            users_query = users_query.filter(role__in=roles)

        if active_only:
            thirty_days_ago = datetime.now() - timedelta(days=30)
            users_query = users_query.filter(
                Q(last_login__gte=thirty_days_ago) | Q(created__gte=thirty_days_ago)
            )

        if verified_only:
            users_query = users_query.filter(is_email_verified=True)

        if query:
            users_query = users_query.filter(
                Q(username__icontains=query)
                | Q(email__icontains=query)
                | Q(fullname__icontains=query)
            )

        if limit:
            users_query = users_query[:limit]

        all_fields = User._meta.get_fields()
        field_names = []

        for field in all_fields:
            if isinstance(field, Field):
                field_name = field.name
                if exclude_fields is None or field_name not in exclude_fields:
                    field_names.append(field_name)

        field_names.append("total_submissions")
        field_names.append("total_team_memberships")

        total_users = users_query.count()

        self.stdout.write(f"Preparing to export {total_users} users to {output_file}")

        with open(output_file, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=field_names)
            writer.writeheader()

            for i, user in enumerate(users_query, 1):
                user_data = {}

                for field_name in field_names:
                    try:
                        value = getattr(user, field_name)

                        if isinstance(value, datetime):
                            value = value.isoformat()
                        user_data[field_name] = value
                    except (AttributeError, TypeError):
                        user_data[field_name] = None

                writer.writerow(user_data)

                if i % 100 == 0 or i == total_users:
                    self.stdout.write(f"Exported {i}/{total_users} users...")

        file_size = os.path.getsize(output_file) / 1024
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully exported {total_users} users to {output_file} ({file_size:.2f} KB)"
            )
        )
