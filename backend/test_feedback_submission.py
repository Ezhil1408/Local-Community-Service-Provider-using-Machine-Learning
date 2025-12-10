import requests
import json

# First, let's login as a user to get a session
login_url = "http://127.0.0.1:5000/api/user/login"
login_data = {
    "email": "user1@email.com",
    "password": "User@123"
}

print("Logging in as user...")
session = requests.Session()
login_response = session.post(login_url, json=login_data)
print(f"Login Status: {login_response.status_code}")

if login_response.status_code == 200:
    print("User logged in successfully")
    
    # Get user ID from the response
    user_data = login_response.json()
    user_id = user_data['user']['id']
    print(f"User ID: {user_id}")
    
    # Create a review
    review_url = "http://127.0.0.1:5000/api/reviews"
    review_data = {
        "user_id": user_id,
        "provider_id": 1,
        "rating": 5,
        "comment": "Excellent service! Highly recommended.",
        "booking_id": 5  # Using the booking we created earlier
    }
    
    print("\nSubmitting review...")
    review_response = session.post(review_url, json=review_data)
    print(f"Review submission status: {review_response.status_code}")
    
    if review_response.status_code == 201:
        review_result = review_response.json()
        print("Review submitted successfully!")
        print(f"Review ID: {review_result.get('review', {}).get('id')}")
        print(f"Sentiment: {review_result.get('sentiment', {})}")
    else:
        print(f"Review submission failed: {review_response.json()}")
else:
    print(f"Login failed: {login_response.json()}")