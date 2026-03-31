"""
挖矿管理模块
处理游戏中的挖矿功能
"""

import logging
import binascii
from . import kpbl_pb2
from .kpbltools import ACManager, mask_account


class WKManager:
    """挖矿管理器"""
    
    mine_cell_type_map = {
        10001: "B",
        10002: "B",
        10003: "B",
        10004: "B",
        10005: "B",
    }
    
    # miner_drop类型映射
    miner_drop_type_map = {
        # type1=1: 未知类型1
        # type1=2: 宝石类
        (None, 2): ("J", "宝石"),
        # type1=3: 强化材料类
        (3, 30): ("X", "强化石"),
        (3, 32): ("T", "锤子"),
        (3, 33): ("N", "蓝鸟"),
        # 可以继续添加其他类型映射
    }

    def __init__(self, account_name, showres=0):
        self.account_name = account_name
        self.ac_manager = ACManager(account_name)
        self.logger = logging.getLogger(f"WKManager_{account_name}")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.StreamHandler())
        self.showres = showres
        # 记录已经点击过的砖头位置，每层重置
        self.clicked_positions = set()
        # 记录当前层是否已经点击过炸弹
        self.bomb_clicked_this_level = False
    
    def getminermap(self):
        """获取挖矿地图"""
        wakuang_config = {"ads": "查询状态", "times": 1, "hexstringheader": "4d4f"}
        response = self.ac_manager.do_common_request(self.account_name, wakuang_config, showres=self.showres)
        miner_resp = kpbl_pb2.miner_main_response()
        miner_resp.ParseFromString(response[6:])
        return miner_resp
    
    def tapminer(self, row, col):
        """
        点击挖矿
        
        Args:
            row: 行号(1-6)
            col: 列号(1-5)
        """
        # 位置编码转换
        position = row * 100 + col
        hex_data = ""
        
        hexstringheader = "4f4f"
        if row == 1:
            # 第1行使用单字节表示
            pos_hex = format(position, 'x')  # 转为十六进制
            hex_data = pos_hex
        else:
            # 第2-6行使用双字节格式
            pos_val = row * 100 + col
            
            # 确定行的后缀
            if row == 2:
                suffix = "01"
            elif row == 3:
                suffix = "02"
                # 第3行位置的特殊编码
                # 301对应ad 02, 302对应ae 02, ...
                prefix_map = {1: "ad", 2: "ae", 3: "af", 4: "b0", 5: "b1"}
                if col in prefix_map:
                    hex_data = prefix_map[col] + suffix
                else:
                    # 取低字节的默认处理方式
                    pos_byte = format(pos_val & 0xFF, 'x').zfill(2)
                    hex_data = pos_byte + suffix
            elif row in [4, 5]:
                suffix = "03"
                # 默认处理方式
                pos_byte = format(pos_val & 0xFF, 'x').zfill(2)
                hex_data = pos_byte + suffix
            elif row == 6:
                suffix = "04"
                # 第6行位置的特殊编码
                prefix_map = {1: "d9", 2: "da", 3: "db", 4: "dc", 5: "dd"}
                if col in prefix_map:
                    hex_data = prefix_map[col] + suffix
                else:
                    # 取低字节的默认处理方式
                    pos_byte = format(pos_val & 0xFF, 'x').zfill(2)
                    hex_data = pos_byte + suffix
            else:
                suffix = "00"  # 默认值
                # 默认处理方式
                pos_byte = format(pos_val & 0xFF, 'x').zfill(2)
                hex_data = pos_byte + suffix
        
        # 如果没有通过特殊处理设置hex_data，则使用默认方法
        if not hex_data:
            pos_byte = format(pos_val & 0xFF, 'x').zfill(2)
            hex_data = pos_byte + suffix
        
        wakuang_config = {
            "ads": f"点击{row},{col}",
            "times": 1,
            "hexstringheader": hexstringheader,
            "request_body_i3": binascii.unhexlify(hex_data) if hex_data else b'',
            "requestbodytype": "miner_tap_request"
        }
        
        response = self.ac_manager.do_common_request(self.account_name, wakuang_config, showres=0)
        if response and len(response) > 15:
            miner_resp = kpbl_pb2.miner_tap_response()
            miner_resp.ParseFromString(response[6:])
            return miner_resp
        return None
    
    def tapK(self):
        """点击卡皮巴拉雕像K"""
        wakuang_config = {"ads": "点击K", "times": 1, "hexstringheader": "5b4f"}
        response = self.ac_manager.do_common_request(self.account_name, wakuang_config, showres=self.showres)
        if response:
            miner_resp = kpbl_pb2.miner_main_response()
            miner_resp.ParseFromString(response[6:])
            return miner_resp
        return None
    
    def tapDoor(self):
        """点击大门和下一层"""
        wakuang_config = {"ads": "点击大门", "times": 1, "hexstringheader": "534f"}
        wakuang_nextlevel_config = {"ads": "点击下一层", "times": 1, "hexstringheader": "574f"}
        self.ac_manager.do_common_request(self.account_name, wakuang_config, showres=0)
        return self.ac_manager.do_common_request(self.account_name, wakuang_nextlevel_config, showres=0)
    
    def tapB(self, row, col):
        """点击炸弹"""
        wakuang_config = {
            "ads": f"点击炸弹{row},{col}",
            "times": 1,
            "hexstringheader": "514f",
            "request_body_i2": int(row * 100 + col)
        }
        response = self.ac_manager.do_common_request(self.account_name, wakuang_config, showres=0)
        if not response or len(response) < 10:
            wakuang_config = {
                "ads": f"点击炸弹{row},{col}",
                "times": 1,
                "hexstringheader": "514f",
                "request_body_i2": int(row * 100 + col)
            }
            response = self.ac_manager.do_common_request(self.account_name, wakuang_config, showres=0)
        miner_resp = kpbl_pb2.miner_tap_response()
        miner_resp.ParseFromString(response[6:])
        return miner_resp
    
    def parse_miner_map(self, miner_map, print_table=False, header="矿区状态", indent="  "):
        """
        解析矿区地图数据，返回格子类型表格
        
        Args:
            miner_map: 从getminermap或点击函数返回的矿区数据
            print_table: 是否打印表格
            header: 打印表格的表头
            indent: 打印表格的缩进
            
        Returns:
            list: 二维数组表示的矿区表格
        """
        # 创建矿区数据表格 (用于显示)
        table = [['·' for _ in range(5)] for _ in range(6)]
        # 存储原始cell_type值，用于调试显示
        cell_types = [[0 for _ in range(5)] for _ in range(6)]
        
        # 记录矿区数据
        if hasattr(miner_map, 'unit') and miner_map.unit:
            if hasattr(miner_map.unit, 'minercells') and miner_map.unit.minercells:
                for cell in miner_map.unit.minercells:
                    position = cell.position_xy
                    cell_type = cell.type
                    
                    # 转化为行列坐标
                    if position > 0:
                        try:
                            row = int(str(position)[0]) - 1
                            col = position % 100 - 1
                        except:
                            # 如果位置格式不对，使用备用方法
                            row = position // 5
                            col = position % 5
                    else:
                        row = position // 5
                        col = position % 5
                    
                    # 标记矿块类型
                    marker = '·'
                    
                    # 检查是否是kpbl (K)
                    if str(cell_type).startswith('5') and len(str(cell_type)) >= 3 and str(cell_type)[2] == '0':
                        marker = 'K'
                    # 检查是否是炸弹
                    elif cell_type == 10001:
                        marker = 'B'
                    # 检查掉落物（优先显示掉落物）
                    elif hasattr(cell, 'drops') and cell.drops:
                        # print(f"  位置({row+1},{col+1}) 发现drops: {len(cell.drops)}个")
                        # for i, drop in enumerate(cell.drops):
                        #     print(f"    Drop{i}: type1={drop.type1}, type2={drop.type2}, count={drop.count}")
                        
                        for drop in cell.drops:
                            if drop.type2 == 2:
                                marker = f'J-{drop.count}'  # 宝石
                                break
                            elif drop.type1 == 3 and drop.type2 == 30:
                                marker = f'X-{drop.count}'  # 强化石
                                break
                            elif drop.type1 == 3 and drop.type2 == 33:
                                marker = f'N-{drop.count}'  # 蓝鸟
                                break
                            elif drop.type2 == 32:
                                marker = f'T-{drop.count}'  # 锤子
                                break
                        else:
                            # 如果没有匹配到特定类型，显示第一个掉落物
                            if cell.drops:
                                first_drop = cell.drops[0]
                                marker = f'{first_drop.type1}-{first_drop.type2}:{first_drop.count}'
                            else:
                                marker = 'O'  # 默认砖头
                    # 检查是否是砖头 (4001) - 放在最后作为默认
                    elif cell_type == 4001:
                        marker = 'O'  # 砖头标记为普通格子
                    else:
                        marker = f'{cell_type}'
                    
                    # 检查是否需要添加星号
                    if str(cell_type).startswith('4') and len(str(cell_type)) >= 2 and str(cell_type)[1] != '0':
                        marker += '*'
                    
                    # 更新表格
                    if 0 <= row < 6 and 0 <= col < 5:
                        table[row][col] = marker
                        cell_types[row][col] = cell_type
        
        # 如果需要打印表格
        if print_table:
            print(f"{indent}{header}")  
            # 打印矩阵格式的表格 - 类型标记
            print(f"{indent}矿区类型标记:")
            for row in table:
                print(f"{indent}" + " ".join(f"{cell:6}" for cell in row))
            
            # 打印矩阵格式的表格 - cell_type值
            print(f"{indent}矿区cell_type值:")
            for row_idx in range(6):
                row_values = []
                for col_idx in range(5):
                    row_values.append(str(cell_types[row_idx][col_idx]))
                print(f"{indent}" + " ".join(f"{val:6}" for val in row_values))
        # input('parse_miner_map end')
        return table
    
    def debug_print_mine_map(self, miner_map, header="矿图调试信息"):
        """
        调试用函数：模块化显示矿图信息
        """
        # 清屏并定位到顶部
        print("\033[2J\033[H", end="")
        
        if not miner_map or not hasattr(miner_map, 'unit') or not miner_map.unit:
            print("无效的矿图数据")
            return
            
        # 创建6x5的网格来存储信息
        grid_types = [[0 for _ in range(5)] for _ in range(6)]
        grid_markers = [['·' for _ in range(5)] for _ in range(6)]
        
        # 解析矿区数据
        if hasattr(miner_map.unit, 'minercells') and miner_map.unit.minercells:
            for cell in miner_map.unit.minercells:
                position = cell.position_xy
                cell_type = cell.type
                is_zhuantou = getattr(cell, 'isZhuantou', 0)
                
                # 转化为行列坐标
                if position > 0:
                    try:
                        row = int(str(position)[0]) - 1
                        col = position % 100 - 1
                    except:
                        row = position // 5
                        col = position % 5
                else:
                    row = position // 5
                    col = position % 5
                
                if 0 <= row < 6 and 0 <= col < 5:
                    grid_types[row][col] = cell_type
                    
                    # 生成标记
                    marker = '·'
                    if str(cell_type).startswith('5') and len(str(cell_type)) >= 3 and str(cell_type)[2] == '0':
                        marker = 'K'
                    elif cell_type == 10001:
                        marker = 'B'
                    elif hasattr(cell, 'drops') and cell.drops:
                        for drop in cell.drops:
                            drop_key = (drop.type1, drop.type2)
                            type2_key = (None, drop.type2)
                            if drop_key in self.miner_drop_type_map:
                                symbol, name = self.miner_drop_type_map[drop_key]
                                marker = f'{symbol}{drop.count}'
                                break
                            elif type2_key in self.miner_drop_type_map:
                                symbol, name = self.miner_drop_type_map[type2_key]
                                marker = f'{symbol}{drop.count}'
                                break
                        else:
                            marker = '_'  # 有掉落物但未匹配到映射
                    elif cell_type == 4001:
                        marker = '_'  # 普通砖头，无特殊内容
                    else:
                        marker = f'{cell_type}'
                    
                    if str(cell_type).startswith('4') and len(str(cell_type)) >= 2 and str(cell_type)[1] != '0':
                        marker = '*'  # 特殊砖头直接显示为*
                    
                    # 根据砖头状态添加标识
                    if is_zhuantou == 1:
                        marker = f'[{marker}]'  # 有覆盖层：[_] 或 [X5] 或 [*] 等
                    elif is_zhuantou == 0:
                        marker = f'{marker}'     # 无覆盖层：_ 或 X5 或 * 等
                    
                    grid_markers[row][col] = marker

        # 获取计划挖矿顺序
        planned_sequence = self.get_planned_mining_sequence(miner_map, rows=6, cols=5)
        
        # 模块化显示
        print(f"╔══════════════════════════════════════════════════════════════════════════════╗")
        print(f"║ {header:<76} ║")
        print(f"║ 层数:{miner_map.unit.minerlevel:<3} | 已点击:{len(self.clicked_positions):<2} | 炸弹:{'已点击' if self.bomb_clicked_this_level else '未点击':<4} | 计划序列长度:{len(planned_sequence):<2}           ║")
        print(f"╠══════════════════════════════════════════════════════════════════════════════╣")
        
        sequence_str = str(planned_sequence)[:70] + "..." if len(str(planned_sequence)) > 70 else str(planned_sequence)
        print(f"║ 计划挖矿顺序: {sequence_str:<63} ║")
        print(f"╠══════════════════════════════════════════════════════════════════════════════╣")
        
        print(f"║ 矿图标记: [_]=有覆盖层 _=无覆盖层 | 坐标: 左上(1,1) 右下(6,5)                ║")
        print(f"║      x=1    x=2    x=3    x=4    x=5                                        ║")
        for row in range(6):
            y = row + 1
            row_markers = "".join(f"{grid_markers[row][col]:6}" for col in range(5))
            print(f"║ y={y} {row_markers:<66} ║")
        
        print(f"╠══════════════════════════════════════════════════════════════════════════════╣")
        print(f"║ 类型码:                                                                     ║")
        for row in range(6):
            y = row + 1
            row_types = "".join(f"{grid_types[row][col]:6}" for col in range(5))
            print(f"║ y={y} {row_types:<66} ║")
        
        print(f"╚══════════════════════════════════════════════════════════════════════════════╝")
        print(f"状态: 砖头检查=✓ | 掉落物=✓ | 优化算法=✓ | 炸弹限制=✓")
    
    def get_next_mining_position(self, mine_grid, rows=6, cols=5):
        """
        调试用函数：打印详细的矿图信息
        
        Args:
            miner_map: 从getminermap返回的矿区数据
            header: 打印的标题
        """
        print(f"\n=== {header} ===")
        
        if not miner_map or not hasattr(miner_map, 'unit') or not miner_map.unit:
            print("无效的矿图数据")
            return
    
    def find_bombs_in_grid(self, mine_grid, rows=6, cols=5):
        """
        在矿区网格中查找炸弹位置
        
        Args:
            mine_grid: 矿区网格数据
            rows: 矿区行数，默认6
            cols: 矿区列数，默认5
            
        Returns:
            list: 炸弹位置列表，每个元素是(row, col)
        """
        bombs = []
        for row in range(rows):
            for col in range(cols):
                cell_type = mine_grid[row][col]
                # 检查是否是炸弹，跳过带*的特殊砖头
                if cell_type == 'B':
                    bombs.append((row, col))
        return bombs
    
    def find_k_in_grid(self, mine_grid, rows=6, cols=5):
        """
        在矿区网格中查找K的位置
        
        Args:
            mine_grid: 矿区网格数据
            rows: 矿区行数，默认6
            cols: 矿区列数，默认5
            
        Returns:
            list: K位置列表，每个元素是(row, col)
        """
        k_positions = []
        for row in range(rows):
            for col in range(cols):
                cell_type = mine_grid[row][col]
                if cell_type == 'K':
                    k_positions.append((row, col))
        return k_positions
    
    def get_next_mining_position(self, mine_grid, rows=6, cols=5):
        """
        获取下一个挖矿位置（按序挖矿，跳过特殊砖头和已点击的位置）
        
        Args:
            mine_grid: 矿区网格数据
            rows: 矿区行数，默认6
            cols: 矿区列数，默认5
            
        Returns:
            tuple: (row, col) 或 None（如果没有可挖的位置）
        """
        # 按从左到右，从上到下的顺序遍历
        for row in range(rows):
            for col in range(cols):
                cell_type = mine_grid[row][col]
                position_key = (row, col)
                
                # 跳过空格子、K、炸弹、带*的特殊砖头和已点击过的位置
                if (cell_type != '·' and 
                    cell_type != 'K' and 
                    cell_type != 'B' and 
                    '*' not in cell_type and
                    position_key not in self.clicked_positions):
                    return (row, col)
        return None
    
    def analyze_miner_plan_new(self, miner_map, rows=6, cols=5):
        """
        新的挖矿策略分析：优先炸弹，然后按序挖矿，只挖有砖头的位置
        
        Args:
            miner_map: 原始矿区数据对象
            rows: 矿区行数，默认6
            cols: 矿区列数，默认5
            
        Returns:
            dict: 包含策略信息的字典
        """
        # 解析矿区数据为网格
        mine_grid = self.parse_miner_map(miner_map, print_table=False)
        
        # 查找炸弹
        bombs = self.find_bombs_in_grid(mine_grid, rows, cols)
        
        # 查找K
        k_positions = self.find_k_in_grid(mine_grid, rows, cols)
        
        # 获取下一个普通挖矿位置（使用优化的K发现算法）
        next_position = self.get_optimal_k_discovery_position(miner_map, mine_grid, rows, cols)
        
        return {
            'bombs': bombs,
            'k_positions': k_positions,
            'next_position': next_position,
            'has_bombs': len(bombs) > 0,
            'has_k': len(k_positions) > 0
        }
    
    def get_optimal_k_discovery_position(self, miner_map, mine_grid, rows=6, cols=5):
        """
        获取最优的K发现位置
        K的尺寸: 1x1, 2x2, 2x3
        策略: 使用棋盘模式点击，确保能覆盖所有可能的K位置
        
        Args:
            miner_map: 原始矿区数据对象
            mine_grid: 解析后的矿区网格数据
            rows: 矿区行数，默认6
            cols: 矿区列数，默认5
            
        Returns:
            tuple: (row, col) 或 None
        """
        # 创建位置到cell的映射
        position_to_cell = {}
        if hasattr(miner_map, 'unit') and hasattr(miner_map.unit, 'minercells'):
            for cell in miner_map.unit.minercells:
                position = cell.position_xy
                if position > 0:
                    try:
                        row = int(str(position)[0]) - 1
                        col = position % 100 - 1
                    except:
                        row = position // 5
                        col = position % 5
                else:
                    row = position // 5
                    col = position % 5
                
                if 0 <= row < rows and 0 <= col < cols:
                    position_to_cell[(row, col)] = cell
        
        # 新的优先级顺序：指定的优化点击序列
        priority_positions = [
            (1, 1),  # (2,2) 转换为0-based
            (1, 3),  # (2,4)
            (2, 2),  # (3,3)
            (3, 1),  # (4,2)
            (3, 3),  # (4,4)
            (4, 1),  # (5,2)
            (4, 3),  # (5,4)
            (0, 2),  # (1,3)
            (5, 2),  # (6,3)
        ]
        
        # 第二优先级：其余位置按行列顺序
        secondary_positions = []
        for row in range(rows):
            for col in range(cols):
                if (row, col) not in priority_positions:
                    secondary_positions.append((row, col))
        
        # 按优先级检查可挖掘位置
        all_positions = priority_positions + secondary_positions
        
        for row, col in all_positions:
            cell_type = mine_grid[row][col]
            position_key = (row, col)
            
            # 跳过空格子、K、炸弹、带*的特殊砖头和已点击过的位置
            if (cell_type != '·' and 
                cell_type != 'K' and 
                cell_type != 'B' and 
                '*' not in cell_type and
                position_key not in self.clicked_positions):
                
                # 检查是否有砖头（isZhuantou == 1）
                if position_key in position_to_cell:
                    cell = position_to_cell[position_key]
                    is_zhuantou = getattr(cell, 'isZhuantou', 0)
                    if is_zhuantou == 1:  # 只挖有砖头的位置
                        return (row, col)
        return None
    
    def get_next_mining_position_with_zhuantou(self, miner_map, mine_grid, rows=6, cols=5):
        """
        获取下一个挖矿位置（只挖有砖头的位置）- 原始按序算法
        
        Args:
            miner_map: 原始矿区数据对象
            mine_grid: 解析后的矿区网格数据
            rows: 矿区行数，默认6
            cols: 矿区列数，默认5
            
        Returns:
            tuple: (row, col) 或 None（如果没有可挖的位置）
        """
        # 创建位置到cell的映射
        position_to_cell = {}
        if hasattr(miner_map, 'unit') and hasattr(miner_map.unit, 'minercells'):
            for cell in miner_map.unit.minercells:
                position = cell.position_xy
                if position > 0:
                    try:
                        row = int(str(position)[0]) - 1
                        col = position % 100 - 1
                    except:
                        row = position // 5
                        col = position % 5
                else:
                    row = position // 5
                    col = position % 5
                
                if 0 <= row < rows and 0 <= col < cols:
                    position_to_cell[(row, col)] = cell
        
        # 按从左到右，从上到下的顺序遍历
        for row in range(rows):
            for col in range(cols):
                cell_type = mine_grid[row][col]
                position_key = (row, col)
                
                # 跳过空格子、K、炸弹、带*的特殊砖头和已点击过的位置
                if (cell_type != '·' and 
                    cell_type != 'K' and 
                    cell_type != 'B' and 
                    '*' not in cell_type and
                    position_key not in self.clicked_positions):
                    
                    # 检查是否有砖头（isZhuantou == 1）
                    if position_key in position_to_cell:
                        cell = position_to_cell[position_key]
                        is_zhuantou = getattr(cell, 'isZhuantou', 0)
                        if is_zhuantou == 1:  # 只挖有砖头的位置
                            return (row, col)
        return None
    
    def get_planned_mining_sequence(self, miner_map, rows=6, cols=5):
        """
        获取计划的挖矿顺序（基于优化算法的完整规划）
        
        Args:
            miner_map: 原始矿区数据对象
            rows: 矿区行数，默认6
            cols: 矿区列数，默认5
            
        Returns:
            list: 计划的挖矿坐标序列 [(row, col), ...]
        """
        # 解析矿区数据为网格
        mine_grid = self.parse_miner_map(miner_map, print_table=False)
        
        # 创建位置到cell的映射
        position_to_cell = {}
        if hasattr(miner_map, 'unit') and hasattr(miner_map.unit, 'minercells'):
            for cell in miner_map.unit.minercells:
                position = cell.position_xy
                if position > 0:
                    try:
                        row = int(str(position)[0]) - 1
                        col = position % 100 - 1
                    except:
                        row = position // 5
                        col = position % 5
                else:
                    row = position // 5
                    col = position % 5
                
                if 0 <= row < rows and 0 <= col < cols:
                    position_to_cell[(row, col)] = cell
        
        # 新的优先级顺序：指定的优化点击序列
        priority_positions = [
            (1, 1),  # (2,2) 转换为0-based
            (1, 3),  # (2,4)
            (2, 2),  # (3,3)
            (3, 1),  # (4,2)
            (3, 3),  # (4,4)
            (4, 1),  # (5,2)
            (4, 3),  # (5,4)
            (0, 2),  # (1,3)
            (5, 2),  # (6,3)
        ]
        
        # 第二优先级：其余位置按行列顺序
        secondary_positions = []
        for row in range(rows):
            for col in range(cols):
                if (row, col) not in priority_positions:
                    secondary_positions.append((row, col))
        
        # 按优先级生成可挖掘的完整序列
        all_positions = priority_positions + secondary_positions
        planned_sequence = []
        
        for row, col in all_positions:
            cell_type = mine_grid[row][col]
            position_key = (row, col)
            
            # 跳过空格子、K、炸弹、带*的特殊砖头和已点击的位置
            if (cell_type != '·' and 
                cell_type != 'K' and 
                cell_type != 'B' and 
                '*' not in cell_type and
                position_key not in self.clicked_positions):
                
                # 检查是否有砖头（isZhuantou == 1）
                if position_key in position_to_cell:
                    cell = position_to_cell[position_key]
                    is_zhuantou = getattr(cell, 'isZhuantou', 0)
                    if is_zhuantou == 1:  # 只包含有砖头的位置
                        # 转换为1-based坐标显示
                        planned_sequence.append((row + 1, col + 1))
        
        return planned_sequence
    
    def do_wakuang_new(self, print_table=False):
        """
        新的挖矿功能：优先炸弹，然后按序挖矿，跳过特殊砖头，每次检查K
        
        Args:
            print_table: 是否打印矿区表格，默认False
        """
        print(f"<{mask_account(self.account_name)}> 开始新的挖矿流程")
        minelevel = 0
        
        while True:
            # 获取挖矿地图
            miner_map = self.getminermap()
            
            # 检查返回的对象是否有效
            if not miner_map or not hasattr(miner_map, 'unit') or not miner_map.unit:
                print(f"<{mask_account(self.account_name)}> 无法获取有效的挖矿地图")
                return True
                
            minelevel = miner_map.unit.minerlevel
            
            # 调试：打印详细矿图信息
            self.debug_print_mine_map(miner_map, f"<{mask_account(self.account_name)}> 第{minelevel}层矿图")
            
            # 解析矿区数据
            table = self.parse_miner_map(miner_map, print_table=print_table, 
                                       header=f"<{mask_account(self.account_name)}> 矿区状态")
            # print(f"<{mask_account(self.account_name)}> 当前层数{minelevel}，矿区状态: {table}")
            
            # 使用新的策略分析
            strategy = self.analyze_miner_plan_new(miner_map)
            
            # 检查是否已经有K
            if strategy['has_k']:
                print(f"<{mask_account(self.account_name)}> 发现K，需要点击所有K格子")
                k_positions = strategy['k_positions']
                print(f"<{mask_account(self.account_name)}> 找到{len(k_positions)}个K格子: {k_positions}")
                
                # 点击所有的K格子
                for i, (k_row, k_col) in enumerate(k_positions):
                    k_row_real = k_row + 1
                    k_col_real = k_col + 1
                    print(f"<{mask_account(self.account_name)}> 点击第{i+1}个K格子，位置[{k_row_real},{k_col_real}]")
                    
                    # 使用tapminer点击K格子
                    updated_map = self.tapminer(k_row_real, k_col_real)
                    if not updated_map or not hasattr(updated_map, 'unit') or not updated_map.unit:
                        print(f"<{mask_account(self.account_name)}> 点击K格子失败，尝试使用tapK")
                        # 如果tapminer失败，尝试使用tapK
                        updated_map = self.tapK()
                        if not updated_map or not hasattr(updated_map, 'unit') or not updated_map.unit:
                            print(f"<{mask_account(self.account_name)}> 无法获取有效的挖矿地图，挖矿结束")
                            return True
                        break  # tapK成功后跳出循环
                
                print(f"<{mask_account(self.account_name)}> 所有K格子点击完成，现在调用tapK()函数")
                
                # 调用tapK()函数（这是必需的步骤）
                updated_map = self.tapK()
                if not updated_map or not hasattr(updated_map, 'unit') or not updated_map.unit:
                    print(f"<{mask_account(self.account_name)}> tapK()调用失败，挖矿结束")
                    return False
                
                # 点击大门进入下一层
                response = self.tapDoor()
                if len(response) < 20:
                    print(f"<{mask_account(self.account_name)}> 收到的响应过短，挖矿结束 at tapdoor")
                    return False
                
                # 成功进入下一层，重置已点击位置记录
                self.clicked_positions.clear()
                self.bomb_clicked_this_level = False
                print(f"<{mask_account(self.account_name)}> 进入下一层，重置已点击位置记录和炸弹标记")
                continue
            
            # 优先处理炸弹（每层只点击一次）
            if strategy['has_bombs'] and not self.bomb_clicked_this_level:
                bomb_row, bomb_col = strategy['bombs'][0]  # 取第一个炸弹
                row_real = bomb_row + 1
                col_real = bomb_col + 1
                
                print(f"<{mask_account(self.account_name)}> 发现炸弹在位置[{row_real},{col_real}]，点击炸弹")
                
                # 点击炸弹
                updated_map = self.tapB(row_real, col_real)
                if not updated_map or not hasattr(updated_map, 'unit') or not updated_map.unit:
                    print(f"<{mask_account(self.account_name)}> 无法获取有效的挖矿地图，挖矿结束")
                    return True
                
                # 检查炸弹触发后的数据是否有效
                if (not hasattr(updated_map.unit, 'minercells') or 
                    not updated_map.unit.minercells or 
                    all(cell.type == 0 for cell in updated_map.unit.minercells)):
                    print(f"<{mask_account(self.account_name)}> 炸弹触发后数据异常，重新获取矿图")
                    updated_map = self.getminermap()
                    if not updated_map or not hasattr(updated_map, 'unit') or not updated_map.unit:
                        print(f"<{mask_account(self.account_name)}> 重新获取矿图失败，挖矿结束")
                        return False
                
                # 标记本层已点击炸弹
                self.bomb_clicked_this_level = True
                print(f"<{mask_account(self.account_name)}> 本层炸弹已点击，后续不再点击炸弹")
                
                # 调试：打印炸弹触发后的详细矿图
                if updated_map:
                    self.debug_print_mine_map(updated_map, f"<{mask_account(self.account_name)}> 炸弹触发后矿图")
                    table = self.parse_miner_map(updated_map, print_table=print_table, 
                                               header="炸弹触发后的矿区状态")
                    print(f"<{mask_account(self.account_name)}> 炸弹触发后矿区状态: {table}")
                
                # 检查炸弹后是否出现K
                new_strategy = self.analyze_miner_plan_new(updated_map)
                if new_strategy['has_k']:
                    print(f"<{mask_account(self.account_name)}> 炸弹后出现K！发现{len(new_strategy['k_positions'])}个K格子")
                    continue  # 返回循环开头处理K
                    
            # 没有炸弹或炸弹处理后，按序挖矿
            elif strategy['next_position']:
                next_row, next_col = strategy['next_position']
                row_real = next_row + 1
                col_real = next_col + 1
                
                print(f"<{mask_account(self.account_name)}> 按序挖矿位置[{row_real},{col_real}]")
                
                # 点击挖矿
                updated_map = self.tapminer(row_real, col_real)
                if not updated_map or not hasattr(updated_map, 'unit') or not updated_map.unit:
                    print(f"<{mask_account(self.account_name)}> 无法获取有效的挖矿地图，挖矿结束")
                    return True
                
                # 记录已点击的位置
                self.clicked_positions.add((next_row, next_col))
                print(f"<{mask_account(self.account_name)}> 已记录点击位置[{row_real},{col_real}]，当前已点击{len(self.clicked_positions)}个位置")
                
                # 调试：打印挖矿后的详细矿图
                if updated_map:
                    self.debug_print_mine_map(updated_map, f"<{mask_account(self.account_name)}> 挖矿后矿图")
                    table = self.parse_miner_map(updated_map, print_table=print_table, 
                                               header="挖矿后的矿区状态")
                    # print(f"<{mask_account(self.account_name)}> 挖矿后矿区状态: {table}")
                
                # 检查挖矿后是否出现K
                new_strategy = self.analyze_miner_plan_new(updated_map)
                if new_strategy['has_k']:
                    print(f"<{mask_account(self.account_name)}> 挖矿后出现K！发现{len(new_strategy['k_positions'])}个K格子")
                    continue  # 返回循环开头处理K
                    
            else:
                # 没有可挖的位置，可能需要特殊处理
                print(f"<{mask_account(self.account_name)}> 没有可挖的位置，结束挖矿")
                return False
        
        return True

    def start_mining(self, print_table=False):
        """
        开始挖矿的接口方法，与main.py兼容
        
        Args:
            print_table: 是否打印矿区表格，默认False
        """
        try:
            print(f"<{mask_account(self.account_name)}> 开始挖矿（使用新逻辑）")
            return self.do_wakuang_new(print_table)
        except Exception as e:
            print(f"<{mask_account(self.account_name)}> 挖矿执行失败: {e}")
            return False