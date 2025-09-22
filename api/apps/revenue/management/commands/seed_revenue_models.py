from django.core.management.base import BaseCommand
from apps.revenue.models import RevenueModel


class Command(BaseCommand):
    help = 'Seed revenue models data'

    def handle(self, *args, **options):
        """Create default revenue models."""
        
        revenue_models = [
            {
                'name': 'Subscription (SaaS / Recurring)',
                'description': 'Monthly or annual subscription fees for software or services.',
                'order': 1,
                'is_active': True
            },
            {
                'name': 'Freemium',
                'description': 'Free basic service with premium features available for a fee.',
                'order': 2,
                'is_active': True
            },
            {
                'name': 'Advertising',
                'description': 'Revenue generated through displaying advertisements to users.',
                'order': 3,
                'is_active': True
            },
            {
                'name': 'Commission / Transaction Fee',
                'description': 'Percentage or fixed fee charged on each transaction processed.',
                'order': 4,
                'is_active': True
            },
            {
                'name': 'Marketplace Fee (Take Rate)',
                'description': 'Percentage fee taken from transactions on a marketplace platform.',
                'order': 5,
                'is_active': True
            },
            {
                'name': 'One-Time Purchase',
                'description': 'Single payment for a product or service without recurring fees.',
                'order': 6,
                'is_active': True
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for model_data in revenue_models:
            model, created = RevenueModel.objects.get_or_create(
                name=model_data['name'],
                defaults=model_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created revenue model: {model.name}')
                )
            else:
                # Update existing model
                for key, value in model_data.items():
                    setattr(model, key, value)
                model.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated revenue model: {model.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {len(revenue_models)} revenue models. '
                f'Created: {created_count}, Updated: {updated_count}'
            )
        )
