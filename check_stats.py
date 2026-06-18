import urllib.request
import json
import sqlite3

BASE = "http://localhost:8000"

def req(method, path, data=None):
    url = BASE + path
    body = json.dumps(data).encode('utf-8') if data else None
    r = urllib.request.Request(url, data=body, method=method)
    r.add_header('Content-Type', 'application/json')
    try:
        resp = urllib.request.urlopen(r, timeout=5)
        return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')

# 直接查数据库
conn = sqlite3.connect('backend/flashcards.db')
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM cards")
db_count = cursor.fetchone()[0]
print(f"数据库 cards 表行数: {db_count}")

cursor.execute("SELECT deck_id, COUNT(*) FROM cards GROUP BY deck_id")
print("各卡组卡片数:", cursor.fetchall())

cursor.execute("SELECT COUNT(*) FROM decks")
print(f"数据库 decks 表行数: {cursor.fetchone()[0]}")

s, stats = req("GET", "/api/stats")
print(f"\n统计 API total_cards: {stats['total_cards']}")

s, decks = req("GET", "/api/decks")
print(f"卡组 API 返回: {len(decks)} 个")
total = 0
for d in decks:
    s, cs = req("GET", f"/api/cards?deck_id={d['id']}")
    print(f"  卡组 {d['name']}(id={d['id']}): {len(cs)} 张")
    total += len(cs)
print(f"逐卡组累加: {total}")

conn.close()
