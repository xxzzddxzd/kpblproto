#!/usr/bin/env python3
"""检查 ghxs query response 的 field10 是否包含已领取奖励信息"""
import subprocess, os

PROTOC = './protoc'
OUT_DIR = '/tmp/chlsj_extract'

def decode_full(filepath, skip):
    try:
        p = subprocess.run(
            f"tail -c +{skip+1} '{filepath}' | {PROTOC} --decode_raw 2>/dev/null",
            shell=True, capture_output=True, text=True, timeout=5
        )
        return p.stdout.strip()
    except:
        return ''

# 查询1 [66] 和 查询2 [165] 对比 field9/field10
for idx in [66, 165]:
    print(f"\n{'='*50}")
    print(f"[{idx}] 1f78 公会悬赏查询 — field 7~13")
    print(f"{'='*50}")
    resp = decode_full(os.path.join(OUT_DIR, f'{idx}-res.dat'), 6)
    lines = resp.split('\n')
    depth = 0
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped == '}':
            depth -= 1
        if depth == 0:
            # 打印顶层 field 7~13
            for fn in ['7:', '8:', '9:', '10:', '10 ', '11:', '12:', '13:']:
                if stripped.startswith(fn):
                    print(f"  {line}")
                    break
        if stripped.endswith('{'):
            depth += 1

# 也看看 field10 的 hex 值
print(f"\n{'='*50}")
print("field10 raw hex (如果存在)")
print(f"{'='*50}")
for idx in [66, 165]:
    res_file = os.path.join(OUT_DIR, f'{idx}-res.dat')
    with open(res_file, 'rb') as f:
        data = f.read()[6:]  # skip 6 bytes
    # 搜索 field 10 (wire type 2 = length-delimited, field 10 = 0x52)
    # varint key = (10 << 3) | 2 = 82 = 0x52
    pos = 0
    while pos < len(data):
        if data[pos] == 0x52:  # field 10, wire type 2
            # 下一字节是长度
            length = data[pos+1]
            field10_data = data[pos+2:pos+2+length]
            print(f"  [{idx}] field10 ({length} bytes): {field10_data.hex()}")
            # 也打印 bits
            bits = ''.join(f'{b:08b}' for b in field10_data)
            print(f"  [{idx}] field10 bits: {bits}")
            break
        pos += 1
    else:
        print(f"  [{idx}] field10 未找到(可能为空)")
