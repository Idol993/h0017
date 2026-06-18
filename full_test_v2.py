import urllib.request
import json
from datetime import datetime, timedelta
import sqlite3
import io
import time

BASE = "http://localhost:8000"

def req(method, path, data=None):
    url = BASE + path
    body = json.dumps(data).encode('utf-8') if data else None
    r = urllib.request.Request(url, data=body, method=method)
    r.add_header('Content-Type', 'application/json')
    try:
        resp = urllib.request.urlopen(r, timeout=10)
        text = resp.read().decode('utf-8')
        return resp.status, json.loads(text) if text else None
    except urllib.error.HTTPError as e:
        text = e.read().decode('utf-8')
        try:
            return e.code, json.loads(text)
        except:
            return e.code, text

print("=" * 60)
print("  综合验证测试 v2")
print("=" * 60)

print("\n0. 清理数据库")
conn = sqlite3.connect('backend/flashcards.db')
cursor = conn.cursor()
cursor.execute("DELETE FROM review_logs")
cursor.execute("DELETE FROM cards")
cursor.execute("DELETE FROM decks")
conn.commit()
conn.close()
print("  ✅ 已清空")

print("\n1. 创建测试数据")
s, deck1 = req("POST", "/api/decks", {"name": "测试卡组A", "language_pair": "zh-jp", "cover_color": "#3b82f6"})
print(f"  卡组A: id={deck1['id']}")

for i in range(3):
    s, c = req("POST", "/api/cards", {
        "front": f"卡{i+1}正面",
        "back": f"卡{i+1}背面",
        "deck_id": deck1['id'],
        "tags": ["test"]
    })
    print(f"  卡片{i+1}: id={c['id']}")

s, cards = req("GET", "/api/today")
print(f"  今日学习卡片数: {len(cards)}")

print("\n2. SM-2 算法验证")
first_card = cards[0]
intervals = []
import sys
sys.path.insert(0, 'backend')
from sm2 import calculate_next_interval

class FakeCard:
    def __init__(self, s=2.5, c=0, i=0):
        self.memory_strength = s
        self.consecutive_correct = c
        self.interval_days = i

fc = FakeCard()
for i in range(7):
    r = calculate_next_interval(fc, 5)
    intervals.append(r['interval_days'])
    fc = FakeCard(r['memory_strength'], r['consecutive_correct'], r['interval_days'])
print(f"  连续5分间隔: {intervals}")

ok = True
for i in range(1, len(intervals)):
    p, c = intervals[i-1], intervals[i]
    if p == 0 or c >= 30:
        continue
    ratio = c / p
    if ratio < 1.5 or ratio > 2.0:
        ok = False
        print(f"  ❌ {p}d→{c}d 倍率={ratio:.2f} 超出范围")
if ok:
    print("  ✅ 全部在 1.5-2x 范围")

if intervals[1] == 6:
    print("  ❌ 还有 1→6 天跳跃")
else:
    print(f"  ✅ 无 1→6 跳跃，第2次={intervals[1]}天")

print("\n3. 评分后刷新今日列表")
card_id = cards[0]['id']
s, result = req("POST", "/api/review", {"card_id": card_id, "rating": 5, "duration_seconds": 10})
print(f"  评分5分: 新间隔={result['interval_days']}天")

s, cards2 = req("GET", "/api/today")
still_there = any(c['id'] == card_id for c in cards2)
print(f"  评分后卡片是否仍在今日列表: {'是' if still_there else '否'}")
if not still_there:
    print("  ✅ 评分后不再出现")
else:
    print("  ⚠️  仍在列表中（可能间隔=1天）")

print("\n4. 今日排序验证")
# 重新清空并创建不同到期时间的卡
conn = sqlite3.connect('backend/flashcards.db')
cursor = conn.cursor()
cursor.execute("DELETE FROM review_logs")
cursor.execute("DELETE FROM cards")
cursor.execute("DELETE FROM decks")
conn.commit()

s, deck = req("POST", "/api/decks", {"name": "排序测试", "language_pair": "zh-jp", "cover_color": "#22c55e"})
now = datetime.now()

test_cards = [
    ("今天到期1", now),
    ("过期7天", now - timedelta(days=7)),
    ("今天到期2", now),
    ("过期3天", now - timedelta(days=3)),
    ("过期1天", now - timedelta(days=1)),
]

for front, nr in test_cards:
    cursor.execute(
        "INSERT INTO cards (front, back, deck_id, next_review, memory_strength, consecutive_correct, interval_days) VALUES (?, ?, ?, ?, 2.5, 0, 1)",
        (front, "背面", deck['id'], nr.strftime('%Y-%m-%d %H:%M:%S'))
    )
conn.commit()
conn.close()

s, today = req("GET", "/api/today")
print(f"  今日卡片顺序:")
for i, c in enumerate(today):
    print(f"    {i+1}. {c['front']} - 过期={c['is_overdue']}, 天数={c['overdue_days']}")

order_ok = True
saw_overdue = False
for i, c in enumerate(today):
    if not c['is_overdue']:
        if saw_overdue:
            order_ok = False
    else:
        saw_overdue = True
        if i > 0 and today[i-1]['is_overdue'] and c['overdue_days'] > today[i-1]['overdue_days']:
            order_ok = False

print(f"  排序结果: {'✅ 正确' if order_ok else '❌ 错误'}")

print("\n5. JSON 导出 + 增量导入验证")
s, export1 = req("GET", "/api/export/json")
print(f"  导出: {len(export1['decks'])}卡组, {len(export1['cards'])}卡片, {len(export1['review_logs'])}记录")

# 先在现有数据中新建一个卡组和一张卡（当前已有的新数据）
s, new_deck = req("POST", "/api/decks", {"name": "新增卡组（不应被删）", "language_pair": "en-zh", "cover_color": "#f97316"})
s, new_card = req("POST", "/api/cards", {"front": "新增卡片", "back": "不应被删", "deck_id": new_deck['id'], "tags": []})
print(f"  新增了卡组 '{new_deck['name']}' 和卡片")

# 导入同一份备份
boundary = '----XYZ'
json_str = json.dumps(export1)
body = (
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="file"; filename="b.json"\r\n'
    f'Content-Type: application/json\r\n\r\n'
    f'{json_str}\r\n'
    f'--{boundary}--\r\n'
).encode('utf-8')

r = urllib.request.Request(BASE + '/api/import/json', data=body, method='POST')
r.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
resp = urllib.request.urlopen(r, timeout=10)
result = json.loads(resp.read().decode('utf-8'))
print(f"  第1次导入: {result}")

# 再次导入同一份，验证去重
r2 = urllib.request.Request(BASE + '/api/import/json', data=body, method='POST')
r2.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
resp2 = urllib.request.urlopen(r2, timeout=10)
result2 = json.loads(resp2.read().decode('utf-8'))
print(f"  第2次导入(去重): {result2}")

s, all_decks = req("GET", "/api/decks")
print(f"  导入后卡组总数: {len(all_decks)}")
deck_names = [d['name'] for d in all_decks]
print(f"  卡组列表: {deck_names}")

if "新增卡组（不应被删）" in deck_names:
    print("  ✅ 当前已有的新卡组被保留")
else:
    print("  ❌ 新卡组丢失了！")

if result2.get('cards_imported', 0) == 0 and result2.get('cards_updated', 0) >= 0:
    print("  ✅ 重复导入无重复卡片产生")
else:
    print(f"  ⚠️  重复导入卡片数: 新增{result2.get('cards_imported',0)}, 更新{result2.get('cards_updated',0)}")

print("\n6. JSON 格式错误提示")
bad_body = (
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="file"; filename="bad.json"\r\n'
    f'Content-Type: application/json\r\n\r\n'
    f'this is not valid json {{\r\n'
    f'--{boundary}--\r\n'
).encode('utf-8')

try:
    r3 = urllib.request.Request(BASE + '/api/import/json', data=bad_body, method='POST')
    r3.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    resp3 = urllib.request.urlopen(r3, timeout=10)
    print("  ❌ 应返回错误但成功了")
except urllib.error.HTTPError as e:
    err = json.loads(e.read().decode('utf-8'))
    print(f"  ✅ 正确返回错误: status={e.code}, detail={err.get('detail','')[:50]}")

print("\n7. 统计页数据一致性")
s, stats = req("GET", "/api/stats")
s, decks_all = req("GET", "/api/decks")
total_cards_check = 0
for d in decks_all:
    s, cs = req("GET", f"/api/cards?deck_id={d['id']}")
    total_cards_check += len(cs)

print(f"  统计报告总卡片: {stats['total_cards']}, 实际数: {total_cards_check}")
if stats['total_cards'] == total_cards_check:
    print("  ✅ 卡片总数一致")
else:
    print("  ❌ 卡片总数不一致")

print(f"  卡组掌握率数据: {[(d['deck_name'], d['total_cards']) for d in stats['deck_mastery_rates']]}")

print("\n8. 前端页面渲染测试")
import urllib.request as u2
front_ok = True
try:
    html = u2.urlopen('http://localhost:5173/', timeout=5).read().decode('utf-8')
    if '<div id="app">' in html:
        print("  ✅ 首页 HTML 正常")
    for page in ['App.svelte', 'main.js', 'routes/Today.svelte', 'routes/Decks.svelte', 'routes/Stats.svelte', 'routes/Import.svelte']:
        try:
            resp = u2.urlopen(f'http://localhost:5173/src/{page}', timeout=5)
            if resp.status != 200:
                print(f"  ❌ {page} 状态: {resp.status}")
                front_ok = False
        except Exception as ex:
            print(f"  ❌ {page} 加载失败: {ex}")
            front_ok = False
    if front_ok:
        print("  ✅ 所有前端资源编译成功")
except Exception as e:
    print(f"  ❌ 前端不可达: {e}")
    front_ok = False

print("\n" + "=" * 60)
print("  测试完成")
print("=" * 60)
