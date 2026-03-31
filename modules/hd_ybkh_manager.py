"""
活动月饼狂欢管理模块
处理游戏中的月饼狂欢活动功能
"""

import logging
from .kpbltools import ACManager, mask_account
from . import kpbl_pb2

class HdYbkhManager:
    """活动月饼狂欢管理器"""
    
    # ANSI颜色代码
    COLOR_GREEN = '\033[92m'
    COLOR_RESET = '\033[0m'
    
    # itemid 映射表
    ITEM_ID_MAP = {
        1: "枣花",
        2: "樱花",
        3: "黑巧",
        4: "抹茶",
        5: "莲花",
        6: "特殊=2,钻石",
        6: "特殊=6,钥匙",
        7: "特殊=2538,桂花",
        8: "炸弹",
        12: "锤子",
    }
    
    # status 状态映射表
    STATUS_MAP = {
        0: "未翻开",
        1: "翻开",
        2: "空"
    }
    
    # 物品颜色映射（itemid -> 颜色代码）
    ITEM_COLOR_MAP = {
        5: COLOR_GREEN,  # 莲花 -> 绿色
    }
    
    def __init__(self, account_name, showres=0, delay=0.5):
        """
        初始化月饼狂欢管理器
        
        Args:
            account_name: 账号名称
            showres: 是否显示响应详情，0=不显示，1=显示
            delay: 请求延迟时间（秒）
        """
        self.account_name = account_name
        self.ac_manager = ACManager(account_name, showres=showres, delay=delay)
        self.logger = logging.getLogger(f"HdYbkhManager_{account_name}")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.StreamHandler())
        self.showres = showres
        self.I8_VALUE = self.ac_manager.I8_VALUE
        self.unknown_item_ids = set()  # 记录未知的 itemid
    
    def pos_to_xy(self, pos):
        """
        将pos反向推导为x, y坐标
        根据公式: pos = (x-1)*8 + (y-1)
        反向推导: x = pos // 8 + 1, y = pos % 8 + 1
        
        Args:
            pos: 线性位置值（0-63表示8x8网格）
            
        Returns:
            tuple: (x, y) 坐标，从1开始
        """
        x = pos // 8 + 1
        y = pos % 8 + 1
        return (x, y)
    
    def xy_to_pos(self, x, y):
        """
        将x, y坐标转换为pos
        公式: pos = (x-1)*8 + (y-1)
        
        Args:
            x: 行坐标（从1开始）
            y: 列坐标（从1开始）
            
        Returns:
            int: pos位置值
        """
        return (x - 1) * 8 + (y - 1)
    
    def get_item_name(self, itemid, with_color=False):
        """
        获取物品名称，如果未知则记录并提示用户补充
        
        Args:
            itemid: 物品ID
            with_color: 是否添加颜色代码
            
        Returns:
            str: 物品名称或 "未知物品(ID: xxx)"
        """
        if itemid in self.ITEM_ID_MAP:
            name = self.ITEM_ID_MAP[itemid]
            if with_color and itemid in self.ITEM_COLOR_MAP:
                return f"{self.ITEM_COLOR_MAP[itemid]}{name}{self.COLOR_RESET}"
            return name
        else:
            # 记录未知的 itemid，避免重复提示
            if itemid not in self.unknown_item_ids:
                self.unknown_item_ids.add(itemid)
                self.logger.warning(f"⚠️  发现未知物品ID: {itemid}，请补充到 ITEM_ID_MAP 映射表中")
            return f"未知物品(ID: {itemid})"
    
    def get_status_name(self, status):
        """
        获取状态名称
        
        Args:
            status: 状态值 (0=未翻开, 1=翻开, 2=空)
            
        Returns:
            str: 状态名称
        """
        return self.STATUS_MAP.get(status, f"未知状态({status})")
    
    def parse_cell_info_list(self, cell_info_list, verbose=False):
        """
        解析 cell_info 列表，转换为字典格式
        
        Args:
            cell_info_list: repeated type_cell_info 列表
            verbose: 是否打印详细信息，默认False
            
        Returns:
            dict: key为(x,y)坐标，value为cell信息字典
        """
        cell_dict = {}
        
        for i, cell in enumerate(cell_info_list):
            cell_pos = cell.pos
            cell_x, cell_y = self.pos_to_xy(cell_pos)
            item_name = self.get_item_name(cell.itemid)
            item_name_colored = self.get_item_name(cell.itemid, with_color=True)
            status_name = self.get_status_name(cell.status)
            
            # 添加到字典
            cell_dict[(cell_x, cell_y)] = {
                'pos': cell_pos,
                'itemid': cell.itemid,
                'status': cell.status,
                'status_name': status_name,
                'item_name': item_name,
                'item_name_colored': item_name_colored
            }
            
            if verbose:
                self.logger.info(f"  Cell {i+1}:")
                self.logger.info(f"    坐标: (x={cell_x}, y={cell_y}) [pos={cell_pos}]")
                self.logger.info(f"    物品: {item_name} (itemid={cell.itemid})")
                self.logger.info(f"    状态: {status_name} (status={cell.status})")
            
            if cell.HasField('spec_item_info'):
                spec = cell.spec_item_info
                spec_item_name = self.get_item_name(spec.specitemid)
                if verbose:
                    self.logger.info(f"    特殊物品: {spec_item_name} (specitemid={spec.specitemid}), 数量: {spec.count}")
                cell_dict[(cell_x, cell_y)]['spec_item_name'] = spec_item_name
                cell_dict[(cell_x, cell_y)]['spec_itemid'] = spec.specitemid
                cell_dict[(cell_x, cell_y)]['spec_count'] = spec.count
            
            if verbose:
                # 验证反向推导
                reconstructed_pos = self.xy_to_pos(cell_x, cell_y)
                if reconstructed_pos == cell_pos:
                    self.logger.info(f"    ✓ 坐标反向推导验证成功")
                else:
                    self.logger.warning(f"    ✗ 坐标反向推导验证失败: {cell_pos} != {reconstructed_pos}")
        
        return cell_dict
    
    def display_width(self, text):
        """计算字符串的实际显示宽度（中文字符算2，英文算1），忽略ANSI颜色代码"""
        import re
        # 移除ANSI颜色代码
        text_no_color = re.sub(r'\033\[\d+m', '', text)
        
        width = 0
        for char in text_no_color:
            if '\u4e00' <= char <= '\u9fff':  # 中文字符
                width += 2
            else:
                width += 1
        return width
    
    def pad_text(self, text, target_width):
        """填充文本到指定显示宽度"""
        current_width = self.display_width(text)
        if current_width >= target_width:
            return text
        padding = target_width - current_width
        left_pad = padding // 2
        right_pad = padding - left_pad
        return ' ' * left_pad + text + ' ' * right_pad
    
    def print_grid(self, cell_dict):
        """
        按照8x8网格的形式打印cell信息
        左上角为(1,1)，右上角为(1,8)，左下角为(8,1)，右下角为(8,8)
        
        Args:
            cell_dict: 字典，key为(x,y)坐标，value为cell信息
        """
        CELL_WIDTH = 10  # 每个格子的宽度
        
        self.logger.info("\n" + "="*94)
        self.logger.info("月饼狂欢网格图 (8x8) - 左上(1,1) 右上(1,8) 左下(8,1) 右下(8,8)")
        self.logger.info("="*94)
        
        # 打印列标题
        header = "     "
        for y in range(1, 9):
            header += f" {self.pad_text(f'y={y}', CELL_WIDTH)}"
        self.logger.info(header)
        self.logger.info("-" * 94)
        
        # 打印每一行
        for x in range(1, 9):
            # 为每个格子准备2行信息
            line1_parts = []  # 物品名称
            line2_parts = []  # 状态信息
            
            for y in range(1, 9):
                if (x, y) in cell_dict:
                    cell = cell_dict[(x, y)]
                    status = cell['status']
                    status_name = cell['status_name']
                    item_name_colored = cell['item_name_colored']
                    
                    # 根据状态决定显示内容
                    if status == 0:  # 未翻开
                        display_name = ""  # 不显示物品
                    elif status == 1:  # 翻开
                        # 显示物品名称（带颜色），可能包含"未知物品"
                        if self.display_width(item_name_colored) > CELL_WIDTH - 2:
                            # 需要截断 - 先移除颜色代码，截断后再添加回颜色
                            import re
                            # 提取颜色代码
                            color_match = re.match(r'(\033\[\d+m)(.*?)(\033\[0m)', item_name_colored)
                            if color_match:
                                color_start = color_match.group(1)
                                text_only = color_match.group(2)
                                color_end = color_match.group(3)
                                
                                # 截断文本
                                display_text = ""
                                for char in text_only:
                                    test = display_text + char
                                    if self.display_width(test) <= CELL_WIDTH - 3:
                                        display_text = test
                                    else:
                                        break
                                display_name = f"{color_start}{display_text}…{color_end}"
                            else:
                                # 没有颜色代码，直接截断
                                display_text = ""
                                for char in item_name_colored:
                                    test = display_text + char
                                    if self.display_width(test) <= CELL_WIDTH - 3:
                                        display_text = test
                                    else:
                                        break
                                display_name = display_text + "…"
                        else:
                            display_name = item_name_colored
                    elif status == 2:  # 空
                        display_name = "空"
                    else:
                        display_name = ""
                    
                    line1_parts.append(self.pad_text(display_name, CELL_WIDTH))
                    line2_parts.append(self.pad_text(status_name, CELL_WIDTH))
                else:
                    line1_parts.append(self.pad_text("--", CELL_WIDTH))
                    line2_parts.append(self.pad_text("", CELL_WIDTH))
            
            # 打印这一行的信息
            self.logger.info(f"x={x} |" + "|".join(line1_parts) + "|")
            self.logger.info(f"    |" + "|".join(line2_parts) + "|")
            
            if x < 8:
                self.logger.info("-" * 94)
        
        self.logger.info("="*94 + "\n")
    
    def tap(self, x, y):
        """
        执行月饼狂欢活动的tap操作
        
        Args:
            x: 行坐标（从1开始）
            y: 列坐标（从1开始）
            
        Returns:
            bool: 操作是否成功
        """
        try:
            pos = self.xy_to_pos(x, y)
            self.logger.info(f"开始执行月饼狂欢tap操作，参数x={x},y={y},坐标={pos}")

            req_config = {
                "ads": "点击",
                "times": 1,
                "hexstringheader": "5736",
                "request_body_i3": pos,
                # "savetofile": "response_hd_ybkh_tap"
            }
            response = self.ac_manager.do_common_request(
                self.account_name, 
                req_config, 
                showres=self.showres
            )
            
            # 解析响应
            if response and len(response) > 6:
                try:
                    data = response[6:]  # 跳过前6个字节
                    tap_resp = kpbl_pb2.hd_ybkh_tap_response()
                    tap_resp.ParseFromString(data)
                    
                    # 解析cell_info并显示坐标信息
                    if len(tap_resp.cell_info) > 0:
                        self.logger.info(f"收到 {len(tap_resp.cell_info)} 个cell信息：")
                        
                        # 使用抽象的解析函数
                        cell_dict = self.parse_cell_info_list(tap_resp.cell_info)
                        
                        # 打印8x8网格图
                        self.print_grid(cell_dict)
                    
                except Exception as parse_error:
                    self.logger.warning(f"解析响应时出错: {parse_error}")
            
            self.logger.info(f"月饼狂欢tap操作执行成功")
            return True
            
        except Exception as e:
            self.logger.error(f"月饼狂欢tap操作失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def tapB(self, x, y):
        """
        执行月饼狂欢活动的tap炸弹操作
        
        Args:
            x: 行坐标（从1开始）
            y: 列坐标（从1开始）
            
        Returns:
            bool: 操作是否成功
        """
        try:
            pos = self.xy_to_pos(x, y)
            self.logger.info(f"开始执行月饼狂欢tap操作，参数x={x},y={y},坐标={pos}")

            req_config = {
                "ads": "点击",
                "times": 1,
                "hexstringheader": "5d36",
                "request_body_i3": pos,
                # "savetofile": "response_hd_ybkh_tap"
            }
            response = self.ac_manager.do_common_request(
                self.account_name, 
                req_config, 
                showres=self.showres
            )
            
            # 解析响应
            if response and len(response) > 6:
                try:
                    data = response[6:]  # 跳过前6个字节
                    tap_resp = kpbl_pb2.hd_ybkh_tap_response()
                    tap_resp.ParseFromString(data)
                    
                    # 解析cell_info并显示坐标信息
                    if len(tap_resp.cell_info) > 0:
                        self.logger.info(f"收到 {len(tap_resp.cell_info)} 个cell信息：")
                        
                        # 使用抽象的解析函数
                        cell_dict = self.parse_cell_info_list(tap_resp.cell_info)
                        
                        # 打印8x8网格图
                        self.print_grid(cell_dict)
                    
                except Exception as parse_error:
                    self.logger.warning(f"解析响应时出错: {parse_error}")
            
            self.logger.info(f"月饼狂欢tap操作执行成功")
            return True
            
        except Exception as e:
            self.logger.error(f"月饼狂欢tap操作失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def tapLH(self, x, y):
        """
        执行月饼狂欢活动的tap莲花操作
        
        Args:
            x: 行坐标（从1开始）
            y: 列坐标（从1开始）
            
        Returns:
            bool: 操作是否成功
        """
        try:
            pos = self.xy_to_pos(x, y)
            self.logger.info(f"开始执行月饼狂欢tap操作，参数x={x},y={y},坐标={pos}")

            req_config = {
                "ads": "点击",
                "times": 1,
                "hexstringheader": "5b36",
                "request_body_i3": pos,
                # "savetofile": "response_hd_ybkh_tap"
            }
            response = self.ac_manager.do_common_request(
                self.account_name, 
                req_config, 
                showres=self.showres
            )
            
            # 解析响应
            if response and len(response) > 6:
                try:
                    data = response[6:]  # 跳过前6个字节
                    tap_resp = kpbl_pb2.hd_ybkh_tap_response()
                    tap_resp.ParseFromString(data)
                    
                    # 解析cell_info并显示坐标信息
                    if len(tap_resp.cell_info) > 0:
                        self.logger.info(f"收到 {len(tap_resp.cell_info)} 个cell信息：")
                        
                        # 使用抽象的解析函数
                        cell_dict = self.parse_cell_info_list(tap_resp.cell_info)
                        
                        # 打印8x8网格图
                        self.print_grid(cell_dict)
                    
                except Exception as parse_error:
                    self.logger.warning(f"解析响应时出错: {parse_error}")
            
            self.logger.info(f"月饼狂欢tap操作执行成功")
            return True
            
        except Exception as e:
            self.logger.error(f"月饼狂欢tap操作失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def tap_all(self, start_x=None, start_y=None):
        """
        遍历所有位置（0-63），挨个执行tap操作，仅对未翻开的格子操作
        
        Args:
            start_x: 起始行坐标（可选），如果提供则从该坐标开始
            start_y: 起始列坐标（可选），如果提供则从该坐标开始
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 1. 先执行status获取当前状态
            self.logger.info("执行status查询当前状态...")
            if not self.status():
                self.logger.error("获取状态失败，取消批量操作")
                return False
            
            # 2. 获取当前的cell状态（从最后一次status调用中获取）
            # 需要先调用一次来获取状态数据
            req_config = {
                "ads": "查询状态",
                "times": 1,
                "hexstringheader": "4d36",
            }
            response = self.ac_manager.do_common_request(
                self.account_name, 
                req_config, 
                showres=0
            )
            
            cell_status_map = {}  # (x,y) -> status
            if response and len(response) > 6:
                try:
                    data = response[6:]
                    status_resp = kpbl_pb2.hd_ybkh_status_response()
                    status_resp.ParseFromString(data)
                    
                    if status_resp.HasField('i3'):
                        for cell in status_resp.i3.cell_info:
                            cell_x, cell_y = self.pos_to_xy(cell.pos)
                            cell_status_map[(cell_x, cell_y)] = cell.status
                except Exception as e:
                    self.logger.warning(f"解析状态时出错: {e}")
            
            # 3. 确定起始位置
            if start_x is not None and start_y is not None:
                start_pos = self.xy_to_pos(start_x, start_y)
                self.logger.info(f"从指定坐标开始: (x={start_x}, y={start_y}), pos={start_pos}")
            else:
                start_pos = 0
                self.logger.info("从位置0开始遍历")
            
            self.logger.info("开始批量执行月饼狂欢tap操作（仅未翻开格子）")
            success_count = 0
            fail_count = 0
            skip_count = 0
            
            # 4. 遍历执行
            for pos in range(start_pos, 64):  # 从start_pos到63
                x, y = self.pos_to_xy(pos)
                
                # 检查状态，只对未翻开（status=0）的格子操作
                cell_status = cell_status_map.get((x, y), None)
                if cell_status == 0:  # 未翻开
                    self.logger.info(f"--- 执行位置 {pos}: (x={x}, y={y}) [未翻开] ---")
                    
                    if self.tap(x, y):
                        success_count += 1
                    else:
                        fail_count += 1
                else:
                    status_name = self.get_status_name(cell_status) if cell_status is not None else "未知"
                    self.logger.info(f"跳过位置 {pos}: (x={x}, y={y}) [状态: {status_name}]")
                    skip_count += 1
            
            self.logger.info(f"批量tap操作完成！成功: {success_count}, 失败: {fail_count}, 跳过: {skip_count}")
            return fail_count == 0
            
        except Exception as e:
            self.logger.error(f"批量tap操作失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def tap_all_lh(self, start_x=None, start_y=None):
        """
        遍历所有位置（0-63），挨个执行tapLH（莲花）操作，仅对未翻开的格子操作
        
        Args:
            start_x: 起始行坐标（可选），如果提供则从该坐标开始
            start_y: 起始列坐标（可选），如果提供则从该坐标开始
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 1. 先执行status获取当前状态
            self.logger.info("执行status查询当前状态...")
            if not self.status():
                self.logger.error("获取状态失败，取消批量操作")
                return False
            
            # 2. 获取当前的cell状态
            req_config = {
                "ads": "查询状态",
                "times": 1,
                "hexstringheader": "4d36",
            }
            response = self.ac_manager.do_common_request(
                self.account_name, 
                req_config, 
                showres=0
            )
            
            cell_status_map = {}  # (x,y) -> status
            if response and len(response) > 6:
                try:
                    data = response[6:]
                    status_resp = kpbl_pb2.hd_ybkh_status_response()
                    status_resp.ParseFromString(data)
                    
                    if status_resp.HasField('i3'):
                        for cell in status_resp.i3.cell_info:
                            cell_x, cell_y = self.pos_to_xy(cell.pos)
                            cell_status_map[(cell_x, cell_y)] = cell.status
                except Exception as e:
                    self.logger.warning(f"解析状态时出错: {e}")
            
            # 3. 确定起始位置
            if start_x is not None and start_y is not None:
                start_pos = self.xy_to_pos(start_x, start_y)
                self.logger.info(f"从指定坐标开始: (x={start_x}, y={start_y}), pos={start_pos}")
            else:
                start_pos = 0
                self.logger.info("从位置0开始遍历")
            
            self.logger.info("开始批量执行月饼狂欢tapLH操作（仅未翻开格子）")
            success_count = 0
            fail_count = 0
            skip_count = 0
            
            # 4. 遍历执行
            for pos in range(start_pos, 64):  # 从start_pos到63
                x, y = self.pos_to_xy(pos)
                
                # 检查状态，只对未翻开（status=0）的格子操作
                cell_status = cell_status_map.get((x, y), None)
                if cell_status == 0:  # 未翻开
                    self.logger.info(f"--- 执行莲花位置 {pos}: (x={x}, y={y}) [未翻开] ---")
                    
                    if self.tapLH(x, y):
                        success_count += 1
                    else:
                        fail_count += 1
                else:
                    status_name = self.get_status_name(cell_status) if cell_status is not None else "未知"
                    self.logger.info(f"跳过位置 {pos}: (x={x}, y={y}) [状态: {status_name}]")
                    skip_count += 1
            
            self.logger.info(f"批量tapLH操作完成！成功: {success_count}, 失败: {fail_count}, 跳过: {skip_count}")
            return fail_count == 0
            
        except Exception as e:
            self.logger.error(f"批量tapLH操作失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def status(self):
        """
        查询月饼狂欢活动状态
        
        Returns:
            bool: 操作是否成功
        """
        try:
            self.logger.info("开始查询月饼狂欢活动状态")
            
            req_config = {
                "ads": "查询状态",
                "times": 1,
                "hexstringheader": "4d36",
                # "savetofile": "response_hd_ybkh_status"
            }
            response = self.ac_manager.do_common_request(
                self.account_name, 
                req_config, 
                showres=self.showres
            )
            
            # 解析响应
            if response and len(response) > 6:
                try:
                    data = response[6:]  # 跳过前6个字节
                    status_resp = kpbl_pb2.hd_ybkh_status_response()
                    status_resp.ParseFromString(data)
                    
                    # 检查是否有i3字段和cell_info
                    if status_resp.HasField('i3') and len(status_resp.i3.cell_info) > 0:
                        self.logger.info(f"收到 {len(status_resp.i3.cell_info)} 个cell信息：")
                        
                        # 使用抽象的解析函数
                        cell_dict = self.parse_cell_info_list(status_resp.i3.cell_info)
                        
                        # 打印8x8网格图
                        self.print_grid(cell_dict)
                    else:
                        self.logger.info("当前没有cell信息")
                    
                except Exception as parse_error:
                    self.logger.warning(f"解析响应时出错: {parse_error}")
            
            self.logger.info(f"月饼狂欢状态查询完成")
            return True
            
        except Exception as e:
            self.logger.error(f"月饼狂欢状态查询失败: {e}")
            import traceback
            traceback.print_exc()
            return False

