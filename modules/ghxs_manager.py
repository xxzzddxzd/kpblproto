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
