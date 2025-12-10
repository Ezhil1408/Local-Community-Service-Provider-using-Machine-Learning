from flask import Blueprint, request, jsonify, current_app
import os
import json
import random
from textblob import TextBlob
import requests
from dotenv import load_dotenv
from functools import wraps

# Load environment variables
load_dotenv()

# Initialize the blueprint
chatbot_bp = Blueprint('chatbot', __name__)

# Get Groq API key from environment
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
if not GROQ_API_KEY:
    print("Warning: GROQ_API_KEY not found in environment variables. Using fallback responses.")
    GROQ_API_KEY = ""

# Project context for the chatbot
PROJECT_CONTEXT = {
    "role": "system",
    "content": """You are LocalServe Assistant, an AI helper for a local service provider platform.
    Your purpose is to assist users with:
    - Finding and booking local service providers
    - Understanding how the recommendation system works
    - Answering questions about service categories and providers
    - Explaining verification and review processes
    - Helping with account and booking related queries

    Do not:
    - Answer questions unrelated to local services
    - Share personal opinions or make recommendations outside the platform
    - Provide information not relevant to the LocalServe platform
    - Share personal or sensitive information about users or providers"""
}

# Knowledge base for the chatbot
knowledge_base = {
    'greeting': [
        "Hi there! How can I help you today?",
        "Hello! What can I assist you with?",
        "Hi! I'm here to help you find the best local service providers."
    ],
    'services': [
        "We offer various services including electricians, plumbers, tutors, drivers, and more.",
        "Our platform connects you with professionals like electricians, plumbers, tutors, and drivers.",
        "You can find electricians, plumbers, tutors, drivers, and other local service providers here."
    ],
    'recommendation': [
        "Our system uses machine learning to analyze ratings, reviews, and provider performance to recommend the best matches for your needs.",
        "We use a hybrid recommendation system that combines collaborative filtering and content-based filtering to find the most suitable providers.",
        "The recommendation system considers factors like ratings, reviews, experience, and your preferences to suggest the best local service providers."
    ],
    'verification': [
        "All providers go through a strict verification process including ID verification, background checks, and service history validation.",
        "We verify each provider's identity, qualifications, and work history before they can join our platform.",
        "Our verification process includes document verification, background checks, and previous client reviews to ensure reliability."
    ],
    'booking': [
        "To book a service, simply search for the type of service you need, select a provider, and choose an available time slot.",
        "Booking is easy! Just find your preferred service provider and click on 'Book Now' to see their availability.",
        "You can book a service by selecting a provider, choosing a time that works for you, and confirming your booking."
    ],
    'sentiment': [
        "We analyze reviews using sentiment analysis to understand customer satisfaction and improve our recommendations.",
        "Our sentiment analysis helps us gauge customer experiences and ensure we only recommend highly-rated providers.",
        "We use natural language processing to analyze review sentiment and continuously improve our service quality."
    ],
    'default': [
        "I'm not sure I understand. Could you rephrase that?",
        "I'm here to help with service provider recommendations. Could you be more specific?",
        "I'm designed to assist with finding local service providers. How can I help you with that?"
    ]
}

def analyze_intent(message):
    """Analyze user message to determine intent"""
    if not message or not isinstance(message, str):
        return 'default'
        
    message = message.lower().strip()
    
    # Check for greetings
    if any(word in message for word in ['hi', 'hello', 'hey', 'greetings']):
        return 'greeting'
    
    # Check for booking questions (more specific than services)
    if any(word in message for word in ['book', 'schedule', 'appointment', 'how to hire', 'reserve', 'availability']):
        return 'booking'
        
    # Check for service-related queries
    if any(word in message for word in ['service', 'provide', 'offer', 'available', 'what can you do', 'type of services']):
        return 'services'
    
    # Check for recommendation questions
    if any(word in message for word in ['recommend', 'suggest', 'find', 'how do you choose', 'how does it work', 'best', 'top rated']):
        return 'recommendation'
    
    # Check for verification questions
    if any(word in message for word in ['verify', 'verified', 'trust', 'reliable', 'legit', 'background check']):
        return 'verification'
        
    # Check for account related questions
    if any(word in message for word in ['account', 'login', 'sign up', 'register', 'profile']):
        return 'account'
        
    # Check for pricing questions
    if any(word in message for word in ['price', 'cost', 'how much', 'rate', 'fee']):
        return 'pricing'
        
    # Check for support questions
    if any(word in message for word in ['help', 'support', 'problem', 'issue', 'contact']):
        return 'support'
    
    # Check for sentiment/rating questions
    if any(word in message for word in ['rating', 'review', 'sentiment', 'feedback']):
        return 'sentiment'
    
    return 'default'

def generate_groq_response(prompt):
    """Generate a response using Groq API"""
    if not GROQ_API_KEY:
        # Fallback to knowledge base if API key is not available
        intent = analyze_intent(prompt)
        responses = knowledge_base.get(intent, knowledge_base['default'])
        return random.choice(responses)
        
    headers = {
        'Authorization': f'Bearer {GROQ_API_KEY}',
        'Content-Type': 'application/json',
    }
    
    messages = [
        PROJECT_CONTEXT,
        {"role": "user", "content": prompt}
    ]
    
    try:
        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers=headers,
            json={
                'model': 'mixtral-8x7b-32768',
                'messages': messages,
                'temperature': 0.7,
                'max_tokens': 500,
                'top_p': 1,
                'frequency_penalty': 0,
                'presence_penalty': 0,
            },
            timeout=10  # 10 seconds timeout
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
        else:
            current_app.logger.error(f"Groq API error: {response.status_code} - {response.text}")
            return "I'm having trouble connecting to the AI service. Please try again later."
            
    except Exception as e:
        current_app.logger.error(f"Error in generate_groq_response: {str(e)}")
        # Fallback to knowledge base
        intent = analyze_intent(prompt)
        responses = knowledge_base.get(intent, knowledge_base['default'])
        return random.choice(responses)

@chatbot_bp.route('/api/chat', methods=['POST'])
@chatbot_bp.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages from the frontend"""
    try:
        data = request.get_json()
        if not data or 'message' not in data or not data['message'].strip():
            return jsonify({
                'success': False,
                'error': 'Message is required',
                'response': 'Please provide a message.'
            }), 400
        
        user_message = data['message'].strip()
        
        # First try to handle with our knowledge base
        intent = analyze_intent(user_message)
        if intent != 'default':
            response = random.choice(knowledge_base.get(intent, knowledge_base['default']))
        else:
            # If no specific intent matched, use Groq API
            response = generate_groq_response(user_message)
            if not response:
                response = "I'm having trouble connecting to the AI service. Please try again later."
        
        return jsonify({
            'success': True,
            'response': response
        })
        
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while processing your message.'
        }), 500
