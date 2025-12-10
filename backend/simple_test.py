import requests
import json

# Test provider login with correct credentials
url = "http://127.0.0.1:5000/api/provider/login"
data = {
    "name": "Sanjay Raj",
    "email": "provider1@service.com"
}

print("Testing provider login...")
try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")