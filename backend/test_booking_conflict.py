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
    
    # Now try to create a booking
    booking_url = "http://127.0.0.1:5000/api/bookings/create"
    booking_data = {
        "provider_id": 1,
        "date": "2025-12-01",
        "time_slot": "10:00 AM - 11:00 AM",
        "hours_booked": 2.0,
        "user_upi_id": "testuser@okaxis",
        "service_description": "Test booking"
    }
    
    print("\nCreating first booking...")
    booking_response = session.post(booking_url, json=booking_data)
    print(f"First booking status: {booking_response.status_code}")
    if booking_response.status_code == 201:
        print("First booking created successfully")
        booking_result = booking_response.json()
        print(f"Booking ID: {booking_result.get('booking', {}).get('id')}")
    else:
        print(f"First booking failed: {booking_response.json()}")
    
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
    print(f"Login failed: {login_response.json()}")