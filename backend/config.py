import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'smart-community-ml-2025'
    
    # Database configuration - using SQLite for easier setup (can switch to MySQL)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///community_service.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # ML Model paths
    MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
    RELIABILITY_MODEL_PATH = os.path.join(MODEL_DIR, 'reliability_classifier.pkl')
    RECOMMENDATION_MODEL_PATH = os.path.join(MODEL_DIR, 'recommender.pkl')
    
    # CORS settings
    CORS_HEADERS = 'Content-Type'
