"""
暖春管理模块
处理暖春活动相关功能
"""


import logging
from .kpbltools import ACManager, mask_account
import modules.kpbl_pb2 as kpbl_pb2


class NuanChunManager:
    """暖春管理器"""
    
    def __init__(self, account_name, delay=0, showres=0):
        self.account_name = account_name
        self.ac_manager = ACManager(account_name, delay=delay, showres=showres)
        self.logger = logging.getLogger(f"NuanChunManager_{account_name}")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.StreamHandler())
        self.showres = showres
        self.delay = delay

    def dogacha(self):
        # 从baginfo获取itemid 1211的数量
        self.ac_manager.login(self.account_name, showloginres=0)
        baginfo = self.ac_manager.get_account(self.account_name, 'baginfo') or {}
        item_count_1211 = baginfo.get(1211, 0)
        item_count_1261 = baginfo.get(1261, 0)
        print(f"抽卡券: {item_count_1211},财神帽: {item_count_1261}")
        # return 0

        while item_count_1211 >9:
            req = {"ads":"req_11", "times":1, "hexstringheader":"c12c", "request_body_i2": 10, "request_body_i3": 202602161}
            self.ac_manager.do_common_request(self.account_name, req, showres=self.showres)
            item_count_1211-=10
        
        while item_count_1211 > 0:
            req = {"ads":"req_11", "times":1, "hexstringheader":"c12c", "request_body_i2": 1, "request_body_i3": 202602161}
            self.ac_manager.do_common_request(self.account_name, req, showres=self.showres)
            item_count_1211-=1
        
        self.ac_manager.login(self.account_name, showloginres=0)
        baginfo = self.ac_manager.get_account(self.account_name, 'baginfo') or {}
        item_count_1211 = baginfo.get(1211, 0)
        item_count_1261 = baginfo.get(1261, 0)
        print(f"抽卡券: {item_count_1211},财神帽: {item_count_1261}")
        return item_count_1261






    def shangdiangoumai(self):
        req =  {"ads":"商店购买", "times":1, "hexstringheader":"a12c", "request_body_i2": 202602161, "request_body_i3": 12609, "request_body_i4": 1}      
        res = self.ac_manager.do_common_request(self.account_name, req, showres=self.showres)
        if len(res)<20:
            print("error on buy")
        
    def quangoumai(self):
        req =  {"ads":"券购买", "times":1, "hexstringheader":"a52c", "request_body_i2": 202602161, "request_body_i3": 9874}
        res = self.ac_manager.do_common_request(self.account_name, req, showres=self.showres)
        req =  {"ads":"券购买", "times":1, "hexstringheader":"a52c", "request_body_i2": 202602161, "request_body_i3": 9875}      
        res = self.ac_manager.do_common_request(self.account_name, req, showres=self.showres)
        if len(res)<20:
            print("error on buy")

    def nuanchunrenwu(self):
        reqs = [
            {"ads":"req_0", "times":1, "hexstringheader":"9f2c", "request_body_i2": 202602162, "request_body_i3": 103480},
            {"ads":"req_1", "times":1, "hexstringheader":"9f2c", "request_body_i2": 202602162, "request_body_i3": 103481},
            {"ads":"req_2", "times":1, "hexstringheader":"9f2c", "request_body_i2": 202602162, "request_body_i3": 103482},
            {"ads":"req_3", "times":1, "hexstringheader":"9f2c", "request_body_i2": 202602162, "request_body_i3": 103483},
            {"ads":"req_4", "times":1, "hexstringheader":"9f2c", "request_body_i2": 202602162, "request_body_i3": 103484},
            {"ads":"req_5", "times":1, "hexstringheader":"9f2c", "request_body_i2": 202602162, "request_body_i3": 103485},
            {"ads":"req_6", "times":1, "hexstringheader":"9f2c", "request_body_i2": 202602162, "request_body_i3": 103486},
            {"ads":"req_7", "times":1, "hexstringheader":"9f2c", "request_body_i2": 202602162, "request_body_i3": 103487},
            {"ads":"req_8", "times":1, "hexstringheader":"9f2c", "request_body_i2": 202602162, "request_body_i3": 103488},
            {"ads":"req_9", "times":1, "hexstringheader":"9f2c", "request_body_i2": 202602162, "request_body_i3": 103489},
            {"ads":"req_91", "times":1, "hexstringheader":"9f2c", "request_body_i2": 202602162, "request_body_i3": 103490},
            {"ads":"req_92", "times":1, "hexstringheader":"9f2c", "request_body_i2": 202602162, "request_body_i3": 103491},
        ]
        self.ac_manager.do_common_request_list(self.account_name, reqs, showres=self.showres)

    def dailylogin(self):
        """暖春兑换"""
        UNTITLED_REQUESTS = [
    {"ads":"req_0", "times":1, "hexstringheader":"af2c", "request_body_i2": 202602163, "request_body_i3": 53},  # 0-req.bin
    {"ads":"req_6", "times":1, "hexstringheader":"af2c", "request_body_i2": 202602163, "request_body_i3": 54},  # 6-req.bin
    {"ads":"req_1", "times":1, "hexstringheader":"af2c", "request_body_i2": 202602163, "request_body_i3": 55},  # 1-req.bin
    {"ads":"req_5", "times":1, "hexstringheader":"af2c", "request_body_i2": 202602163, "request_body_i3": 56},  # 5-req.bin
    {"ads":"req_2", "times":1, "hexstringheader":"af2c", "request_body_i2": 202602163, "request_body_i3": 57},  # 2-req.bin
    {"ads":"req_4", "times":1, "hexstringheader":"af2c", "request_body_i2": 202602163, "request_body_i3": 58},  # 4-req.bin
    {"ads":"req_3", "times":1, "hexstringheader":"af2c", "request_body_i2": 202602163, "request_body_i3": 59},  # 3-req.bin
    {"ads":"req_7", "times":1, "hexstringheader":"af2c", "request_body_i2": 202602163, "request_body_i3": 60},  # 7-req.bin
    {"ads":"req_8", "times":1, "hexstringheader":"af2c", "request_body_i2": 202602163, "request_body_i3": 61},  # 8-req.bin
    {"ads":"req_9", "times":1, "hexstringheader":"af2c", "request_body_i2": 202602163, "request_body_i3": 62},  # 9-req.bin
    {"ads":"req_9", "times":1, "hexstringheader":"af2c", "request_body_i2": 202602163, "request_body_i3": 63},  # 9-req.bin
    {"ads":"req_9", "times":1, "hexstringheader":"af2c", "request_body_i2": 202602163, "request_body_i3": 64},  # 9-req.bin
    {"ads":"req_9", "times":1, "hexstringheader":"af2c", "request_body_i2": 202602163, "request_body_i3": 65},  # 9-req.bin
    {"ads":"req_9", "times":1, "hexstringheader":"af2c", "request_body_i2": 202602163, "request_body_i3": 66},  # 9-req.bin
    {"ads":"req_10", "times":1, "hexstringheader":"a52c", "request_body_i2": 202602161, "request_body_i3": 9875},  # 10-req.bin
    {"ads":"券购买", "times":1, "hexstringheader":"a52c", "request_body_i2": 202602161, "request_body_i3": 9874}
    # {"ads":"req_11", "times":2, "hexstringheader":"c12c", "request_body_i2": 10, "request_body_i3": 202602161},  # 12-req.bin
    # {"ads":"req_12", "times":1, "hexstringheader":"c12c", "request_body_i2": 1, "request_body_i3": 202602161},  # 14-req.bin
]

        req_fl = {"ads":"fl_5", "times":1, "hexstringheader":"9d2c"}
        self.ac_manager.do_common_request(self.account_name, req_fl, showres=self.showres)
        self.ac_manager.do_common_request_list(self.account_name, UNTITLED_REQUESTS, showres=self.showres)
        return self.dogacha()

    def sellhuoguo(self):
        req = {"ads":"获取价格", "times":1, "hexstringheader":"eb2e"}
        res = self.ac_manager.do_common_request(self.account_name, req, showres=self.showres)      
        response = kpbl_pb2.huoguo_price_response()
        response.ParseFromString(res[6:])
        # print(response)
        highprice = 0
        highpricecharaid = 0
        for ppinfo in response.i3.ppinfos:
            if ppinfo.price > highprice:
                highprice = ppinfo.price
                highpricecharaid = ppinfo.pp.charaid
        print(f"highprice: {highprice}, highpricecharaid: {highpricecharaid}")

        # return
        # self.ac_manager.login(self.account_name, showloginres=0)
        baginfo = self.ac_manager.get_account(self.account_name, 'baginfo') or {}
        item_count_3516 = baginfo.get(3516, 0)
        print(f"火锅: {item_count_3516}")
        req = {"ads":"req_0", "times":1, "hexstringheader":"ef2e", "request_body_i2": item_count_3516, "request_body_i3": highpricecharaid}
        self.ac_manager.do_common_request(self.account_name, req, showres=self.showres)      
        self.ac_manager.login(self.account_name, showloginres=0)
        baginfo = self.ac_manager.get_account(self.account_name, 'baginfo') or {}
        item_count_3517 = baginfo.get(3517, 0)
        print(f"火锅票: {item_count_3517}")  

    def doncxh(self):
        # self.quangoumai()
        # self.shangdiangoumai()
        self.nuanchunrenwu()
        self.nuanchunrenwu()
        self.nuanchunrenwu()
        self.sellhuoguo()
        return