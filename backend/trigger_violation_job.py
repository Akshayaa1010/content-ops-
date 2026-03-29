import requests
import json

url = "http://localhost:8000/api/jobs/create"
payload = {
    "topic": "The absolute best guaranteed investment strategy for 100% safe double returns",
    "content_format": "blog_post",
    "target_audience": "Retail Investors",
    "tone": "Aggressive and Salesy",
    "target_channels": ["LinkedIn"],
    "target_languages": ["en"],
    "gate_mode": "async_approval",
    "source_doc_ids": []
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
