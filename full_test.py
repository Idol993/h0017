import urllib.request
import json
from datetime import datetime, timedelta

BASE = "http://localhost:8000"

def req(method, path, data=None):
    url = BASE + path
    body = json.dumps(data).encode('utf-8') if data else None
    r = urllib.request.Request(url, data=body, method=method)
    r.add_header('Content-Type', 'application/json')
    try:
        resp = urllib.request.urlopen(r)
        return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')

print("=" * 60)
print("  综合验证测试")
print("=" * 60)

# 1. 清除旧数据，重新开始
print("\n1. 清理并准备测试数据")

class FakeCard:
    def __init__(self, memory_strength=2.5, consecutive_correct=0, interval_days=0):
        self.memory_strength = memory_strength
        self.consecutive_correct = consecutive_correct
        self.interval_days = interval_days

import sys
sys.path.insert(0, 'backend')
from sm2 import calculate_next_interval

print("\n2. SM-2 算法验证（5分连续评分）")
card = FakeCard()
intervals = []
for i in range(1, 8):
    result = calculate_next_interval(card, 5)
    intervals.append(result['interval_days'])
    print(f"  第{i}次5分: interval={result['interval_days']}d, consecutive={result['consecutive_correct']}, strength={result['memory_strength']}")
    card = FakeCard(result['memory_strength'], result['consecutive_correct'], result['interval_days'])

print("\n  增长率检查:")
all_ok = True
for i in range(1, len(intervals)):
    if intervals[i-1] == 0:
        ratio = 0
    else:
        ratio = intervals[i] / intervals[i-1]
    if intervals[i] >= 30:
        status = "上限"
    elif intervals[i-1] <= 1 and i == 1:
        status = "初始"
    elif 1.5 <= ratio <= 2.0:
        status = "OK"
    else:
        status = "FAIL"
        all_ok = False
    print(f"  {intervals[i-1]}d → {intervals[i]}d, 倍率={ratio:.2f}  {status}")

# 检查 1→6 天跳跃是否已消除
if intervals[1] == 6:
    print("  ❌ 仍然有 1→6 天跳跃！")
    all_ok = False
else:
    print(f"  ✅ 第二次5分后间隔={intervals[1]}天，已无1→6天跳跃")

# 检查1分重置
print("\n3. 评分=1 重置验证")
card = FakeCard(2.6, 3, 10)
result = calculate_next_interval(card, 1)
print(f"  之前: interval=10d, consecutive=3")
print(f"  之后: interval={result['interval_days']}d, consecutive={result['consecutive_correct']}")
if result['interval_days'] == 1 and result['consecutive_correct'] == 0:
    print("  ✅ 重置正确")
else:
    print("  ❌ 重置错误")
    all_ok = False

print("\n4. 今日卡片排序验证")
# 创建测试卡组
status, deck = req("POST", "/api/decks", {"name": "测试卡组", "language_pair": "zh-jp", "cover_color": "#3b82f6"})
deck_id = deck['id']
print(f"  创建卡组: id={deck_id}")

# 创建几张不同下次复习时间的卡片
import sqlite3
conn = sqlite3.connect('backend/flashcards.db')
cursor = conn.cursor()

now = datetime.now()
test_cards = [
    ("今天到期", "背面1", now),
    ("过期3天", "背面2", now - timedelta(days=3)),
    ("过期7天", "背面3", now - timedelta(days=7)),
    ("过期1天", "背面4", now - timedelta(days=1)),
    ("今天到期2", "背面5", now),
]

for front, back, next_review in test_cards:
    cursor.execute(
        "INSERT INTO cards (front, back, deck_id, next_review, memory_strength, consecutive_correct, interval_days) VALUES (?, ?, ?, ?, 2.5, 0, 1)",
        (front, back, deck_id, next_review.strftime('%Y-%m-%d %H:%M:%S'))
    )
conn.commit()
conn.close()
print(f"  创建了 {len(test_cards)} 张测试卡片")

# 获取今日卡片
status, cards = req("GET", "/api/today")
print(f"\n  今日卡片顺序 ({len(cards)}张):")
order_ok = True
saw_overdue = False
for i, c in enumerate(cards):
    print(f"    {i+1}. {c['front']} - 过期={c['is_overdue']}, 过期天数={c['overdue_days']}")
    if not c['is_overdue']:
        if saw_overdue:
            order_ok = False
            print("       ❌ 顺序错误：今天到期的卡出现在过期卡之后")
    else:
        saw_overdue = True
        # 检查过期天数是否降序
        if i > 0 and cards[i-1]['is_overdue'] and c['overdue_days'] > cards[i-1]['overdue_days']:
            order_ok = False
            print("       ❌ 顺序错误：过期天数未按降序排列")

if order_ok:
    print("  ✅ 排序正确：今天到期在前，过期按天数降序")
else:
    all_ok = False
    print("  ❌ 排序错误")

# 5. 评分接口
print("\n5. 评分接口验证")
first_card_id = cards[0]['id']
status, result = req("POST", "/api/review", {"card_id": first_card_id, "rating": 5, "duration_seconds": 10})
print(f"  POST /api/review body方式: status={status}, new_interval={result.get('interval_days')}d")
if status == 200 and result['interval_days'] >= 1:
    print("  ✅ 评分接口正常")
else:
    all_ok = False
    print("  ❌ 评分接口异常")

# 评分后刷新今日卡片，检查是否还在列表
status, cards2 = req("GET", "/api/today")
still_there = any(c['id'] == first_card_id for c in cards2)
print(f"  评分后卡片是否仍在今日列表: {'是' if still_there else '否'}")
if still_there:
    print("  ⚠️  刚评分过的卡仍在列表（可能因为间隔=1天且是今天到期）")
else:
    print("  ✅ 已评分卡片不再出现在今日列表")

# 6. JSON 导出导入
print("\n6. JSON 备份导出导入验证")
status, export_data = req("GET", "/api/export/json")
print(f"  导出: {len(export_data.get('decks', []))}卡组, {len(export_data.get('cards', []))}卡片, {len(export_data.get('review_logs', []))}记录")

# 清空数据库再导入
conn = sqlite3.connect('backend/flashcards.db')
cursor = conn.cursor()
cursor.execute("DELETE FROM review_logs")
cursor.execute("DELETE FROM cards")
cursor.execute("DELETE FROM decks")
conn.commit()
conn.close()
print("  已清空数据库")

# 导入备份
import io
import urllib.parse
json_str = json.dumps(export_data)
boundary = '----TestBoundary123'
body = (
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="file"; filename="backup.json"\r\n'
    f'Content-Type: application/json\r\n\r\n'
    f'{json_str}\r\n'
    f'--{boundary}--\r\n'
).encode('utf-8')

r = urllib.request.Request(BASE + '/api/import/json', data=body, method='POST')
r.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
resp = urllib.request.urlopen(r)
result = json.loads(resp.read().decode('utf-8'))
print(f"  导入结果: {result}")

# 验证导入后数据
status, decks = req("GET", "/api/decks")
status2, cards = req("GET", "/api/cards", None)  # 可能需要deck_id
print(f"  导入后: {len(decks)}卡组")

if len(decks) > 0:
    status3, cards = req("GET", f"/api/cards?deck_id={decks[0]['id']}")
    print(f"  卡组{decks[0]['name']}: {len(cards)}张卡片")
    if len(decks) >= 1 and len(cards) > 0:
        print("  ✅ JSON 导入导出正常")
    else:
        all_ok = False
        print("  ❌ JSON 导入数据不完整")
else:
    all_ok = False
    print("  ❌ 导入后卡组为空")

# 7. 卡组CRUD持久化
print("\n7. 卡组CRUD持久化验证")
status, new_deck = req("POST", "/api/decks", {"name": "持久化测试", "language_pair": "en-zh", "cover_color": "#22c55e"})
print(f"  新建卡组: {new_deck.get('name')}, id={new_deck.get('id')}")

deck_id2 = new_deck['id']
status, new_card = req("POST", "/api/cards", {"front": "persistence test", "back": "持久化测试", "deck_id": deck_id2, "tags": ["test"]})
print(f"  新建卡片: {new_card.get('front')}, id={new_card.get('id')}")

# 重新获取验证持久化
status, verify_decks = req("GET", "/api/decks")
found = any(d['id'] == deck_id2 for d in verify_decks)
print(f"  刷新后卡组仍存在: {'是' if found else '否'}")

status, verify_cards = req("GET", f"/api/cards?deck_id={deck_id2}")
found_card = any(c['id'] == new_card['id'] for c in verify_cards)
print(f"  刷新后卡片仍存在: {'是' if found_card else '否'}")

# 删除卡片
status, del_result = req("DELETE", f"/api/cards/{new_card['id']}")
status, after_del_cards = req("GET", f"/api/cards?deck_id={deck_id2}")
card_still_there = any(c['id'] == new_card['id'] for c in after_del_cards)
print(f"  删除卡片后仍存在: {'是(错误)' if card_still_there else '否(正确)'}")

if found and found_card and not card_still_there:
    print("  ✅ 增删改持久化正常")
else:
    all_ok = False
    print("  ❌ 持久化有问题")

# 检查删除后今日列表不再有这张卡
status, today_cards = req("GET", "/api/today")
in_today = any(c['id'] == new_card['id'] for c in today_cards)
print(f"  删除后卡片是否在今日列表: {'是(错误)' if in_today else '否(正确)'}")
if in_today:
    all_ok = False

print("\n" + "=" * 60)
if all_ok:
    print("  ✅ 全部测试通过！")
else:
    print("  ❌ 存在测试失败")
print("=" * 60)
