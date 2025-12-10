from app import app
from models import db, ServiceProvider

with app.app_context():
    # Find a specific provider to test login
    provider = ServiceProvider.query.filter_by(name="Rajesh Kumar").first()
    if provider:
        print(f"Found provider: {provider.name}")
        print(f"Email: {provider.email}")
        print(f"Service Type: {provider.service_type}")
        print(f"Hourly Rate: ₹{provider.hourly_rate}")
        print(f"UPI ID: {provider.upi_id}")
    else:
        print("Provider 'Rajesh Kumar' not found")
        # List first few providers
        providers = ServiceProvider.query.limit(5).all()
        print("First 5 providers in database:")
        for p in providers:
            print(f"  - {p.name} ({p.email})")