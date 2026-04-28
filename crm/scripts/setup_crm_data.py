from apps.crm.models import Pipeline, Stage, Company, Contact, Deal
from apps.users.models import Organization, User
import uuid

def setup():
    # Get objects
    org = Organization.objects.first()
    if not org:
        print("No organization found. Please run migrations and create a user/org first.")
        return
        
    user = User.objects.first()
    
    # 1. Create Default Pipeline
    pipeline, created = Pipeline.objects.get_or_create(
        tenant=org,
        name="Standard Sales Pipeline",
        defaults={'is_default': True}
    )
    if created:
        print(f"Created Pipeline: {pipeline.name}")
        
    # 2. Create Stages
    stages = [
        ("New Lead", 0, 10),
        ("Qualified", 1, 30),
        ("Proposal", 2, 60),
        ("Negotiation", 3, 80),
        ("Closed Won", 4, 100),
        ("Closed Lost", 5, 0),
    ]
    
    for name, pos, prob in stages:
        stage, s_created = Stage.objects.get_or_create(
            tenant=org,
            pipeline=pipeline,
            name=name,
            defaults={'position': pos, 'win_probability': prob}
        )
        if s_created:
            print(f"Created Stage: {name}")

    # 3. Create a Demo Company & Contact
    company, _ = Company.objects.get_or_create(
        tenant=org,
        name="Global Tech Inc",
        defaults={'domain': 'globaltech.com', 'owner': user}
    )
    
    contact, _ = Contact.objects.get_or_create(
        tenant=org,
        first_name="John",
        last_name="Doe",
        defaults={'email': 'john@globaltech.com', 'company': company, 'owner': user}
    )
    print("Setup complete.")

setup()
