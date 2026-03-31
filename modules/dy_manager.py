"""
钓鱼管理模块
处理游戏中的钓鱼功能
"""

import logging
import binascii
import sys
from . import kpbl_pb2
from .kpbltools import ACManager, mask_account


class DYManager:
    """钓鱼管理器"""
    
    def __init__(self, account_name, delay=0.5):
        self.account_name = account_name
        self.ac_manager = ACManager(account_name, delay=delay)
        self.logger = logging.getLogger(f"DYManager_{account_name}")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.StreamHandler())
        
        # 钓鱼状态追踪变量
        self.initial_next_field = None
        self.next_field_initialized = False
    
    def fishing_start(self, fishfield):
        """
        执行钓鱼开始功能，并返回第一个字节的后4位
        
        Args:
            fishfield: 钓鱼区域
            
        Returns:
            str: 前两个字节的十六进制字符串，失败时返回"0"
        """
        # 钓鱼开始请求配置
        start_config = {
            "ads": f"钓鱼开始",
            "times": 1,
            "hexstringheader": "ed35",
            "request_body_i2": fishfield, # 区域
            "request_body_i3": 1, # 数量
            "request_body_i4": 2  # request_body_i4 命中中心
        }
        
        # 发送钓鱼开始请求
        start_response = self.ac_manager.do_common_request(self.account_name, start_config, showres=0)
        print(f"<{mask_account(self.account_name)}> 钓鱼开始...")
        
        # 解析钓鱼开始响应
        if start_response and len(start_response) > 10:
            try:
                # 从第4个字节开始提取数据
                start_data = start_response[8:]
                
                # 使用fishing_start_response结构解析数据
                fishing_start = kpbl_pb2.fishing_start_response()
                fishing_start.ParseFromString(start_data)
                
                # 提取field3的第一个字节
                if hasattr(fishing_start, 'field3') and fishing_start.field3:
                    field3_bytes = fishing_start.field3
                    if len(field3_bytes) >= 1:
                        first_byte = field3_bytes[0]
                        first_byte_hex = hex(first_byte)[2:].zfill(2)  # 转为两位十六进制
                        
                        # 提取前两个字节的十六进制
                        if len(field3_bytes) >= 2:
                            second_byte = field3_bytes[1]
                            second_byte_hex = hex(second_byte)[2:].zfill(2)
                            first_two_bytes_hex = first_byte_hex + second_byte_hex
                        else:
                            first_two_bytes_hex = first_byte_hex
                        
                        # 将整个field3转为十六进制字符串(调试用)
                        field3_hex = binascii.hexlify(field3_bytes).decode()
                        
                        print(f"<{mask_account(self.account_name)}> 钓鱼开始响应field3前两字节: 0x{first_two_bytes_hex}, 完整数据: 0x{field3_hex}")
                        
                        return first_two_bytes_hex
                    else:
                        print(f"<{mask_account(self.account_name)}> 钓鱼开始响应field3为空")
                else:
                    print(f"<{mask_account(self.account_name)}> 钓鱼开始响应无field3字段")
                    
                # 输出完整的十六进制内容用于调试
                hex_data = binascii.hexlify(start_response).decode()
                print(f"钓鱼开始原始数据: {hex_data[:60]}...")
            except Exception as e:
                print(f"<{mask_account(self.account_name)}> 解析钓鱼开始响应出错: {str(e)}")
                hex_data = binascii.hexlify(start_response).decode()
                print(f"钓鱼开始原始数据: {hex_data[:60]}...")
        
        # 如果无法正常获取后4位，则返回0
        return "0"
    
    def fishing_complete(self):
        """
        执行钓鱼完成功能，并返回捕获的重量
        
        Returns:
            int: 捕获的鱼的重量，0表示失败
        """
        # 钓鱼完成请求配置
        complete_config = {"ads": f"钓鱼完成","times": 1,"hexstringheader": "ef 35 ","request_body_i2": 40}
        
        # 发送钓鱼完成请求
        complete_response = self.ac_manager.do_common_request(self.account_name, complete_config, showres=0)
        
        # 解析钓鱼结果
        if complete_response and len(complete_response) > 20:
            try:
                # 从第4个字节开始提取数据
                data = complete_response[6:]
                
                # 使用proto定义的fishing_response结构解析数据
                fishing_resp = kpbl_pb2.fishing_response()
                fishing_resp.ParseFromString(data)
                
                # 获取当前重量和总重量
                current_weight = fishing_resp.current_weight
                overall_weight = fishing_resp.total_info.overall_weight if hasattr(fishing_resp, 'total_info') else 0
                next_field = fishing_resp.total_info.next_field if hasattr(fishing_resp, 'total_info') and hasattr(fishing_resp.total_info, 'next_field') else 0
                
                # 如果next_field还未初始化，则记录初始值
                if not self.next_field_initialized and next_field > 0:
                    self.initial_next_field = next_field
                    self.next_field_initialized = True
                    print(f"<{mask_account(self.account_name)}> 初始next_field值: {self.initial_next_field}")
                
                # 检查next_field是否发生变化
                if self.next_field_initialized and next_field != self.initial_next_field and next_field > 0:
                    print(f"<{mask_account(self.account_name)}> next_field已变化! 初始值: {self.initial_next_field}, 当前值: {next_field}")
                    print(f"<{mask_account(self.account_name)}> 目标已达成，程序将退出...")
                    sys.exit(0)  # 退出程序
                
                # 打印结果
                if hasattr(fishing_resp, 'total_info') and hasattr(fishing_resp.total_info, 'next_field'):
                    print(f"<{mask_account(self.account_name)}> 钓鱼完成! 当前重量: {current_weight}g, 历史总计: {overall_weight}g/{next_field}")
                else:
                    print(f"<{mask_account(self.account_name)}> 钓鱼完成! 当前重量: {current_weight}g, 历史总计: {overall_weight}g")
                
                return current_weight
            
            except Exception as e:
                print(f"<{mask_account(self.account_name)}> 解析钓鱼结果出错: {str(e)}")
                # 打印原始数据用于调试
                hex_data = binascii.hexlify(complete_response).decode()
                print(f"原始数据: {hex_data}")
        else:
            print(f"<{mask_account(self.account_name)}> 钓鱼完成，但没有收到有效响应")
        
        return 0
    
    def abort_fishing(self):
        """
        执行钓鱼中止功能
        """
        abort_config = {"ads": f"钓鱼中止","times": 1,"hexstringheader": "ef 35 bb 01 "}
        self.ac_manager.do_common_request(self.account_name, abort_config, showres=0)
    
    fish_hex_type_lv = {
        "gold": ["0x9e", "0xa4", "0xaa", "0xb0"],
        "epic": ["0x9c", "0xa2", "0xa8", "0xae","0x9d", "0xa3", "0xa9", "0xaf"],
        "rare": ["0x99", "0x9f", "0xa5", "0xab","0x9a", "0xa0", "0xa6", "0xac","0x9b", "0xa1", "0xa7", "0xad"],
    }

    def do_fishing(self, field=4, times=1, consider_abort=False):
        """
        执行钓鱼功能
        
        Args:
            field: 钓鱼区域，默认为4
            times: 钓鱼次数
            consider_abort: 是否考虑中止（当捕获普通鱼时）
            
        Returns:
            bool: 执行成功返回True
        """
        # 重置next_field相关的实例变量
        self.initial_next_field = None
        self.next_field_initialized = False
        
        # 创建一个字典来统计所有十六进制类型的出现次数
        hex_type_counts = {}
        
        print(f"<{mask_account(self.account_name)}> 开始执行钓鱼操作，次数: {times}")
        total_weight = 0  # 总重量
        
        for i in range(times):
            # 调用钓鱼开始函数
            result = self.fishing_start(field)
            print(f"<{mask_account(self.account_name)}> 第{i+1}/{times}次钓鱼开始，结果: {result}")
            
            # 统计十六进制类型
            hex_type = result[:2]
            hex_type_counts[hex_type] = hex_type_counts.get(hex_type, 0) + 1
            
            # 显示当前统计数据
            print(f"<{mask_account(self.account_name)}> 检测到类型 0x{hex_type}，当前统计:")
            sorted_types = sorted(hex_type_counts.items(), key=lambda x: x[1], reverse=True)
            for h_type, count in sorted_types:
                hex_with_prefix = f"0x{h_type}"
                if hex_with_prefix in self.fish_hex_type_lv["gold"]:
                    color_prefix = "\033[33m"  # yellow
                elif hex_with_prefix in self.fish_hex_type_lv["epic"]:
                    color_prefix = "\033[34m"  # blue
                else:
                    color_prefix = ""
                color_suffix = "\033[0m" if color_prefix else ""
                print(f"{color_prefix}    0x{h_type}: {count}次, 占比 {count/(i+1)*100:.2f}%{color_suffix}")
            
            # if consider_abort and (f"0x{hex_type}" not in self.fish_hex_type_lv["gold"]):
            if consider_abort and (f"0x{hex_type}" in self.fish_hex_type_lv["rare"]):
                print(f'<{mask_account(self.account_name)}> 非金色鱼(0x{hex_type})，中止')
                self.abort_fishing()
            else:
                print(f'<{mask_account(self.account_name)}> (0x{hex_type}) finish')
                # 调用钓鱼完成函数
                current_weight = self.fishing_complete()
                # 更新总重量
                total_weight += current_weight
                if current_weight > 0:
                    print(f"<{mask_account(self.account_name)}> 第{i+1}/{times}次钓鱼完成，捕获: {current_weight}g，累计: {total_weight}g")
                    if (f"0x{hex_type}" in self.fish_hex_type_lv["gold"]):
                        input("press enter to continue")
                else:
                    break
        
        # 打印最终统计结果
        print(f"\n<{mask_account(self.account_name)}> 钓鱼操作完成，共执行{times}次，本次总捕获: {total_weight}g")
        print(f"<{mask_account(self.account_name)}> 十六进制类型统计:")
        
        sorted_types = sorted(hex_type_counts.items(), key=lambda x: x[1], reverse=True)
        for hex_type, count in sorted_types:
            hex_with_prefix = f"0x{hex_type}"
            if hex_with_prefix in self.fish_hex_type_lv["gold"]:
                color_prefix = "\033[33m"  # yellow
            elif hex_with_prefix in self.fish_hex_type_lv["epic"]:
                color_prefix = "\033[34m"  # blue
            else:
                color_prefix = ""
            color_suffix = "\033[0m" if color_prefix else ""
            print(f"{color_prefix}    0x{hex_type}: {count}次, 占比 {count/times*100:.2f}%{color_suffix}")
        
        return True
    
    def execute_fishing(self, field, times, consider_abort=False):
        """
        执行钓鱼的接口方法，与main.py兼容
        
        Args:
            field: 钓鱼区域
            times: 钓鱼次数
            consider_abort: 是否考虑中止
            
        Returns:
            bool: 执行成功返回True
        """
        try:
            return self.do_fishing(field, times, consider_abort)
        except Exception as e:
            print(f"<{mask_account(self.account_name)}> 钓鱼执行失败: {e}")
            return False