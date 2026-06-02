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
    }
    TASK_RARITY_MAP = {
        0: "n",  # 普通
        1: "r",  # 蓝色
        2: "s",  # 金色
    }

    def format_task_type(self, type_id):
        """将type_id转为可读名称"""
        name = self.TASK_TYPE_MAP.get(type_id)
        if name:
            return name
        rarity = self.task_rarity(type_id)
        if rarity:
            return f"{rarity}-未知({type_id})"
        return None

    @classmethod
    def task_rarity(cls, type_id):
        """返回新悬赏ID的稀有度: n=普通, r=蓝色, s=金色。旧ID不再参与判定。"""
        name = cls.TASK_TYPE_MAP.get(type_id)
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

    def __init__(self, account_name, delay=0, showres=0):
        self.account_name = account_name
        self.ac_manager = ACManager(account_name, delay=delay, showres=showres)
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
        return len(response)>20

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

    # ── S钥匙任务全流程 ──────────────────────────────────────

    # 进度奖励积分阶梯
    SCORE_THRESHOLDS = [50, 100, 150, 250, 450, 1000, 1500, 2000, 3200]

    # 钥匙任务类型 → 所需钥匙数量
    KEY_TASK_TYPES = {
        201004: ("n-10次装备", 10),
        201207: ("s-30次装备", 30),
    }

    # S钥匙在 baginfo 中的 type
    S_KEY_TYPE = 62
    # 钥匙自选箱在 baginfo 中的 type
    KEY_BOX_TYPE = 5028

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
        """遍历领取所有进度奖励。先查询当前积分，积分不够的阶梯直接跳过。"""
        # 先查询当前积分
        resp = self.query()
        current_score = resp.field9 if resp and resp.field9 else 0
        print(f"<{mask_account(self.account_name)}> 当前悬赏积分: {current_score}")

        claimed_count = 0
        for i in range(1, len(self.SCORE_THRESHOLDS) + 1):
            threshold = self.SCORE_THRESHOLDS[i - 1]
            if current_score < threshold:
                print(f"<{mask_account(self.account_name)}> - 进度奖励 {i}({threshold}分) 积分不足，跳过后续")
                break
            success = self.claim_score_reward(i)
            if success:
                claimed_count += 1
                print(f"<{mask_account(self.account_name)}> ✓ 领取进度奖励 {i}({threshold}分)")
            else:
                print(f"<{mask_account(self.account_name)}> - 进度奖励 {i}({threshold}分) 已领")
        print(f"<{mask_account(self.account_name)}> 共领取 {claimed_count} 个进度奖励")
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
        task_info = self.KEY_TASK_TYPES.get(task_type_id)
        if not task_info:
            print(f"<{mask_account(self.account_name)}> 未知的钥匙任务类型: {task_type_id}")
            return False
        task_name, required_keys = task_info
        print(f"\n<{mask_account(self.account_name)}> ═══ 开始S钥匙任务: {task_name} (需要{required_keys}把钥匙) ═══")

        # 1. 检查背包
        s_key_count, _ = self._get_bag_item_count(self.S_KEY_TYPE)
        box_count, box_id = self._get_bag_item_count(self.KEY_BOX_TYPE)
        total_available = s_key_count + box_count
        print(f"<{mask_account(self.account_name)}> S钥匙: {s_key_count}, 钥匙自选箱: {box_count}, 总计可用: {total_available}")

        if total_available < required_keys:
            print(f"<{mask_account(self.account_name)}> ✗ 钥匙+箱子不够 ({total_available} < {required_keys})，跳过")
            return False

        # 2. 接任务
        if not task_uuid:
            # 查询获取任务 UUID
            resp = self.query()
            if not resp or not resp.task_entries:
                print(f"<{mask_account(self.account_name)}> ✗ 查询悬赏失败或无任务")
                return False
            # 找对应 type 的任务
            for task in resp.task_entries:
                if task.task_type_id == task_type_id:
                    task_uuid = task.task_uuid
                    break
            if not task_uuid:
                print(f"<{mask_account(self.account_name)}> ✗ 未找到类型 {task_type_id} 的任务")
                return False

        print(f"<{mask_account(self.account_name)}> 接受任务: uuid={task_uuid[:16]}...")
        if not self.accept(task_uuid, task_type_id):
            print(f"<{mask_account(self.account_name)}> ✗ 接受任务失败")
            return False
        print(f"<{mask_account(self.account_name)}> ✓ 接受任务成功")

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

