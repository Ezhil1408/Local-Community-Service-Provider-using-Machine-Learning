from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_mail import Mail, Message
from config import Config
from models import db, User, ServiceProvider, Review, UserProviderInteraction, Admin, PasswordResetToken, Booking
from ml_classifier import ReliabilityClassifier
from recommender import HybridRecommender
from sentiment_analyzer import SentimentAnalyzer
from chatbot import chatbot_bp
import os
from utils.email_utils import send_booking_confirmation_email
import json
import random
from functools import wraps
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)
app.config.from_object(Config)
app.config['SECRET_KEY'] = 'smart-community-ml-secret-2025'
app.config['SESSION_TYPE'] = 'filesystem'

# CORS configuration
CORS(app, 
     resources={"/api/*": {"origins": "*"}},
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
)

# Register blueprints
app.register_blueprint(chatbot_bp, url_prefix='/api')

# Flask-Mail configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'your-email@gmail.com')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'your-app-password')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME', 'your-email@gmail.com')

# Initialize extensions
CORS(app, supports_credentials=True)
db.init_app(app)
mail = Mail(app)

# Initialize ML models
classifier = ReliabilityClassifier()
recommender = HybridRecommender()
sentiment_analyzer = SentimentAnalyzer()

# Load models if they exist
if os.path.exists(Config.MODEL_DIR):
    try:
        classifier.load_models(Config.MODEL_DIR)
        recommender.load_model(Config.MODEL_DIR)
        print("✓ ML models loaded successfully")
    except Exception as e:
        print(f"⚠ Could not load models: {e}")
        print("Run initialize script to train models first")


# Authentication decorator
def provider_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'provider_id' not in session:
            return jsonify({'success': False, 'error': 'Provider authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return jsonify({'success': False, 'error': 'Admin authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'User authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def home():
    """API home endpoint"""
    return jsonify({
        'message': 'Smart Local Community Service Provider API',
        'version': '1.0',
        'endpoints': {
            'auth': {
                'admin_login': '/api/admin/login',
                'user_register': '/api/user/register',
                'user_login': '/api/user/login',
                'logout': '/api/logout'
            },
            'providers': '/api/providers',
            'users': '/api/users',
            'reviews': '/api/reviews',
            'classify': '/api/classify_provider',
            'recommend': '/api/recommend_providers',
            'analyze': '/api/analyze_review'
        }
    })


@app.route('/api/provider/login', methods=['POST'])
def provider_login():
    """Provider login endpoint - using name as ID and email as password"""
    data = request.json
    name = data.get('name')
    email = data.get('email')  # Using email as password
    
    # Find provider by name
    provider = ServiceProvider.query.filter_by(name=name).first()
    
    # Check if provider exists and email matches
    if provider and provider.email == email:
        session['provider_id'] = provider.id
        session['is_provider'] = True
        session['is_admin'] = False
        # Make sure session is saved
        session.permanent = True
        session.modified = True
        return jsonify({
            'success': True,
            'message': 'Provider login successful',
            'provider': provider.to_dict()
        })
    
    return jsonify({
        'success': False,
        'error': 'Invalid credentials'
    }), 401


@app.route('/api/provider/register', methods=['POST'])
def provider_register():
    """Provider self-registration endpoint - using name as ID and email as password"""
    data = request.json
    
    # Check if provider with this name already exists
    if ServiceProvider.query.filter_by(name=data['name']).first():
        return jsonify({
            'success': False,
            'error': 'A provider with this name already exists'
        }), 400
    
    # Check if provider with this email already exists
    if ServiceProvider.query.filter_by(email=data['email']).first():
        return jsonify({
            'success': False,
            'error': 'A provider with this email already exists'
        }), 400
    
    # Create new provider
    provider = ServiceProvider(
        name=data['name'],
        service_type=data['service_type'],
        email=data['email'],
        phone=data.get('phone', ''),
        location=data.get('location', 'Chennai'),
        experience_years=data.get('experience_years', 0),
        verified=False  # New providers are not verified by default
    )
    
    db.session.add(provider)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Provider registration successful. You can now login.',
        'provider': provider.to_dict()
    }), 201


@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """Admin login endpoint"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    admin = Admin.query.filter_by(username=username).first()
    
    if admin and admin.check_password(password):
        session['admin_id'] = admin.id
        session['is_admin'] = True
        # Make sure session is saved
        session.permanent = True
        session.modified = True
        return jsonify({
            'success': True,
            'message': 'Admin login successful',
            'admin': admin.to_dict()
        })
    
    return jsonify({
        'success': False,
        'error': 'Invalid credentials'
    }), 401


@app.route('/api/user/register', methods=['POST'])
def user_register():
    """User registration endpoint"""
    data = request.json
    
    # Check if email already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({
            'success': False,
            'error': 'Email already registered'
        }), 400
    
    user = User(
        name=data['name'],
        email=data['email'],
        phone=data.get('phone'),
        location=data.get('location')
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Registration successful',
        'user': user.to_dict()
    }), 201


@app.route('/api/user/login', methods=['POST'])
def user_login():
    """User login endpoint"""
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    if user and user.check_password(password) and user.is_active:
        session['user_id'] = user.id
        session['is_admin'] = False
        # Make sure session is saved
        session.permanent = True
        session.modified = True
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': user.to_dict()
        })
    
    return jsonify({
        'success': False,
        'error': 'Invalid credentials or account inactive'
    }), 401


@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout endpoint"""
    session.clear()
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    })


@app.route('/api/user/profile', methods=['PUT'])
@login_required
def update_profile():
    """Update user profile"""
    data = request.json
    user = User.query.get(session['user_id'])
    
    if not user:
        return jsonify({
            'success': False,
            'error': 'User not found'
        }), 404
    
    # Update allowed fields
    user.name = data.get('name', user.name)
    user.phone = data.get('phone', user.phone)
    user.location = data.get('location', user.location)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Profile updated successfully',
        'user': user.to_dict()
    })


@app.route('/api/user/change-password', methods=['POST'])
def change_password():
    """Change user password"""
    data = request.json
    
    # Check if admin or user
    if 'admin_id' in session:
        user = Admin.query.get(session['admin_id'])
        if not user or not user.check_password(data.get('currentPassword')):
            return jsonify({
                'success': False,
                'error': 'Current password is incorrect'
            }), 401
    elif 'user_id' in session:
        user = User.query.get(session['user_id'])
        if not user or not user.check_password(data.get('currentPassword')):
            return jsonify({
                'success': False,
                'error': 'Current password is incorrect'
            }), 401
    else:
        return jsonify({
            'success': False,
            'error': 'Authentication required'
        }), 401
    
    # Update password
    user.set_password(data.get('newPassword'))
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Password changed successfully'
    })


@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    """Check authentication status"""
    if 'admin_id' in session:
        admin = Admin.query.get(session['admin_id'])
        if admin:
            return jsonify({
                'authenticated': True,
                'is_admin': True,
                'is_provider': False,
                'user': admin.to_dict()
            })
    elif 'provider_id' in session:
        provider = ServiceProvider.query.get(session['provider_id'])
        if provider:
            return jsonify({
                'authenticated': True,
                'is_admin': False,
                'is_provider': True,
                'user': provider.to_dict()
            })
    elif 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({
                'authenticated': True,
                'is_admin': False,
                'is_provider': False,
                'user': user.to_dict()
            })
    
    return jsonify({
        'authenticated': False
    })


# ==================== Provider Endpoints ====================

@app.route('/api/providers', methods=['GET'])
def get_providers():
    """Get all service providers with optional filters"""
    service_type = request.args.get('service_type')
    location = request.args.get('location')
    min_rating = request.args.get('min_rating', type=float)
    
    query = ServiceProvider.query
    
    if service_type:
        query = query.filter_by(service_type=service_type)
    if location:
        query = query.filter_by(location=location)
    if min_rating:
        query = query.filter(ServiceProvider.rating >= min_rating)
    
    providers = query.all()
    
    return jsonify({
        'count': len(providers),
        'providers': [p.to_dict() for p in providers]
    })


@app.route('/api/providers/<int:provider_id>', methods=['GET'])
def get_provider(provider_id):
    """Get single provider by ID"""
    provider = ServiceProvider.query.get_or_404(provider_id)
    
    # Get provider's reviews
    reviews = Review.query.filter_by(provider_id=provider_id).all()
    
    return jsonify({
        'provider': provider.to_dict(),
        'reviews': [r.to_dict() for r in reviews],
        'total_reviews': len(reviews)
    })


@app.route('/api/providers', methods=['POST'])
@admin_required
def create_provider():
    """Create new service provider (Admin only)"""
    data = request.json
    
    provider = ServiceProvider(
        name=data['name'],
        service_type=data['service_type'],
        email=data['email'],
        phone=data.get('phone'),
        location=data.get('location'),
        latitude=data.get('latitude'),
        longitude=data.get('longitude'),
        experience_years=data.get('experience_years', 0),
        verified=data.get('verified', False)
    )
    
    db.session.add(provider)
    db.session.commit()
    
    return jsonify({
        'message': 'Provider created successfully',
        'provider': provider.to_dict()
    }), 201


@app.route('/api/providers/<int:provider_id>', methods=['PUT'])
@admin_required
def update_provider(provider_id):
    """Update service provider (Admin only)"""
    provider = ServiceProvider.query.get_or_404(provider_id)
    data = request.json
    
    provider.name = data.get('name', provider.name)
    provider.service_type = data.get('service_type', provider.service_type)
    provider.email = data.get('email', provider.email)
    provider.phone = data.get('phone', provider.phone)
    provider.location = data.get('location', provider.location)
    provider.latitude = data.get('latitude', provider.latitude)
    provider.longitude = data.get('longitude', provider.longitude)
    provider.experience_years = data.get('experience_years', provider.experience_years)
    provider.verified = data.get('verified', provider.verified)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Provider updated successfully',
        'provider': provider.to_dict()
    })


@app.route('/api/providers/<int:provider_id>', methods=['DELETE'])
@admin_required
def delete_provider(provider_id):
    """Delete service provider (Admin only)"""
    provider = ServiceProvider.query.get_or_404(provider_id)
    
    db.session.delete(provider)
    db.session.commit()
    
    return jsonify({
        'message': 'Provider deleted successfully'
    })


@app.route('/api/service-types', methods=['GET'])
def get_service_types():
    """Get all unique service types"""
    providers = ServiceProvider.query.all()
    service_types = list(set([p.service_type for p in providers]))
    
    return jsonify({
        'service_types': sorted(service_types)
    })


# ==================== User Endpoints ====================

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users"""
    users = User.query.all()
    return jsonify({
        'count': len(users),
        'users': [u.to_dict() for u in users]
    })


@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get single user by ID"""
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())


@app.route('/api/users', methods=['POST'])
def create_user():
    """Create new user"""
    data = request.json
    
    user = User(
        name=data['name'],
        email=data['email'],
        location=data.get('location'),
        latitude=data.get('latitude'),
        longitude=data.get('longitude')
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'message': 'User created successfully',
        'user': user.to_dict()
    }), 201


# ==================== Review Endpoints ====================

@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    """Get all reviews"""
    provider_id = request.args.get('provider_id', type=int)
    user_id = request.args.get('user_id', type=int)
    
    query = Review.query
    
    if provider_id:
        query = query.filter_by(provider_id=provider_id)
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    reviews = query.order_by(Review.created_at.desc()).all()
    
    return jsonify({
        'count': len(reviews),
        'reviews': [r.to_dict() for r in reviews]
    })


@app.route('/api/reviews', methods=['POST'])
def create_review():
    """Create new review with automatic sentiment analysis"""
    data = request.json
    
    # Analyze sentiment
    sentiment_result = sentiment_analyzer.analyze_sentiment(data.get('comment', ''))
    
    review = Review(
        user_id=data['user_id'],
        provider_id=data['provider_id'],
        booking_id=data.get('booking_id'),  # Optional link to booking
        rating=data['rating'],
        comment=data.get('comment'),
        sentiment_score=sentiment_result['polarity'],
        sentiment_label=sentiment_result['sentiment_label']
    )
    
    db.session.add(review)
    
    # Update provider rating
    provider = ServiceProvider.query.get(data['provider_id'])
    if provider:
        all_reviews = Review.query.filter_by(provider_id=provider.id).all()
        avg_rating = sum(r.rating for r in all_reviews + [review]) / (len(all_reviews) + 1)
        provider.rating = round(avg_rating, 2)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Review created successfully',
        'review': review.to_dict(),
        'sentiment': sentiment_result
    }), 201


# ==================== ML Endpoints ====================

@app.route('/api/classify_provider', methods=['POST'])
def classify_provider():
    """Classify provider reliability using ML"""
    data = request.json
    
    try:
        # Use Random Forest by default
        model_type = data.get('model_type', 'rf')
        prediction = classifier.predict(data, model_type=model_type)
        
        return jsonify({
            'success': True,
            'prediction': prediction
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/recommend_providers', methods=['POST'])
def recommend_providers():
    """Get personalized provider recommendations"""
    data = request.json
    
    user_id = data.get('user_id')
    service_type = data.get('service_type')
    n_recommendations = data.get('n_recommendations', 5)
    
    try:
        # Get user location if user_id provided
        user_location = None
        if user_id:
            user = User.query.get(user_id)
            if user and user.latitude and user.longitude:
                user_location = (user.latitude, user.longitude)
        
        # Get all providers
        providers = ServiceProvider.query.all()
        
        # Get recommendations
        recommendations = recommender.hybrid_recommend(
            user_id=user_id,
            providers=providers,
            user_location=user_location,
            service_type=service_type,
            n_recommendations=n_recommendations
        )
        
        return jsonify({
            'success': True,
            'count': len(recommendations),
            'recommendations': [p.to_dict() for p in recommendations]
        })
    except Exception as e:
        # Fallback to simple rating-based recommendation
        query = ServiceProvider.query
        if service_type:
            query = query.filter_by(service_type=service_type)
        
        providers = query.order_by(ServiceProvider.rating.desc()).limit(n_recommendations).all()
        
        return jsonify({
            'success': True,
            'count': len(providers),
            'recommendations': [p.to_dict() for p in providers],
            'note': 'Using fallback recommendation (rating-based)'
        })


@app.route('/api/analyze_review', methods=['POST'])
def analyze_review():
    """Analyze sentiment of a review text"""
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({
            'success': False,
            'error': 'No text provided'
        }), 400
    
    result = sentiment_analyzer.analyze_sentiment(text)
    
    return jsonify({
        'success': True,
        'sentiment': result
    })


@app.route('/api/provider/<int:provider_id>/sentiment_summary', methods=['GET'])
def get_provider_sentiment_summary(provider_id):
    """Get sentiment summary for a provider's reviews"""
    reviews = Review.query.filter_by(provider_id=provider_id).all()
    
    if not reviews:
        return jsonify({
            'success': False,
            'message': 'No reviews found for this provider'
        })
    
    comments = [r.comment for r in reviews if r.comment]
    summary = sentiment_analyzer.get_sentiment_summary(comments)
    
    return jsonify({
        'success': True,
        'provider_id': provider_id,
        'summary': summary
    })


# ==================== Statistics Endpoints ====================

@app.route('/api/stats', methods=['GET'])
def get_statistics():
    """Get overall platform statistics"""
    total_providers = ServiceProvider.query.count()
    total_users = User.query.count()
    total_reviews = Review.query.count()
    
    # Reliability distribution
    reliability_counts = db.session.query(
        ServiceProvider.reliability_score,
        db.func.count(ServiceProvider.id)
    ).group_by(ServiceProvider.reliability_score).all()
    
    # Handle None values in reliability scores
    reliability_dist = {}
    for label, count in reliability_counts:
        key = label if label is not None else 'Unknown'
        reliability_dist[key] = count
    
    # Service type distribution
    service_counts = db.session.query(
        ServiceProvider.service_type,
        db.func.count(ServiceProvider.id)
    ).group_by(ServiceProvider.service_type).all()
    
    # Handle None values in service types
    service_dist = {}
    for service, count in service_counts:
        key = service if service is not None else 'Unknown'
        service_dist[key] = count
    
    # Sentiment distribution
    sentiment_counts = db.session.query(
        Review.sentiment_label,
        db.func.count(Review.id)
    ).group_by(Review.sentiment_label).all()
    
    # Handle None values in sentiment labels
    sentiment_dist = {}
    for label, count in sentiment_counts:
        key = label if label is not None else 'Unknown'
        sentiment_dist[key] = count
    
    return jsonify({
        'total_providers': total_providers,
        'total_users': total_users,
        'total_reviews': total_reviews,
        'reliability_distribution': reliability_dist,
        'service_distribution': service_dist,
        'sentiment_distribution': sentiment_dist
    })


# ==================== Interaction Endpoints ====================

@app.route('/api/interactions', methods=['POST'])
def create_interaction():
    """Track user-provider interaction"""
    data = request.json
    
    # Check if interaction exists
    interaction = UserProviderInteraction.query.filter_by(
        user_id=data['user_id'],
        provider_id=data['provider_id'],
        interaction_type=data['interaction_type']
    ).first()
    
    if interaction:
        interaction.interaction_count += 1
        from datetime import datetime
        interaction.last_interaction = datetime.utcnow()
    else:
        interaction = UserProviderInteraction(
            user_id=data['user_id'],
            provider_id=data['provider_id'],
            interaction_type=data['interaction_type']
        )
        db.session.add(interaction)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Interaction tracked successfully',
        'interaction': interaction.to_dict()
    })


# ==================== Database Initialization ====================

# ==================== Password Reset Endpoints ====================

@app.route('/api/request-password-reset', methods=['POST'])
def request_password_reset():
    """Request password reset link"""
    data = request.json
    email = data.get('email')
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        # Return success even if user doesn't exist (security best practice)
        return jsonify({
            'success': True,
            'message': 'If an account exists with this email, a password reset link has been sent.'
        })
    
    # Generate secure token
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    token = serializer.dumps(email, salt='password-reset-salt')
    
    # Save token to database
    expires_at = datetime.utcnow() + timedelta(minutes=15)
    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=expires_at
    )
    db.session.add(reset_token)
    db.session.commit()
    
    # Send email
    try:
        reset_url = f"http://localhost:3001/reset-password/{token}"
        msg = Message(
            subject="Password Reset Request - Smart Community Service",
            recipients=[email],
            html=f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #7C3AED;">Password Reset Request</h2>
                    <p>Hello {user.name},</p>
                    <p>We received a request to reset your password for your Smart Community Service account.</p>
                    <p>Click the link below to reset your password:</p>
                    <p style="margin: 20px 0;">
                        <a href="{reset_url}" style="background-color: #7C3AED; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                            Reset Password
                        </a>
                    </p>
                    <p>Or copy this link to your browser:</p>
                    <p style="color: #666; word-break: break-all;">{reset_url}</p>
                    <p><strong>This link will expire in 15 minutes.</strong></p>
                    <p>If you didn't request this password reset, please ignore this email.</p>
                    <br>
                    <p>Best regards,<br>Smart Community Service Team</p>
                </body>
            </html>
            """
        )
        mail.send(msg)
    except Exception as e:
        print(f"Email sending failed: {e}")
        # Continue anyway - token is saved in DB
    
    return jsonify({
        'success': True,
        'message': 'If an account exists with this email, a password reset link has been sent.'
    })


@app.route('/api/reset-password/<token>', methods=['POST'])
def reset_password(token):
    """Reset password with token"""
    data = request.json
    new_password = data.get('new_password')
    
    if not new_password:
        return jsonify({
            'success': False,
            'error': 'New password is required'
        }), 400
    
    # Verify token with timestamp
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=900)  # 15 minutes
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Invalid or expired token'
        }), 400
    
    # Check if token exists in database and not used
    reset_token = PasswordResetToken.query.filter_by(token=token, used=False).first()
    if not reset_token:
        return jsonify({
            'success': False,
            'error': 'Invalid or already used token'
        }), 400
    
    # Check if token has expired
    if datetime.utcnow() > reset_token.expires_at:
        return jsonify({
            'success': False,
            'error': 'Token has expired'
        }), 400
    
    # Find user and update password
    user = User.query.get(reset_token.user_id)
    if not user:
        return jsonify({
            'success': False,
            'error': 'User not found'
        }), 404
    
    user.set_password(new_password)
    reset_token.used = True
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Password has been reset successfully'
    })


@app.route('/api/bookings/provider/<int:provider_id>', methods=['GET'])
@provider_required
def get_provider_bookings(provider_id):
    """Get all bookings for a provider"""
    # Ensure provider can only see their own bookings
    if session.get('provider_id') != provider_id:
        return jsonify({
            'success': False,
            'error': 'Unauthorized access'
        }), 403
    
    bookings = Booking.query.filter_by(provider_id=provider_id).order_by(Booking.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'bookings': [booking.to_dict() for booking in bookings]
    })


@app.route('/api/bookings/create', methods=['POST'])
@login_required
def create_booking():
    """Create a new booking"""
    data = request.json
    
    # Validate required fields
    required_fields = ['provider_id', 'date', 'time_slot', 'hours_booked', 'user_upi_id', 'payment_mode']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'error': f'Missing required field: {field}'
            }), 400
    
    # Check if provider exists
    provider = ServiceProvider.query.get(data['provider_id'])
    if not provider:
        return jsonify({
            'success': False,
            'error': 'Service provider not found'
        }), 404
    
    # Check for time slot conflicts
    existing_booking = Booking.query.filter_by(
        provider_id=data['provider_id'],
        date=data['date'],
        time_slot=data['time_slot']
    ).first()
    
    if existing_booking:
        return jsonify({
            'success': False,
            'error': 'This time slot is already booked. Please choose another time.'
        }), 400
    
    # Calculate total amount based on hourly rate and hours booked
    hours_booked = float(data['hours_booked'])
    total_amount = provider.hourly_rate * hours_booked
    
    # Determine payment status based on payment mode
    payment_mode = data.get('payment_mode', 'Online')
    payment_status = 'Paid' if payment_mode == 'Offline' else 'Pending'
    
    # Create booking
    booking = Booking(
        user_id=session['user_id'],
        provider_id=data['provider_id'],
        date=data['date'],
        time_slot=data['time_slot'],
        hours_booked=hours_booked,
        user_upi_id=data['user_upi_id'],
        payment_mode=payment_mode,
        total_amount=total_amount,
        service_description=data.get('service_description', ''),
        status='Booked',
        payment_status=payment_status
    )
    
    db.session.add(booking)
    db.session.commit()
    
    # Send booking confirmation email
    print(f"Attempting to send booking confirmation email for booking ID: {booking.id}")
    user = User.query.get(session['user_id'])
    if user:
        print(f"Found user: {user.name} ({user.email})")
        # Import here to avoid circular imports
        from utils.email_utils import send_booking_confirmation_email
        email_result = send_booking_confirmation_email(
            username=user.name,
            user_email=user.email,
            service_name=provider.service_type,
            provider_name=provider.name,
            booking_date=data['date'],
            booking_id=booking.id,
            time_slot=data['time_slot'],
            booking_charge=booking.total_amount
        )
        # Log the result for debugging
        if email_result:
            print(f"✅ Booking confirmation email sent successfully to {user.email}")
        else:
            print(f"❌ Failed to send booking confirmation email to {user.email}")
    else:
        print(f"❌ User not found for user_id: {session['user_id']}")
    
    return jsonify({
        'success': True,
        'message': 'Booking created successfully',
        'booking': booking.to_dict()
    }), 201


@app.route('/api/bookings/user/<int:user_id>', methods=['GET'])
@login_required
def get_user_bookings(user_id):
    """Get all bookings for a user"""
    # Ensure user can only see their own bookings (unless admin)
    if session.get('user_id') != user_id and not session.get('is_admin'):
        return jsonify({
            'success': False,
            'error': 'Unauthorized access'
        }), 403
    
    bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'bookings': [booking.to_dict() for booking in bookings]
    })


@app.route('/api/bookings/all', methods=['GET'])
@admin_required
def get_all_bookings():
    """Get all bookings (admin only)"""
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'bookings': [booking.to_dict() for booking in bookings]
    })


@app.route('/api/bookings/payment/confirm', methods=['POST'])
@login_required
def confirm_payment():
    """Confirm payment for a booking"""
    data = request.json
    booking_id = data.get('booking_id')
    
    if not booking_id:
        return jsonify({
            'success': False,
            'error': 'Booking ID is required'
        }), 400
    
    booking = Booking.query.get(booking_id)
    
    if not booking:
        return jsonify({
            'success': False,
            'error': 'Booking not found'
        }), 404
    
    # Ensure user can only update their own bookings
    if session.get('user_id') != booking.user_id and not session.get('is_admin'):
        return jsonify({
            'success': False,
            'error': 'Unauthorized access'
        }), 403
    
    # Update payment status
    booking.payment_status = 'Paid'
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Payment confirmed successfully',
        'booking': booking.to_dict()
    })


@app.route('/api/bookings/<int:booking_id>/delay', methods=['PUT'])
@provider_required
def update_booking_delay(booking_id):
    """Update booking with delay notification (provider only)"""
    data = request.json
    delay_reason = data.get('delay_reason')
    estimated_delay = data.get('estimated_delay')  # in minutes
    
    if not delay_reason:
        return jsonify({
            'success': False,
            'error': 'Delay reason is required'
        }), 400
    
    booking = Booking.query.get(booking_id)
    
    if not booking:
        return jsonify({
            'success': False,
            'error': 'Booking not found'
        }), 404
    
    # Ensure provider can only update their own bookings
    if session.get('provider_id') != booking.provider_id:
        return jsonify({
            'success': False,
            'error': 'Unauthorized access'
        }), 403
    
    # Add delay information to booking (we'll store this in service_description for now)
    delay_message = f"[DELAY NOTIFICATION] {delay_reason}"
    if estimated_delay:
        delay_message += f". Estimated delay: {estimated_delay} minutes."
    
    if booking.service_description:
        booking.service_description += f"\n{delay_message}"
    else:
        booking.service_description = delay_message
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Delay notification sent to user',
        'booking': booking.to_dict()
    })


@app.route('/api/bookings/<int:booking_id>/status', methods=['PUT'])
@admin_required
def update_booking_status(booking_id):
    """Update booking status (admin only)"""
    data = request.json
    new_status = data.get('status')
    reason = data.get('reason')  # Optional reason for status change
    
    if not new_status:
        return jsonify({
            'success': False,
            'error': 'Status is required'
        }), 400
    
    if new_status not in ['Booked', 'Approved', 'Completed', 'Cancelled']:
        return jsonify({
            'success': False,
            'error': 'Invalid status'
        }), 400
    
    booking = Booking.query.get(booking_id)
    
    if not booking:
        return jsonify({
            'success': False,
            'error': 'Booking not found'
        }), 404
    
    # Store the old status for comparison
    old_status = booking.status
    
    booking.status = new_status
    db.session.commit()
    
    # Send email notification if status changed to Approved or Cancelled
    if new_status in ['Approved', 'Cancelled'] and new_status != old_status:
        try:
            # Get user and provider details
            user = User.query.get(booking.user_id)
            provider = ServiceProvider.query.get(booking.provider_id)
            
            if user and provider:
                # Import email utility here to avoid circular imports
                from utils.email_utils import send_booking_status_update_email
                
                email_result = send_booking_status_update_email(
                    username=user.name,
                    user_email=user.email,
                    service_name=provider.service_type,
                    provider_name=provider.name,
                    booking_date=booking.date,
                    booking_id=booking.id,
                    time_slot=booking.time_slot,
                    new_status=new_status,
                    reason=reason
                )
                
                if email_result:
                    print(f"✅ Booking status update email sent successfully to {user.email}")
                else:
                    print(f"❌ Failed to send booking status update email to {user.email}")
            else:
                print(f"❌ User or provider not found for booking ID: {booking_id}")
        except Exception as e:
            print(f"Error sending booking status update email: {str(e)}")
    
    return jsonify({
        'success': True,
        'message': 'Booking status updated successfully',
        'booking': booking.to_dict()
    })


@app.route('/api/bookings/available_slots', methods=['GET'])
def get_available_time_slots():
    """Get available time slots for a provider on a specific date"""
    provider_id = request.args.get('provider_id', type=int)
    date = request.args.get('date')
    
    if not provider_id or not date:
        return jsonify({
            'success': False,
            'error': 'Provider ID and date are required'
        }), 400
    
    # Get all possible time slots
    all_time_slots = [
        '09:00 AM - 10:00 AM',
        '10:00 AM - 11:00 AM',
        '11:00 AM - 12:00 PM',
        '12:00 PM - 01:00 PM',
        '02:00 PM - 03:00 PM',
        '03:00 PM - 04:00 PM',
        '04:00 PM - 05:00 PM',
        '05:00 PM - 06:00 PM'
    ]
    
    # Get booked time slots for this provider and date
    booked_bookings = Booking.query.filter_by(
        provider_id=provider_id,
        date=date
    ).all()
    
    # Extract booked time slots
    booked_time_slots = [booking.time_slot for booking in booked_bookings]
    
    # Calculate available time slots
    available_time_slots = [slot for slot in all_time_slots if slot not in booked_time_slots]
    
    return jsonify({
        'success': True,
        'available_slots': available_time_slots,
        'booked_slots': booked_time_slots
    })


# ==================== CLI Commands ====================

@app.cli.command()
def init_db():
    """Initialize the database"""
    db.create_all()
    print("✓ Database initialized")


@app.cli.command()
def populate_db():
    """Populate database with sample data"""
    from data_generator import populate_database
    populate_database(app)


@app.cli.command()
def train_models():
    """Train ML models"""
    from data_generator import generate_training_data
    from ml_classifier import train_and_save_models
    from recommender import train_recommender
    
    # Generate training data
    providers = ServiceProvider.query.all()
    interactions = UserProviderInteraction.query.all()
    
    # Train classifier
    df = generate_training_data(providers)
    df.to_csv('training_data.csv', index=False)
    train_and_save_models('training_data.csv')
    
    # Train recommender
    train_recommender(interactions, providers)
    
    print("\n✓ All models trained and saved successfully")


if __name__ == '__main__':
    app.run(debug=True, port=5000)
