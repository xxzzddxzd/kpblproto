#!/usr/bin/env python3
"""
通用请求序列生成器
从 Charles 导出的 .chlz 文件生成请求列表，输出到该文件所在目录下

用法: python generate_requests.py <chlz_file_or_dir>
示例: python generate_requests.py nuanchunhuodong/Untitled.chlz
      python generate_requests.py nuanchunhuodong
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
    if '-req.bin' in name:
        return int(name.split('-')[0])
    name = name.replace('index', '').replace('.html', '')
    return int(name) if name else 0

def parse_request_body(body):
    """尝试用 request_body 解析并提取 i2, i3, i4, i5 等参数"""
    params = {}
    try:
        req = kpbl_pb2.request_body()
        req.ParseFromString(body)

        if req.i2 != 0:
            params['request_body_i2'] = req.i2
        if req.i3 != 0:
            params['request_body_i3'] = req.i3
        if req.i4 != 0:
            params['request_body_i4'] = req.i4
        if req.i5:
            params['request_body_i5'] = req.i5

    except Exception:
        pass

    return params

def extract_chlz(chlz_path, extract_dir):
    """解压 .chlz 文件到指定目录"""
    with zipfile.ZipFile(chlz_path, 'r') as zf:
        zf.extractall(extract_dir)

def generate_requests(source_path):
    """
    从 chlz 文件或目录生成请求列表

    Args:
        source_path: .chlz 文件路径或包含 .chlz / *-req.bin 文件的目录

    Returns:
        list: 请求配置列表
    """
    temp_dir = None

    if source_path.endswith('.chlz'):
        temp_dir = tempfile.mkdtemp()
        extract_chlz(source_path, temp_dir)
        work_dir = temp_dir
        file_pattern = '*-req.bin'
    elif os.path.isdir(source_path):
        work_dir = source_path
        chlz_files = glob.glob(os.path.join(source_path, '*.chlz'))
        if chlz_files:
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

    files = glob.glob(os.path.join(work_dir, file_pattern))
    files.sort(key=extract_num)

    # 排除的 header（登录7527和心跳8927）
    excluded_headers = {'7527', '8927'}
    # 需要忽略参数的 header（参数是时间戳或动态值）
    ignore_params_headers = {'8a27', 'f277'}

    results = []
    seen_keys = set()

    for f in files:
        with open(f, 'rb') as fp:
            data = fp.read()

        if len(data) < 4:
            continue

        header_bytes = data[:2]
        header_hex = binascii.hexlify(header_bytes).decode()

        if header_hex in excluded_headers:
            continue

        if '-req.bin' in f:
            body = data[4:]
        else:
            body = data[6:]

        params = parse_request_body(body)

        if header_hex in ignore_params_headers:
            params = {}

        param_values = tuple(sorted(params.items())) if params else ()
        unique_key = (header_hex, param_values)

        if unique_key not in seen_keys:
            seen_keys.add(unique_key)
            results.append({
                'header': header_hex,
                'params': params,
                'file': os.path.basename(f)
            })

    if temp_dir:
        shutil.rmtree(temp_dir)

    return results

def format_request_list(results, list_name='REQUESTS'):
    """格式化请求列表为可导入的 Python 模块"""
    lines = []
    lines.append('"""')
    lines.append('请求列表')
    lines.append('由 generate_requests.py 自动生成')
    lines.append('"""')
    lines.append('')
    lines.append(f'{list_name} = [')

    for i, r in enumerate(results):
        params_str = ""
        if r['params']:
            for k, v in sorted(r['params'].items()):
                params_str += f', "{k}": {repr(v)}'

        lines.append(f'    {{"ads":"req_{i}", "times":1, "hexstringheader":"{r["header"]}"{params_str}}},  # {r["file"]}')

    lines.append(']')
    lines.append('')

    return '\n'.join(lines)

def get_output_path(source_path):
    """根据输入路径确定输出文件路径，输出到输入文件所在目录下"""
    if source_path.endswith('.chlz'):
        base_name = os.path.splitext(os.path.basename(source_path))[0]
        output_dir = os.path.dirname(source_path) or '.'
    elif os.path.isdir(source_path):
        base_name = os.path.basename(os.path.abspath(source_path))
        output_dir = source_path
    else:
        base_name = 'output'
        output_dir = '.'

    # 文件名: requests_<basename>.py
    output_file = os.path.join(output_dir, f'requests_{base_name}.py')
    return output_file

def main():
    if len(sys.argv) < 2:
        print("用法: python generate_requests.py <chlz_file_or_dir>")
        print("示例: python generate_requests.py nuanchunhuodong/Untitled.chlz")
        print("      python generate_requests.py nuanchunhuodong")
        sys.exit(1)

    source_path = sys.argv[1]

    if not os.path.exists(source_path):
        print(f"错误: {source_path} 不存在")
        sys.exit(1)

    results = generate_requests(source_path)

    # 用目录名作为变量名（大写）
    if os.path.isdir(source_path):
        dir_name = os.path.basename(os.path.abspath(source_path)).upper()
    else:
        dir_name = os.path.splitext(os.path.basename(source_path))[0].upper()
    list_name = f'{dir_name}_REQUESTS'

    output = format_request_list(results, list_name=list_name)

    output_file = get_output_path(source_path)
    with open(output_file, 'w') as f:
        f.write(output)
    print(f"已生成 {len(results)} 个请求到 {output_file}")

if __name__ == "__main__":
    main()
