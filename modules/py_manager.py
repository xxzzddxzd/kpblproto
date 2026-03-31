"""
培育管理器

将原 `autopy.py` 中与“培育”相关的流程重构为类，提供交互式运行入口。
不修改原文件，复用必要的算法与打印逻辑。
"""

from __future__ import annotations

import binascii
import json
import time
from typing import Dict, List, Tuple
import importlib
import importlib.util
import os
import sys

# 统一从 modules 目录下导入工具与 pb2，避免与根目录同名文件冲突
from .kpbltools import ACManager
from . import kpbl_pb2 as mod_kpbl_pb2

# 不直接依赖根目录 `petskill` 的常规导入，改为在类中动态加载


class PeiyuManager:
    """
    培育管理器：封装“培育”主流程与辅助函数。

    主要方法：
    - run_interactive(): 交互式运行（与原脚本相同的交互体验）
    - dopy(): 发送培育请求
    - doupdate(): 发送更新请求
    """

    # 技能稀有度与颜色映射（仅用于打印）
    SKILL_RARE_MAPPING: Dict[str, str] = {
        "1f": "B",
        "27": "A",
        "2e": "S",
        "2f": "S",
        "36": "SS",
        "3e": "SSS",
    }

    PINK = "\033[95m"
    CYAN = "\033[96m"
    RESET = "\033[0m"

    SUFFIX_COLOR_MAPPING: Dict[str, str] = {
        "1f": "",
        "27": "",
        "2e": "",
        "2f": "",
        "36": PINK,
        "3e": CYAN,
    }

    # 内置宠物类型数据（精简自原 petskill.py）
    DEFAULT_TYPE_DATA: Dict[int, str] = {
        330503: "黄小飞象",
        330102: "白史莱姆",
        330604: "红史莱姆",
        330201: "绿翠叶蛙",
        330701: "粉艾莎",
        330703: "粉猪",
        330605: "红紫魔狐",
        330704: "粉苏苏",
        330602: "红独角兽",
        330101: "白小鹦鹉",
        330702: "粉芙蕾雅",
        330601: "红小闪",
        330603: "红火龙",
    }

    # 内置技能数据（精简自原 petskill.py）
    DEFAULT_SKILL_DATA: Dict[str, Dict] = {
        # 彩
        "c13e": {"name": "全局攻击", "topvalue": 20},
        "c23e": {"name": "全局生命", "topvalue": 20},
        "c33e": {"name": "全局防御", "topvalue": 20},
        "c43e": {"name": "连击伤害", "topvalue": 100},
        "c53e": {"name": "连击伤害减免", "topvalue": 100},
        "c63e": {"name": "反击伤害", "topvalue": 100},
        "c73e": {"name": "反击伤害减免", "topvalue": 100},
        "c83e": {"name": "暴击伤害", "topvalue": 60},
        "c93e": {"name": "暴击伤害减免", "topvalue": 60},
        "ca3e": {"name": "技能伤害", "topvalue": 60},
        "cb3e": {"name": "技能伤害减免", "topvalue": 60},
        "cc3e": {"name": "普攻伤害", "topvalue": 60},
        "cd3e": {"name": "普攻伤害减免", "topvalue": 60},
        "ce3e": {"name": "宠物伤害", "topvalue": 60},
        "cf3e": {"name": "宠物伤害减免", "topvalue": 60},
        "d03e": {"name": "回复效果", "topvalue": 60},
        "d13e": {"name": "对首领伤害", "topvalue": 60},
        "d23e": {"name": "变异 宠物基础属性", "topvalue": 100},
        "d33e": {"name": "巨人 该宠物伤害增加", "topvalue": 150},
        "d43e": {"name": "史诗领袖 史诗宠物伤害增加", "topvalue": 120},
        "d53e": {"name": "传说领袖 传说宠物伤害增加", "topvalue": 120},
        "d63e": {"name": "神话领袖 神话宠物伤害增加", "topvalue": 120},
        "d73e": {"name": "凶猛 连击率", "topvalue": 10},
        "d83e": {"name": "顽强 反击率", "topvalue": 10},
        "d93e": {"name": "暴虐 暴击率", "topvalue": 10},
        "da3e": {"name": "敏捷 忽视连击率", "topvalue": 10},
        "db3e": {"name": "威武 忽视反击率", "topvalue": 10},
        "dc3e": {"name": "坚韧 忽视暴击率", "topvalue": 10},
        "dd3e": {"name": "不动如山 免控率", "topvalue": 5},
        "de3e": {"name": "燃烧伤害减免", "topvalue": 30},
        "e03e": {"name": "毒伤害", "topvalue": 30},
        "e13e": {"name": "毒伤害减免", "topvalue": 30},
        "e23e": {"name": "持续伤害增伤", "topvalue": 30},
        "e33e": {"name": "持续伤害减免", "topvalue": 30},
        # 粉
        "d936": {"name": "全局攻击", "topvalue": 17.5},
        "da36": {"name": "全局生命", "topvalue": 17.5},
        "db36": {"name": "全局防御", "topvalue": 17.5},
        "dc36": {"name": "连击伤害", "topvalue": 87.5},
        "dd36": {"name": "连击伤害减免", "topvalue": 87.5},
        "de36": {"name": "反击伤害", "topvalue": 87.5},
        "df36": {"name": "反击伤害减免", "topvalue": 87.5},
        "e036": {"name": "暴击伤害", "topvalue": 52},
        "e136": {"name": "暴击伤害减免", "topvalue": 52},
        "e236": {"name": "技能伤害", "topvalue": 52},
        "e336": {"name": "技能伤害减免", "topvalue": 52},
        "e436": {"name": "普攻伤害", "topvalue": 52},
        "e536": {"name": "普攻伤害减免", "topvalue": 52},
        "e636": {"name": "宠物伤害", "topvalue": 52},
        "e736": {"name": "宠物伤害减免", "topvalue": 52},
        "e836": {"name": "回复效果", "topvalue": 52},
        "e936": {"name": "对首领伤害", "topvalue": 52},
        "ea36": {"name": "变异 宠物基础属性", "topvalue": 75},
        "eb36": {"name": "巨人 该宠物伤害增加", "topvalue": 120},
        "ec36": {"name": "史诗领袖 史诗宠物伤害增加", "topvalue": 90},
        "ed36": {"name": "传说领袖 传说宠物伤害增加", "topvalue": 90},
        "ee36": {"name": "神话领袖 神话宠物伤害增加", "topvalue": 90},
        "ef36": {"name": "凶猛 连击率", "topvalue": 5},
        "f036": {"name": "顽强 反击率", "topvalue": 5},
        "f136": {"name": "暴虐 暴击率", "topvalue": 5},
        "f236": {"name": "敏捷 忽视连击率", "topvalue": 5},
        "f336": {"name": "威武 忽视反击率", "topvalue": 5},
        "f436": {"name": "坚韧 忽视暴击率", "topvalue": 5},
        "f536": {"name": "燃烧伤害", "topvalue": 20},
        "f636": {"name": "燃烧伤害减免", "topvalue": 20},
        "f736": {"name": "毒伤害", "topvalue": 20},
        "f836": {"name": "毒伤害减免", "topvalue": 20},
        "f936": {"name": "持续伤害增伤", "topvalue": 20},
        "fa36": {"name": "持续伤害减免", "topvalue": 20},
        # 红
        "f12e": {"name": "全局攻击", "topvalue": 15},
        "f22e": {"name": "全局生命", "topvalue": 15},
        "f32e": {"name": "全局防御", "topvalue": 15},
        "f42e": {"name": "连击伤害", "topvalue": 75},
        "f52e": {"name": "连击伤害减免", "topvalue": 75},
        "f62e": {"name": "反击伤害", "topvalue": 75},
        "f72e": {"name": "反击伤害减免", "topvalue": 75},
        "f82e": {"name": "暴击伤害", "topvalue": 44},
        "f92e": {"name": "暴击伤害减免", "topvalue": 44},
        "fa2e": {"name": "技能伤害", "topvalue": 44},
        "fb2e": {"name": "技能伤害减免", "topvalue": 44},
        "fc2e": {"name": "普攻伤害", "topvalue": 44},
        "fd2e": {"name": "普攻伤害减免", "topvalue": 44},
        "fe2e": {"name": "宠物伤害", "topvalue": 44},
        "ff2e": {"name": "宠物伤害减免", "topvalue": 44},
        "802f": {"name": "回复效果", "topvalue": 44},
        "812f": {"name": "首领伤害", "topvalue": 44},
        "822f": {"name": "变异 宠物基础属性", "topvalue": 50},
        "832f": {"name": "巨人 该宠物伤害增加", "topvalue": 90},
        "842f": {"name": "史诗领袖 史诗宠物伤害增加", "topvalue": 60},
        "852f": {"name": "传说领袖 传说宠物伤害增加", "topvalue": 60},
        "862f": {"name": "神话领袖 神话宠物伤害增加", "topvalue": 60},
        "872f": {"name": "燃烧伤害", "topvalue": 10},
        "882f": {"name": "燃烧伤害减免", "topvalue": 10},
        "892f": {"name": "毒伤害", "topvalue": 10},
        "8a2f": {"name": "毒伤害减免", "topvalue": 10},
        "8b2f": {"name": "持续伤害增伤", "topvalue": 10},
        "8c2f": {"name": "持续伤害减免", "topvalue": 10},
        # 黄
        "8927": {"name": "全局攻击", "topvalue": 12.5},
        "8a27": {"name": "全局生命", "topvalue": 12.5},
        "8b27": {"name": "全局防御", "topvalue": 12.5},
        "8c27": {"name": "连击伤害", "topvalue": 62.5},
        "8d27": {"name": "连击伤害减免", "topvalue": 62.5},
        "8e27": {"name": "反击伤害", "topvalue": 62.5},
        "8f27": {"name": "反击伤害减免", "topvalue": 62.5},
        "9027": {"name": "暴击伤害", "topvalue": 36},
        "9127": {"name": "暴击伤害减免", "topvalue": 36},
        "9227": {"name": "技能伤害", "topvalue": 36},
        "9327": {"name": "技能伤害减免", "topvalue": 36},
        "9427": {"name": "普攻伤害", "topvalue": 36},
        "9527": {"name": "普攻伤害减免", "topvalue": 36},
        "9627": {"name": "宠物伤害", "topvalue": 36},
        "9727": {"name": "宠物伤害减免", "topvalue": 36},
        "9827": {"name": "回复效果", "topvalue": 36},
        "9927": {"name": "对首领伤害", "topvalue": 36},
    }

    def __init__(self, account: str) -> None:
        self.account_name = account
        self.ac_manager = ACManager(account=account)
        # 用实例字段替代全局
        self.deployed_pets_info: List[Dict] = []
        self.skill_data, self.type_data = self._load_skill_and_type_data()
        # 每个技能名对应的最高topvalue（SSS级），用于优秀率计算
        self.max_topvalue_by_name: Dict[str, float] = {}
        for _sid, _info in self.skill_data.items():
            _name = _info.get("name", "")
            _top = _info.get("topvalue", 0)
            if _name not in self.max_topvalue_by_name or _top > self.max_topvalue_by_name[_name]:
                self.max_topvalue_by_name[_name] = _top


    @staticmethod
    def _load_skill_and_type_data() -> Tuple[Dict[str, Dict], Dict[int, str]]:
        """
        优先尝试常规导入 `petskill`；失败则按文件路径加载父目录下的 `petskill.py`。
        返回 (skill_data, type_data)
        """
        # 1) 直接导入
        try:
            mod = importlib.import_module("petskill")
            skill_data = getattr(mod, "skill_data")
            type_data = getattr(mod, "type_data")
            return skill_data, type_data
        except Exception:
            pass

        # 2) 按路径加载父目录下的 petskill.py
        base_dir = os.path.dirname(os.path.dirname(__file__))
        petskill_path = os.path.join(base_dir, "petskill.py")
        # 如果存在文件也允许加载，否则继续返回内置表
        if os.path.isfile(petskill_path):
            try:
                spec = importlib.util.spec_from_file_location("petskill_dyn", petskill_path)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules["petskill_dyn"] = mod
                    spec.loader.exec_module(mod)
                    skill_data = getattr(mod, "skill_data")
                    type_data = getattr(mod, "type_data")
                    return skill_data, type_data
            except Exception:
                pass
        return PeiyuManager.DEFAULT_SKILL_DATA, PeiyuManager.DEFAULT_TYPE_DATA

    # ============================
    # 基础请求
    # ============================
    def dopy(self, pet_id: int) -> bytes | None:
        request = {"ads": "培育", "times": 1, "request_body_i2": pet_id, "hexstringheader": "b14f"}
        return self.ac_manager.do_common_request(self.account_name, request, showres=0)

    def doupdate(self, pet_id: int) -> bytes | None:
        print(f"更新{pet_id}")
        request = {"ads": "更新", "times": 1, "request_body_i2": pet_id, "hexstringheader": "b34f"}
        return self.ac_manager.do_common_request(self.account_name, request, showres=0)

    # ============================
    # 解析与评估
    # ============================
    @staticmethod
    def hex_to_percent(hex_value: str) -> float:
        # 小端序转换为百分比，保持与原逻辑一致
        if len(hex_value) == 4:
            int_value = int(hex_value[2:4] + hex_value[0:2], 16)
        else:
            int_value = int(hex_value, 16)
        if int_value == 0:
            return 100.0
        return round(int_value / 20000 * 100, 2)

    @staticmethod
    def parse_skill_and_value_list(skill_hex: str, value_hex: str) -> Tuple[List[str], List[str]]:
        # 拆分技能为 4 字节分组
        parsed_skills = [skill_hex[i : i + 4] for i in range(0, len(skill_hex), 4) if i + 4 <= len(skill_hex)]
        # 值里遇到 "00" 视为空位补 "0000"
        parsed_values: List[str] = []
        i = 0
        while i < len(value_hex):
            if i + 2 <= len(value_hex) and value_hex[i : i + 2] == "00":
                parsed_values.append("0000")
                i += 2
            elif i + 4 <= len(value_hex):
                parsed_values.append(value_hex[i : i + 4])
                i += 4
            else:
                parsed_values.append("0000")
                i += 2
        # 对齐长度
        min_len = min(len(parsed_skills), len(parsed_values))
        return parsed_skills[:min_len], parsed_values[:min_len]

    def analyze_response(self, response_bytes: bytes) -> Tuple[List[str], List[str], List[str], List[str]]:
        data = response_bytes[6:]
        # 解析 pb
        response = mod_kpbl_pb2.response_py_main()
        response.ParseFromString(data)

        try:
            target_cell = response.py.n_skill[0]
            hex_skill_new = binascii.hexlify(target_cell.n_skillsnew[0]).decode()
            hex_value_new = binascii.hexlify(target_cell.n_valuesnew[0]).decode()
            hex_skill_old = binascii.hexlify(target_cell.n_skillsold[0]).decode()
            hex_value_old = binascii.hexlify(target_cell.n_valuesold[0]).decode()

            # print("--------------------------------")
            # print(f"level: {response.level}，{response.levelvalue}")
            # print(f"hex_str_skillnew: {hex_skill_new}")
            # print(f"hex_str_valuenew: {hex_value_new}")
            # print(f"hex_str_skillold: {hex_skill_old}")
            # print(f"hex_str_valueold: {hex_value_old}")
            # print("--------------------------------")

            skill_new, value_new = self.parse_skill_and_value_list(hex_skill_new, hex_value_new)
            skill_old, value_old = self.parse_skill_and_value_list(hex_skill_old, hex_value_old)
        except Exception as e:
            print(f"解析错误: {e}")
            skill_new, value_new, skill_old, value_old = [], [], [], []

        return skill_new, skill_old, value_new, value_old

    # ============================
    # 打印与统计
    # ============================
    def print_pet_skills(
        self,
        pet_name: str,
        skill_ids: List[str],
        value_list: List[str],
        is_new: bool = False,
        target_skill_types: Dict[str, float] | None = None,
    ) -> Dict[str, float]:
        skill_name_values: Dict[str, float] = {}
        skill_type_totals: Dict[str, float] = {}
        if target_skill_types:
            for k in target_skill_types.keys():
                skill_type_totals[k] = 0

        tag = "新" if is_new else "当前"
        print(f"\n宠物[{pet_name}]的{tag}技能详情:")

        for i, skill_id in enumerate(skill_ids):
            info = self.skill_data.get(skill_id, {"name": "未知技能", "topvalue": 0})
            name = info.get("name", "未知技能")
            top_value = info.get("topvalue", 0)

            actual_value = 0.0
            if i < len(value_list):
                percent = self.hex_to_percent(value_list[i])
                actual_value = round(percent * top_value / 100, 2)

            skill_name_values[name] = skill_name_values.get(name, 0.0) + actual_value
            if target_skill_types and name in target_skill_types:
                skill_type_totals[name] = skill_type_totals.get(name, 0.0) + actual_value

            suffix = skill_id[-2:]
            color = self.SUFFIX_COLOR_MAPPING.get(suffix, "")
            rare = self.SKILL_RARE_MAPPING.get(suffix, "")
            display = f"{i+1}. {rare}: {name}{actual_value}({top_value})"
            if color:
                display = f"{color}{display}{self.RESET}"
            print(display)

        print("\n相同词条数值统计:")
        for name, total in skill_name_values.items():
            print(f"{name}: {total}")

        if target_skill_types:
            # 优先使用上阵3宠总和与目标值的对比
            if getattr(self, "deployed_pets_info", None):
                print("\n上阵3宠目标对比:")
                deployed_totals: Dict[str, float] = {k: 0.0 for k in target_skill_types.keys()}
                for pet in self.deployed_pets_info:
                    if pet.get("no_skills_data"):
                        continue
                    for s in pet.get("skills", []):
                        name = s["name"]
                        if name in deployed_totals:
                            deployed_totals[name] += s["actual_value"]

                for k, target in target_skill_types.items():
                    current = deployed_totals.get(k, 0.0)
                    mark = "✓" if current >= target else f"✗ (差距: {target - current:.2f})"
                    print(f"{k}: {current:.2f}/{target} {mark}")
            else:
                # 回退：仅当前宠物词条与目标值对比（无上阵信息时）
                print("\n目标技能类型总值统计:")
                for k, target in target_skill_types.items():
                    current = skill_type_totals.get(k, 0.0)
                    mark = "✓" if current >= target else f"✗ (差距: {target - current:.2f})"
                    print(f"{k}: {current:.2f}/{target} {mark}")

        return skill_type_totals

    def _compute_skill_details(self, skill_ids: List[str], value_list: List[str]) -> List[Dict]:
        """将技能ID和数值列表解析为详细信息字典列表"""
        result = []
        for i, skill_id in enumerate(skill_ids):
            info = self.skill_data.get(skill_id)
            if info is None:
                print(f"  \033[93m⚠ 未记录的词条ID: {skill_id}\033[0m")
                info = {"name": f"未知({skill_id})", "topvalue": 0}
                input("  按回车键继续...")
            name = info.get("name", "未知技能")
            top_value = info.get("topvalue", 0)
            actual_value = 0.0
            if i < len(value_list):
                percent = self.hex_to_percent(value_list[i])
                actual_value = round(percent * top_value / 100, 2)
            suffix = skill_id[-2:]
            rare = self.SKILL_RARE_MAPPING.get(suffix, "")
            color = self.SUFFIX_COLOR_MAPPING.get(suffix, "")
            result.append({
                "id": skill_id, "name": name, "top_value": top_value,
                "actual_value": actual_value, "rare": rare, "color": color,
            })
        return result

    def _format_skill_line(self, idx: int, d: Dict) -> str:
        """格式化单个技能行"""
        text = f"  {idx}. [{d['rare']:>3}] {d['name']} {d['actual_value']}/{d['top_value']}"
        if d["color"]:
            text = f"  {d['color']}{idx}. [{d['rare']:>3}] {d['name']} {d['actual_value']}/{d['top_value']}{self.RESET}"
        return text

    # 评估是否建议更新
    def analyze_skill(
        self,
        response_bytes: bytes,
        current_pet_name: str | None = None,
        target_skill_types: Dict[str, float] | None = None,
        round_num: int = 0,
    ) -> Tuple[bool, List[Dict]]:
        """分析培育结果，返回 (是否建议更新, 新技能详情列表)"""
        skill_new, skill_old, value_new, value_old = self.analyze_response(response_bytes)
        old_details = self._compute_skill_details(skill_old, value_old)
        new_details = self._compute_skill_details(skill_new, value_new)

        pet_label = current_pet_name or "未知宠物"
        print(f"\n{'═' * 50}")
        print(f"  培育 #{round_num}  {pet_label}")
        print(f"{'═' * 50}")

        # 当前词条
        print("  当前:")
        for i, d in enumerate(old_details):
            print(self._format_skill_line(i + 1, d))

        print("  新:")
        for i, d in enumerate(new_details):
            print(self._format_skill_line(i + 1, d))

        # SS/SSS 统计
        sss = sum(1 for d in new_details if d["rare"] == "SSS")
        condition2 = sss >= 2

        condition1 = False
        if target_skill_types:
            # 当前宠旧词条合计（数值 + 优秀率，优秀率以SSS最高值为基准）
            old_pet_totals: Dict[str, float] = {}
            old_pet_rates: Dict[str, float] = {}
            for d in old_details:
                if d["name"] in target_skill_types:
                    old_pet_totals[d["name"]] = old_pet_totals.get(d["name"], 0) + d["actual_value"]
                    max_top = self.max_topvalue_by_name.get(d["name"], d["top_value"])
                    rate = (d["actual_value"] / max_top * 100) if max_top > 0 else 0
                    old_pet_rates[d["name"]] = old_pet_rates.get(d["name"], 0) + rate
            # 当前宠新词条合计（数值 + 优秀率）
            new_pet_totals: Dict[str, float] = {}
            new_pet_rates: Dict[str, float] = {}
            for d in new_details:
                if d["name"] in target_skill_types:
                    new_pet_totals[d["name"]] = new_pet_totals.get(d["name"], 0) + d["actual_value"]
                    max_top = self.max_topvalue_by_name.get(d["name"], d["top_value"])
                    rate = (d["actual_value"] / max_top * 100) if max_top > 0 else 0
                    new_pet_rates[d["name"]] = new_pet_rates.get(d["name"], 0) + rate

            # 全局当前总值
            global_before: Dict[str, float] = {k: 0.0 for k in target_skill_types}
            if self.deployed_pets_info:
                for pet in self.deployed_pets_info:
                    if pet.get("no_skills_data"):
                        continue
                    for s in pet.get("skills", []):
                        if s["name"] in global_before:
                            global_before[s["name"]] += s["actual_value"]

            # 更新后全局 = 全局当前 - 当前宠旧词条 + 新词条
            global_after: Dict[str, float] = dict(global_before)
            if current_pet_name and self.deployed_pets_info:
                for pet in self.deployed_pets_info:
                    if pet.get("name") == current_pet_name:
                        for s in pet.get("skills", []):
                            if s["name"] in global_after:
                                global_after[s["name"]] -= s["actual_value"]
                        break
            for k, v in new_pet_totals.items():
                global_after[k] = global_after.get(k, 0) + v

            # 关注词条变化表（基于优秀率）
            print(f"\n  ★ 关注词条变化:")
            total_rate_delta = 0.0
            all_met = True
            for k, target in target_skill_types.items():
                old_rate = old_pet_rates.get(k, 0)
                new_rate = new_pet_rates.get(k, 0)
                old_v = old_pet_totals.get(k, 0)
                new_v = new_pet_totals.get(k, 0)
                rate_delta = new_rate - old_rate
                total_rate_delta += rate_delta
                g_before = global_before.get(k, 0)
                g_after = global_after.get(k, 0)
                met = g_after >= target if target > 0 else True
                all_met = all_met and met

                if rate_delta > 0:
                    delta_str = f"\033[92m▲{rate_delta:.1f}%\033[0m"
                elif rate_delta < 0:
                    delta_str = f"\033[91m▼{abs(rate_delta):.1f}%\033[0m"
                else:
                    delta_str = "─"
                if target > 0:
                    mark = "\033[92m✓\033[0m" if met else "\033[91m✗\033[0m"
                    print(f"  {k}: {old_v:.2f}[{old_rate:.1f}%]→{new_v:.2f}[{new_rate:.1f}%]({delta_str}) 全局:{g_before:.2f}→{g_after:.2f}/{target} {mark}")
                else:
                    print(f"  {k}: {old_rate:.1f}%→{new_rate:.1f}%({delta_str})")

            if all_met and any(t > 0 for t in target_skill_types.values()):
                print(f"\n  \033[92m✓ 所有目标已达成，强烈建议更新\033[0m")
                print(f"{'═' * 50}")
                return True, new_details

            if total_rate_delta > 0:
                print(f"\n  优秀率总变化: \033[92m+{total_rate_delta:.1f}%\033[0m")
                condition1 = True
            elif total_rate_delta < 0:
                print(f"\n  优秀率总变化: \033[91m{total_rate_delta:.1f}%\033[0m")
            else:
                print(f"\n  优秀率总变化: 0")

        if condition2:
            print(f"  发现{sss}个\033[96mSSS\033[0m技能")

        result = condition1 or condition2
        if result:
            print(f"\n  → \033[92m建议更新 ✓\033[0m")
        else:
            print(f"\n  → 不建议更新")
        print(f"{'═' * 50}")
        return result, new_details

    def _update_deployed_pet_skills(self, pet_name: str, new_details: List[Dict]) -> None:
        """更新出战宠物的技能数据（doupdate后调用，刷新本地缓存）"""
        for pet in self.deployed_pets_info:
            if pet.get("name") == pet_name:
                pet["skills"] = [
                    {
                        "id": d["id"],
                        "name": d["name"],
                        "value": "",
                        "percent": 0,
                        "actual_value": d["actual_value"],
                    }
                    for d in new_details
                ]
                pet.pop("no_skills_data", None)
                print(f"  ✓ 已刷新 [{pet_name}] 的本地词条数据")
                break

    # ============================
    # 业务流程（交互式）
    # ============================
    @staticmethod
    def _jstopvalue(level: int) -> int:
        return level + 15 if level <= 140 else 155 + (level - 140) * 2

    def _init_deployed_pets(self, target_skill_types: Dict[str, float]) -> None:
        self.deployed_pets_info = []
        account_data = self.ac_manager.accounts.get(self.account_name)
        if not account_data or "pets" not in account_data:
            print("未找到宠物信息")
            return

        pets_info = account_data.get("pets", [])

        # 从login的position字段自动判断出战宠物
        candidate_pets: List[Dict] = []
        for pet in pets_info:
            pet_type = str(pet.get("type", ""))
            if pet_type.startswith("3305") or pet_type.startswith("3306") or pet_type.startswith("3307"):
                candidate_pets.append(pet)

        if not candidate_pets:
            print("未找到3305/3306/3307类型的宠物")
            return

        selected_pets = [p for p in candidate_pets if p.get("position", 0) > 0]
        selected_pets.sort(key=lambda p: p.get("position", 0))

        if not selected_pets:
            print("未找到出战宠物(position>0)")
            return

        # 收集选中宠物的词条
        for pet in selected_pets:
            pet_id = pet.get("id")
            pet_type = str(pet.get("type", ""))
            pet_name = self.type_data.get(int(pet_type), f"UNKNOWN({pet_type})")
            pet_data = {
                "id": pet_id,
                "name": pet_name,
                "type": pet_type,
                "level": pet.get("level", "未知"),
                "skills": [],
            }

            if pet.get("skillsold") and pet.get("valuesold"):
                skills_hex = pet["skillsold"]
                values_hex = pet["valuesold"]
                skill_ids, values = self.parse_skill_and_value_list(skills_hex, values_hex)
                for i, sid in enumerate(skill_ids):
                    if i < len(values):
                        info = self.skill_data.get(sid, {"name": "未知技能", "topvalue": 0})
                        name = info.get("name", "未知技能")
                        percent = self.hex_to_percent(values[i])
                        top = info.get("topvalue", 0)
                        actual = round(percent * top / 100, 2)
                        pet_data["skills"].append(
                            {"id": sid, "name": name, "value": values[i], "percent": percent, "actual_value": actual}
                        )
            else:
                pet_data["no_skills_data"] = True

            self.deployed_pets_info.append(pet_data)

        # 汇总：展示每只宠物的完整词条
        print(f"\n{'═' * 50}")
        print(f"  出战宠物信息汇总({len(self.deployed_pets_info)}只)")
        print(f"{'═' * 50}")
        for pet in self.deployed_pets_info:
            print(f"\n  ◆ {pet['name']} (ID:{pet['id']}, 等级:{pet['level']})")
            if pet.get("no_skills_data"):
                print("    (无词条数据)")
            else:
                for i, s in enumerate(pet["skills"]):
                    sid = s.get("id", "")
                    suffix = sid[-2:] if len(sid) >= 2 else ""
                    rare = self.SKILL_RARE_MAPPING.get(suffix, "")
                    color = self.SUFFIX_COLOR_MAPPING.get(suffix, "")
                    info = self.skill_data.get(sid, {"topvalue": 0})
                    top = info.get("topvalue", 0)
                    line = f"    {i+1}. [{rare:>3}] {s['name']} {s['actual_value']}/{top}"
                    if color:
                        line = f"    {color}{i+1}. [{rare:>3}] {s['name']} {s['actual_value']}/{top}{self.RESET}"
                    print(line)

        print(f"\n  {'─' * 46}")
        print("  词条总计统计:")
        totals: Dict[str, float] = {}
        for pet in self.deployed_pets_info:
            if pet.get("no_skills_data"):
                continue
            for s in pet["skills"]:
                totals[s["name"]] = totals.get(s["name"], 0.0) + s["actual_value"]
        for name in sorted(totals.keys()):
            if name in target_skill_types:
                target = target_skill_types[name]
                val = totals[name]
                mark = "✓" if val >= target else f"✗ (差距: {target - val:.2f})"
                print(f"  {name}: {val:.2f}/{target} {mark}")
            else:
                print(f"  {name}: {totals[name]:.2f}")
        print(f"{'═' * 50}")

    def run_interactive(self) -> bool:
        account_data = self.ac_manager.accounts.get(self.account_name)
        default_level = 1
        if account_data and "gqxx" in account_data:
            default_level = account_data["gqxx"]
            print(f"从账户信息中获取当前关卡等级：{default_level}")

        session_path = None  # 不再使用单独文件

        # 尝试从账户数据加载上次会话
        reuse = False
        saved_session = (account_data or {}).get('py_session')

        if saved_session:
            s_targets = saved_session.get("target_skill_types", {})
            s_pet_id = saved_session.get("pet_id")
            s_pet_name = saved_session.get("pet_name", "未知")
            print(f"\n  上次培育配置:")
            print(f"  培育宠物: {s_pet_name} (ID:{s_pet_id})")
            print(f"  关注词条:")
            for k, v in s_targets.items():
                print(f"    {k}: {v}")
            # 打印出战宠物位置信息
            pets_info = (account_data or {}).get("pets", [])
            deployed = [p for p in pets_info if p.get("position", 0) > 0]
            if deployed:
                deployed.sort(key=lambda p: p.get("position", 0))
                print(f"  出战宠物:")
                for p in deployed:
                    p_name = self.type_data.get(int(str(p.get("type", ""))), f"UNKNOWN({p.get('type')})")
                    print(f"    位置{p['position']}: {p_name} (ID:{p.get('id')}, 等级:{p.get('level')})")
            confirm = input("  是否复用此配置？([y]/n): ").strip().lower()
            if confirm != "n":
                reuse = True
                target_skill_types = {k: float(v) for k, v in s_targets.items()}
                pet_id = s_pet_id
                pname = s_pet_name

        if not reuse:
            # 选择目标技能类型
            available_skill_types = {
                "1": "技能伤害减免",
                "2": "暴击伤害减免",
                "3": "技能伤害",
                "4": "暴击伤害",
            }

            print("请选择需要命中的目标技能类型（多选请用逗号分隔，例如：1,2,3）：")
            for k, v in available_skill_types.items():
                print(f"{k}. {v}")
            choice = input("请输入选项编号: ")
            selected = [available_skill_types[num.strip()] for num in choice.split(",") if num.strip() in available_skill_types]
            if not selected:
                print("未选择任何技能类型，将使用默认值：技能伤害减免和暴击伤害减免")
                selected = ["技能伤害减免", "暴击伤害减免"]

            target_skill_types: Dict[str, float] = {}
            js_need = self._jstopvalue(default_level)
            for t in selected:
                if t in ["技能伤害减免", "暴击伤害减免"]:
                    target_skill_types[t] = js_need
                    print(f"[{t}] 目标值自动设置为: {js_need}")
                else:
                    while True:
                        try:
                            val = input(f"请为[{t}]设置目标值: ")
                            target_skill_types[t] = float(val)
                            break
                        except ValueError:
                            print("请输入有效的数字")

            # 默认追踪的词条（目标值0，仅用于显示变化）
            default_track = ["技能伤害", "坚韧 忽视暴击率"]
            for dt in default_track:
                if dt not in target_skill_types:
                    target_skill_types[dt] = 0

            print("\n已选择的目标技能类型和目标值:")
            for k, v in target_skill_types.items():
                print(f"{k}: {v}")

        # 初始化并展示当前出战宠物数据
        self._init_deployed_pets(target_skill_types)

        if not reuse:
            input("按回车键继续...")

            # 选择要培育的宠物（仅展示 3305/3306/3307）
            pets_info = (account_data or {}).get("pets", [])
            pet_list: List[Dict] = []
            displayed_indices: List[int] = []
            print("\n请选择要培育的宠物:")
            for i, pet in enumerate(pets_info, 1):
                ptype = str(pet.get("type", ""))
                if ptype.startswith("3305") or ptype.startswith("3306") or ptype.startswith("3307"):
                    name = self.type_data.get(int(ptype), f"UNKNOWN({ptype})")
                    print(f"{i}. {name} (ID:{pet.get('id')}, 等级:{pet.get('level')}, 类型:{ptype})")
                    pet_list.append(pet)
                    displayed_indices.append(i)

            if not pet_list:
                print("未找到3305、3306、3307开头的高级别宠物")
                return False

            selected_pet = None
            while True:
                try:
                    c = input("请输入编号选择一个宠物: ")
                    if not c.strip():
                        selected_pet = pet_list[0]
                        ptype = str(selected_pet.get("type", ""))
                        pname = self.type_data.get(int(ptype), f"UNKNOWN({ptype})")
                        print(f"未输入，默认选择: {pname}")
                        break
                    num = int(c)
                    if num in displayed_indices:
                        idx = displayed_indices.index(num)
                        selected_pet = pet_list[idx]
                        ptype = str(selected_pet.get("type", ""))
                        pname = self.type_data.get(int(ptype), f"UNKNOWN({ptype})")
                        print(f"已选择: {pname}")
                        break
                    else:
                        print("请输入显示列表中的有效编号")
                except ValueError:
                    print("请输入有效的数字")

            pet_id = selected_pet.get("id")
            ptype = str(selected_pet.get("type", ""))
            pname = self.type_data.get(int(ptype), f"UNKNOWN({ptype})")

            # 保存会话配置到账户数据
            self.ac_manager.update_account(self.account_name, 'py_session', {
                "target_skill_types": target_skill_types,
                "pet_id": pet_id,
                "pet_name": pname,
            })
            self.ac_manager.save_accounts()
            print(f"  ✓ 已保存会话配置")
        print(f"\n开始培育{pname}...")

        round_num = 0
        while True:
            round_num += 1
            res = self.dopy(pet_id)
            if not res:
                print("no response")
                return False
            if res and len(res) < 10:
                print("no more stone")
                return True

            should_update, new_details = self.analyze_skill(
                res, current_pet_name=pname,
                target_skill_types=target_skill_types,
                round_num=round_num,
            )
            if should_update:
                user_input = input("是否更新？(y/[n]): ")
                if user_input.lower() == "y":
                    self.doupdate(pet_id)
                    self._update_deployed_pet_skills(pname, new_details)
                    input("按回车键继续或cmd+c退出")
            # time.sleep(1)

    # 预留非交互接口（一次培育并返回结果）
    def peiyu_once(self, pet_id: int) -> bytes | None:
        return self.dopy(pet_id)

