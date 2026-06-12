"""
钓鱼管理模块
处理游戏中的钓鱼功能
"""

import logging
import binascii
from . import kpbl_pb2
from .kpbltools import ACManager, mask_account


class DYManager:
    """钓鱼管理器"""

    FISHING_ACTIVITY_ID = 202602091
    BAIT_TYPE = 2001
    FISH_WEIGHT_TYPE = 2002
    SHIP_TICKET_SHOP_ID = 22100
    SHOP_EQUIP_BOX_ID = 200002
    INVENTORY_BOX_TYPE = 71
    FIELD2_MIN_WEIGHT = 7500

    TASK_TARGETS = {
        104000: 1,
        104001: 2,
        104002: 3,
        104003: 400,
        104007: 10,
        104008: 10,
        104009: 50,
        104010: 10,
    }

    TASK_NAMES = {
        104000: "钓鱼每日104000",
        104001: "钓鱼每日104001",
        104002: "钓鱼每日104002",
        104003: "钓鱼每日104003",
        104004: "钓鱼每日104004",
        104005: "钓鱼每日104005",
        104006: "钓鱼每日104006",
        104007: "黑市购买10次",
        104008: "商店开箱10次",
        104009: "钓鱼每日104009",
        104010: "背包开箱10次",
    }

    SUPPLEMENT_TASK_IDS = {104007, 104008, 104010}
    TASK_COMPLETED_VALUES = {
        # 104007 在 9d2c 中完成后出现的是奖励鱼饵数 3，不是 10 次进度。
        104007: 3,
    }
    
    def __init__(self, account_name, delay=0.5, showres=0, ac_manager=None):
        self.account_name = account_name
        self.ac_manager = ac_manager or ACManager(account_name, delay=delay, showres=showres)
        self.logger = logging.getLogger(f"DYManager_{account_name}")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.StreamHandler())
        self.showres = showres
        self.last_bait_count = None
        self.last_overall_weight = 0
        self.last_next_field = 0
        self.available_fishing_areas = []
        
        # 钓鱼状态追踪变量
        self.initial_next_field = None
        self.next_field_initialized = False

    @staticmethod
    def _decode_varint(data, pos):
        result = 0
        shift = 0
        while pos < len(data):
            byte = data[pos]
            pos += 1
            result |= (byte & 0x7F) << shift
            if not (byte & 0x80):
                return result, pos
            shift += 7
        return None, pos

    @classmethod
    def _iter_proto_fields(cls, data):
        pos = 0
        while pos < len(data):
            key, pos = cls._decode_varint(data, pos)
            if key is None:
                break
            field_no = key >> 3
            wire_type = key & 7
            if wire_type == 0:
                value, pos = cls._decode_varint(data, pos)
                yield field_no, wire_type, value
            elif wire_type == 1:
                if pos + 8 > len(data):
                    break
                yield field_no, wire_type, data[pos:pos + 8]
                pos += 8
            elif wire_type == 2:
                size, pos = cls._decode_varint(data, pos)
                if size is None or pos + size > len(data):
                    break
                yield field_no, wire_type, data[pos:pos + size]
                pos += size
            elif wire_type == 5:
                if pos + 4 > len(data):
                    break
                yield field_no, wire_type, data[pos:pos + 4]
                pos += 4
            else:
                break

    @classmethod
    def _scalar_fields(cls, data):
        scalars = {}
        repeated = {}
        for field_no, wire_type, value in cls._iter_proto_fields(data):
            if wire_type != 0:
                continue
            if field_no in scalars:
                repeated.setdefault(field_no, [scalars[field_no]]).append(value)
            else:
                scalars[field_no] = value
        for field_no, values in repeated.items():
            scalars[field_no] = values
        return scalars

    @classmethod
    def _extract_new_complete_info(cls, data):
        """解析新版 ef35 响应: field2 内含奖励和累计进度。"""
        current_weight = 0
        overall_weight = 0
        next_field = 0

        for field_no, wire_type, value in cls._iter_proto_fields(data):
            if field_no != 2 or wire_type != 2:
                continue
            for inner_no, inner_wire, inner_value in cls._iter_proto_fields(value):
                if inner_no == 3 and inner_wire == 2:
                    reward = cls._scalar_fields(inner_value)
                    if reward.get(2) == 2002 and reward.get(3):
                        current_weight = int(reward.get(3))
                elif inner_no == 7 and inner_wire == 2:
                    for item_no, item_wire, item_value in cls._iter_proto_fields(inner_value):
                        if item_no != 2 or item_wire != 2:
                            continue
                        item = cls._scalar_fields(item_value)
                        if item.get(2) == 2002:
                            overall_weight = int(item.get(5) or item.get(3) or overall_weight)
                elif inner_no == 49 and inner_wire == 2:
                    for progress_no, progress_wire, progress_value in cls._iter_proto_fields(inner_value):
                        if progress_no != 2 or progress_wire != 2:
                            continue
                        progress = cls._scalar_fields(progress_value)
                        overall_weight = int(progress.get(5) or overall_weight)
                        raw_next = progress.get(7)
                        if isinstance(raw_next, int):
                            next_field = raw_next
            break

        return current_weight, overall_weight, next_field

    @classmethod
    def _extract_item_count(cls, data, item_type):
        """从通用主响应 field2.field7 中提取指定物品类型的最新数量。"""
        found = None
        for field_no, wire_type, value in cls._iter_proto_fields(data):
            if field_no != 2 or wire_type != 2:
                continue
            for inner_no, inner_wire, inner_value in cls._iter_proto_fields(value):
                if inner_no != 7 or inner_wire != 2:
                    continue
                for item_no, item_wire, item_value in cls._iter_proto_fields(inner_value):
                    if item_no != 2 or item_wire != 2:
                        continue
                    item = cls._scalar_fields(item_value)
                    if item.get(2) == item_type:
                        found = int(item.get(5) or item.get(3) or 0)
            break
        return found

    @classmethod
    def _extract_reward_items(cls, data):
        """从通用主响应 field2.field3 中提取奖励物品。"""
        rewards = []
        for field_no, wire_type, value in cls._iter_proto_fields(data):
            if field_no != 2 or wire_type != 2:
                continue
            for inner_no, inner_wire, inner_value in cls._iter_proto_fields(value):
                if inner_no == 3 and inner_wire == 2:
                    reward = cls._scalar_fields(inner_value)
                    if reward:
                        rewards.append(reward)
            break
        return rewards

    @classmethod
    def _extract_activity_updates(cls, data, activity_id):
        """从动作响应 field48/field49 中提取活动任务进度更新。"""
        updates = {}
        for field_no, wire_type, value in cls._iter_proto_fields(data):
            if field_no != 2 or wire_type != 2:
                continue
            for inner_no, inner_wire, inner_value in cls._iter_proto_fields(value):
                if inner_no not in (48, 49) or inner_wire != 2:
                    continue
                activity = cls._scalar_fields(inner_value)
                if activity.get(1) != activity_id:
                    continue
                for progress_no, progress_wire, progress_value in cls._iter_proto_fields(inner_value):
                    if progress_no != 2 or progress_wire != 2:
                        continue
                    progress = cls._scalar_fields(progress_value)
                    task_id = progress.get(1)
                    if task_id:
                        updates[int(task_id)] = int(progress.get(2) or 0)
            break
        return updates

    def _remember_bait_count(self, response):
        if not response or len(response) <= 6:
            return None
        bait_count = self._extract_item_count(response[6:], self.BAIT_TYPE)
        if bait_count is not None:
            self.last_bait_count = bait_count
        return bait_count

    def get_bait_count(self):
        if self.last_bait_count is not None:
            return self.last_bait_count
        _, count = self.ac_manager.getItemIdByType(self.BAIT_TYPE)
        return count

    def get_fish_weight(self):
        _, count = self.ac_manager.getItemIdByType(self.FISH_WEIGHT_TYPE)
        return count

    def _status_code(self, response):
        if not response or len(response) <= 6:
            return None
        try:
            return self.ac_manager.get_status_code(response)
        except Exception:
            return None

    def _print_short_response(self, action, response):
        status = self._status_code(response)
        if status is None:
            print(f"<{mask_account(self.account_name)}> {action}失败: 无有效响应")
        else:
            print(f"<{mask_account(self.account_name)}> {action}失败: status={status}, len={len(response)}")
        return status

    def query_fishing_area_status(self):
        """fd35: 查询钓鱼入口/区域状态。"""
        config = {"ads": "钓鱼入口状态", "times": 1, "hexstringheader": "fd35"}
        res = self.ac_manager.do_common_request(self.account_name, config, showres=0)
        areas = set()
        rankings = []
        max_area = 0
        if not res or len(res) <= 6:
            return [], rankings

        for field_no, wire_type, value in self._iter_proto_fields(res[6:]):
            if wire_type == 0 and field_no in (6, 8):
                max_area = max(max_area, int(value or 0))
            elif field_no in (3, 4) and wire_type == 2:
                entry = self._scalar_fields(value)
                area_id = int(entry.get(2) or 0)
                ranking = (area_id, int(entry.get(3) or 0))
                if area_id:
                    areas.add(area_id)
                if area_id and ranking not in rankings:
                    rankings.append(ranking)
        if max_area:
            areas = {area_id for area_id in areas if area_id <= max_area}
            if not areas:
                areas = set(range(1, max_area + 1))
        return sorted(areas), rankings

    def _field_for_overall_weight(self, overall_weight, areas=None):
        areas = sorted(areas if areas is not None else self.available_fishing_areas)
        if not areas:
            return 1
        if overall_weight >= self.FIELD2_MIN_WEIGHT and 2 in areas:
            return 2
        return min(areas)

    def resolve_fishing_field(self, fishfield=None, overall_weight=0):
        if fishfield:
            return int(fishfield)
        areas, rankings = self.query_fishing_area_status()
        self.available_fishing_areas = areas
        if areas:
            selected = self._field_for_overall_weight(overall_weight, areas)
            print(f"<{mask_account(self.account_name)}> 钓鱼自动区域: {selected}，可用区域={areas}，历史总计={overall_weight}g")
            return selected
        print(f"<{mask_account(self.account_name)}> 未解析到钓鱼区域，默认使用区域1")
        return 1
    
    def fishing_start(self, fishfield):
        """
        执行钓鱼开始功能，并返回第一个字节的后4位
        
        Args:
            fishfield: 钓鱼区域
            
        Returns:
            str: 前两个字节的十六进制字符串，失败时返回"00"
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
        bait_count = self._remember_bait_count(start_response)
        if bait_count is not None:
            print(f"<{mask_account(self.account_name)}> 当前鱼饵: {bait_count}")
        
        # 解析钓鱼开始响应
        if start_response and len(start_response) > 10:
            try:
                # 响应包头为 6 字节，body 从第 6 字节后开始。
                start_data = start_response[6:]
                
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
                    
                print(f"<{mask_account(self.account_name)}> 钓鱼开始响应无旧版鱼种字段，按新版响应继续")
            except Exception as e:
                print(f"<{mask_account(self.account_name)}> 解析钓鱼开始响应出错: {str(e)}")
                hex_data = binascii.hexlify(start_response).decode()
                print(f"钓鱼开始原始数据: {hex_data[:60]}...")
        else:
            status = self._print_short_response("钓鱼开始", start_response)
            if status == 13701:
                print(f"<{mask_account(self.account_name)}> 钓鱼开始条件不满足，检查区域/鱼饵或先执行 dy rw")
            return None
        
        # 如果无法正常获取后4位，则返回0
        return "00"
    
    def fishing_complete(self, fishfield):
        """
        执行钓鱼完成功能，并返回捕获的重量
        
        Returns:
            int: 捕获的鱼的重量，0表示失败
        """
        # 钓鱼完成请求配置
        complete_config = {"ads": f"钓鱼完成","times": 1,"hexstringheader": "ef 35 ","request_body_i2": fishfield}
        
        # 发送钓鱼完成请求
        complete_response = self.ac_manager.do_common_request(self.account_name, complete_config, showres=0)
        self._remember_bait_count(complete_response)
        
        # 解析钓鱼结果
        if complete_response and len(complete_response) > 20:
            try:
                # 响应包头为 6 字节，body 从第 6 字节后开始。
                data = complete_response[6:]
                
                # 使用proto定义的fishing_response结构解析数据
                fishing_resp = kpbl_pb2.fishing_response()
                fishing_resp.ParseFromString(data)
                
                # 获取当前重量和总重量；新版响应把信息放在 field2 的通用主响应里。
                current_weight = fishing_resp.current_weight
                overall_weight = fishing_resp.total_info.overall_weight if hasattr(fishing_resp, 'total_info') else 0
                next_field = fishing_resp.total_info.next_field if hasattr(fishing_resp, 'total_info') and hasattr(fishing_resp.total_info, 'next_field') else 0
                if current_weight == 0 and overall_weight == 0:
                    current_weight, overall_weight, next_field = self._extract_new_complete_info(data)
                self.last_overall_weight = overall_weight
                self.last_next_field = next_field
                
                # 如果next_field还未初始化，则记录初始值
                if not self.next_field_initialized and next_field > 0:
                    self.initial_next_field = next_field
                    self.next_field_initialized = True
                    print(f"<{mask_account(self.account_name)}> 初始next_field值: {self.initial_next_field}")
                
                # 检查next_field是否发生变化
                if self.next_field_initialized and next_field != self.initial_next_field and next_field > 0:
                    print(f"<{mask_account(self.account_name)}> next_field已变化! 初始值: {self.initial_next_field}, 当前值: {next_field}")
                    self.initial_next_field = next_field
                
                # 打印结果
                if next_field > 0:
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
            status = self._print_short_response("钓鱼完成", complete_response)
            if status == 702:
                print(f"<{mask_account(self.account_name)}> 当前没有可结算的钓鱼记录，跳过完成")
        
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

    def do_fishing(self, field=None, times=1, consider_abort=False, pause_on_gold=False):
        """
        执行钓鱼功能
        
        Args:
            field: 钓鱼区域，默认为4
            times: 钓鱼次数，<=0 表示用完当前鱼饵
            consider_abort: 是否考虑中止（当捕获普通鱼时）
            pause_on_gold: 钓到金色鱼时是否暂停等待输入
            
        Returns:
            bool: 执行成功返回True
        """
        auto_field = field is None
        initial_overall_weight = self.get_fish_weight() if auto_field else 0
        self.last_overall_weight = initial_overall_weight
        self.last_next_field = 0
        field = self.resolve_fishing_field(field, initial_overall_weight)
        bait_count = self.get_bait_count()
        if bait_count <= 0:
            print(f"<{mask_account(self.account_name)}> 鱼饵不足: {bait_count}，先执行 dy rw 领取/补钓鱼每日任务")
            return False
        times = int(times)
        if times <= 0:
            times = bait_count
            print(f"<{mask_account(self.account_name)}> 钓鱼次数: 全部鱼饵({times})")
        if times > bait_count:
            print(f"<{mask_account(self.account_name)}> 鱼饵不足以执行{times}次，自动调整为{bait_count}次")
            times = bait_count
        print(f"<{mask_account(self.account_name)}> 当前鱼饵: {bait_count}")

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
            if result is None:
                break
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
                current_weight = self.fishing_complete(field)
                # 更新总重量
                total_weight += current_weight
                if current_weight > 0:
                    print(f"<{mask_account(self.account_name)}> 第{i+1}/{times}次钓鱼完成，捕获: {current_weight}g，累计: {total_weight}g")
                    if auto_field:
                        next_field = self._field_for_overall_weight(self.last_overall_weight)
                        if next_field != field:
                            print(f"<{mask_account(self.account_name)}> 历史总计 {self.last_overall_weight}g，自动切换钓鱼区域: {field} -> {next_field}")
                            field = next_field
                    if pause_on_gold and (f"0x{hex_type}" in self.fish_hex_type_lv["gold"]):
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

    def query_daily_tasks(self):
        """9d2c: 查询钓鱼活动任务当前条目。"""
        config = {"ads": "钓鱼活动任务查询", "times": 1, "hexstringheader": "9d2c"}
        res = self.ac_manager.do_common_request(self.account_name, config, showres=0)
        tasks = {}
        if not res or len(res) <= 20:
            print(f"<{mask_account(self.account_name)}> 钓鱼任务查询无有效响应")
            return tasks
        try:
            resp = kpbl_pb2.acmanager_activity_info_response()
            resp.ParseFromString(res[6:])
            for activity in resp.activities:
                if activity.activity_id != self.FISHING_ACTIVITY_ID:
                    continue
                for reward in activity.rewards:
                    if reward.reward_id:
                        tasks[int(reward.reward_id)] = int(reward.reward_count)
                break
        except Exception as e:
            print(f"<{mask_account(self.account_name)}> 解析钓鱼任务出错: {e}")
        return tasks

    def print_daily_tasks(self, tasks, title="钓鱼每日任务"):
        if not tasks:
            print(f"<{mask_account(self.account_name)}> {title}: 无任务条目")
            return
        parts = []
        for task_id in sorted(tasks):
            name = self.TASK_NAMES.get(task_id, f"任务{task_id}")
            target = self.TASK_TARGETS.get(task_id)
            progress = tasks[task_id]
            completed_value = self.TASK_COMPLETED_VALUES.get(task_id)
            if completed_value is not None and progress == completed_value:
                parts.append(f"{name}({task_id})=可领取({progress})")
            elif target:
                parts.append(f"{name}({task_id})={progress}/{target}")
            else:
                parts.append(f"{name}({task_id})={progress}")
        print(f"<{mask_account(self.account_name)}> {title}: " + ", ".join(parts))

    def _is_claimable_task(self, task_id, progress):
        completed_value = self.TASK_COMPLETED_VALUES.get(task_id)
        if completed_value is not None and progress == completed_value:
            return True
        target = self.TASK_TARGETS.get(task_id)
        return target is not None and progress >= target

    def claim_fishing_task(self, task_id):
        config = {
            "ads": f"领取钓鱼任务{task_id}",
            "times": 1,
            "hexstringheader": "9f2c",
            "request_body_i2": self.FISHING_ACTIVITY_ID,
            "request_body_i3": int(task_id),
        }
        res = self.ac_manager.do_common_request(self.account_name, config, showres=0)
        if not res or len(res) <= 6:
            print(f"<{mask_account(self.account_name)}> {task_id} 领取失败: 无响应")
            return False

        body = res[6:]
        rewards = self._extract_reward_items(body)
        bait_reward = sum(int(r.get(3) or 0) for r in rewards if r.get(2) == self.BAIT_TYPE)
        bait_count = self._remember_bait_count(res)
        if bait_reward:
            print(f"<{mask_account(self.account_name)}> 领取{self.TASK_NAMES.get(task_id, task_id)}: 鱼饵 +{bait_reward}，当前 {bait_count if bait_count is not None else '?'}")
            return True

        status = None
        try:
            status = self.ac_manager.get_status_code(res)
        except Exception:
            pass
        print(f"<{mask_account(self.account_name)}> {task_id} 未领取到鱼饵，status={status}, len={len(res)}")
        return False

    def claim_ready_fishing_tasks(self, tasks):
        claimed = []
        for task_id, progress in sorted(tasks.items()):
            if self._is_claimable_task(task_id, progress):
                if self.claim_fishing_task(task_id):
                    claimed.append(task_id)
        return claimed

    def buy_ship_tickets_for_task(self, count=10):
        count = max(0, int(count))
        if count <= 0:
            return {}
        config = {
            "ads": f"钓鱼任务-黑市购买船票{count}",
            "times": 1,
            "hexstringheader": "6532",
            "request_body_i2": 2,
            "request_body_i3": self.SHIP_TICKET_SHOP_ID,
            "request_body_i4": count,
        }
        res = self.ac_manager.do_common_request(self.account_name, config, showres=0)
        if res and len(res) > 6:
            return self._extract_activity_updates(res[6:], self.FISHING_ACTIVITY_ID)
        return {}

    def open_shop_boxes_for_task(self, count=10):
        count = max(0, int(count))
        if count <= 0:
            return {}
        config = {
            "ads": f"钓鱼任务-商店开箱10连(缺{count})",
            "times": 1,
            "hexstringheader": "c72b",
            "request_body_i2": self.SHOP_EQUIP_BOX_ID,
            "request_body_i3": 2,
            "request_body_i4": 2,
        }
        res = self.ac_manager.do_common_request(self.account_name, config, showres=0)
        if res and len(res) > 6:
            return self._extract_activity_updates(res[6:], self.FISHING_ACTIVITY_ID)
        return {}

    def open_inventory_boxes_for_task(self, count=10):
        box_id, box_count = self.ac_manager.getItemIdByType(self.INVENTORY_BOX_TYPE)
        if not box_id:
            print(f"<{mask_account(self.account_name)}> 未找到type={self.INVENTORY_BOX_TYPE}的背包箱子")
            return {}
        actual = min(int(count), int(box_count or 0))
        if actual <= 0:
            print(f"<{mask_account(self.account_name)}> 背包箱子数量不足: {box_count}")
            return {}
        config = {
            "ads": f"钓鱼任务-背包开箱{actual}",
            "times": 1,
            "hexstringheader": "074f",
            "request_body_i2": int(box_id),
            "request_body_i3": actual,
        }
        res = self.ac_manager.do_common_request(self.account_name, config, showres=0)
        if res and len(res) > 6:
            return self._extract_activity_updates(res[6:], self.FISHING_ACTIVITY_ID)
        return {}

    def _task_missing(self, tasks, task_id):
        target = self.TASK_TARGETS.get(task_id, 0)
        progress = int(tasks.get(task_id, 0) or 0)
        if self._is_claimable_task(task_id, progress):
            return 0, progress, target
        return max(target - progress, 0), progress, target

    def _has_supplement_daily_tasks(self, tasks):
        return bool(self.SUPPLEMENT_TASK_IDS.intersection(tasks.keys()))

    def _should_supplement_task(self, tasks, task_id, claimed_tasks):
        if task_id in claimed_tasks:
            print(f"<{mask_account(self.account_name)}> {self.TASK_NAMES[task_id]} 已领取，跳过补做")
            return False
        if task_id in tasks:
            return True
        print(f"<{mask_account(self.account_name)}> 未检测到{self.TASK_NAMES[task_id]}，跳过补做")
        return False

    def _run_task_action(self, task_id, label, action, missing):
        if missing <= 0:
            return {}
        print(f"<{mask_account(self.account_name)}> 执行{label}: 当前缺 {missing}")
        updates = action()
        if updates:
            print(f"<{mask_account(self.account_name)}> 活动进度更新: {updates}")
        tasks = self.query_daily_tasks()
        progress = tasks.get(task_id, updates.get(task_id, 0))
        if self._is_claimable_task(task_id, progress):
            self.claim_fishing_task(task_id)
        else:
            missing_now, progress_now, target = self._task_missing(tasks, task_id)
            print(f"<{mask_account(self.account_name)}> {self.TASK_NAMES.get(task_id, task_id)} 仍未完成: {progress_now}/{target}，还差 {missing_now}")
        return updates

    def run_daily_tasks(self):
        """钓鱼每日任务：查询已完成项，补已定义动作，领取鱼饵。"""
        tasks = self.query_daily_tasks()
        self.print_daily_tasks(tasks, "初始钓鱼任务")
        has_supplement_tasks = self._has_supplement_daily_tasks(tasks)
        claimed_tasks = set(self.claim_ready_fishing_tasks(tasks))

        if not has_supplement_tasks:
            print(f"<{mask_account(self.account_name)}> 未检测到可补钓鱼每日任务，跳过补做")
            tasks = self.query_daily_tasks()
            self.print_daily_tasks(tasks, "剩余钓鱼任务")
            print(f"<{mask_account(self.account_name)}> 最终鱼饵数量: {self.get_bait_count()}")
            return True

        tasks = self.query_daily_tasks()
        missing, _, _ = self._task_missing(tasks, 104007)
        if self._should_supplement_task(tasks, 104007, claimed_tasks) and missing:
            self._run_task_action(104007, f"黑市购买{missing}张船票", lambda: self.buy_ship_tickets_for_task(missing), missing)
        elif self._is_claimable_task(104007, tasks.get(104007, 0)):
            self.claim_fishing_task(104007)

        tasks = self.query_daily_tasks()
        missing, _, _ = self._task_missing(tasks, 104008)
        if self._should_supplement_task(tasks, 104008, claimed_tasks) and missing:
            self._run_task_action(104008, f"商店开箱10连(缺{missing})", lambda: self.open_shop_boxes_for_task(missing), missing)
        elif self._is_claimable_task(104008, tasks.get(104008, 0)):
            self.claim_fishing_task(104008)

        tasks = self.query_daily_tasks()
        missing, _, _ = self._task_missing(tasks, 104010)
        if self._should_supplement_task(tasks, 104010, claimed_tasks) and missing:
            self._run_task_action(104010, f"背包开箱{missing}次", lambda: self.open_inventory_boxes_for_task(missing), missing)
        elif self._is_claimable_task(104010, tasks.get(104010, 0)):
            self.claim_fishing_task(104010)

        tasks = self.query_daily_tasks()
        self.print_daily_tasks(tasks, "剩余钓鱼任务")
        self.claim_ready_fishing_tasks(tasks)
        print(f"<{mask_account(self.account_name)}> 最终鱼饵数量: {self.get_bait_count()}")
        return True
    
    def execute_fishing(self, field, times, consider_abort=False, pause_on_gold=False):
        """
        执行钓鱼的接口方法，与main.py兼容
        
        Args:
            field: 钓鱼区域
            times: 钓鱼次数
            consider_abort: 是否考虑中止
            pause_on_gold: 钓到金色鱼时是否暂停等待输入
            
        Returns:
            bool: 执行成功返回True
        """
        try:
            return self.do_fishing(field, times, consider_abort, pause_on_gold=pause_on_gold)
        except Exception as e:
            print(f"<{mask_account(self.account_name)}> 钓鱼执行失败: {e}")
            return False
