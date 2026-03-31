#!/usr/bin/env python3
"""
从 lg 目录的 Charles 导出文件生成 day_first_login 请求列表
支持 .chlz 文件（Charles 会话存档）和 *-req.bin 文件

用法: python generate_first_login.py [chlz_file_or_dir]
"""

import os
import sys
import glob
import binascii
import zipfile
import tempfile
import shutil

sys.path.append('modules')
import kpbl_pb2

def extract_num(f):
    """从文件名提取序号"""
    name = os.path.basename(f)
    # 处理 N-req.bin 格式
    if '-req.bin' in name:
        return int(name.split('-')[0])
    # 处理 indexN.html 格式
    name = name.replace('index', '').replace('.html', '')
    return int(name) if name else 0

def parse_request_body(body):
    """尝试用 request_body 解析并提取 i2, i3, i4, i5 等参数"""
    params = {}
    try:
        req = kpbl_pb2.request_body()
        req.ParseFromString(body)

        # proto3 中检查非默认值
        if req.i2 != 0:
            params['request_body_i2'] = req.i2
        if req.i3 != 0:
            params['request_body_i3'] = req.i3
        if req.i4 != 0:
            params['request_body_i4'] = req.i4
        if req.i5:  # string type
            params['request_body_i5'] = req.i5

    except Exception:
        pass

    return params

def extract_chlz(chlz_path, extract_dir):
    """解压 .chlz 文件到指定目录"""
    with zipfile.ZipFile(chlz_path, 'r') as zf:
        zf.extractall(extract_dir)

def generate_first_login_requests(source_path='lg'):
    """
    从 chlz 文件或目录生成 day_first_login 请求列表

    Args:
        source_path: .chlz 文件路径或包含 *-req.bin 文件的目录

    Returns:
        list: 请求配置列表
    """
    temp_dir = None

    # 判断输入类型
    if source_path.endswith('.chlz'):
        # 解压 chlz 文件到临时目录
        temp_dir = tempfile.mkdtemp()
        extract_chlz(source_path, temp_dir)
        work_dir = temp_dir
        file_pattern = '*-req.bin'
    elif os.path.isdir(source_path):
        work_dir = source_path
        # 优先查找 chlz 文件
        chlz_files = glob.glob(os.path.join(source_path, '*.chlz'))
        if chlz_files:
            # 使用第一个 chlz 文件
            temp_dir = tempfile.mkdtemp()
            extract_chlz(chlz_files[0], temp_dir)
            work_dir = temp_dir
            file_pattern = '*-req.bin'
            print(f"# 使用 chlz 文件: {chlz_files[0]}", file=sys.stderr)
        elif glob.glob(os.path.join(source_path, '*-req.bin')):
            file_pattern = '*-req.bin'
        else:
            file_pattern = 'index*.html'
    else:
        print(f"错误: {source_path} 不存在", file=sys.stderr)
        return []

    # 获取所有请求文件并按序号排序
    files = glob.glob(os.path.join(work_dir, file_pattern))
    files.sort(key=extract_num)

    # 排除的 header（登录7527和心跳8927）
    excluded_headers = {'7527', '8927'}

    # 需要忽略参数的 header（参数是时间戳或动态值）
    ignore_params_headers = {'8a27', 'f277'}

    results = []
    seen_keys = set()  # 用于去重

    for f in files:
        with open(f, 'rb') as fp:
            data = fp.read()

        if len(data) < 4:
            continue

        # 提取 header（前2字节）
        header_bytes = data[:2]
        header_hex = binascii.hexlify(header_bytes).decode()

        # 检查是否需要排除
        if header_hex in excluded_headers:
            continue

        # 判断 body 起始位置
        # *-req.bin 格式: 2字节header + 2字节长度 + protobuf body
        # index*.html 格式可能不同，需要跳过6字节
        if '-req.bin' in f:
            body = data[4:]  # 跳过4字节头部
        else:
            body = data[6:]  # 跳过6字节头部

        # 解析参数
        params = parse_request_body(body)

        # 对于某些 header，忽略参数（因为是动态值）
        if header_hex in ignore_params_headers:
            params = {}

        # 创建唯一key用于去重
        param_values = tuple(sorted(params.items())) if params else ()
        unique_key = (header_hex, param_values)

        if unique_key not in seen_keys:
            seen_keys.add(unique_key)
            results.append({
                'header': header_hex,
                'params': params,
                'file': os.path.basename(f)
            })

    # 清理临时目录
    if temp_dir:
        shutil.rmtree(temp_dir)

    return results

def format_request_list(results):
    """格式化请求列表为可导入的 Python 模块"""
    lines = []
    lines.append('"""')
    lines.append('每日首次登录请求列表')
    lines.append('由 generate_first_login.py 自动生成')
    lines.append('"""')
    lines.append('')
    lines.append('FIRST_LOGIN_REQUESTS = [')

    for i, r in enumerate(results):
        params_str = ""
        if r['params']:
            for k, v in sorted(r['params'].items()):
                params_str += f', "{k}": {repr(v)}'

        lines.append(f'    {{"ads":"fl_{i}", "times":1, "hexstringheader":"{r["header"]}"{params_str}}},  # {r["file"]}')

    lines.append(']')
    lines.append('')

    return '\n'.join(lines)

def main():
    source_path = sys.argv[1] if len(sys.argv) > 1 else 'lg'

    if not os.path.exists(source_path):
        print(f"错误: {source_path} 不存在")
        sys.exit(1)

    results = generate_first_login_requests(source_path)

    output = format_request_list(results)

    # 保存到 modules 目录
    output_file = 'modules/first_login_requests.py'
    with open(output_file, 'w') as f:
        f.write(output)
    print(f"已生成 {len(results)} 个请求到 {output_file}")

if __name__ == "__main__":
    main()
