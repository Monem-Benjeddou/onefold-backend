from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Seed all necessary data for the application'

    def handle(self, *args, **options):
        """Run all seed commands."""
        
        self.stdout.write('Starting to seed all data...')
        
        try:
            # Seed development stages
            self.stdout.write('Seeding development stages...')
            call_command('seed_development_stages')
            
            # Seed revenue models
            self.stdout.write('Seeding revenue models...')
            call_command('seed_revenue_models')
            
            self.stdout.write(
                self.style.SUCCESS('Successfully seeded all data!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error seeding data: {str(e)}')
            )
            raise
