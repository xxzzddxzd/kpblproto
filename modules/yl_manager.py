"""
游历管理模块
处理游戏中的游历功能
"""

import logging
import binascii
from . import kpbl_pb2
from .kpbltools import ACManager, mask_account


class YLManager:
    """游历管理器"""
    
    def __init__(self, account_name, showres=0,delay=1):
        self.account_name = account_name
        self.ac_manager = ACManager(account_name, showres=showres, delay=delay)
        self.logger = logging.getLogger(f"YLManager_{account_name}")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.StreamHandler())
        self.showres = showres
        
        # 物品类型映射（使用共享映射表）
        from .item_names import ITEM_NAMES
        self.items_type = ITEM_NAMES
    
    def ylhd(self, sub_step):
        """游历活动处理"""
        ylifid = self.ac_manager.get_account(self.account_name, 'ylifid')
        req_config_hd1 = {
            "ads": "活动1a-幸运星",
            "times": 1,
            "hexstringheader": "192b",
            "request_body_i2": sub_step,
            "request_body_i3": ylifid
        }
        rev = self.ac_manager.do_common_request(self.account_name, req_config_hd1, showres=self.showres)
        
        xyx_resp = kpbl_pb2.xyx_response()
        xyx_resp.ParseFromString(rev[6:])
        print(f"<{mask_account(self.account_name)}> 活动1a-幸运星: {xyx_resp.point_left}")

    def ylhd2(self, sub_step):
        """游历活动处理"""
        # seasonid = self.ac_manager.get_account(self.account_name, 'seasonid')
        ylifid = self.ac_manager.get_account(self.account_name, 'ylifid')
        req_config_hd1 = {
            "ads": "活动2",
            "times": 1,
            "hexstringheader": "012b",
            "request_body_i2": sub_step,
            "request_body_i3": ylifid
        }
        print(req_config_hd1)
        rev = self.ac_manager.do_common_request(self.account_name, req_config_hd1, showres=self.showres)
        print(len(rev))
    
    def youli(self, bio, level, xyx):
        """
        执行游历功能
        
        Args:
            bio: 倍数，默认1
            level: 游历等级，如果为None则从账户信息中获取
        """
        # 如果没有指定level，从账户信息中获取
        if level is None:
            level = self.ac_manager.get_account(self.account_name, 'gqxx')
        
        print(f"<{mask_account(self.account_name)}> 游历开始，level={level}")
        
        step = 60
        
        # 开始游历
        req_config_ksyl = {
            "ads": "开始游历",
            "times": 1,
            "hexstringheader": "032b",
            "request_body_i3": bio,
            "savetofile": "response_yl"
        }
        response = self.ac_manager.do_common_request(self.account_name, req_config_ksyl, showres=self.showres)
        
        # 解析response，提取field 7中的步骤
        response_data = response[6:]  # 跳过前6个字节
        youli_resp = kpbl_pb2.youli_response()
        youli_resp.ParseFromString(response_data)
        
        # 提取所有活动步骤
        print(f"<{mask_account(self.account_name)}> 开始解析游历响应...")
        
        # 创建一个列表来存储所有步骤信息
        steps = []
        
        global_typeid=0
        # 检查并提取字段7中的huodonglist1
        if hasattr(youli_resp, 'huodonglist1') and youli_resp.huodonglist1:
            for step_info in youli_resp.huodonglist1:
                if hasattr(step_info, 'stepid') and hasattr(step_info, 'content'):
                    step_id = step_info.stepid
                    
                    hid1 = 0
                    if hasattr(step_info.content, 'metadata'):
                        hid1 = step_info.content.metadata
                        hex_data = binascii.hexlify(hid1).decode('utf-8')
                        print(f"<{mask_account(self.account_name)}> 游历步骤 {step_id} 的hid1: {hex_data}, typeid:{step_info.content.type_id}")
                        global_typeid = step_info.content.type_id
                    
                    steps.append((step_id, hid1,step_info.content.type_id))
        
        # 打印提取的步骤信息
        print(f"<{mask_account(self.account_name)}> 从游历响应中提取了{len(steps)}个步骤")
        for i, (step_id, hid1,type_id) in enumerate(steps):
            print(f"<{mask_account(self.account_name)}> 步骤 {i+1}: step_id={step_id}, hid1={hid1},type_id={type_id}")
        
        # 使用提取的步骤调用ylhd函数
        if steps:
            for step_id, hid1,type_id in steps:
                if xyx:
                    self.ylhd(step_id)
                else:
                    self.ylhd2(step_id)
            # for step_id, hid1 in steps:
            #     self.ylhd(step_id)
        
        # 结束游历
        req_config_jsyl1 = {
            "ads": "结束游历1",
            "times": 1,
            "hexstringheader": "052b",
            "request_body_i2": level,
            "request_body_i3": step
        }
        req_config_jsyl2 = {
            "ads": "结束游历2",
            "times": 1,
            "hexstringheader": "0f2b"
        }
        
        result_response = self.ac_manager.do_common_request(self.account_name, req_config_jsyl1, showres=self.showres)
        
        # 解析游历结果响应
        if result_response and len(result_response) > 6:
            result_data = result_response[6:]  # 跳过前6个字节
            youli_result = kpbl_pb2.youli_result_response()
            youli_result.ParseFromString(result_data)
            
            # 提取和打印items信息
            if hasattr(youli_result, 'mainresponse') and youli_result.mainresponse:
                if hasattr(youli_result.mainresponse, 'items') and youli_result.mainresponse.items:
                    print(f"<{mask_account(self.account_name)}> 游历奖励物品信息:")
                    books_found = False
                    
                    for i, item in enumerate(youli_result.mainresponse.items):
                        if hasattr(item, 'typeid') and hasattr(item, 'count'):
                            item_type = item.typeid
                            item_count = item.count
                            item_name = self.items_type.get(item_type, f"未知物品({item_type})")
                            
                            # 书类型（41-45）标记为红色
                            if 41 <= item_type <= 45 or item_type == 5018:
                                print(f"<{mask_account(self.account_name)}> 物品 {i+1}: \033[31m{item_name}\033[0m, 数量={item_count}")
                                books_found = True
                            else:
                                print(f"<{mask_account(self.account_name)}> 物品 {i+1}: {item_name}, 数量={item_count}")
                    
                    if books_found:
                        self.logger.info(f"发现书籍奖励！")
        
        self.ac_manager.do_common_request(self.account_name, req_config_jsyl2, showres=self.showres)
        print(f"<{mask_account(self.account_name)}> 游历完成")
    
    def do_youli_with_params(self, bio=1, level=None,times=1,xyx=1):
        """
        带参数的游历执行方法，与main.py接口兼容
        
        Args:
            bio: 倍数，默认1
            level: 游历等级，如果为None则从账户信息中获取
        """
        while times > 0:
            print(f"<{mask_account(self.account_name)}> 开始游历，次数剩余: {times}")
            self.youli(bio, level,xyx)
            times -= 1
        return True


    def xyx(self, bio=20):
        req_config_xyx = {
            "ads": "幸运星",
            "times": 1,
            "hexstringheader": "1b2b",
            "request_body_i2": bio
        }
        rev = self.ac_manager.do_common_request(self.account_name, req_config_xyx, showres=self.showres)
        xyx_resp = kpbl_pb2.xyx_response()
        xyx_resp.ParseFromString(rev[6:])
        print(f"<{mask_account(self.account_name)}> 幸运星: {xyx_resp.point}")

    def checkpoint(self):
        req_config_xyx = {"ads": "幸运星", "times": 1, "hexstringheader": "1b2b", "request_body_i2": 1}
        rev = self.ac_manager.do_common_request(self.account_name, req_config_xyx, showres=self.showres)
        xyx_resp = kpbl_pb2.xyx_response()
        xyx_resp.ParseFromString(rev[6:])
        print(f"<{mask_account(self.account_name)}> 幸运星: {xyx_resp.point_left}")
        return xyx_resp.point_left

    def xyx_all(self):
        # 1:20
        point_left = self.checkpoint()
        while point_left >= 400:
            req_config_xyx = {"ads": "幸运星", "times": 5, "hexstringheader": "1b2b", "request_body_i2": 20}
            self.ac_manager.do_common_request_list(self.account_name, [req_config_xyx], showres=self.showres)
            point_left = self.checkpoint()
        while point_left >= 200:
            req_config_xyx = {"ads": "幸运星", "times": 5, "hexstringheader": "1b2b", "request_body_i2": 10}
            self.ac_manager.do_common_request_list(self.account_name, [req_config_xyx], showres=self.showres)
            point_left = self.checkpoint()
        while point_left >= 100:
            req_config_xyx = {"ads": "幸运星", "times": 5, "hexstringheader": "1b2b", "request_body_i2": 5}
            self.ac_manager.do_common_request_list(self.account_name, [req_config_xyx], showres=self.showres)
            point_left = self.checkpoint()
        while point_left >= 60:
            req_config_xyx = {"ads": "幸运星", "times": 5, "hexstringheader": "1b2b", "request_body_i2": 3}
            self.ac_manager.do_common_request_list(self.account_name, [req_config_xyx], showres=self.showres)
            point_left = self.checkpoint()

        