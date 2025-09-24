from django.core.management.base import BaseCommand
from apps.company.models import DevelopmentStage


class Command(BaseCommand):
    help = 'Seed development stages data'

    def handle(self, *args, **options):
        """Create default development stages."""
        
        development_stages = [
            {
                'name': 'Pre-Seed/Ideation',
                'description': 'Early stage where the idea is being developed and initial validation is happening.',
                'order': 1,
                'is_active': True
            },
            {
                'name': 'Seed',
                'description': 'Initial funding stage to develop the product and validate the market.',
                'order': 2,
                'is_active': True
            },
            {
                'name': 'Series A',
                'description': 'First major round of venture capital funding to scale the business.',
                'order': 3,
                'is_active': True
            },
            {
                'name': 'Series B',
                'description': 'Second round of venture capital funding for further expansion.',
                'order': 4,
                'is_active': True
            },
            {
                'name': 'Series C',
                'description': 'Third round of venture capital funding for continued growth.',
                'order': 5,
                'is_active': True
            },
            {
                'name': 'Series D',
                'description': 'Fourth round of venture capital funding for advanced scaling.',
                'order': 6,
                'is_active': True
            },
            {
                'name': 'Mezzanine (Pre-IPO)',
                'description': 'Final funding round before going public or being acquired.',
                'order': 7,
                'is_active': True
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for stage_data in development_stages:
            stage, created = DevelopmentStage.objects.get_or_create(
                name=stage_data['name'],
                defaults=stage_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created development stage: {stage.name}')
                )
            else:

                for key, value in stage_data.items():
                    setattr(stage, key, value)
                stage.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated development stage: {stage.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {len(development_stages)} development stages. '
                f'Created: {created_count}, Updated: {updated_count}'
            )
        )
