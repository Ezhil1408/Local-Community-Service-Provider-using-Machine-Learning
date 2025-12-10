from app import app
from models import db, ServiceProvider

with app.app_context():
    providers = ServiceProvider.query.all()
    print(f"Total providers: {len(providers)}")
    if providers:
        print("First 5 providers:")
        for i, provider in enumerate(providers[:5]):
            print(f"  {i+1}. {provider.name} - {provider.service_type} - {provider.email}")
    else:
        print("No providers found")