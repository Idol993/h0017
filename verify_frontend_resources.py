import urllib.request
import sys

print("=== 前端资源验证 ===")

# 1. 测试 HTML
try:
    resp = urllib.request.urlopen('http://localhost:5173/', timeout=5)
    html = resp.read().decode('utf-8')
    print(f"HTML: {resp.status}, has app div: {'id=\"app\"' in html}, has main.js: {'main.js' in html}")
except Exception as e:
    print(f"HTML 错误: {e}")
    sys.exit(1)

# 2. 测试 main.js
try:
    resp = urllib.request.urlopen('http://localhost:5173/src/main.js', timeout=5)
    js = resp.read().decode('utf-8')
    print(f"main.js: {resp.status}, length: {len(js)}")
except Exception as e:
    print(f"main.js 错误: {e}")

# 3. 测试 App.svelte 编译
try:
    resp = urllib.request.urlopen('http://localhost:5173/src/App.svelte', timeout=5)
    js = resp.read().decode('utf-8')
    print(f"App.svelte: {resp.status}, length: {len(js)}")
    print(f"  has mount: {'mount' in js}")
    print(f"  has $state: {'$state' in js or 'state(' in js}")
    # 检查是否有编译错误
    if 'error' in js.lower() and len(js) < 500:
        print(f"  可能有编译错误: {js[:300]}")
except Exception as e:
    print(f"App.svelte 错误: {e}")

# 4. 测试各个页面组件
for page in ['Today', 'Decks', 'Stats', 'Import']:
    try:
        resp = urllib.request.urlopen(f'http://localhost:5173/src/routes/{page}.svelte', timeout=5)
        js = resp.read().decode('utf-8')
        has_error = 'CompileError' in js or 'SyntaxError' in js
        print(f"{page}.svelte: {resp.status}, length: {len(js)}, error: {has_error}")
    except Exception as e:
        print(f"{page}.svelte 错误: {e}")

# 5. 测试 API 模块
try:
    resp = urllib.request.urlopen('http://localhost:5173/src/lib/api.js', timeout=5)
    js = resp.read().decode('utf-8')
    print(f"api.js: {resp.status}, length: {len(js)}")
except Exception as e:
    print(f"api.js 错误: {e}")

print("\n=== 验证完成 ===")
