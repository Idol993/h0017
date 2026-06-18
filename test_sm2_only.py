import sys
sys.path.insert(0, 'backend')
from sm2 import calculate_next_interval

class FakeCard:
    def __init__(self, memory_strength=2.5, consecutive_correct=0, interval_days=0):
        self.memory_strength = memory_strength
        self.consecutive_correct = consecutive_correct
        self.interval_days = interval_days

print("=== SM-2 算法验证（评分=5，strength=2.5 起始）===")
card = FakeCard()
intervals = []
for i in range(1, 10):
    result = calculate_next_interval(card, 5)
    intervals.append(result['interval_days'])
    print(f"  第{i}次: interval={result['interval_days']}d, consecutive={result['consecutive_correct']}, strength={result['memory_strength']}")
    card = FakeCard(result['memory_strength'], result['consecutive_correct'], result['interval_days'])

print("\n增长率检查:")
all_ok = True
for i in range(1, len(intervals)):
    prev = intervals[i-1]
    curr = intervals[i]
    if prev == 0:
        ratio = 0
        status = "初始"
    elif curr >= 30 and prev >= 30:
        ratio = curr / prev
        status = "上限"
    else:
        ratio = curr / prev
        if 1.5 <= ratio <= 2.0:
            status = "OK ✓"
        else:
            status = "FAIL ✗"
            all_ok = False
    print(f"  {prev}d → {curr}d, 倍率={ratio:.2f}  {status}")

# 检查是否有 1→6 天跳跃
if len(intervals) >= 2 and intervals[1] == 6:
    print("\n❌ 仍然有 1→6 天跳跃！")
    all_ok = False
else:
    print(f"\n✅ 第2次后间隔={intervals[1]}天，无 1→6 天跳跃")

print("\n=== 评分=1 重置测试 ===")
card = FakeCard(2.6, 3, 10)
result = calculate_next_interval(card, 1)
print(f"  之前: interval=10d, consecutive=3")
print(f"  之后: interval={result['interval_days']}d, consecutive={result['consecutive_correct']}")
if result['interval_days'] == 1 and result['consecutive_correct'] == 0:
    print("  ✅ 重置正确")
else:
    print("  ❌ 重置错误")
    all_ok = False

print("\n" + "=" * 50)
if all_ok:
    print("  ✅ 全部通过！")
else:
    print("  ❌ 存在失败")
print("=" * 50)
