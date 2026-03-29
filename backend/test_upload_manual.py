import requests

url = "http://127.0.0.1:8000/api/documents/upload"
file_path = "test.pdf"

print(f"Testing upload to {url} with {file_path}...")
try:
    with open(file_path, "rb") as f:
        files = {"file": (file_path, f, "text/plain")}
        response = requests.post(url, files=files)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")
