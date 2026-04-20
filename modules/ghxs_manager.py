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
        102006: "金-20次秘宝箱",
        101013: "紫-秘宝箱",
    }

    def format_task_type(self, type_id):
        """将type_id转为可读名称"""
        return self.TASK_TYPE_MAP.get(type_id)

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
