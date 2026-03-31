"""
活动boss管理模块 (rzsg)
处理活动boss相关功能，包括开始和结束活动boss
活动：赠送礼品
需要 代币id、活动id
"""

import logging
import binascii
from .kpbltools import ACManager, mask_account
from . import kpbl_pb2


class RZSGManager:
    """活动boss管理器"""

    def __init__(self, account_name, showres=0, delay=0.5):
        self.account_name = account_name
        self.ac_manager = ACManager(account_name, showres=showres, delay=delay)
        self.logger = logging.getLogger(f"RZSGManager_{account_name}")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.StreamHandler())
        self.showres = showres
        self.I8_VALUE = str(self.ac_manager.I8_VALUE)
        self.hdid = 202512081

    def rzsg2hd(self):
        req_configs = [
            {"ads":"进入主菜单1","times":1,"hexstringheader":"293c"},
            {"ads":"进入主菜单2","times":1,"hexstringheader":"333c"},
            {"ads":"签到","times":1,"hexstringheader":"1b2e"},
            
        ]
        # for req_config in req_configs:
        self.ac_manager.do_common_request_list(self.account_name, req_configs, showres=self.showres)
            
        # i = 102600
        # while i < 102700:
        #     lq_config = {"ads":f"任务领取{i}","times":1,"hexstringheader":"9f2c", 'request_body_i2':20250908, 'request_body_i3':i}
        #     docommonrequest(account_name,lq_config,showres=0)
        #     i+=1

        lq_com_configs = [
            {"ads":f"登录_1","times":1,"hexstringheader":"9f2c", 'request_body_i2':self.hdid, 'request_body_i3':102600},
            {"ads":f"任务领取pvp_1","times":1,"hexstringheader":"9f2c", 'request_body_i2':self.hdid, 'request_body_i3':102608},
            {"ads":f"任务领取pvp_2","times":1,"hexstringheader":"9f2c", 'request_body_i2':self.hdid, 'request_body_i3':102609},
            {"ads":f"任务领取pvp_3","times":1,"hexstringheader":"9f2c", 'request_body_i2':self.hdid, 'request_body_i3':102610},
            {"ads":f"任务领取pvp_4","times":1,"hexstringheader":"9f2c", 'request_body_i2':self.hdid, 'request_body_i3':102611},
            {"ads":f"地牢_1","times":1,"hexstringheader":"9f2c", 'request_body_i2':self.hdid, 'request_body_i3':102605},
            {"ads":f"地牢_2","times":1,"hexstringheader":"9f2c", 'request_body_i2':self.hdid, 'request_body_i3':102606},
            {"ads":f"地牢_3","times":1,"hexstringheader":"9f2c", 'request_body_i2':self.hdid, 'request_body_i3':102607},
            # {"ads":f"地牢_4","times":1,"hexstringheader":"9f2c", 'request_body_i2':20250908, 'request_body_i3':102608},
        ]

        for req_config in lq_com_configs:
            self.ac_manager.do_common_request(self.account_name, req_config, showres=self.showres)

    # kpblzd 转蛋活动，类似rzsg2hd，但是是转蛋活动
    def kpblzd(self, missionidfrom = 103500):
        req_configs = [
            {"ads":"进入主菜单1","times":1,"hexstringheader":"293c"},
            {"ads":"进入主菜单2","times":1,"hexstringheader":"333c"},
            {"ads":"签到","times":1,"hexstringheader":"1b2e"},
            
        ]
        for req_config in req_configs:
            self.ac_manager.do_common_request(self.account_name, req_config, showres=self.showres)
            

        lq_com_configs = [
            {"ads":f"任务领取_{i}","times":1,"hexstringheader":"9f2c", 'request_body_i2':self.hdid, 'request_body_i3':i}
            for i in range(missionidfrom, missionidfrom+56)
        ]

        for req in lq_com_configs:
            self.ac_manager.do_common_request(self.account_name, req, showres=self.showres)


    def get_coin_count(self, typeid=3510):  # 3510 20251208卡皮活动的代币id
        self.ac_manager.login(self.account_name)
        bag_info = self.ac_manager.get_account(self.account_name, 'baginfo')
        if typeid not in bag_info:
            return 0
        return bag_info[typeid]
    
    def get_gift_count(self, typeid=3513):  # 3513 20251208卡皮活动的礼物id
        self.ac_manager.login(self.account_name)
        bag_info = self.ac_manager.get_account(self.account_name, 'baginfo')
        if typeid not in bag_info:
            return 0
        print(f"礼物数量：{bag_info[typeid]}")
        return bag_info[typeid]
    
    def check_gift_receive_count(self):
        reqconfig = {"ads":"进入主菜单1","times":1,"hexstringheader":"293c"}
        res = self.ac_manager.do_common_request(self.account_name,reqconfig,showres=0)
        response_lzqd_cd = kpbl_pb2.response_lzqd_cd()
        response_lzqd_cd.ParseFromString(res[6:])
        print(f"checkgiftcount: {response_lzqd_cd.res.giftcount}")
        return response_lzqd_cd.res.giftcount == 99

    def zengsong(self, target_account):
        giftcount = self.get_gift_count()
        if giftcount == 0 :
            print('无礼物')
            return
        # input('即将添加好友')
        target_acm = ACManager(account=target_account, accounts_file=f'ac_{target_account}.json')
        target_id = target_acm.get_account(target_account,attribute_name='charaid')
        req_friend = {"ads":"好友申请","times":1,"hexstringheader":"a13a", 'request_body_i3':target_id}
        self.ac_manager.do_common_request(self.account_name, req_friend, showres=self.showres)
        # input('即将接受好友')
        accept_friend = {"ads":"好友申请通过","times":1,"hexstringheader":"a13a", 'request_body_i2':1, 'request_body_i3':self.ac_manager.get_account(self.account_name,attribute_name='charaid')}
        target_acm.do_common_request(target_account,accept_friend,showres=self.showres)
        # input('即将送礼')
        
        config = {"ads":"送礼","times":1,"hexstringheader":"2d3c","request_body_i2":target_id,"request_body_i3":1}
        print(config)
        while giftcount > 0:
            self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
            giftcount -= 1
        
        # input('即将删除好友')
        delete_friend = {"ads":"删除好友","times":1,"hexstringheader":"a13a", 'request_body_i2':5, 'request_body_i3':self.ac_manager.get_account(self.account_name,attribute_name='charaid')}
        target_acm.do_common_request(target_account,delete_friend,showres=self.showres)
        return giftcount


    def gacha_n(self):
        coin = self.get_coin_count()
        print(f"扭蛋币：{coin}")
        while coin > 0:
            print(f"扭蛋币：{coin}")
            tempcount = coin 
            if coin < 10:
                niudan_request = {"ads":"扭蛋-自定义次数","times":1,"hexstringheader":"2f3c", 'request_body_i2':1}
                while tempcount>0:
                    self.ac_manager.do_common_request(self.account_name, niudan_request, showres=self.showres)
                    tempcount-=1
            else:
                niudan_request = {"ads":"扭蛋-自定义次数","times":1,"hexstringheader":"2f3c", 'request_body_i2':10}
                while tempcount>9:
                    self.ac_manager.do_common_request(self.account_name, niudan_request, showres=self.showres)
                    tempcount-=10        
            
            coin = self.get_coin_count()
        
        print("扭蛋币已用完")

    def licheng(self):
        req_config = {"ads":"里程","times":1,"hexstringheader":"353c"}
        self.ac_manager.do_common_request(self.account_name, req_config, showres=self.showres)

    def buy_coin(self):
        req_config = {"ads":"购买扭蛋","times":1,"hexstringheader":"313c", 'request_body_i2':1}
        self.ac_manager.do_common_request(self.account_name, req_config, showres=self.showres)


    def do_activity_boss(self):
        """
        执行活动boss功能（活动boss开始和结束）

        Returns:
            bool: 执行是否成功
        """
        try:
            self.logger.info(f"[{self.account_name}] 开始执行活动boss功能")

            # 活动boss请求配置
            req_configs = [
                {"ads": "活动boss开始", "times": 1, "hexstringheader": "7b29"},
                {
                    "ads": "活动boss结束",
                    "times": 1,
                    "hexstringheader": "7929",
                    "request_body_i2": binascii.unhexlify('b7db06a48d06839206e98e06eb8e06ec8e069adc069fdc06fb9106fa9106'),
                    "request_body_i3": self.I8_VALUE,
                    "requestbodytype": "request_body_for_geren"
                },
                {"ads": "活动boss开始", "times": 1, "hexstringheader": "7b29"},
                {
                    "ads": "活动boss结束",
                    "times": 1,
                    "hexstringheader": "7929",
                    "request_body_i2": binascii.unhexlify('b7db06a48d06839206e98e06eb8e06ec8e069adc069fdc06fb9106fa9106'),
                    "request_body_i3": self.I8_VALUE,
                    "requestbodytype": "request_body_for_geren"
                },
            ]

            for req_config in req_configs:
                self.logger.info(f"[{self.account_name}] 执行: {req_config['ads']}")
                res = self.ac_manager.do_common_request(self.account_name, req_config, showres=self.showres)

                if res:
                    self.logger.info(f"[{self.account_name}] {req_config['ads']} 执行成功")
                else:
                    self.logger.error(f"[{self.account_name}] {req_config['ads']} 执行失败")
                    return False

            self.logger.info(f"[{self.account_name}] 活动boss功能执行完成")
            return True

        except Exception as e:
            self.logger.error(f"[{self.account_name}] 执行活动boss功能时发生错误: {str(e)}")
            return False

    def openChest(self, isGold = 0):
        # 银箱 200001 金箱 200002
        # 单抽 10连 
        if isGold:
            req_config = {"ads":"商店-金箱10连1次","times":1,"request_body_i2":200002,"request_body_i3":2,"request_body_i4":2,"hexstringheader":"c72b"}
        else:
            req_config = {"ads":"商店-银箱1次","times":1,"request_body_i2":200001,"request_body_i3":2,"request_body_i4":2,"hexstringheader":"c72b"}
        self.ac_manager.do_common_request(self.account_name, req_config, showres=self.showres)

    def refreshinfo(self):
        self.ac_manager.login(self.account_name)
        id, self.count_ticket = self.ac_manager.getItemIdByType(self.ticket_id)
        id, self.count_coin_normal = self.ac_manager.getItemIdByType(self.coin_normal_id)
        id, self.count_coin_gold = self.ac_manager.getItemIdByType(self.coin_gold_id)
        print(f'票:{self.count_ticket} 银币:{self.count_coin_normal} 金币:{self.count_coin_gold}')
        id, self.count_txz_ticket = self.ac_manager.getItemIdByType(self.txz_ticket_id)
        print(f'通行证票:{self.count_txz_ticket}')

    def doguaguaka(self):
        self.refreshinfo()
        gua_req=[{"ads":"刮","times":6,"hexstringheader":"5f44"}]
        shuaxin_req = {"ads":"刷新","times":1,"hexstringheader":"6144"}

        # 6次一轮
        while self.count_ticket>=6:
            self.ac_manager.do_common_request_list(self.account_name, gua_req, showres=self.showres)
            self.ac_manager.do_common_request(self.account_name, shuaxin_req, showres=self.showres)
            self.count_ticket -= 6
            # self.refreshinfo()
        shuaxin_req = {"ads":"进度奖励","times":1,"hexstringheader":"6344"}
        self.ac_manager.do_common_request(self.account_name, shuaxin_req, showres=self.showres)
        
    def gettongxingzheng(self):
        """领取通行证奖励"""
        req_config = {
            "ads": "通行证领取",
            "times": 1,
            "hexstringheader": "a72c",
            "request_body_i2": self.hdid,
            "request_body_i3": binascii.unhexlify('f50c'),
            "requestbodytype": "request_body_for_sd"
        }
        self.ac_manager.do_common_request(self.account_name, req_config, showres=self.showres)

    def txz_gacha(self):
        req = {
            "ads": "通行证转蛋",
            "times": 1,
            "hexstringheader": "c12c",
            "request_body_i2": self.count_txz_ticket,
            "request_body_i3": self.hdzdid
        }
        res = self.ac_manager.do_common_request(self.account_name, req, showres=self.showres)
        response_hd20260330_nd = kpbl_pb2.hd20260330_nd_response()
        response_hd20260330_nd.ParseFromString(res[6:])
        print(response_hd20260330_nd.i3)
        from .item_names import ITEM_NAMES as item_names
        for item in response_hd20260330_nd.i3:
            if item.item_type in item_names:
                print(f'物品类型:{item_names[item.item_type]} 物品数量:{item.item_count}')
            else:
                print(f'物品类型:{item.item_type} 物品数量:{item.item_count}')

    def hd20260330(self):
        # 奇妙马戏团，hd1 通行证，hd2 转蛋，hd3 刮刮卡，hd4 签到
        self.hdid = 20260330
        self.hdzdid = 202603301
        self.txz_ticket_id = 1202
        self.ticket_id = 1508
        self.coin_normal_id = 1509
        self.coin_gold_id = 1510



        # self.ac_manager.openBox(71)
        # self.ac_manager.openBox(71)
        # chestopencount = 0

        # id, count = self.ac_manager.getItemIdByType(60)
        # while count>=10 and chestopencount < 100:
        #     self.openChest(isGold=0)
        #     count -= 10
        #     chestopencount += 10
        #     # id, count = self.ac_manager.getItemIdByType(60)

        # id, count = self.ac_manager.getItemIdByType(70)
        # while count>=10 and chestopencount < 100:
        #     self.openChest(isGold=1)
        #     count -= 10
        #     chestopencount += 10

            
        # # 宠物蛋
        # req = {"ads":"培养-宠物蛋35","request_body_i2":13,"hexstringheader":"f14e","times":1}
        # eggopencount = 0
        # id, count = self.ac_manager.getItemIdByType(11)
        # while count>=1 and eggopencount < 370:
        #     self.ac_manager.do_common_request(self.account_name, req, showres=self.showres)
        #     eggopencount += 35
        #     count -= 30
            # id, count = self.ac_manager.getItemIdByType(11)
        self.kpblzd(missionidfrom=103600)

        self.refreshinfo()    
        self.doguaguaka()
        self.gettongxingzheng()
        self.refreshinfo()
        self.txz_gacha()
        self.refreshinfo()