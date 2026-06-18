import urllib.request
import json

BASE = "http://localhost:8000"

r = urllib.request.urlopen(BASE + "/api/cards?deck_id=1", timeout=5)
data = json.loads(r.read().decode('utf-8'))
print(f"返回卡片数: {len(data)}")
for i, c in enumerate(data[:30]):
    print(f"  {i+1}. id={c['id']}, front={c['front'][:20]}, deck_id={c['deck_id']}")
