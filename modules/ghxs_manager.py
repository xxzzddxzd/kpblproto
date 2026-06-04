"""
公会悬赏管理模块
处理公会悬赏相关功能
"""

import logging
from . import kpbl_pb2
from .kpbltools import ACManager, mask_account

class GHXSManager:
    """公会悬赏管理器"""

    TASK_TYPE_MAP = {
        201001: "n-3次pvp",
        201002: "n-5次任意副本",
        201003: "n-1ur船",
        201004: "n-50次挖矿",
        201005: "n-100体力",
        
        201102: "r-10次任意副本",
        201103: "r-2ur船",
        201104: "r-100次挖矿",  # ，2次咕噜
        201105: "r-100体力",  # 
        201106: "r-2次咕噜",  # 100次挖矿，2次咕噜
        201107: "r-10次装备",
        201108: "r-2个魔方",
        201207: "s-30次装备",
        201208: "s-6个魔方",
        
        203107: "r-500次宠物蛋",
        203207: "s-1500次宠物蛋",
        204107: "r-开宝箱650分",
        204207: "s-开宝箱2000分",
    }
    TASK_RARITY_MAP = {
        0: "n",  # 普通
        1: "r",  # 蓝色
        2: "s",  # 金色
    }
    COMMON_TASK_CANONICAL_DAY = 1

    def format_task_type(self, type_id):
        """将type_id转为可读名称"""
        name = self.TASK_TYPE_MAP.get(type_id)
        if not name:
            name = self.TASK_TYPE_MAP.get(self.task_group_id(type_id))
        if name:
            return name
        rarity = self.task_rarity(type_id)
        if rarity:
            return f"{rarity}-未知({type_id})"
        return None

    @classmethod
    def task_day(cls, type_id):
        if 200000 <= type_id < 300000:
            return (type_id // 1000) % 10
        return None

    @classmethod
    def task_code(cls, type_id):
        if 200000 <= type_id < 300000:
            return type_id % 100
        return None

    @classmethod
    def task_group_id(cls, type_id):
        """00~06 是跨星期共用任务，统一归到 day=1；07/08 保留每日独立ID。"""
        code = cls.task_code(type_id)
        day = cls.task_day(type_id)
        if code is None or day is None:
            return type_id
        if 0 <= code <= 6:
            return type_id + (cls.COMMON_TASK_CANONICAL_DAY - day) * 1000
        return type_id

    @classmethod
    def is_known_task_type(cls, type_id):
        return type_id in cls.TASK_TYPE_MAP or cls.task_group_id(type_id) in cls.TASK_TYPE_MAP

    @classmethod
    def task_rarity(cls, type_id):
        """返回新悬赏ID的稀有度: n=普通, r=蓝色, s=金色。旧ID不再参与判定。"""
        name = cls.TASK_TYPE_MAP.get(type_id) or cls.TASK_TYPE_MAP.get(cls.task_group_id(type_id))
        if name:
            prefix = name.split("-", 1)[0].lower()
            if prefix in ("n", "r", "s"):
                return prefix
        if 200000 <= type_id < 300000:
            return cls.TASK_RARITY_MAP.get((type_id // 100) % 10)
        return None

    @classmethod
    def is_gold_task(cls, type_id):
        """新规则下只有s级任务按金色保留。"""
        return cls.task_rarity(type_id) == "s"

    def __init__(self, account_name, delay=0, showres=0, ac_manager=None):
        self.account_name = account_name
        self.ac_manager = ac_manager or ACManager(account_name, delay=delay, showres=showres)
        self.logger = logging.getLogger(f"GHXSManager_{account_name}")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.StreamHandler())
        self.showres = showres
        self.delay = delay

    def query(self):
        """查询公会悬赏状态"""
        config = {"ads": "查询公会悬赏", "times": 1, "hexstringheader": "1f78"}
        response = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        if response and len(response) > 6:
            resp = kpbl_pb2.ghxs_query_response()
            resp.ParseFromString(response[6:])
            return resp
        return None

    def accept(self, task_uuid, task_type_id):
        """接受公会悬赏任务"""
        config = {
            "ads": "接受公会悬赏",
            "times": 1,
            "hexstringheader": "2178",
            "requestbodytype": "request_qh",
            "request_body_i2": task_uuid,
            "request_body_i3": task_type_id,
        }
        response = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        # if response and len(response) > 6:
        #     resp = kpbl_pb2.ghxs_query_response()
        #     resp.ParseFromString(response[6:])
        #     return resp
        # return None
        return bool(response and len(response) > 20)

    def buy_times(self):
        """购买公会悬赏次数"""
        config = {"ads": "购买悬赏次数", "times": 1, "hexstringheader": "d12b", "request_body_i2": 191, "request_body_i3": 1}
        return self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)

    def abort(self):
        """放弃当前公会悬赏任务"""
        config = {"ads": "放弃公会悬赏", "times": 1, "hexstringheader": "2378"}
        response = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        # if response and len(response) > 6:
        #     resp = kpbl_pb2.ghxs_query_response()
        #     resp.ParseFromString(response[6:])
        #     return resp
        # return None

    def complete(self):
        """完成/交公会悬赏任务 (2578)"""
        config = {"ads": "完成公会悬赏", "times": 1, "hexstringheader": "2578"}
        response = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        return response and len(response) > 20

    def claim_score_reward(self, reward_id):
        """领取公会悬赏进度奖励 (2978), reward_id=1~9 对应9个积分阶梯"""
        config = {"ads": f"悬赏进度奖励{reward_id}", "times": 1, "hexstringheader": "2978", "request_body_i2": reward_id}
        response = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        return response and len(response) > 20

    # ── 悬赏任务全流程 ──────────────────────────────────────

    # 进度奖励积分阶梯
    SCORE_THRESHOLDS = [50, 100, 150, 250, 450, 1000, 1500, 2000, 3200]

    # task_type_id -> flow配置。新增可执行任务时只需要补这里和对应执行器。
    TASK_FLOW_CONFIGS = {
        201207: {
            "kind": "s_key",
            "label": "S钥匙装备gacha",
            "required_keys": 30,
        },
        203107: {
            "kind": "pet_egg",
            "label": "宠物蛋10连",
            "draw_count": 500,
            "draws_per_request": 10,
        },
        203207: {
            "kind": "pet_egg",
            "label": "宠物蛋10连",
            "draw_count": 1500,
            "draws_per_request": 10,
        },
        204107: {
            "kind": "open_box",
            "label": "开宝箱",
            "target_score": 650,
        },
        204207: {
            "kind": "open_box",
            "label": "开宝箱",
            "target_score": 2000,
        },
    }

    # 兼容旧代码：需要走钥匙全流程的悬赏任务类型 → 所需钥匙数量。
    KEY_TASK_TYPES = {201207: TASK_FLOW_CONFIGS[201207]["required_keys"]}

    # S钥匙在 baginfo 中的 type
    S_KEY_TYPE = 62
    # 钥匙自选箱在 baginfo 中的 type
    KEY_BOX_TYPE = 5028
    PET_EGG_COUNT_PER_MULTIPLIER = 35
    PET_EGG_MULTIPLIERS = (10, 5, 3, 1)
    CHEST_SCORE_BY_TYPE = {
        74: 50,  # 宠物宝箱
        73: 20,  # 金宝箱
        72: 10,  # 银宝箱
        71: 1,   # 铜宝箱
    }

    @classmethod
    def task_flow_config(cls, task_type_id):
        return cls.TASK_FLOW_CONFIGS.get(task_type_id) or cls.TASK_FLOW_CONFIGS.get(cls.task_group_id(task_type_id))

    @classmethod
    def task_flow_label(cls, task_type_id):
        config = cls.task_flow_config(task_type_id)
        return config.get("label") if config else None

    def _resolve_task_uuid(self, task_uuid, task_type_id):
        """没有传 uuid 时，从当前悬赏池里找同类型任务。"""
        if task_uuid:
            return task_uuid
        resp = self.query()
        if not resp or not resp.task_entries:
            print(f"<{mask_account(self.account_name)}> ✗ 查询悬赏失败或无任务")
            return None
        target_group_id = self.task_group_id(task_type_id)
        for task in resp.task_entries:
            if task.task_type_id == task_type_id or self.task_group_id(task.task_type_id) == target_group_id:
                return task.task_uuid
        print(f"<{mask_account(self.account_name)}> ✗ 未找到类型 {task_type_id} 的任务")
        return None

    def _accept_resolved_task(self, task_uuid, task_type_id):
        print(f"<{mask_account(self.account_name)}> 接受任务: uuid={task_uuid[:16]}...")
        if not self.accept(task_uuid, task_type_id):
            print(f"<{mask_account(self.account_name)}> ✗ 接受任务失败")
            return False
        print(f"<{mask_account(self.account_name)}> ✓ 接受任务成功")
        return True

    @classmethod
    def pet_egg_gacha_plan(cls, draw_count, max_multiplier=10):
        """按宠物蛋任务次数生成抽蛋档位计划，返回(所需倍率总数, 实际计数, [(倍率, 请求次数)])。"""
        draw_count = int(draw_count)
        max_multiplier = int(max_multiplier)
        if draw_count <= 0 or max_multiplier <= 0:
            raise ValueError("draw_count/max_multiplier must be positive")

        required_multiplier = (draw_count + cls.PET_EGG_COUNT_PER_MULTIPLIER - 1) // cls.PET_EGG_COUNT_PER_MULTIPLIER
        allowed = [m for m in cls.PET_EGG_MULTIPLIERS if m <= max_multiplier]
        if not allowed or allowed[-1] != 1:
            raise ValueError(f"unsupported pet egg max_multiplier: {max_multiplier}")

        plan = []
        remaining = required_multiplier
        for multiplier in allowed:
            times, remaining = divmod(remaining, multiplier)
            if times:
                plan.append((multiplier, times))
        actual_count = required_multiplier * cls.PET_EGG_COUNT_PER_MULTIPLIER
        return required_multiplier, actual_count, plan

    def _get_bag_item_count(self, item_type):
        """从 baginfo 获取指定 type 的物品数量和 id"""
        baginfo = self.ac_manager.get_account(self.account_name, 'baginfo') or {}
        item_type_key = item_type
        if item_type_key in baginfo:
            return int(baginfo[item_type_key].get('count', 0)), baginfo[item_type_key].get('id')
        # baginfo 的 key 可能是 str
        item_type_str = str(item_type)
        if item_type_str in baginfo:
            return int(baginfo[item_type_str].get('count', 0)), baginfo[item_type_str].get('id')
        return 0, None

    def open_key_box(self, count):
        """开钥匙自选箱 (db27), count=数量。复刻抓包参数: i2=物品id, i3=count"""
        _, box_id = self._get_bag_item_count(self.KEY_BOX_TYPE)
        if not box_id:
            print(f"<{mask_account(self.account_name)}> 未找到钥匙自选箱(type={self.KEY_BOX_TYPE})")
            return False
        config = {
            "ads": f"开钥匙自选箱x{count}",
            "times": 1,
            "hexstringheader": "db27",
            "request_body_i2": box_id,
            "request_body_i3": count,
        }
        response = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        if response and len(response) > 20:
            # 开箱后重新登录以刷新 baginfo
            self.ac_manager.login(self.account_name)
            return True
        return False

    def chest_score_inventory(self):
        """返回当前有积分宝箱库存: box_type -> (count, item_id, score)。"""
        inventory = {}
        for box_type, score in self.CHEST_SCORE_BY_TYPE.items():
            count, item_id = self._get_bag_item_count(box_type)
            inventory[box_type] = (count, item_id, score)
        return inventory

    def chest_open_plan(self, target_score):
        """按高分箱优先生成开箱计划，返回 [(box_type, count, score)]。"""
        target_score = int(target_score)
        inventory = self.chest_score_inventory()
        total_score = sum(count * score for count, _, score in inventory.values())
        if total_score < target_score:
            return None, total_score

        remaining = target_score
        plan = []
        left_counts = {box_type: count for box_type, (count, _, _) in inventory.items()}

        for box_type, score in sorted(self.CHEST_SCORE_BY_TYPE.items(), key=lambda item: item[1], reverse=True):
            count = left_counts.get(box_type, 0)
            if count <= 0:
                continue
            use_count = min(count, remaining // score)
            if use_count:
                plan.append((box_type, use_count, score))
                left_counts[box_type] -= use_count
                remaining -= use_count * score
            if remaining == 0:
                return plan, total_score

        if remaining > 0:
            # 无法精确凑齐时，用最小可用箱补一次，允许超过目标分。
            for box_type, score in sorted(self.CHEST_SCORE_BY_TYPE.items(), key=lambda item: item[1]):
                if left_counts.get(box_type, 0) > 0:
                    plan.append((box_type, 1, score))
                    remaining = 0
                    break

        if remaining > 0:
            return None, total_score
        return plan, total_score

    def open_score_chests(self, target_score):
        """打开 71/72/73/74 四种积分宝箱，直到达到目标积分。"""
        plan, total_score = self.chest_open_plan(target_score)
        if not plan:
            print(f"<{mask_account(self.account_name)}> ✗ 积分宝箱不足: 可用{total_score}分 < 目标{target_score}分")
            return False

        plan_score = sum(count * score for _, count, score in plan)
        plan_text = ", ".join(f"type={box_type} x{count} ({score}分/个)" for box_type, count, score in plan)
        print(f"<{mask_account(self.account_name)}> 开宝箱计划: {plan_text}, 合计{plan_score}分")

        inventory = self.chest_score_inventory()
        for box_type, count, _ in plan:
            _, item_id, _ = inventory.get(box_type, (0, None, 0))
            if not item_id:
                print(f"<{mask_account(self.account_name)}> ✗ 未找到宝箱 type={box_type}")
                return False
            config = {
                "ads": f"开积分宝箱{box_type}x{count}",
                "times": 1,
                "hexstringheader": "074f",
                "request_body_i2": item_id,
                "request_body_i3": count,
            }
            response = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
            if not response:
                print(f"<{mask_account(self.account_name)}> ✗ 开宝箱失败 type={box_type} x{count}")
                return False

        self.ac_manager.login(self.account_name)
        return True

    def use_s_keys(self):
        """使用S钥匙抽装备 (c72b i2=201004, i3=2, i4=2), 复刻抓包发3次共30个"""
        config = {
            "ads": "S钥匙装备gacha",
            "times": 3,
            "hexstringheader": "c72b",
            "request_body_i2": 201004,
            "request_body_i3": 2,
            "request_body_i4": 2,
        }
        response = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        return response and len(response) > 20

    def claim_all_score_rewards(self):
        """遍历领取所有进度奖励（无API查已领状态，逐个尝试，已领的会自动跳过）"""
        claimed_count = 0
        for i in range(1, len(self.SCORE_THRESHOLDS) + 1):
            threshold = self.SCORE_THRESHOLDS[i - 1]
            success = self.claim_score_reward(i)
            if success:
                claimed_count += 1
                print(f"<{mask_account(self.account_name)}> ✓ 领取进度奖励 {i}({threshold}分)")
        if claimed_count:
            print(f"<{mask_account(self.account_name)}> 共领取 {claimed_count} 个进度奖励")
        else:
            print(f"<{mask_account(self.account_name)}> 无新的进度奖励可领")
        return claimed_count

    def run_s_key_task(self, task_uuid=None, task_type_id=201207):
        """
        S钥匙悬赏全流程：
        1. 检查背包S钥匙+自选箱够不够
        2. 接任务
        3. 开箱补齐S钥匙
        4. 使用S钥匙抽装备
        5. 交任务
        6. 领进度奖励
        """
        required_keys = self.KEY_TASK_TYPES.get(task_type_id)
        if not required_keys:
            print(f"<{mask_account(self.account_name)}> 未知的钥匙任务类型: {task_type_id}")
            return False
        task_name = self.format_task_type(task_type_id) or str(task_type_id)
        print(f"\n<{mask_account(self.account_name)}> ═══ 开始钥匙任务: {task_name} (需要{required_keys}把钥匙) ═══")

        # 1. 检查背包
        s_key_count, _ = self._get_bag_item_count(self.S_KEY_TYPE)
        box_count, box_id = self._get_bag_item_count(self.KEY_BOX_TYPE)
        total_available = s_key_count + box_count
        print(f"<{mask_account(self.account_name)}> S钥匙: {s_key_count}, 钥匙自选箱: {box_count}, 总计可用: {total_available}")

        if total_available < required_keys:
            print(f"<{mask_account(self.account_name)}> ✗ 钥匙+箱子不够 ({total_available} < {required_keys})，跳过")
            return False

        # 2. 接任务
        task_uuid = self._resolve_task_uuid(task_uuid, task_type_id)
        if not task_uuid:
            return False
        if not self._accept_resolved_task(task_uuid, task_type_id):
            return False

        # 3. 如果S钥匙不够，开箱补齐
        need_from_box = required_keys - s_key_count
        if need_from_box > 0:
            print(f"<{mask_account(self.account_name)}> 需要从箱子补 {need_from_box} 把S钥匙，开箱...")
            if not self.open_key_box(need_from_box):
                print(f"<{mask_account(self.account_name)}> ✗ 开箱失败")
                return False
            print(f"<{mask_account(self.account_name)}> ✓ 开箱成功")

        # 4. 使用S钥匙抽装备
        print(f"<{mask_account(self.account_name)}> 使用{required_keys}把S钥匙抽装备...")
        if not self.use_s_keys():
            print(f"<{mask_account(self.account_name)}> ✗ 钥匙gacha失败")
            return False
        print(f"<{mask_account(self.account_name)}> ✓ 装备gacha完成")

        # 5. 交任务
        print(f"<{mask_account(self.account_name)}> 交任务...")
        if not self.complete():
            print(f"<{mask_account(self.account_name)}> ✗ 交任务失败")
            return False
        print(f"<{mask_account(self.account_name)}> ✓ 任务完成")

        # 6. 领进度奖励
        print(f"<{mask_account(self.account_name)}> 领取进度奖励...")
        self.claim_all_score_rewards()

        print(f"<{mask_account(self.account_name)}> ═══ S钥匙任务全流程完成 ═══\n")
        return True

    def run_pet_egg_task(self, task_uuid=None, task_type_id=203107):
        """
        宠物蛋悬赏全流程：
        1. 接任务
        2. 抽宠物蛋到满足任务次数（f14e i2=13, i3=1/3/5/10）
        3. 交任务
        4. 领进度奖励
        """
        config = self.task_flow_config(task_type_id) or {}
        draw_count = int(config.get("draw_count", 500))
        max_multiplier = int(config.get("draws_per_request", 10))
        try:
            required_multiplier, actual_count, plan = self.pet_egg_gacha_plan(draw_count, max_multiplier)
        except ValueError:
            print(f"<{mask_account(self.account_name)}> ✗ 宠物蛋任务配置不合法: {config}")
            return False
        task_name = self.format_task_type(task_type_id) or str(task_type_id)
        plan_text = " + ".join(f"x{multiplier}*{times}" for multiplier, times in plan)
        print(
            f"\n<{mask_account(self.account_name)}> ═══ 开始宠物蛋任务: {task_name} "
            f"(目标{draw_count}次, 倍率{required_multiplier}, 实际{actual_count}次: {plan_text}) ═══"
        )

        task_uuid = self._resolve_task_uuid(task_uuid, task_type_id)
        if not task_uuid:
            return False
        if not self._accept_resolved_task(task_uuid, task_type_id):
            return False

        print(f"<{mask_account(self.account_name)}> 抽宠物蛋: {plan_text}...")
        from .da_manager import DAManager
        da = DAManager(
            self.account_name,
            showres=self.showres,
            delay=self.delay,
            ac_manager=self.ac_manager,
        )
        for multiplier, times in plan:
            if not da.petegggacha(times, multiplier=multiplier):
                print(f"<{mask_account(self.account_name)}> ✗ 宠物蛋gacha失败: x{multiplier}*{times}")
                return False
        print(f"<{mask_account(self.account_name)}> ✓ 宠物蛋gacha完成")

        print(f"<{mask_account(self.account_name)}> 交任务...")
        if not self.complete():
            print(f"<{mask_account(self.account_name)}> ✗ 交任务失败")
            return False
        print(f"<{mask_account(self.account_name)}> ✓ 任务完成")

        print(f"<{mask_account(self.account_name)}> 领取进度奖励...")
        self.claim_all_score_rewards()

        print(f"<{mask_account(self.account_name)}> ═══ 宠物蛋任务全流程完成 ═══\n")
        return True

    def run_open_box_task(self, task_uuid=None, task_type_id=204107):
        """
        开宝箱悬赏全流程：
        1. 接任务
        2. 打开积分宝箱到目标分数（71=1, 72=10, 73=20, 74=50）
        3. 交任务
        4. 领进度奖励
        """
        config = self.task_flow_config(task_type_id) or {}
        target_score = int(config.get("target_score", 650))
        task_name = self.format_task_type(task_type_id) or str(task_type_id)
        print(f"\n<{mask_account(self.account_name)}> ═══ 开始开宝箱任务: {task_name} (目标{target_score}分) ═══")

        task_uuid = self._resolve_task_uuid(task_uuid, task_type_id)
        if not task_uuid:
            return False
        if not self._accept_resolved_task(task_uuid, task_type_id):
            return False

        if not self.open_score_chests(target_score):
            return False
        print(f"<{mask_account(self.account_name)}> ✓ 开宝箱完成")

        print(f"<{mask_account(self.account_name)}> 交任务...")
        if not self.complete():
            print(f"<{mask_account(self.account_name)}> ✗ 交任务失败")
            return False
        print(f"<{mask_account(self.account_name)}> ✓ 任务完成")

        print(f"<{mask_account(self.account_name)}> 领取进度奖励...")
        self.claim_all_score_rewards()

        print(f"<{mask_account(self.account_name)}> ═══ 开宝箱任务全流程完成 ═══\n")
        return True

    def run_task_flow(self, task_uuid=None, task_type_id=None):
        """按 TASK_FLOW_CONFIGS 执行对应悬赏全流程。"""
        config = self.task_flow_config(task_type_id)
        if not config:
            print(f"<{mask_account(self.account_name)}> 未配置任务全流程: {task_type_id}")
            return False
        kind = config.get("kind")
        if kind == "s_key":
            return self.run_s_key_task(task_uuid=task_uuid, task_type_id=task_type_id)
        if kind == "pet_egg":
            return self.run_pet_egg_task(task_uuid=task_uuid, task_type_id=task_type_id)
        if kind == "open_box":
            return self.run_open_box_task(task_uuid=task_uuid, task_type_id=task_type_id)
        print(f"<{mask_account(self.account_name)}> 未支持的任务流程类型: {kind}")
        return False
