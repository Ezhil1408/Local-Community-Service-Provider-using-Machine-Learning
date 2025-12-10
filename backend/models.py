from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Float, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Admin(db.Model):
    """Admin model for admin users"""
    __tablename__ = 'admins'
    
    id = db.Column(Integer, primary_key=True)
    username = db.Column(String(80), unique=True, nullable=False)
    password_hash = db.Column(String(200), nullable=False)
    email = db.Column(String(120), unique=True, nullable=False)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email
        }

class User(db.Model):
    """User model for customers"""
    __tablename__ = 'users'
    
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False)
    email = db.Column(String(120), unique=True, nullable=False)
    password_hash = db.Column(String(200), nullable=False)
    phone = db.Column(String(20))
    location = db.Column(String(200))
    latitude = db.Column(Float)
    longitude = db.Column(Float)
    is_active = db.Column(Boolean, default=True)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # Relationships
    reviews = relationship('Review', back_populates='user', cascade='all, delete-orphan')
    interactions = relationship('UserProviderInteraction', back_populates='user', cascade='all, delete-orphan')
    bookings = relationship('Booking', back_populates='user', cascade='all, delete-orphan')
    reset_tokens = relationship('PasswordResetToken', back_populates='user', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude
        }


class ServiceProvider(db.Model):
    """Service provider model"""
    __tablename__ = 'service_providers'
    
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False)
    service_type = db.Column(String(50), nullable=False)  # Electrician, Plumber, Tutor, Driver
    email = db.Column(String(120), unique=True, nullable=False)
    phone = db.Column(String(20))
    location = db.Column(String(200))
    latitude = db.Column(Float)
    longitude = db.Column(Float)
    experience_years = db.Column(Integer, default=0)
    rating = db.Column(Float, default=0.0)
    total_jobs = db.Column(Integer, default=0)
    completion_rate = db.Column(Float, default=0.0)
    response_time = db.Column(Float, default=0.0)  # in hours
    reliability_score = db.Column(String(30))  # Highly Reliable, Moderately Reliable, Low Reliability
    verified = db.Column(db.Boolean, default=False)
    hourly_rate = db.Column(Float, default=500.0)  # Per hour wage in INR
    upi_id = db.Column(String(100))  # UPI ID for payments
    qr_code_url = db.Column(String(200))  # Path to QR code image
    price_range = db.Column(String(50))  # e.g., "₹300–₹1500"
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    reviews = relationship('Review', back_populates='provider', cascade='all, delete-orphan')
    interactions = relationship('UserProviderInteraction', back_populates='provider', cascade='all, delete-orphan')
    bookings = relationship('Booking', back_populates='provider', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'service_type': self.service_type,
            'email': self.email,
            'phone': self.phone,
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'experience_years': self.experience_years,
            'rating': self.rating,
            'total_jobs': self.total_jobs,
            'completion_rate': self.completion_rate,
            'response_time': self.response_time,
            'reliability_score': self.reliability_score,
            'verified': self.verified,
            'hourly_rate': self.hourly_rate,
            'upi_id': self.upi_id,
            'qr_code_url': self.qr_code_url,
            'price_range': self.price_range
        }


class Review(db.Model):
    """Review model for user feedback"""
    __tablename__ = 'reviews'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('users.id'), nullable=False)
    provider_id = db.Column(Integer, ForeignKey('service_providers.id'), nullable=False)
    booking_id = db.Column(Integer, ForeignKey('bookings.id'), nullable=True)  # Link to booking
    rating = db.Column(Float, nullable=False)
    comment = db.Column(Text)
    sentiment_score = db.Column(Float)  # Polarity score from sentiment analysis
    sentiment_label = db.Column(String(20))  # Positive, Neutral, Negative
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='reviews')
    provider = relationship('ServiceProvider', back_populates='reviews')
    booking = relationship('Booking', back_populates='reviews')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'provider_id': self.provider_id,
            'provider_name': self.provider.name if self.provider else None,
            'booking_id': self.booking_id,
            'rating': self.rating,
            'comment': self.comment,
            'sentiment_score': self.sentiment_score,
            'sentiment_label': self.sentiment_label,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class UserProviderInteraction(db.Model):
    """Track user-provider interactions for collaborative filtering"""
    __tablename__ = 'user_provider_interactions'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('users.id'), nullable=False)
    provider_id = db.Column(Integer, ForeignKey('service_providers.id'), nullable=False)
    interaction_type = db.Column(String(50))  # view, contact, hire, favorite
    interaction_count = db.Column(Integer, default=1)
    last_interaction = db.Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='interactions')
    provider = relationship('ServiceProvider', back_populates='interactions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'provider_id': self.provider_id,
            'interaction_type': self.interaction_type,
            'interaction_count': self.interaction_count,
            'last_interaction': self.last_interaction.isoformat() if self.last_interaction else None
        }


class PasswordResetToken(db.Model):
    """Password reset token model"""
    __tablename__ = 'password_reset_tokens'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('users.id'), nullable=False)
    token = db.Column(String(200), unique=True, nullable=False)
    expires_at = db.Column(DateTime, nullable=False)
    used = db.Column(Boolean, default=False)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='reset_tokens')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'used': self.used
        }


class Booking(db.Model):
    """Booking model for service appointments"""
    __tablename__ = 'bookings'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('users.id'), nullable=False)
    provider_id = db.Column(Integer, ForeignKey('service_providers.id'), nullable=False)
    date = db.Column(String(20), nullable=False)  # YYYY-MM-DD format
    time_slot = db.Column(String(20), nullable=False)  # e.g., "10:00 AM - 11:00 AM"
    hours_booked = db.Column(Float, default=1.0)  # Number of hours booked
    user_upi_id = db.Column(String(100))  # User's UPI ID for payment verification
    payment_mode = db.Column(String(20), default='Online')  # Online, Offline
    status = db.Column(String(20), default='Booked')  # Booked, Completed, Cancelled
    payment_status = db.Column(String(20), default='Pending')  # Pending, Paid
    total_amount = db.Column(Float, nullable=False)
    service_description = db.Column(Text)  # Optional description of service needed
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='bookings')
    provider = relationship('ServiceProvider', back_populates='bookings')
    reviews = relationship('Review', back_populates='booking', cascade='all, delete-orphan')
    
    def to_dict(self):
        # Check if this booking has a review
        has_review = len(self.reviews) > 0 if self.reviews else False
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'user_email': self.user.email if self.user else None,
            'user_phone': self.user.phone if self.user else None,
            'provider_id': self.provider_id,
            'provider_name': self.provider.name if self.provider else None,
            'provider_service_type': self.provider.service_type if self.provider else None,
            'provider_phone': self.provider.phone if self.provider else None,
            'provider_upi_id': self.provider.upi_id if self.provider else None,
            'provider_qr_code_url': self.provider.qr_code_url if self.provider else None,
            'date': self.date,
            'time_slot': self.time_slot,
            'hours_booked': self.hours_booked,
            'user_upi_id': self.user_upi_id,
            'payment_mode': self.payment_mode,
            'status': self.status,
            'payment_status': self.payment_status,
            'total_amount': self.total_amount,
            'service_description': self.service_description,
            'has_review': has_review,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
