import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.billing.models import Plan, FeatureEntitlement

def setup_billing():
    # Create Plans
    starter, _ = Plan.objects.get_or_create(
        slug='starter',
        defaults={
            'name': 'Starter',
            'amount_cents': 2900,
            'interval': 'month'
        }
    )
    
    pro, _ = Plan.objects.get_or_create(
        slug='pro',
        defaults={
            'name': 'Pro',
            'amount_cents': 7900,
            'interval': 'month'
        }
    )
    
    enterprise, _ = Plan.objects.get_or_create(
        slug='enterprise',
        defaults={
            'name': 'Enterprise',
            'amount_cents': 29900,
            'interval': 'month'
        }
    )
    
    # Entitlements
    FeatureEntitlement.objects.get_or_create(plan=starter, feature_key='contacts_limit', defaults={'limit_int': 1000})
    FeatureEntitlement.objects.get_or_create(plan=pro, feature_key='contacts_limit', defaults={'limit_int': 10000})
    FeatureEntitlement.objects.get_or_create(plan=enterprise, feature_key='contacts_limit', defaults={'limit_int': 100000})

    print("Billing plans setup complete.")

if __name__ == "__main__":
    setup_billing()
