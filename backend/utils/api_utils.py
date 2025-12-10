import os
import json
import time
from functools import wraps
from flask import jsonify, request
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Initialize Groq API configuration
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment variables")

# Rate limiting setup
RATE_LIMIT = int(os.getenv('RATE_LIMIT', 100))
RATE_WINDOW = 60  # seconds
request_timestamps = []

# Define allowed domains and use cases
ALLOWED_DOMAINS = [
    'localhost',  # For development
    'localserve.example.com'  # Your production domain
]

# Define project-specific context
PROJECT_CONTEXT = {
    "role": "system",
    "content": """You are LocalServe Assistant, an AI helper for a local service provider platform.
    Your purpose is to assist users with:
    - Finding and booking local service providers
    - Understanding how the recommendation system works
    - Answering questions about service categories and providers
    - Explaining verification and review processes

    Do not:
    - Answer questions unrelated to local services
    - Share personal opinions or make recommendations outside the platform
    - Provide information not relevant to the LocalServe platform"""
}

def check_rate_limit():
    """Check if the rate limit has been exceeded"""
    global request_timestamps
    now = datetime.now()
    
    # Remove timestamps older than the rate limit window
    request_timestamps = [ts for ts in request_timestamps if now - ts < timedelta(seconds=RATE_WINDOW)]
    
    # Check if we've exceeded the rate limit
    if len(request_timestamps) >= RATE_LIMIT:
        return False
    
    # Add current timestamp and return True
    request_timestamps.append(now)
    return True

def validate_request(f):
    """Decorator to validate API requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check rate limiting
        if not check_rate_limit():
            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded. Please try again later.'
            }), 429
            
        # Check origin header if available
        allowed_domains = os.getenv('ALLOWED_DOMAINS', '').split(',')
        origin = request.headers.get('Origin', '')
        
        if origin and not any(domain.strip() in origin for domain in allowed_domains if domain.strip()):
            return jsonify({
                'success': False,
                'error': 'Unauthorized domain'
            }), 403
            
        # Check for required headers or tokens
        auth_token = request.headers.get('Authorization')
        if not auth_token or not auth_token.startswith('Bearer '):
            return jsonify({
                'success': False,
                'error': 'Missing or invalid authorization token'
            }), 401
            
        return f(*args, **kwargs)
    return decorated_function

def generate_response(prompt, context=None):
    """Generate a response using Groq API with project-specific context"""
    try:
        if context is None:
            context = PROJECT_CONTEXT
            
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        messages = [context]
        
        # Add the user's message
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        data = {
            "model": "mixtral-8x7b-32768",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024,
            "top_p": 0.8,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "stop": None
        }
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30  # 30 seconds timeout
        )
        
        response.raise_for_status()
        result = response.json()
        
        return {
            'success': True,
            'response': result['choices'][0]['message']['content'].strip()
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f"API request failed: {str(e)}"
        }
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        return {
            'success': False,
            'error': f"Failed to parse API response: {str(e)}"
        }
    except Exception as e:
        return {
            'success': False,
            'error': f"An unexpected error occurred: {str(e)}"
        }
