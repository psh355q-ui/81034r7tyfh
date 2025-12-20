"""
Test RSS crawl stream directly
"""
import requests

url = "http://localhost:8001/api/news/crawl/stream?extract_content=true"
print(f"Connecting to {url}...")

response = requests.get(url, stream=True, timeout=15)
print(f"Status: {response.status_code}")
print(f"Headers: {response.headers}")

print("\nStream content (first 10 messages):")
count = 0
for line in response.iter_lines():
    if line:
        decoded = line.decode('utf-8')
        print(decoded)
        count += 1
        if count >= 10:
            break

print(f"\nReceived {count} lines")
