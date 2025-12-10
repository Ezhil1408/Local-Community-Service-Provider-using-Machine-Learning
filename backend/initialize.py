#!/usr/bin/env python
"""
Initialize the Smart Community Service Provider application
This script sets up the database and trains ML models
"""

from app import app
from models import db, Admin
from data_generator import populate_database
from ml_classifier import train_and_save_models
from recommender import train_recommender
from models import ServiceProvider, UserProviderInteraction
import os


def create_admin():
    """Create default admin user"""
    print("\n[0/3] Creating admin user...")
    
    admin = Admin.query.filter_by(username='admin').first()
    if not admin:
        admin = Admin(
            username='admin',
            email='admin@smartcommunity.com'
        )
        admin.set_password('Admin@123')
        db.session.add(admin)
        db.session.commit()
        print("✓ Admin user created")
        print("  Username: admin")
        print("  Password: Admin@123")
    else:
        print("✓ Admin user already exists")


def main():
    """Main initialization function"""
    print("="*70)
    print(" SMART COMMUNITY SERVICE PROVIDER - INITIALIZATION")
    print("="*70)
    
    with app.app_context():
        # Step 1: Populate database (this creates all tables)
        print("\n[1/3] Populating database with sample data...")
        df = populate_database(app)
        
        # Step 0: Create admin AFTER database population
        create_admin()
        
        # Step 2: Train ML classifier
        print("\n[2/3] Training ML classification models...")
        train_and_save_models('training_data.csv')
        
        # Step 3: Train recommender system
        print("\n[3/3] Training recommendation system...")
        providers = ServiceProvider.query.all()
        interactions = UserProviderInteraction.query.all()
        train_recommender(interactions, providers)
        
    print("\n" + "="*70)
    print(" INITIALIZATION COMPLETE!")
    print("="*70)
    print("\n✓ Database populated with sample data")
    print("✓ ML models trained and saved")
    print("✓ Recommendation engine ready")
    print("\nYou can now run the application:")
    print("  python app.py")
    print("\nAPI will be available at: http://localhost:5000")
    print("="*70)


if __name__ == "__main__":
    main()
