import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from models import db, User, ServiceProvider, Review, UserProviderInteraction

# Service types and locations (Chennai, India)
SERVICE_TYPES = ['Electrician', 'Plumber', 'Tutor', 'Driver', 'Carpenter', 'Cleaner', 'Gardener', 'Painter']
LOCATIONS = [
    'T Nagar', 'Anna Nagar', 'Velachery', 'Adyar', 'Mylapore',
    'Chromepet', 'Tambaram', 'Porur', 'Guindy', 'Saidapet',
    'Royapettah', 'Egmore', 'Nungambakkam', 'Kodambakkam', 'Ashok Nagar'
]

# Indian names
FIRST_NAMES = [
    'Rajesh', 'Priya', 'Arun', 'Divya', 'Karthik', 'Lakshmi', 'Vijay', 'Anitha',
    'Suresh', 'Meera', 'Kumar', 'Pooja', 'Ravi', 'Deepa', 'Ganesh', 'Kavitha',
    'Manoj', 'Sneha', 'Prakash', 'Saranya', 'Naveen', 'Reshma', 'Arjun', 'Sowmya',
    'Ramesh', 'Nithya', 'Venkat', 'Prema', 'Sanjay', 'Keerthi', 'Dinesh', 'Bhavani'
]
LAST_NAMES = [
    'Kumar', 'Raj', 'Krishnan', 'Murugan', 'Raman', 'Nair', 'Iyer', 'Sharma',
    'Reddy', 'Rao', 'Naidu', 'Pillai', 'Menon', 'Babu', 'Das', 'Gupta',
    'Singh', 'Patel', 'Shah', 'Joshi', 'Desai', 'Kulkarni', 'Chandra', 'Bose'
]

# Sample reviews
POSITIVE_REVIEWS = [
    "Excellent service! Very professional and quick.",
    "Highly recommend! Great work quality.",
    "Amazing experience. Very reliable and trustworthy.",
    "Outstanding service! Will definitely hire again.",
    "Fantastic job! Exceeded my expectations.",
    "Very skilled and professional. Great communication.",
    "Superb quality work. Highly satisfied!",
    "Excellent professional. Very thorough and detail-oriented."
]

NEUTRAL_REVIEWS = [
    "Service was okay. Got the job done.",
    "Average experience. Nothing special.",
    "Work was completed as expected.",
    "Standard service. Fair pricing.",
    "Decent work. Could be better.",
    "Satisfactory service. Met basic requirements."
]

NEGATIVE_REVIEWS = [
    "Very disappointing. Poor quality work.",
    "Not satisfied with the service. Unprofessional.",
    "Terrible experience. Would not recommend.",
    "Poor communication and delayed service.",
    "Unsatisfactory work. Had to hire someone else to fix it.",
    "Not reliable. Missed appointments multiple times."
]


def generate_coordinates(location):
    """Generate realistic coordinates based on Chennai location"""
    # Chennai base coordinates: 13.0827° N, 80.2707° E
    base_coords = {
        'T Nagar': (13.0418, 80.2341),
        'Anna Nagar': (13.0850, 80.2101),
        'Velachery': (12.9750, 80.2212),
        'Adyar': (13.0067, 80.2575),
        'Mylapore': (13.0339, 80.2619),
        'Chromepet': (12.9516, 80.1462),
        'Tambaram': (12.9229, 80.1275),
        'Porur': (13.0358, 80.1560),
        'Guindy': (13.0067, 80.2206),
        'Saidapet': (13.0211, 80.2230),
        'Royapettah': (13.0530, 80.2619),
        'Egmore': (13.0732, 80.2609),
        'Nungambakkam': (13.0569, 80.2424),
        'Kodambakkam': (13.0524, 80.2254),
        'Ashok Nagar': (13.0358, 80.2093)
    }
    
    base_lat, base_lon = base_coords.get(location, (13.0827, 80.2707))
    # Add small random offset
    lat = base_lat + random.uniform(-0.01, 0.01)
    lon = base_lon + random.uniform(-0.01, 0.01)
    return lat, lon


def generate_users(n=50):
    """Generate synthetic user data"""
    users = []
    for i in range(n):
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        location = random.choice(LOCATIONS)
        lat, lon = generate_coordinates(location)
        
        user = User(
            name=name,
            email=f"user{i+1}@email.com",
            phone=f"+91-{random.randint(70000, 99999)}{random.randint(10000, 99999)}",
            location=location,
            latitude=lat,
            longitude=lon
        )
        user.set_password('User@123')  # Default password for demo users
        users.append(user)
    
    return users


def generate_providers(n=100):
    """Generate synthetic service provider data"""
    providers = []
    
    for i in range(n):
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        service_type = random.choice(SERVICE_TYPES)
        location = random.choice(LOCATIONS)
        lat, lon = generate_coordinates(location)
        
        # Generate realistic metrics
        experience_years = random.randint(1, 20)
        total_jobs = random.randint(10, 500)
        completion_rate = random.uniform(0.6, 1.0)
        response_time = random.uniform(0.5, 24.0)  # hours
        rating = random.uniform(2.5, 5.0)
        
        # Generate hourly rate based on service type and experience
        base_rates = {
            'Electrician': 500,
            'Plumber': 450,
            'Tutor': 400,
            'Driver': 350,
            'Carpenter': 550,
            'Cleaner': 300,
            'Gardener': 350,
            'Painter': 500
        }
        base_rate = base_rates.get(service_type, 400)
        # Add experience bonus
        hourly_rate = base_rate + (experience_years * 20)
        # Add some randomness
        hourly_rate = hourly_rate + random.randint(-50, 100)
        
        # Generate UPI ID
        upi_id = f"{name.lower().replace(' ', '')}@okaxis"
        
        # Determine reliability based on metrics (ensure balanced distribution)
        if rating >= 4.2 and completion_rate >= 0.85 and response_time <= 8:
            reliability = "Highly Reliable"
        elif rating >= 3.0 and completion_rate >= 0.65:
            reliability = "Moderately Reliable"
        else:
            reliability = "Low Reliability"
        
        provider = ServiceProvider(
            name=name,
            service_type=service_type,
            email=f"provider{i+1}@service.com",
            phone=f"+91-{random.randint(70000, 99999)}{random.randint(10000, 99999)}",
            location=location,
            latitude=lat,
            longitude=lon,
            experience_years=experience_years,
            rating=round(rating, 2),
            total_jobs=total_jobs,
            completion_rate=round(completion_rate, 2),
            response_time=round(response_time, 2),
            reliability_score=reliability,
            verified=random.choice([True, True, True, False]),  # 75% verified
            hourly_rate=round(hourly_rate, 2),
            upi_id=upi_id,
            qr_code_url=f"/static/qr_codes/{service_type.lower()}_{i+1}.png",
            price_range=f"₹{int(hourly_rate * 0.8)}–₹{int(hourly_rate * 1.5)}"
        )
        providers.append(provider)
    
    return providers


def generate_reviews(users, providers, n=300):
    """Generate synthetic review data"""
    reviews = []
    
    for _ in range(n):
        user = random.choice(users)
        provider = random.choice(providers)
        
        # Rating influences review sentiment
        rating = random.uniform(1, 5)
        
        if rating >= 4.0:
            comment = random.choice(POSITIVE_REVIEWS)
            sentiment_score = random.uniform(0.3, 1.0)
            sentiment_label = "Positive"
        elif rating >= 3.0:
            comment = random.choice(NEUTRAL_REVIEWS)
            sentiment_score = random.uniform(-0.2, 0.3)
            sentiment_label = "Neutral"
        else:
            comment = random.choice(NEGATIVE_REVIEWS)
            sentiment_score = random.uniform(-1.0, -0.2)
            sentiment_label = "Negative"
        
        # Random date in last 6 months
        days_ago = random.randint(0, 180)
        created_at = datetime.utcnow() - timedelta(days=days_ago)
        
        review = Review(
            user_id=user.id,
            provider_id=provider.id,
            rating=round(rating, 1),
            comment=comment,
            sentiment_score=round(sentiment_score, 3),
            sentiment_label=sentiment_label,
            created_at=created_at
        )
        reviews.append(review)
    
    return reviews


def generate_interactions(users, providers, n=500):
    """Generate user-provider interaction data"""
    interactions = []
    interaction_types = ['view', 'contact', 'hire', 'favorite']
    
    for _ in range(n):
        user = random.choice(users)
        provider = random.choice(providers)
        
        interaction = UserProviderInteraction(
            user_id=user.id,
            provider_id=provider.id,
            interaction_type=random.choice(interaction_types),
            interaction_count=random.randint(1, 10),
            last_interaction=datetime.utcnow() - timedelta(days=random.randint(0, 90))
        )
        interactions.append(interaction)
    
    return interactions


def generate_training_data(providers):
    """Generate training data for ML models"""
    data = []
    
    for provider in providers:
        data.append({
            'experience_years': provider.experience_years,
            'rating': provider.rating,
            'total_jobs': provider.total_jobs,
            'completion_rate': provider.completion_rate,
            'response_time': provider.response_time,
            'verified': 1 if provider.verified else 0,
            'reliability': provider.reliability_score
        })
    
    df = pd.DataFrame(data)
    
    # Map reliability to numeric labels
    reliability_map = {
        'Highly Reliable': 2,
        'Moderately Reliable': 1,
        'Low Reliability': 0
    }
    df['reliability_label'] = df['reliability'].map(reliability_map)
    
    return df


def populate_database(app):
    """Populate database with synthetic data"""
    with app.app_context():
        # Drop all tables and recreate
        db.drop_all()
        db.create_all()
        
        print("Generating users...")
        users = generate_users(50)
        db.session.add_all(users)
        db.session.commit()
        
        print("Generating service providers...")
        providers = generate_providers(100)
        db.session.add_all(providers)
        db.session.commit()
        
        print("Generating reviews...")
        reviews = generate_reviews(users, providers, 300)
        db.session.add_all(reviews)
        db.session.commit()
        
        print("Generating interactions...")
        interactions = generate_interactions(users, providers, 500)
        db.session.add_all(interactions)
        db.session.commit()
        
        print("Database populated successfully!")
        print(f"- {len(users)} users")
        print(f"- {len(providers)} service providers")
        print(f"- {len(reviews)} reviews")
        print(f"- {len(interactions)} interactions")
        
        # Generate and save training data
        print("\nGenerating training data...")
        df = generate_training_data(providers)
        df.to_csv('training_data.csv', index=False)
        print("Training data saved to training_data.csv")
        
        return df
