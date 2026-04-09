"""
公会考古管理模块
处理公会考古活动：领取奖励、自动挖掘
"""

import binascii
import time
from . import kpbl_pb2
from .kpbltools import ACManager


class KGManager:
    """公会考古管理器"""

    # 锤子的背包物品类型
    HAMMER_TYPE = 151

    def __init__(self, account_name, ac_manager=None):
        self.account_name = account_name
        self.ac_manager = ac_manager or ACManager(account_name)

    def _build_and_send(self, hexstringheader, request_body):
        """构建带header的请求并发送"""
        serialized = request_body.SerializeToString()
        header = binascii.unhexlify(hexstringheader)[:2]
        length = len(serialized)
        len_bytes = bytes([length & 0xFF, (length >> 8) & 0xFF])
        binary_data = header + len_bytes + serialized
        return self.ac_manager.send_binary_data(
            self.account_name, binary_data, describe=hexstringheader, showres=0
        )

    def _make_requester(self):
        account = self.ac_manager.get_account(self.account_name)
        return self.ac_manager.common_header_requester1(account)

    def _parse_kg(self, res):
        """解析考古响应"""
        if not res or len(res) <= 20:
            return None
        resp = kpbl_pb2.kg_response()
        resp.ParseFromString(res[6:])
        return resp

    def query_kg(self):
        """d959: 查询考古状态"""
        config = {"ads": "考古查询", "times": 1, "hexstringheader": "d959"}
        res = self.ac_manager.do_common_request(self.account_name, config, showres=0)
        return self._parse_kg(res)

    def claim_reward(self, tier):
        """e159: 领取考古奖励"""
        config = {"ads": f"考古领奖{tier}", "times": 1, "hexstringheader": "e159",
                  "request_body_i2": tier}
        res = self.ac_manager.do_common_request(self.account_name, config, showres=0)
        if not res or len(res) <= 20:
            return False
        sc = self.ac_manager.get_status_code(res)
        return sc == 1

    def dig(self, layer, x, y):
        """db59: 在指定层的(x,y)坐标挖掘"""
        req = kpbl_pb2.request_body_for_kg()
        req.r1.CopyFrom(self._make_requester())
        req.i2 = layer
        req.i3.x = x
        req.i3.y = y
        res = self._build_and_send("db59", req)
        if not res:
            return None
        return self._parse_kg(res.content)

    def query_board(self, layer):
        """db59: 查询指定层棋盘(不挖掘)"""
        config = {"ads": f"考古查询层{layer}", "times": 1, "hexstringheader": "db59",
                  "request_body_i2": layer}
        res = self.ac_manager.do_common_request(self.account_name, config, showres=0)
        return self._parse_kg(res)

    def claim_all_rewards(self):
        """尝试领取所有可领取的奖励，返回成功领取的数量"""
        for tier in range(31):
            ok = self.claim_reward(tier)
            if ok:
                print(f"  领取奖励 tier {tier} 成功")
            else:
                return 
        return 

    def get_undug_cells(self, board):
        """获取未挖掘的格子坐标列表"""
        dug_set = set()
        for dc in board.dug_cells:
            dug_set.add((dc.pos.x, dc.pos.y))
        undug = []
        for y in range(board.height):
            for x in range(board.width):
                if (x, y) not in dug_set:
                    undug.append((x, y))
        return undug

    def print_board(self, board):
        """打印棋盘状态"""
        # 构建宝物地图
        treasure_map = {}
        for item in board.items:
            for c in item.cells:
                treasure_map[(c.x, c.y)] = item.treasure_type
        # 构建已挖掘集合
        dug_set = set()
        completing_set = set()
        for dc in board.dug_cells:
            dug_set.add((dc.pos.x, dc.pos.y))
            if dc.is_completing:
                completing_set.add((dc.pos.x, dc.pos.y))

        total = board.width * board.height
        dug_count = len(dug_set)
        print(f"  棋盘 {board.board_id} ({board.width}x{board.height}), 已挖 {dug_count}/{total}, 宝物 {len(board.items)} 个")
        for y in range(board.height - 1, -1, -1):
            row = f"  y={y}: "
            for x in range(board.width):
                if (x, y) in dug_set:
                    if (x, y) in treasure_map:
                        t = treasure_map[(x, y)]
                        mark = f"{t}*" if (x, y) in completing_set else f"{t} "
                    else:
                        mark = "o "
                else:
                    mark = ". "
                row += mark
            print(row)
        print("       " + "".join(f"{x} " for x in range(board.width)))

    def run(self):
        """执行考古：领取奖励 → login刷新背包 → 缓存锤子数量 → 自动挖掘"""
        # 登录刷新背包
        self.ac_manager.login(self.account_name)

        # 1. 领取奖励
        print("== 步骤1: 领取考古奖励 ==")
        self.claim_all_rewards()

        # 2. login一次刷新背包，获取锤子数量并缓存
        self.ac_manager.login(self.account_name)
        baginfo = self.ac_manager.get_account(self.account_name, 'baginfo') or {}
        entry = baginfo.get(self.HAMMER_TYPE, 0)
        hammer = entry.get('count', 0) if isinstance(entry, dict) else entry
        print(f"== 步骤2: 锤子数量 = {hammer} ==")
        if hammer <= 0:
            print("  没有锤子，结束")
            return

        # 3. 查询棋盘并挖掘
        print("== 步骤3: 自动挖掘 ==")
        kg = self.query_kg()
        if not kg or not kg.boards.board1.board_id:
            print("  无法获取考古数据")
            return

        board = kg.boards.board1
        layer = board.layers[0] if board.layers else 0
        if not layer:
            print("  无法获取层数")
            return

        self.print_board(board)
        undug = self.get_undug_cells(board)
        print(f"  层 {layer}, 未挖 {len(undug)} 格, 锤子 {hammer}")

        # 间隔1挖掘（棋盘格式: 先挖偶数位置，再挖奇数位置）
        dig_order = sorted(undug, key=lambda c: (c[1], c[0]))
        # 间隔1: 先挖 (x+y)%2==0 的格子，再挖其余
        phase1 = [c for c in dig_order if (c[0] + c[1]) % 2 == 0]
        phase2 = [c for c in dig_order if (c[0] + c[1]) % 2 == 1]
        ordered = phase1 + phase2

        dug_count = 0
        for x, y in ordered:
            if hammer <= 0:
                break
            result = self.dig(layer, x, y)
            hammer -= 1
            dug_count += 1
            if result and result.boards.board1.board_id:
                new_board = result.boards.board1
                new_items = len(new_board.items)
                old_items = len(board.items)
                found = f", 发现宝物! ({old_items}->{new_items})" if new_items > old_items else ""
                board = new_board
            else:
                found = ""
            print(f"  挖掘 ({x},{y}) 剩余锤子 {hammer}{found}")
            time.sleep(0.3)

        print(f"== 完成: 共挖 {dug_count} 格 ==")
        self.print_board(board)
