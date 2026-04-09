"""
地牢管理模块
处理地牢自动战斗相关功能

协议流程 (from1to3boss 抓包):
4d33(init) → 8927 → 4f33(选技能) → 5d33 x5 → 5333(boss通关) → 4f33 → 5d33 x5 → 5333 → ... → 5b33(失败)

每层5战(index 0-4)，第5战即boss。
胜负判断(5e33响应): i3=1为赢, i3缺失为输。
技能增长: 初始10个, boss_complete时+1, 下一轮prepare时+2。
"""

import random
from .kpbltools import mask_account, ACManager
from . import kpbl_pb2


# 技能表 (从 old/skill.py 复制)
SKILL_TABLE = {
    "969106": {"desc": "怒冰", "level": 1, "rare": 1},
    "a48d06": {"desc": "白暴击率", "level": 1, "rare": 1},
    "a58d06": {"desc": "白反击率", "level": 1, "rare": 1},
    "a78d06": {"desc": "白连击率", "level": 1, "rare": 1},
    "aa8d06": {"desc": "白普攻中毒", "level": 1, "rare": 1},
    "ac8d06": {"desc": "硬皮", "level": 1, "rare": 1},
    "ad8d06": {"desc": "开场反击（Deprecated）", "level": 1, "rare": 1},
    "b19006": {"desc": "回合火焰", "level": 1, "rare": 1},
    "b28d06": {"desc": "怒伤⬆️", "level": 1, "rare": 1},
    "b29006": {"desc": "怒火焰", "level": 1, "rare": 1},
    "b38d06": {"desc": "连击伤害", "level": 1, "rare": 1},
    "b39006": {"desc": "开场火焰波", "level": 1, "rare": 1},
    "b49006": {"desc": "普攻闪电", "level": 1, "rare": 1},
    "b68d06": {"desc": "开场怒气", "level": 1, "rare": 1},
    "b78d06": {"desc": "普攻盾", "level": 1, "rare": 1},
    "b88d06": {"desc": "怒盾", "level": 1, "rare": 1},
    "c29306": {"desc": "回合光枪（Deprecated）", "level": 1, "rare": 1},
    "c39306": {"desc": "反击光枪", "level": 1, "rare": 1},
    "c49306": {"desc": "怒光枪", "level": 1, "rare": 1},
    "cd8f06": {"desc": "回合闪电", "level": 1, "rare": 1},
    "ce8f06": {"desc": "怒闪电", "level": 1, "rare": 1},
    "d08f06": {"desc": "五回合闪电", "level": 1, "rare": 1},
    "d78f06": {"desc": "受击火焰波", "level": 1, "rare": 1},
    "dd9206": {"desc": "普攻剑气", "level": 1, "rare": 1},
    "de9206": {"desc": "怒剑气（Deprecated）", "level": 1, "rare": 1},
    "f99106": {"desc": "飞刀", "level": 1, "rare": 1},
    "fa9106": {"desc": "飞刀毒", "level": 1, "rare": 1},
    "fb9106": {"desc": "飞刀怒", "level": 1, "rare": 1},
    "fc9106": {"desc": "飞刀血", "level": 1, "rare": 1},
    "fd9106": {"desc": "飞刀闪电", "level": 1, "rare": 1},
    "b4db06": {"desc": "白暴击率", "level": 2, "rare": 1},
    "b7db06": {"desc": "白连击率", "level": 2, "rare": 1},
    "dddd06": {"desc": "回合闪电", "level": 2, "rare": 1},
    "dedd06": {"desc": "怒闪电", "level": 2, "rare": 1},
    "e0dd06": {"desc": "五回合闪电", "level": 2, "rare": 1},
    "e7dd06": {"desc": "受击火焰波", "level": 2, "rare": 1},
    "ede006": {"desc": "普攻剑气", "level": 2, "rare": 1},
    "eee006": {"desc": "怒剑气（Deprecated）", "level": 2, "rare": 1},
    "89e006": {"desc": "飞刀", "level": 2, "rare": 1},
    "8ae006": {"desc": "飞刀毒", "level": 2, "rare": 1},
    "8be006": {"desc": "飞刀怒", "level": 2, "rare": 1},
    "8ce006": {"desc": "飞刀血", "level": 2, "rare": 1},
    "8de006": {"desc": "飞刀闪电", "level": 2, "rare": 1},
    "819206": {"desc": "飞刀掌握", "level": 1, "rare": 2},
    "868e06": {"desc": "攻击回怒", "level": 1, "rare": 2},
    "8b8e06": {"desc": "暴君", "level": 1, "rare": 2},
    "8c8e06": {"desc": "狂战士", "level": 1, "rare": 2},
    "8d8e06": {"desc": "技伤提升", "level": 1, "rare": 2},
    "8e8e06": {"desc": "王冠", "level": 1, "rare": 2},
    "8f8e06": {"desc": "连击⬆️", "level": 1, "rare": 2},
    "908e06": {"desc": "反击⬆️", "level": 1, "rare": 2},
    "918e06": {"desc": "暴击⬆️", "level": 1, "rare": 2},
    "928e06": {"desc": "怒气精通", "level": 1, "rare": 2},
    "938e06": {"desc": "连击流血", "level": 1, "rare": 2},
    "95eb01": {"desc": "猪猪猛击", "level": 1, "rare": 2},
    "999106": {"desc": "冰刺杀", "level": 1, "rare": 2},
    "c79306": {"desc": "黄光枪精通", "level": 1, "rare": 2},
    "c89306": {"desc": "黄光枪护盾", "level": 1, "rare": 2},
    "ca9306": {"desc": "光枪地震", "level": 1, "rare": 2},
    "d28f06": {"desc": "闪电精通", "level": 1, "rare": 2},
    "d58f06": {"desc": "闪电+1", "level": 1, "rare": 2},
    "95dc06": {"desc": "开场双倍", "level": 2, "rare": 2},
    "96dc06": {"desc": "攻击回怒", "level": 2, "rare": 2},
    "9adc06": {"desc": "中毒增伤", "level": 2, "rare": 2},
    "9bdc06": {"desc": "暴君", "level": 2, "rare": 2},
    "9cdc06": {"desc": "狂战士", "level": 2, "rare": 2},
    "9ddc06": {"desc": "技伤提升", "level": 2, "rare": 2},
    "9edc06": {"desc": "王冠", "level": 2, "rare": 2},
    "9fdc06": {"desc": "连击⬆️", "level": 2, "rare": 2},
    "a0dc06": {"desc": "反击⬆️", "level": 2, "rare": 2},
    "a1dc06": {"desc": "暴击⬆️", "level": 2, "rare": 2},
    "a2dc06": {"desc": "怒气精通", "level": 2, "rare": 2},
    "829206": {"desc": "飞刀冷却", "level": 1, "rare": 2},
    "ff9106": {"desc": "飞刀精通", "level": 1, "rare": 2},
    "d68f06": {"desc": "超级闪电", "level": 1, "rare": 3},
    "839206": {"desc": "飞刀两次", "level": 1, "rare": 3},
    "9b9106": {"desc": "冰冻提升", "level": 1, "rare": 3},
    "e98e06": {"desc": "回合攻击", "level": 1, "rare": 3},
    "eb8e06": {"desc": "怒气连发", "level": 1, "rare": 3},
    "ec8e06": {"desc": "连击之魂", "level": 1, "rare": 3},
    "f28e06": {"desc": "超级生命", "level": 1, "rare": 3},
    "f38e06": {"desc": "反击之魂", "level": 1, "rare": 3},
    "f48e06": {"desc": "三相", "level": 1, "rare": 3},
    "f58e06": {"desc": "爆竹", "level": 1, "rare": 3},
    "f68e06": {"desc": "玻璃大炮", "level": 1, "rare": 3},
    "fa8e06": {"desc": "三倍连击", "level": 1, "rare": 3},
}


class DungeonManager:
    def __init__(self, account_name, showres=1, delay=0.5, ac_manager=None):
        self.account_name = account_name
        self.showres = showres
        self.ac_manager = ac_manager or ACManager(account_name, showres=showres, delay=delay)

        # 状态
        self.skills = []          # 当前技能ID列表(hex字符串)
        self.current_hp = 0       # 当前HP
        self.current_buff = None  # dungeon_buff_info (累积buff)
        self.battle_count = 0
        self.boss_count = 0
        self.floor = 1            # 当前楼层
        self.battle_in_floor = 0  # 当前楼层内的战斗序号(0-4)

    # ── 技能管理 ──────────────────────────────────────

    def _select_skills(self, count):
        """随机选择技能,同一技能的不同等级版本不能同时存在"""
        selected_descs = {SKILL_TABLE[k]["desc"] for k in self.skills if k in SKILL_TABLE}
        available = [k for k in SKILL_TABLE
                     if k and k not in self.skills and SKILL_TABLE[k]["desc"] not in selected_descs]
        random.shuffle(available)
        new_skills = available[:count]
        self.skills.extend(new_skills)
        return new_skills

    def _skills_to_bytes(self):
        """将技能ID列表转为packed varint bytes"""
        result = b''
        for skill_hex in self.skills:
            value = int(skill_hex, 16)
            while value > 0x7F:
                result += bytes([(value & 0x7F) | 0x80])
                value >>= 7
            result += bytes([value])
        return result

    # ── 协议请求 ──────────────────────────────────────

    def init_dungeon(self):
        """4d33 - 初始化地牢,返回楼层号,失败返回None"""
        config = {"ads": "dungeon-init", "hexstringheader": "4d33", "times": 1}
        res = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        if res and len(res) > 6:
            resp = kpbl_pb2.dungeon_init_response()
            resp.ParseFromString(res[6:])
            if resp.i1 and not resp.i3:
                return None
            if resp.i3:
                return resp.i3 // 1000
        return None

    def send_8927(self):
        """8927 - init后的附加请求"""
        config = {"ads": "dungeon-8927", "hexstringheader": "8927", "times": 1}
        self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)

    def prepare_battle(self):
        """4f33 - 选技能并准备战斗"""
        config = {
            "ads": "dungeon-prepare",
            "hexstringheader": "4f33",
            "times": 1,
            "requestbodytype": "dungeon_prepare_request",
            "request_body_i2": self._skills_to_bytes(),
            "request_body_i3": self.current_hp,
        }
        return self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)

    def do_battle(self):
        """5d33 - 执行一次战斗, 返回 (win, hp)"""
        level_id = self.floor * 1000 + self.battle_in_floor
        config = {
            "ads": "dungeon-battle",
            "hexstringheader": "5d33",
            "times": 1,
            "requestbodytype": "dungeon_battle_request",
            "request_body_i2": str(self.ac_manager.I8_VALUE),
            "request_body_i3": level_id,
        }
        res = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        if res and len(res) > 6:
            resp = kpbl_pb2.dungeon_battle_response()
            resp.ParseFromString(res[6:])
            win = (resp.i3 == 1)
            hp = resp.i5 if resp.i5 else 0
            return win, hp
        return False, 0

    def boss_complete(self):
        """5333 - Boss通关"""
        config = {
            "ads": "dungeon-boss",
            "hexstringheader": "5333",
            "times": 1,
            "requestbodytype": "dungeon_boss_complete_request",
            "request_body_i2": self._skills_to_bytes(),
            "request_body_i4": self.current_hp,
        }
        if self.current_buff:
            pass

        res = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        if res and len(res) > 6:
            resp = kpbl_pb2.dungeon_boss_complete_response()
            resp.ParseFromString(res[6:])
            if resp.i5 and resp.i5.i1:
                self.current_buff = resp.i5
        return res

    def battle_fail(self, level_id):
        """5b33 - 战斗失败结算"""
        config = {
            "ads": "dungeon-fail",
            "hexstringheader": "5b33",
            "times": 1,
            "requestbodytype": "dungeon_fail_request",
            "request_body_i2": level_id,
        }
        return self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)

    # ── 主循环 ────────────────────────────────────────

    def auto_battle(self):
        """自动战斗主循环"""
        # 1. 初始化
        init_floor = self.init_dungeon()
        if init_floor is None:
            return 0
        self.floor = init_floor

        # 2. 8927 附加请求
        self.send_8927()

        # 3. 初始选10个技能 + 首次prepare
        self.skills = []
        self._select_skills(10)
        self.prepare_battle()

        # 4. 战斗循环
        while True:
            self.battle_count += 1
            win, hp = self.do_battle()

            if not win:
                level_id = self.floor * 1000 + self.battle_in_floor
                self.battle_fail(level_id)
                break

            self.current_hp = hp
            self.battle_in_floor += 1

            if self.battle_in_floor >= 5:
                self.boss_count += 1
                self._select_skills(1)
                self.boss_complete()
                self._select_skills(2)
                self.floor += 1
                self.battle_in_floor = 0
                self.prepare_battle()

        print(f"[{mask_account(self.account_name)}] 地牢: 楼层{self.floor}, Boss={self.boss_count}")
        return self.boss_count
