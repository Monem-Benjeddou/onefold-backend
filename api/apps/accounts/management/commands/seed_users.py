from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Seed the database with fake users"

    def add_arguments(self, parser):
        parser.add_argument("count", type=int, nargs="?", default=10, help="Number of users to create")

    def handle(self, *args, **options):
        User = get_user_model()
        count = options["count"]
        created = 0
        for i in range(count):
            email = f"user{i+1}@example.com"
            if not User.objects.filter(email=email).exists():
                User.objects.create_user(email=email, password="password123", role="member")
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Created {created} users"))


