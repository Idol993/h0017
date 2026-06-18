import urllib.request
import json

print("=== Testing Frontend ===")
try:
    resp = urllib.request.urlopen('http://localhost:5173/', timeout=5)
    html = resp.read().decode('utf-8')
    print(f"Status: {resp.status}")
    print(f"Has <div id=\"app\">: {'id=\"app\"' in html}")
    print(f"Has main.js: {'main.js' in html}")
    print("Frontend HTML OK")
except Exception as e:
    print(f"Frontend error: {e}")

print()
print("=== Testing Backend ===")
try:
    resp = urllib.request.urlopen('http://localhost:8000/api/decks', timeout=5)
    data = json.loads(resp.read().decode('utf-8'))
    print(f"Status: {resp.status}")
    print(f"Decks count: {len(data)}")
    print("Backend API OK")
except Exception as e:
    print(f"Backend error: {e}")

print()
print("=== Testing Today API ===")
try:
    resp = urllib.request.urlopen('http://localhost:8000/api/today', timeout=5)
    data = json.loads(resp.read().decode('utf-8'))
    print(f"Status: {resp.status}")
    print(f"Today cards count: {len(data)}")
    for c in data:
        print(f"  - {c['front']} (overdue={c['is_overdue']}, days={c['overdue_days']})")
    print("Today API OK")
except Exception as e:
    print(f"Today API error: {e}")
