from django.core.management.base import BaseCommand
from apps.users.models import Organization
from apps.integrations.models import IntegrationProvider
import secrets

class Command(BaseCommand):
    help = 'Setup TalesTimeline integration for a tenant'

    def add_arguments(self, parser):
        parser.add_argument('org_slug', type=str, help='Slug of the organization')

    def handle(self, *args, **options):
        slug = options['org_slug']
        try:
            org = Organization.objects.get(slug=slug)
            provider, created = IntegrationProvider.objects.get_or_create(
                tenant=org,
                provider_type='tales_timeline',
                defaults={
                    'name': 'TalesTimeline Main',
                    'webhook_secret': secrets.token_hex(16)
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created integration for {org.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Integration already exists for {org.name}'))
            
            self.stdout.write(f"Webhook URL: /api/v1/integrations/tales-timeline/webhook/")
            self.stdout.write(f"Webhook Secret (X-Webhook-Secret): {provider.webhook_secret}")
            
        except Organization.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Organization with slug {slug} not found'))
