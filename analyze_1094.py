#!/usr/bin/env python3
"""最终分析：确认哪个请求让 kg 积分生效"""
import json
import os
import base64
import subprocess

PROTOC = './protoc'

filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chlz', '1094.chlsj')
with open(filepath, 'r') as f:
    data = json.load(f)

game_reqs = []
for i, entry in enumerate(data):
    if entry.get('host') != 'prod.advrpg.com':
        continue
    if entry.get('method') != 'PUT':
        continue
    if entry.get('status') != 'COMPLETE':
        continue

    req = entry.get('request', {})
    resp = entry.get('response', {})

    req_body_raw = b''
    resp_body_raw = b''

    req_body_data = req.get('body', {})
    if isinstance(req_body_data, dict) and req_body_data.get('encoding') == 'base64':
        try:
            req_body_raw = base64.b64decode(req_body_data.get('encoded', ''))
        except:
            pass

    resp_body_data = resp.get('body', {})
    if isinstance(resp_body_data, dict) and resp_body_data.get('encoding') == 'base64':
        try:
            resp_body_raw = base64.b64decode(resp_body_data.get('encoded', ''))
        except:
            pass

    req_hex = req_body_raw[:2].hex() if len(req_body_raw) >= 2 else '??'
    times = entry.get('times', {})
    start = times.get('start', '')[:19]

    game_reqs.append({
        'idx': i,
        'start': start,
        'req_hex': req_hex,
        'req_raw': req_body_raw,
        'resp_raw': resp_body_raw,
    })

def decode_raw(binary_data, skip):
    try:
        p = subprocess.run(
            [PROTOC, '--decode_raw'],
            input=binary_data[skip:],
            capture_output=True,
            timeout=5
        )
        return p.stdout.decode('utf-8', errors='replace').strip()
    except:
        return ''

# ====== 分析 ylxyx 完整流程 ======

# 1780444800 是什么时间？
import datetime
ts = 1780444800
dt = datetime.datetime.fromtimestamp(ts)
print(f"1780444800 = {dt}")  # 应该是 2026-06-10 的某个时间

ts2 = 1781136000
dt2 = datetime.datetime.fromtimestamp(ts2)
print(f"1781136000 = {dt2}")

# 120260608 分析
val = 120260608
print(f"\n120260608 分析:")
print(f"  可能是 1+20260608 = 活动ID含日期20260608 (2026-06-08)")
print(f"  或 12026+0608 = ?")

# ====== 分析 017d (prime_activity_tracking) response ======
print("\n" + "="*80)
print("017d (活动入口索引) response 详细")
print("="*80)

for g in game_reqs:
    if g['req_hex'] != '017d':
        continue
    print(f"\n[{g['idx']}] time={g['start']}")
    resp_decoded = decode_raw(g['resp_raw'], 6)
    print(f"  RESPONSE:")
    for line in resp_decoded.split('\n'):
        print(f"    {line}")
    req_decoded = decode_raw(g['req_raw'], 4)
    lines = req_decoded.split('\n')
    non_header = []
    in_field1 = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('1 {'):
            in_field1 = True
        elif stripped == '}' and in_field1:
            in_field1 = False
        elif not in_field1:
            non_header.append(stripped)
    print(f"  REQUEST params: {' | '.join(non_header)}")

# ====== 分析 132b response 的 field4 变化 ======
print("\n" + "="*80)
print("132b response 的 field4 变化 (可能是 kg 积分)")
print("="*80)

for g in game_reqs:
    if g['req_hex'] != '132b':
        continue

    req_decoded = decode_raw(g['req_raw'], 4)
    lines = req_decoded.split('\n')
    non_header = []
    in_field1 = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('1 {'):
            in_field1 = True
        elif stripped == '}' and in_field1:
            in_field1 = False
        elif not in_field1:
            non_header.append(stripped)

    resp_decoded = decode_raw(g['resp_raw'], 6)

    print(f"[{g['idx']}] time={g['start']}  params: {' | '.join(non_header)}")
    print(f"  RESPONSE:")
    for line in resp_decoded.split('\n'):
        print(f"    {line}")

# ====== 对比 ylxyx 流程前后所有 132b 的 field4 ======
print("\n" + "="*80)
print("分析 132b 的 i3 参数含义")
print("="*80)

for g in game_reqs:
    if g['req_hex'] != '132b':
        continue

    req_decoded = decode_raw(g['req_raw'], 4)
    lines = req_decoded.split('\n')
    non_header = []
    in_field1 = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('1 {'):
            in_field1 = True
        elif stripped == '}' and in_field1:
            in_field1 = False
        elif not in_field1:
            non_header.append(stripped)

    resp_decoded = decode_raw(g['resp_raw'], 6)
    # 提取 field4 值
    for line in resp_decoded.split('\n'):
        stripped = line.strip()
        if stripped.startswith('4:'):
            f4_val = stripped.split(':')[1].strip()
            break
    else:
        f4_val = '?'

    params_str = ' | '.join(non_header)
    print(f"[{g['idx']}] {g['start']}  i2={non_header[0] if non_header else '?'}  i3={non_header[1] if len(non_header) > 1 else '?'}  → field4={f4_val}")

# ====== 分析 057d 的 i4=120260608 跟日期的关系 ======
print("\n" + "="*80)
print("057d 的 i4=120260608 分析")
print("="*80)

# 看有没有活动 ID 120260608 出现在 017d 或 1329 的 response 中
for g in game_reqs:
    if g['req_hex'] in ['017d', '1329']:
        resp_decoded = decode_raw(g['resp_raw'], 6)
        if '120260608' in resp_decoded:
            print(f"  找到 120260608 在 [{g['idx']}] hexstring={g['req_hex']}")
            lines = resp_decoded.split('\n')
            for i, line in enumerate(lines):
                if '120260608' in line:
                    start = max(0, i-3)
                    end = min(len(lines), i+5)
                    for j in range(start, end):
                        print(f"    {lines[j]}")
                    print()

# 另外搜索所有请求
for g in game_reqs:
    resp_decoded = decode_raw(g['resp_raw'], 6)
    if '120260608' in resp_decoded:
        print(f"  找到 120260608 在 [{g['idx']}] hexstring={g['req_hex']}")

# ====== 看第一组 ylxyx 操作和第二组的区别 ======
print("\n" + "="*80)
print("两组 ylxyx 操作前后的关键差异")
print("="*80)
print("""
第一组 (13:03:50 ~ 13:04:22):
  时间节点:
  [109] 13:03:41 017d (活动入口索引) -- 这是 prime_activity_tracking!
  [148] 13:03:45 d959 (考古查询) -- score=2200, field8=200
  [175] 13:03:50 057d (ylxyx 触发?)
  [187] 13:04:04 057d (重复)
  [188] 13:04:04 3f33 (i2=1002, i3=1, i4=1, i6=1, i7=3 → 某种PVP/战斗)
  [189] 13:04:04 1329 (进入考古, i2=3993518)
  [198] 13:04:08 032b (开始游历, i3=20) → response含 3:20000
  [205] 13:04:22 132b (step 10, i3=1780444800) → field4=40
  [206] 13:04:22 192b (step 10, i3=4000085 → ylifid)
  [207] 13:04:22 132b (step 13, i3=1780444800) → field4=80
  [208] 13:04:22 192b (step 13, i3=4000085 → ylifid)

第二组 (13:04:40 ~ 13:04:48):
  [223] 13:04:40 192b (step 58, i3=4000085) → 大包
  [224] 13:04:40 132b (step 58, i3=1780444800) → field4=140
  [225] 13:04:40 052b (结束游历, i2=35, i3=60)
  [233] 13:04:41 0f2b (游历结算确认) → field1=36, field2={1:240}
  [252] 13:04:48 057d (又一次 ylxyx)
  [253] 13:04:48 3f33 (同样 i2=1002 → 战斗)
  [254] 13:04:48 1329 (进入考古, i2=3993518)
""")

print("""
关键发现:
1. 132b response 中的 field4 从 40→80→140 递增:
   - step 10: field4=40 (20000*40/140 ≈ 5714?)
   - step 13: field4=80
   - step 58: field4=140

2. 132b 的 i3=1780444800 是时间戳 2026-06-10 00:00:00 UTC+8 (今天的零点)
   这说明132b是与"今天"有关的请求!

3. 192b 的 i3=4000085 是 ylifid（游历活动ID）

4. 132b 可能就是让 kg 积分生效的关键请求:
   - i2=step_id (10/13/58 来自032b游历开始的步骤)
   - i3=1780444800 (今天零点时间戳)

5. 132b 是 yl_manager.py 中的 ylhd() 方法，hexstringheader="192b"
   但 132b 是 ylhd2() ??? 不，看代码:
   - 192b = ylhd() = "活动1a-幸运星"
   - 012b = ylhd2() = "活动2"

   但实际抓包中出现了 132b，这在代码中没有对应！
""")

# 看看 132b 是否出现在代码中
print("\n搜索代码中 132b 的出现...")
