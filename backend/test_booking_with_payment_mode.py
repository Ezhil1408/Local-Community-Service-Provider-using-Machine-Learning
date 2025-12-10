import requests
import json
from datetime import datetime, timedelta

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
    
    # Create a booking with payment mode
    booking_url = "http://127.0.0.1:5000/api/bookings/create"
    
    # Calculate a future date to avoid conflicts
    future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    
    booking_data = {
        "provider_id": 1,
        "date": future_date,
        "time_slot": "10:00 AM - 11:00 AM",
        "hours_booked": 2.5,
        "user_upi_id": "testuser@okaxis",
        "payment_mode": "Online",  # This is the new field
        "service_description": "Testing payment mode functionality"
    }
    
    print("\nCreating booking with payment mode...")
    booking_response = session.post(booking_url, json=booking_data)
    print(f"Booking creation status: {booking_response.status_code}")
    
    if booking_response.status_code == 201:
        booking_result = booking_response.json()
        print("Booking created successfully!")
        print(f"Booking ID: {booking_result.get('booking', {}).get('id')}")
        print(f"Payment Mode: {booking_result.get('booking', {}).get('payment_mode')}")
        print(f"Total Amount: ₹{booking_result.get('booking', {}).get('total_amount')}")
    else:
        print(f"Booking creation failed: {booking_response.json()}")
else:
    print(f"Login failed: {login_response.json()}")