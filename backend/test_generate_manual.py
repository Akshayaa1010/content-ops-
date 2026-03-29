import requests

url = "http://127.0.0.1:8000/api/documents/generate_content"
payload = {"text": "This is a product specification for SmartAir Pro, an AI powered air purifier."}

print(f"Testing generation to {url}...")
try:
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")
