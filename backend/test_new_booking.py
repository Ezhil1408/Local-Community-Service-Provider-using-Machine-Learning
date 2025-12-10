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
    
    # Use a future date to avoid conflicts
    future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    
    # Now try to create a booking
    booking_url = "http://127.0.0.1:5000/api/bookings/create"
    booking_data = {
        "provider_id": 1,
        "date": future_date,
        "time_slot": "02:00 PM - 03:00 PM",
        "hours_booked": 2.0,
        "user_upi_id": "testuser@okaxis",
        "service_description": "Test booking for conflict testing"
    }
    
    print(f"\nCreating first booking for {future_date}...")
    booking_response = session.post(booking_url, json=booking_data)
    print(f"First booking status: {booking_response.status_code}")
    if booking_response.status_code == 201:
        print("First booking created successfully")
        booking_result = booking_response.json()
        booking_id = booking_result.get('booking', {}).get('id')
        print(f"Booking ID: {booking_id}")
        
        # Try to create another booking for the same time slot
        print("\nCreating second booking for same time slot...")
        booking_response2 = session.post(booking_url, json=booking_data)
        print(f"Second booking status: {booking_response2.status_code}")
        if booking_response2.status_code == 400:
            print("Second booking correctly rejected due to time slot conflict")
            print(f"Error: {booking_response2.json()}")
        else:
            print(f"Unexpected result: {booking_response2.json()}")
    else:
        print(f"First booking failed: {booking_response.json()}")
else:
    print(f"Login failed: {login_response.json()}")