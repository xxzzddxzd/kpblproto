"""
日常任务管理模块
处理游戏中的日常任务功能
"""

import logging
import binascii
import json
from .kpbltools import ACManager, mask_account
from .wk_manager import WKManager
from . import kpbl_pb2
from .first_login_requests import FIRST_LOGIN_REQUESTS, FIRST_LOGIN_REQUESTS_PLUS, FIRST_LOGIN_LV31_REQUESTS

class DAManager:
    """日常任务管理器"""
    
    def __init__(self, account_name, showres=0, delay=0.5, accounts_file=None, ac_manager=None):
        self.account_name = account_name
        if ac_manager:
            self.ac_manager = ac_manager
        else:
            self.ac_manager = ACManager(account_name, showres=showres, delay=delay, accounts_file=accounts_file)
        self.logger = logging.getLogger(f"DAManager_{account_name}")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.StreamHandler())
        self.showres = showres
        self.I8_VALUE = self.ac_manager.I8_VALUE
    
    def get_daily_config(self):
        """
        获取日常任务配置列表
        
        Returns:
            list: 日常任务配置字典列表
        """
        return [
            {"ads":"活动日历签到","times":1,"hexstringheader":"d32b","request_body_i2":250},
            # {"ads":"骰子广告","times":1,"hexstringheader":"2f35","request_body_i2":9218},
            {"ads":"hd20260330广告","hexstringheader":"a52c","times":1,"request_body_i2":202603301,'request_body_i3':9735},
            # {"ads":"中秋x5","hexstringheader":"a52c","times":5,"request_body_i2":20251006,'request_body_i3':9799},
            # {"ads":"周年","hexstringheader":"a52c","times":1,"request_body_i2":202512223,'request_body_i3':3010},
            # {"ads":"周年","hexstringheader":"a52c","times":2,"request_body_i2":202512223,'request_body_i3':3020},
            {"ads":"魔法币礼包","hexstringheader":"a52c","times":2,"request_body_i2":202604271,'request_body_i3':9859},
            {"ads":"魔法放大镜礼包","hexstringheader":"a52c","times":5,"request_body_i2":20260427,'request_body_i3':9850},
            # {"ads":"异星矿场广告","hexstringheader":"a52c","times":1,"request_body_i2":2505027,'request_body_i3':1201},
            # {"ads":"星域礼包","hexstringheader":"a52c","times":2,"request_body_i2":2505025,'request_body_i3':1072},
            # {"ads":"星域礼包-武装","hexstringheader":"a52c","times":1,"request_body_i2":2505026,'request_body_i3':1080},
            # {"ads":"星域 挖矿礼包","hexstringheader":"a52c","times":1,"request_body_i2":2505024,'request_body_i3':1090},
            {"ads":"盲盒机礼包","hexstringheader":"a52c","times":1,"request_body_i2":202512227,'request_body_i3':3010},
            {"ads":"盲盒机礼包","hexstringheader":"a52c","times":1,"request_body_i2":202512227,'request_body_i3':3020},

            {"ads":"yxkc挂机奖励","times":1,"hexstringheader":"0156"},
            {"ads":"yxkc矿洞挂机","times":1,"hexstringheader":"5d78"},
            # {"ads":"周年","hexstringheader":"eb2e"},
            # {"ads":"购买1次深渊钥匙x1","hexstringheader":"5151","times":1,"request_body_i2":10104,'request_body_i3':1},
            {"ads":"工会捐献5","hexstringheader":"2977","times":5},
            {"ads":"黑市购买1","hexstringheader":"6532","times":1, "request_body_i2":2,"request_body_i3":21300},
            {"ads":"黑市购买2","hexstringheader":"6532","times":1, "request_body_i2":2,"request_body_i3":21400},
            {"ads":"黑市购买3","hexstringheader":"6532","times":1, "request_body_i2":2,"request_body_i3":21500},
            {"ads":"黑市购买4","hexstringheader":"6532","times":1, "request_body_i2":2,"request_body_i3":21600},
            {"ads":"黑市购买5","hexstringheader":"6532","times":1, "request_body_i2":2,"request_body_i3":21700},
            {"ads":"黑市购买6","hexstringheader":"6532","times":1, "request_body_i2":2,"request_body_i3":21800},
            # {"ads":"黑市购买7","hexstringheader":"6532","times":1, "request_body_i2":2,"request_body_i3":21900},
            # {"ads":"黑市购买8","hexstringheader":"6532","times":1, "request_body_i2":2,"request_body_i3":22000},
            {"ads":"2特惠星免费","hexstringheader":"b52c","times":1, "request_body_i2":310},
            {"ads":"特权卡","hexstringheader":"d129","times":1},

            {"ads":"公会战转盘（败者）","hexstringheader":"cb76","times":2,"request_body_i2":1},
            {"ads":"公会战转盘（胜者）","hexstringheader":"cb76","times":2},

            # 副本up基金: 动态获取活动ID，在execute_daily_tasks末尾执行
            
            {"ads":"挑战-挖矿次数","hexstringheader":"5d4f","times":2},
            {"ads":"挑战-蛋票","request_body_i2":2,"hexstringheader":"d52b","times":2},
            {"ads":"挑战-体力票","request_body_i2":1,"hexstringheader":"d52b","times":2},
            {"ads":"培养-宠物蛋3次","request_body_i2":11,"hexstringheader":"f14e","times":3},
            {"ads":"主界面-15体力2次","request_body_i2":2,"hexstringheader":"a527","times":2},
            {"ads":"黑市-免费金币1次","request_body_i2":100001,"request_body_i3":1,"hexstringheader":"c32b","times":1},
            {"ads":"商店-普通装备箱3次","request_body_i2":200001,"request_body_i3":1,"request_body_i4":1,"hexstringheader":"c72b","times":3},
            {"ads":"挑战-箱子票2次","request_body_i2":3,"hexstringheader":"d52b","times":2},
            {"ads":"商店-高级装备箱1次","request_body_i2":200002,"request_body_i3":1,"request_body_i4":1,"hexstringheader":"c72b","times":1},
            {"ads":"挑战-尘票","request_body_i2":4,"hexstringheader":"d52b","request_body_i2":4,"times":2},
            
            {"ads":"卡皮币","request_body_i2":9000,"hexstringheader":"c12d","times":1},
            {"ads":"卡皮币20250208","times":1,"hexstringheader":"c12d","request_body_i2":9000},
            {"ads":"挂机奖励","times":1,"hexstringheader":"112b"},
            
            {"ads":"签到","times":1,"hexstringheader":"ef2c"},
            {"ads":"免费10体力","times":1,"hexstringheader":"a527"},
            {"ads":"免费罗盘x2","times":1,"hexstringheader":"4735","request_body_i2":9310},
            {"ads":"冒险日记免费","times":1,"hexstringheader":"4735","request_body_i2":9320},
            {"ads":"免费贝壳x2","times":1,"hexstringheader":"4735","request_body_i2":9330},
            # 8f2c 特惠弹框已由 claim_popup_deals() 动态处理
            {"ads":"0428活动免费2","times":1,"hexstringheader":"89 2e ","request_body_i2":9130},
            {"ads":"钓鱼广告","times":1,"hexstringheader":"89 2e ","request_body_i2":9110},

            {"ads":"锦鲤1","times":1,"hexstringheader":"b92c","request_body_i2":101},
            {"ads":"锦鲤2","times":1,"hexstringheader":"b92c","request_body_i2":102},
            {"ads":"锦鲤3","times":1,"hexstringheader":"b92c","request_body_i2":103},
            # {"ads":"骰子广告","times":1,"hexstringheader":"2f35","request_body_i2":9211},
            {"ads":"公会讨伐奖励", "times":1, "hexstringheader":"2b77"}, 
            {"ads":"公会船票购买(D)", "times":1, "hexstringheader":"6532", "request_body_i2":1, "request_body_i3":10601, "request_body_i4":2},
            {"ads":"公会船票购买(W)", "times":1, "hexstringheader":"6532", "request_body_i2":1, "request_body_i3":12301, "request_body_i4":1}, 
            {"ads":"公会宝石购买(W)", "times":1, "hexstringheader":"6532", "request_body_i2":1, "request_body_i3":11200, "request_body_i4":1}, 

            {"ads":"大扫除1600购买","times":1,"hexstringheader":"512d","request_body_i2":20402, "request_body_i3":20132},


            {"ads":"简述训练1600购买","times":1,"hexstringheader":"512d","request_body_i2":20502, "request_body_i3":20250},

            {"ads":"奇妙马戏团特惠礼包","times":2,"hexstringheader":"8d2c","request_body_i2":122},
            {"ads":"体力活动排名奖励","times":1,"hexstringheader":"092b"},
            
        ]
    
    def dodailyjl(self):
        from modules import TradeManager
        trade_manager_xh = TradeManager('xh')
        boats = trade_manager_xh.getboat(20)
        if len(boats) == 0:
            print("没有找到船只")
            return False
        trade_manager = TradeManager(self.account_name)
        baginfo = trade_manager.ac_manager.get_account(self.account_name, 'baginfo') or {}
        for slotslen, max_135, boat in boats:
            
            trade_manager.attack(boat)
            trade_manager.ac_manager.login(self.account_name)
            baginfo1 = trade_manager.ac_manager.get_account(self.account_name, 'baginfo') or {}
            # print(f"劫掠船只: {boat}")
            from modules.item_names import ITEM_NAMES
            diff = {ITEM_NAMES.get(k, k): baginfo1.get(k, 0) - baginfo.get(k, 0) for k in set(baginfo) | set(baginfo1) if baginfo1.get(k, 0) != baginfo.get(k, 0)}
            print(f"变化: {diff}")
            
    def guild_war_reqs(self):
        return [
            {"ads":"个人战开始","times":1,"hexstringheader":"b328",},
            {"ads":"个人战结束180b","times":1,"hexstringheader":"b128","request_body_i2":binascii.unhexlify('b7db06a48d06839206e98e06eb8e06ec8e069adc069fdc06fb9106fa9106'),"request_body_i3":str(self.ac_manager.I8_VALUE),"requestbodytype":"request_body_for_geren"},
            {"ads":"个人战开始","times":1,"hexstringheader":"b328",},
            {"ads":"个人战结束180b","times":1,"hexstringheader":"b128","request_body_i2":binascii.unhexlify('b7db06a48d06839206e98e06eb8e06ec8e069adc069fdc06fb9106fa9106'),"request_body_i3":str(self.ac_manager.I8_VALUE),"requestbodytype":"request_body_for_geren"},
            {"ads":"公会战结束300b","times":2,"hexstringheader":"0376","request_body_i2":binascii.unhexlify('b7db06a48d06839206e98e06eb8e06ec8e069adc069fdc06fb9106fa9106'),"requestbodytype":"request_body_for_dilao"},
            
        ]
    
    def petegggacha(self,times):
        print('egggacha')
        req = {"ads":"宠物蛋3抽卡10倍","times":times,"hexstringheader":"f14e","request_body_i2":13, 'request_body_i3':10}
        return len(self.ac_manager.do_common_request(self.account_name, req, showres=self.showres))>20

    def execute_daily_tasks(self):
        """
        执行所有日常任务
        
        Returns:
            bool: 执行成功返回True
        """
        try:
            self.get_jsxl_id()
            # print(f"<{mask_account(self.account_name)}> 开始活动广告任务...")
            # req_list = []
            # if self.ac_manager.get_account(self.account_name, 'adlist'):
            #     for ad in self.ac_manager.get_account(self.account_name, 'adlist'):
            #         for adid, adsubid in ad.items():
            #             print(f"<{mask_account(self.account_name)}> 开始执行广告{adid} {adsubid}")
            #             req_config = {"ads":f"广告{adid}","times":1,"hexstringheader":"a52c","request_body_i2":adid,"request_body_i3":adsubid}
            #             req_list.append(req_config)
            # print(f"<{mask_account(self.account_name)}> 开始 adlist(并发): {req_list}")
            # self.ac_manager.do_common_request_list(self.account_name, req_list, showres=1)
            # self.claim_activity_ads()
            print(f"<{mask_account(self.account_name)}> 开始执行日常任务...")
            # 获取配置列表
            requests_config = self.get_daily_config()
            print(f"<{mask_account(self.account_name)}> 开始 daily_config(并发)")
            # self.ac_manager.do_common_request_list(self.account_name, requests_config, showres=self.showres)
            
            # 执行每个日常任务请求
            for config in requests_config:
                print(f"<{mask_account(self.account_name)}> 开始 {config['ads']}")
                self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
            
            print(f"<{mask_account(self.account_name)}> 开始 guild_war_reqs")
            for config in self.guild_war_reqs():
                self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)

            print(f"<{mask_account(self.account_name)}> 开始执行PVP")
            self.dopvpinit()
            i = 5
            while i > 0:
                self.dopvp()
                i -= 1
            
            # 执行挖矿任务
            print(f"<{mask_account(self.account_name)}> 开始执行挖矿任务...")
            wk_manager = WKManager(self.account_name)
            wk_manager.start_mining()
            
            print(f"<{mask_account(self.account_name)}> 日常任务执行完成")
            
            print(f"<{mask_account(self.account_name)}> 开始执行武道大会点赞")
            self.wddh_dz()
            print(f"<{mask_account(self.account_name)}> 开始执行圣杯战争点赞")
            self.sbzz_dz()
            print(f"<{mask_account(self.account_name)}> 开始执行武道大会预选")

            self.wddh_yuxuan()
            
            
            # 副本up基金全部领取
            self.fbup_claim()

            # 限时祈愿任务领取
            self.xsqy_claim()

            # 特惠弹框领取
            self.claim_popup_deals()

            print(f"<{mask_account(self.account_name)}> 开始执行个人船刷新开船")
            from .trade_manager import TradeManager
            TradeManager(self.account_name, showres=self.showres, ac_manager=self.ac_manager).run_grc()

            return True
        except Exception as e:
            print(f"<{mask_account(self.account_name)}> 日常任务执行失败: {e}")
            return False

    def fbup_claim(self):
        """副本up基金全部领取（a72c），动态获取活动ID"""
        activity_info = self.ac_manager.get_account(self.account_name, 'activity_info')
        if not activity_info:
            activity_info = self.ac_manager.fetch_activity_info(self.account_name)
        for act_id in activity_info:
            if 259980 <= act_id <= 260030:
                print(f"<{mask_account(self.account_name)}> 副本up基金领取: 活动ID={act_id}")
                config = {"ads":"副本up基金全部领取","hexstringheader":"a72c","times":1,"request_body_i2":act_id,"request_body_i3":'9', "requestbodytype":"request_body_for_stringi3"}
                self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
                return
        print(f"<{mask_account(self.account_name)}> 未找到副本up基金活动")

    def xsqy_claim(self):
        """限时祈愿任务领取（9f2c），动态获取活动ID，i3从140000到140030并发领取"""
        
        activity_info = self.ac_manager.get_account(self.account_name, 'activity_info')
        # print(f'xsqy_claim activity_info: {activity_info}')
        if not activity_info:
            activity_info = self.ac_manager.fetch_activity_info(self.account_name)
        print(f'xsqy_claim activity_info: {activity_info}')
        # 查找25xxxxx范围的活动ID
        act_id = None
        for aid in activity_info:
            if 2509070 <= aid <= 2509120: #2509095
                act_id = aid
                break
        if not act_id:
            print(f"<{mask_account(self.account_name)}> 未找到限时祈愿活动")
            return
        print(f"<{mask_account(self.account_name)}> 限时祈愿领取: 活动ID={act_id}")
        req_list = []
        for i3 in range(140000, 140051):
            req = {"ads": f"限时祈愿{i3}", "hexstringheader": "9f2c", "times": 1, "request_body_i2": act_id, "request_body_i3": i3}
            self.ac_manager.do_common_request(self.account_name, req, showres=self.showres)

    def claim_popup_deals(self):
        """领取特惠弹框奖励：先8b2c获取列表，再8d2c领活动特惠、8f2c领每日特惠"""
        # 1. 获取特惠列表
        config = {"ads": "特惠弹框列表", "hexstringheader": "8b2c", "times": 1}
        res = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        if not res or len(res) <= 6:
            print(f"<{mask_account(self.account_name)}> 获取特惠弹框列表失败")
            return
        resp = kpbl_pb2.da_ads_list_response()
        resp.ParseFromString(res[6:])

        # 2. 收集所有领取请求
        req_list1 = []
        req_list2 = []
        if resp.i2 and resp.i2.i1:
            ad_id = resp.i2.i1
            steps = resp.i2.i5
            print(f"<{mask_account(self.account_name)}> 活动特惠 id={ad_id}, 阶梯={len(steps)}")
            # for step in steps[:2]:
            step = steps[0]
            req_list1.append({"ads": f"活动特惠{ad_id}-{step.i1}", "hexstringheader": "8d2c", "times": 1,
                                 "requestbodytype": "request_body_for_mfssth",
                                 "request_body_i2": step.i1, "request_body_i3": ad_id})
            step = steps[1]
            req_list2.append({"ads": f"活动特惠{ad_id}-{step.i1}", "hexstringheader": "8d2c", "times": 1,
                                 "requestbodytype": "request_body_for_mfssth",
                                 "request_body_i2": step.i1, "request_body_i3": ad_id})

        if resp.i3 and resp.i3.i37:
            for daily in resp.i3.i37:
                ad_id = daily.i1
                steps = daily.i5
                print(f"<{mask_account(self.account_name)}> 每日特惠 id={ad_id}, 阶梯={len(steps)}")
                # for step in steps[:4]:
                step = steps[0]
                req_list1.append({"ads": f"每日特惠{ad_id}-{step.i1}", "hexstringheader": "8f2c", "times": 1,
                                     "requestbodytype": "request_body_for_mfssth",
                                     "request_body_i2": step.i1, "request_body_i3": ad_id})
                step = steps[1]
                req_list2.append({"ads": f"每日特惠{ad_id}-{step.i1}", "hexstringheader": "8f2c", "times": 1,
                                     "requestbodytype": "request_body_for_mfssth",
                                     "request_body_i2": step.i1, "request_body_i3": ad_id})

        # 3. 一次性并发发送
        if req_list1 and req_list2:
            print(f"<{mask_account(self.account_name)}> 特惠弹框领取: {len(req_list1)}个请求")
            print(req_list1)
            print(req_list2)
            for req in req_list1:
                self.ac_manager.do_common_request(self.account_name, req, showres=1)
            for req in req_list2:
                self.ac_manager.do_common_request(self.account_name, req, showres=1)
            # self.ac_manager.do_common_request_list(self.account_name, req_list1, showres=1)
            # self.ac_manager.do_common_request_list(self.account_name, req_list2, showres=1)

    def execute_daily_tasks_nowk(self):  #周年用
        """
        执行所有日常任务
        
        Returns:
            bool: 执行成功返回True
        """
        try:
            print(f"<{mask_account(self.account_name)}> 开始执行日常任务...")
            
            # 获取配置列表
            requests_config = self.get_daily_config()
            
            # 执行每个日常任务请求
            for config in requests_config:
                self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
            
            print(f"<{mask_account(self.account_name)}> 开始执行PVP")
            self.dopvpinit()
            i = 5
            while i > 0:
                self.dopvp()
                i -= 1
            
            
            print(f"<{mask_account(self.account_name)}> 日常任务执行完成")
            
            req_config = {"ads":"商店购买1次","times":1,"hexstringheader":"6532","request_body_i2":2,'request_body_i3':20101}
            self.ac_manager.do_common_request(self.account_name,req_config,showres=self.showres)
            return True
        except Exception as e:
            print(f"<{mask_account(self.account_name)}> 日常任务执行失败: {e}")
            return False
    
    def execute_daily(self):
        """
        执行日常任务的接口方法，与main.py兼容
        
        Returns:
            bool: 执行成功返回True
        """
        return self.execute_daily_tasks()
    
    def saodang(self, dungeonType, level, times):
        """
        执行扫荡功能
        
        Args:
            dungeonType: 副本类型ID (1~4)
            level: 层数，0表示从登录数据自动读取
            times: 扫荡次数
        """
        if level == 0:
            # 从llogin数据读取已通关层数
            cleared = self.ac_manager.get_account(self.account_name, f'ac{dungeonType}_cleared') or 0
            level = cleared if cleared > 0 else 1
            print(f"从llogin读取ac{dungeonType}已通关: {cleared}，扫荡层数: {level}")
        print(f"开始执行副本ID {dungeonType}：{level} 的扫荡，次数：{times}")
        config = {
            "ads": f"扫荡-副本{dungeonType}",
            "times": times,
            "request_body_i2": dungeonType,
            "request_body_i3": level,
            "request_body_i4": 1,  
            "request_body_i5": str(self.ac_manager.I8_VALUE),
            "hexstringheader": "9530",
        }
        self.ac_manager.do_common_request(self.account_name,config,showres=self.showres)

    def dodl(self): # 地牢
        config = {"ads":"地牢-开始","times":1,"hexstringheader":"4d33"}
        self.ac_manager.do_common_request(self.account_name,config,showres=self.showres)

    def doqh(self):
        print('强化任务')
        # 从装备列表中找一个等级为1的装备
        eq_list = self.ac_manager.get_account(self.account_name, 'eq_list') or []
        # print(eq_list)
        eq_uid = None
        for eq in eq_list:
            if eq.get('eq_level') == 1:
                eq_uid = eq.get('eq_uid')
                eq_level = eq.get('eq_level')
                break
        if not eq_uid:
            print('没有找到等级为1的装备，跳过强化任务')
            return
        print(f'使用装备 eq_uid: {eq_uid} , level {eq_level}')
        
        req_config = {"ads":"强化任务-强化","times":1,"hexstringheader":"612b","request_body_i2":eq_uid, "request_body_i3":1}
        self.ac_manager.do_common_request(self.account_name,req_config,showres=self.showres)
        req_config = {"ads":"强化任务-还原","times":1,"hexstringheader":"652b","request_body_i2":eq_uid}
        return len(self.ac_manager.do_common_request(self.account_name,req_config,showres=self.showres)) > 20

    def dopetqh(self):
        """宠物还原和强化：找出level最低的宠物，先还原后强化"""
        pets = self.ac_manager.get_account(self.account_name, 'pets') or []
        if not pets:
            print('账号中没有宠物信息，跳过宠物强化')
            return
        min_pet = min(pets, key=lambda p: p.get('level', 0))
        pet_uid = min_pet['id']
        print(f'宠物还原和强化: id={pet_uid}, level={min_pet.get("level", 0)}')
        req_config = {"ads":"宠物还原","times":1,"hexstringheader":"ed4e","request_body_i2":pet_uid}
        self.ac_manager.do_common_request(self.account_name,req_config,showres=self.showres)
        req_config = {"ads":"宠物强化","times":5,"hexstringheader":"e94e","request_body_i2":pet_uid}
        self.ac_manager.do_common_request(self.account_name,req_config,showres=self.showres)

    def dodefaultdailyquest(self, isxh=0):
        print('强化任务')
        self.doqh()
        self.dopvpinit()
        i = 5
        while i > 0:
            self.dopvp()
            i -= 1
        
        print('扫荡')
        for dt in range(1, 5):
            self.saodang(dt, 0, 4)
        print('开箱子')
        self.ac_manager.openBox(71, 5)
        self.dopetqh()


        print('每日任务单独领取')
        todo = range(1, 16)
        req_list = []
        for t in todo:
            req_config = {"ads":f"领取任务{t}","times":1,"hexstringheader":"0729","request_body_i2":t}
            req_list.append(req_config)
        self.ac_manager.do_common_request_list(self.account_name, req_list, showres=self.showres)
        req_config = {"ads":"日活领取","times":1,"hexstringheader":"0d29","request_body_i2":1}
        self.ac_manager.do_common_request(self.account_name,req_config,showres=self.showres)
        req_config = {"ads":"周活领取","times":1,"hexstringheader":"0d29","request_body_i2":2}
        self.ac_manager.do_common_request(self.account_name,req_config,showres=self.showres)
        req_config = {"ads":"锦鲤","times":1,"hexstringheader":"b92c","request_body_i2":101}
        req_config = {"ads":"锦鲤","times":1,"hexstringheader":"b92c","request_body_i2":102}
        req_config = {"ads":"锦鲤","times":1,"hexstringheader":"b92c","request_body_i2":103}
        return 1
    # def dailyforkpkpj(self): # 卡皮转蛋日常
        
    def dobuypvp(self):
        req = {"ads":"PVP购买5次","times":1,"hexstringheader":"d12b", 'request_body_i2':10, 'request_body_i3':5}
        self.ac_manager.do_common_request(self.account_name,req,showres=self.showres)

    def dopvpinit(self):
        config1 = {"ads":"pvpinit1","times":1,"hexstringheader":"3733"}
        config2 = {"ads":"pvpinit2","times":1,"hexstringheader":"3333", 'request_body_i2':1}
        self.ac_manager.do_common_request(self.account_name,config1,showres=self.showres)
        self.ac_manager.do_common_request(self.account_name,config2,showres=self.showres)

    def dopvp(self):
        global ac_manager
        config1 = {"ads":"pvplist","times":1,"hexstringheader":"2f33"}
        config2 = {"ads":"pvpstart","times":1,"hexstringheader":"3133","request_body_i2":1, "request_body_i3" : str(self.ac_manager.I8_VALUE), 'requestbodytype':'request_body_for_stringi3'}
        res = self.ac_manager.do_common_request(self.account_name,config1,showres=self.showres)
        
        # 解析二进制响应数据
        if res and len(res) > 6:
            try:
                # 从第6个字节开始提取数据(跳过头部)
                response_data = res[6:]
                
                # 使用pvplist_response解析数据
                pvp_list = kpbl_pb2.pvplist_response()
                pvp_list.ParseFromString(response_data)
                
                # 检查是否有玩家列表
                if hasattr(pvp_list, 'players') and pvp_list.players:
                    # print(f"找到 {len(pvp_list.players)} 个PVP对手")
                    
                    # 选择第一个玩家的ID
                    playerid = pvp_list.players[0].pid
                    # print(f"选择了playerid: {playerid}")
                    
                    # 更新config2中的playerid
                    config2["request_body_i2"] = playerid
                    
                    # 发起PVP战斗
                    # print(f"正在开始对战playerid: {playerid}")
                    # print(config2)
                    self.ac_manager.do_common_request(self.account_name, config2, showres=self.showres)
                    return
                else:
                    print("未找到可用的PVP对手")
            except Exception as e:
                print(f"解析PVP列表出错: {str(e)}")
    
    def dowdh(self, target):
        req_config = {"ads":"武道会","times":1,"hexstringheader":"1d79", 'request_body_i2':target}
        self.ac_manager.do_common_request(self.account_name, req_config, showres=self.showres)
    
    def yjcc(self):
        """研究传承"""
        # 获取账号信息中的cc字典 {id: jd}
        cc_dict = self.ac_manager.get_account(self.account_name, 'cc')
        
        if not cc_dict:
            print(f"<{mask_account(self.account_name)}> 没有找到传承信息")
            return False
        
        print(f"<{mask_account(self.account_name)}> 传承字典: {cc_dict}")
        
        # 按系列分组分析
        research_targets = []
        
        for series in ['1', '2', '3', '4', '5']:
            # 找出这个系列的所有传承
            series_cc = {k: v for k, v in cc_dict.items() if k[0] == series}
            if not series_cc:
                continue
            
            print(f"\n系列{series}当前状态:")
            
            # 找出当前最高层（第3位最大的）
            max_layer = max(int(cc_id[2]) for cc_id in series_cc.keys())
            current_layer_cc = {k: v for k, v in series_cc.items() if int(k[2]) == max_layer}
            
            print(f"  当前最高层: {max_layer}")
            print(f"  当前层传承: {current_layer_cc}")
            
            # 检查当前层的完成情况
            branch_node = None  # 分支点 XXX01
            left_nodes = []     # 左线节点 XXX02,03,04
            right_nodes = []    # 右线节点 XXX05,06,07
            
            for cc_id, cc_jd in current_layer_cc.items():
                fifth_digit = int(cc_id[4])
                if fifth_digit == 1:
                    branch_node = (cc_id, cc_jd)
                elif fifth_digit in [2, 3, 4]:
                    left_nodes.append((cc_id, cc_jd, fifth_digit))
                elif fifth_digit in [5, 6, 7]:
                    right_nodes.append((cc_id, cc_jd, fifth_digit))
            
            # 找出左右线的最高节点
            left_max_node = max(left_nodes, key=lambda x: x[2]) if left_nodes else None
            right_max_node = max(right_nodes, key=lambda x: x[2]) if right_nodes else None
            
            # 判断需要研究的节点
            branch_done = branch_node and branch_node[1] >= 1
            
            # 检查分支点
            if branch_node and branch_node[1] < 1:
                research_targets.append((branch_node[0], branch_node[1], 1, "分支点"))
            
            # 检查左线
            left_done = False
            if left_max_node:
                cc_id, cc_jd, fifth_digit = left_max_node
                # 左线所有节点的最大值都是10
                max_jd = 10
                if fifth_digit == 4 and cc_jd >= 10:
                    # 左线终点完成
                    left_done = True
                elif cc_jd >= max_jd and fifth_digit < 4:
                    # 当前节点满级但不是终点，开启下一个节点
                    next_fifth = fifth_digit + 1
                    next_left = f"{series}0{max_layer}0{next_fifth}"
                    # 从cc_dict获取下一个节点的实际进度
                    next_jd = cc_dict.get(next_left, 0)
                    research_targets.append((next_left, next_jd, max_jd, f"左线下一节点(0{next_fifth})"))
                else:
                    # 左线未完成，需要继续研究当前节点
                    if cc_jd < max_jd:
                        research_targets.append((cc_id, cc_jd, max_jd, "左线当前节点"))
            else:
                # 左线不存在，如果分支点完成了就需要开启左线
                if branch_done:
                    next_left = f"{series}0{max_layer}02"
                    next_jd = cc_dict.get(next_left, 0)
                    research_targets.append((next_left, next_jd, 10, "左线起点"))
            
            # 检查右线
            right_done = False
            if right_max_node:
                cc_id, cc_jd, fifth_digit = right_max_node
                # 右线所有节点的最大值都是5
                max_jd = 5
                if fifth_digit == 7 and cc_jd >= 5:
                    # 右线终点完成
                    right_done = True
                else:
                    # 右线未完成，需要继续研究
                    if cc_jd < max_jd:
                        research_targets.append((cc_id, cc_jd, max_jd, "右线"))
            else:
                # 右线不存在，如果分支点完成了或者左线已存在，就需要开启右线
                # 判断条件：分支点完成 或 左线已存在（说明已经过了分支点）
                if branch_done or left_nodes:
                    next_right = f"{series}0{max_layer}05"
                    next_jd = cc_dict.get(next_right, 0)
                    research_targets.append((next_right, next_jd, 5, "右线起点"))
            
            # 如果当前层完成（左右线都完成），可以进入下一层
            if left_done and right_done:
                next_layer = max_layer + 1
                next_branch = f"{series}0{next_layer}01"
                research_targets.append((next_branch, 0, 1, "下一层分支点"))
                print(f"  当前层完成，可进入第{next_layer}层")
        
        print(f"\n<{mask_account(self.account_name)}> 应该研究的传承:")
        for target_id, current_jd, max_jd, desc in research_targets:
            print(f"  {target_id} ({desc}): 当前{current_jd} → 目标{max_jd}")
            req_config = {"ads":"研究传承","times":1,"hexstringheader":"8530","request_body_i2": int(str(target_id)[:1]), "request_body_i3":int(target_id)}
            self.ac_manager.do_common_request(self.account_name,req_config,showres=self.showres)
        
        
        
        return True

    def wddh_info(self):
        req_config = {"ads":"武道大会信息","times":1,"hexstringheader":"2179"}
        rev = self.ac_manager.do_common_request(self.account_name,req_config,showres=self.showres)
        wddh_resp = kpbl_pb2.wddh_response()
        wddh_resp.ParseFromString(rev[6:])
        return wddh_resp

    def wddh_dz(self): # 武道大会点赞
        wddh_resp = self.wddh_info()
        print(wddh_resp.field3.huojiangren)
        for huojiangren in wddh_resp.field3.huojiangren:
            req_config = {"ads":"武道大会点赞","times":1,"hexstringheader":"2b79","request_body_i2":huojiangren.id}
            self.ac_manager.do_common_request(self.account_name,req_config,showres=self.showres)
        return True

    def sbzz_info(self):
        req_config = {"ads":"圣杯战争信息","times":1,"hexstringheader":"4d7a"}
        rev = self.ac_manager.do_common_request(self.account_name,req_config,showres=self.showres)
        sbzz_resp = kpbl_pb2.sbzz_response()
        sbzz_resp.ParseFromString(rev[6:])
        return sbzz_resp

    def sbzz_dz(self): # 圣杯战争点赞
        sbzz_resp = self.sbzz_info()
        targets = []
        seen = set()
        for zone in sbzz_resp.zones:
            zone_id = zone.zone_id
            members = sorted(zone.detail.team.members, key=lambda member: member.slot)
            for member in members:
                player_id = member.player.id
                key = (zone_id, player_id)
                if not zone_id or not player_id or key in seen:
                    continue
                seen.add(key)
                targets.append(key)

        print(f"圣杯战争点赞目标: {targets}")
        if not targets:
            print("圣杯战争点赞目标为空，跳过")
            return False
        if len(targets) != 6:
            print(f"圣杯战争点赞目标数量异常: {len(targets)}，期望 6 个")

        for zone_id, player_id in targets:
            req_config = {"ads":"圣杯战争点赞","times":1,"hexstringheader":"577a","request_body_i2":player_id,"request_body_i3":zone_id}
            self.ac_manager.do_common_request(self.account_name,req_config,showres=self.showres)
        return True



    def wddh_list(self):
        req_config = {"ads":"武道大会列表","times":1,"hexstringheader":"1979"}
        rev = self.ac_manager.do_common_request(self.account_name,req_config,showres=self.showres)
        wddh_resp = kpbl_pb2.wddh_list_response()
        wddh_resp.ParseFromString(rev[6:])
        if not wddh_resp.pvpplayer:
            print("武道大会列表为空")
            return None
        minzhanli = min(wddh_resp.pvpplayer, key=lambda x: x.zhanli)
        print(f"最低战力玩家: {minzhanli.userid} 战力: {minzhanli.zhanli}")
        return minzhanli.userid

    def wddh_battle(self, target):
        req_config = {"ads":"武道大会对战","times":1,"hexstringheader":"1d79","request_body_i2":target}
        rev = self.ac_manager.do_common_request(self.account_name,req_config,showres=self.showres)
        return rev
    
    def wddh_yuxuan(self): #预选
        i = 10
        while i > 0:
            wddh_resp = self.wddh_info()
            print(f"排名积分: {wddh_resp.field3.jf}，排名: {wddh_resp.field3.pm}")
            userid = self.wddh_list()
            if userid:
                self.wddh_battle(userid)
            else:
                return 
            i -= 1
        return 

    def day_first_login(self):
        """每日首次登录请求，从 first_login_requests 模块导入"""

        # for req in FIRST_LOGIN_REQUESTS:
        self.ac_manager.do_common_request_list(self.account_name, FIRST_LOGIN_REQUESTS, showres=self.showres)

    def day_first_login_full(self):
        """每日首次登录请求(完整)，串行执行 FIRST_LOGIN_REQUESTS + FIRST_LOGIN_REQUESTS_PLUS"""
        for req in FIRST_LOGIN_REQUESTS + FIRST_LOGIN_REQUESTS_PLUS:
            self.ac_manager.do_common_request(self.account_name, req, showres=self.showres)

    def day_first_login_lv31(self):
        """31级账号首次登录完整请求，包含教学跳过链路"""
        for req in FIRST_LOGIN_LV31_REQUESTS:
            self.ac_manager.do_common_request(self.account_name, req, showres=self.showres)

    def zn_sell(self):
        req_config = {"ads":"周年庆监控","times":1,"hexstringheader":"eb2e"}
        rev = self.ac_manager.do_common_request(self.account_name,req_config,showres=self.showres)
        zn_resp = kpbl_pb2.zhounian_sell_response()
        zn_resp.ParseFromString(rev[6:])
        for zn_player in zn_resp.zndetail.zn_player:
            print(f"玩家ID: {zn_player.player.player_id}, 出售价格: {zn_player.sell_price}")
            if zn_player.sell_price > 520:
                req_config = {"ads":"周年庆出售","times":1,"hexstringheader":"ef2e","request_body_i2":1, "request_body_i3":zn_player.player.player_id}
                self.ac_manager.do_common_request(self.account_name,req_config,showres=self.showres)

        return True

    def zn_quest(self):
        req_config_list = [
            {"ads":"周年庆任务","times":1,"hexstringheader":"9f2c","request_body_i2":202510274,'request_body_i3':103200},
            {"ads":"周年庆任务","times":1,"hexstringheader":"9f2c","request_body_i2":202510274,'request_body_i3':103211},
            {"ads":"周年庆任务","times":1,"hexstringheader":"9f2c","request_body_i2":202510274,'request_body_i3':103204},
            {"ads":"周年庆任务","times":1,"hexstringheader":"9f2c","request_body_i2":202510274,'request_body_i3':103201},
            {"ads":"周年庆任务","times":1,"hexstringheader":"9f2c","request_body_i2":202510274,'request_body_i3':103210},
        ]
        for req_config in req_config_list:
            self.ac_manager.do_common_request(self.account_name,req_config,showres=self.showres)
        return True

    def zn_get_myprice(self):
        req_config = {"ads":"周年庆监控","times":1,"hexstringheader":"eb2e"}
        rev = self.ac_manager.do_common_request(self.account_name,req_config,showres=self.showres)
        zn_resp = kpbl_pb2.zhounian_sell_response()
        zn_resp.ParseFromString(rev[6:])
        return zn_resp.zndetail.myprice

    def zn_refresh(self):
        times=10
        while times > 0:
            price = self.zn_get_myprice()
            print(f"当前价格: {price}")
            if price > 520:
                
                return True
            times -= 1
            req_config = {"ads":"周年庆刷新","times":1,"hexstringheader":"ed2e"}
            self.ac_manager.do_common_request(self.account_name,req_config,showres=self.showres)
        return False

    def useitem(self, itemid,count=1):
        # 3358412  书箱子
        req_config = {"ads":"使用物品","times":1,"hexstringheader":"db27",
        "request_body_i2":itemid,
        "request_body_i3":count,
        "request_body_i4":-1}
        reslen = len(self.ac_manager.do_common_request(self.account_name,req_config,showres=self.showres))
        return reslen > 20

    def sdgm(self): # shop buy
        req_config = {"ads":"商店购买1次","times":1,"hexstringheader":"a12c","request_body_i2":41,'request_body_i3':3202,'request_body_i4':1}
        rev = self.ac_manager.do_common_request(self.account_name,req_config,showres=self.showres)
        print(rev)
        return len(rev)>20
    
    def kpkpj(self):
        """卡皮卡皮机"""
        i2 = 1002
        while i2 < 1021:
            req_config = {"ads":"卡皮卡皮机","times":1,"hexstringheader":"bd2d","request_body_i2":i2}
            self.ac_manager.do_common_request(self.account_name, req_config, showres=self.showres)
            i2 += 1
        return True


    def ggl(self):
        req = {"ads":"刮刮乐","times":1,"hexstringheader":"6144"}
        rev = self.ac_manager.do_common_request(self.account_name, req, showres=1)
        print(rev)
        ggl_resp = kpbl_pb2.qdggl_sx_response()
        ggl_resp.ParseFromString(rev[6:])
        itemtype={
            '1501':'银铃',
            '1502':'金铃',
        }
        for item in ggl_resp.field3.itemlist:
            if str(item.itemid) in itemtype:
                print(f"刮刮乐刷新: {itemtype[str(item.itemid)]} x {item.itemcount}")

    def get_jsxl_id(self):  # 箭术训练
        """获取竞赛系列动态ID"""
        # 1. 发送552d请求获取活动列表
        req_list = {"ads":"箭术训练","times":1,"hexstringheader":"552d"}
        rev = self.ac_manager.do_common_request(self.account_name, req_list, showres=self.showres)
        if not rev or len(rev) < 6:
            print("获取箭术训练失败")
            return None

        # 2. 解析response，通过entry_bytes特征定位动态ID
        resp = kpbl_pb2.hd_jslx_response()
        resp.ParseFromString(rev[6:])
        target_bytes = b'\xd0\xf0\x01'
        entry_id = None
        for e in resp.rank_entries:
            if e.detail.entry_bytes == target_bytes:
                entry_id = e.detail.entry_id
                break
        if entry_id is None:
            print(f"未找到特征值 {target_bytes.hex()} 对应的条目")
            return None
        print(f"箭术训练ID: {entry_id}")

        # 3. 发送512d请求，i2=20502, i3=动态ID
        rq_list = []
        rq_list.append({"ads":"竞赛系列","times":1,"hexstringheader":"512d","request_body_i2":20502,"request_body_i3":entry_id})
        rq_list.append({"ads":"竞赛系列","times":50,"hexstringheader":"512d","request_body_i2":20509,"request_body_i3":entry_id})
        self.ac_manager.do_common_request_list(self.account_name, rq_list, showres=self.showres)
        return entry_id

    def receive_mail(self):
        """收取邮件奖励（使用独立的邮件REST API，非通用protobuf接口）"""
        import requests as http_requests
        import time as _time

        account = self.ac_manager.get_account(self.account_name)
        if not account:
            print(f"<{mask_account(self.account_name)}> 账户未找到")
            return False

        user_id = str(account.get('charaid', ''))
        if not user_id:
            print(f"<{mask_account(self.account_name)}> 缺少charaid，请先登录")
            return False

        udid = account.get('udid', '')

        # 构建 clientData
        client_data = {
            "protocolVersion": "",
            "appLanguage": "zh-CN",
            "deviceId": udid,
            "appVersion": self.ac_manager.VERSION,
            "osVersion": "iOS 16.1.1",
            "systemLanguage": "ChineseSimplified",
            "appBundle": "com.habby.capybara",
            "deviceModel": "iPhone14,3",
            "os": 1,
            "channelId": 1,
            "openServerTimeStamp": int(_time.time()),
        }

        mail_base_url = "https://prod-mail.habbyservice.com"

        def _mail_headers():
            return {
                "Content-Type": "application/json",
                "X-Unity-Version": "2022.3.62f2",
                "Accept": "*/*",
                "sendtime": str(int(_time.time() * 1000)),
                "sdkversion": "2.0",
                "clientversion": self.ac_manager.VERSION,
                "clientdata": json.dumps(client_data, separators=(',', ':')),
                "User-Agent": "capybara/1 CFNetwork/1399 Darwin/22.1.0",
                "Accept-Language": "zh-CN,zh-Hans;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
            }

        # 1. 获取邮件列表
        list_payload = {
            "userId": user_id,
            "clientData": client_data,
        }
        try:
            resp = http_requests.post(
                f"{mail_base_url}/Capybara/api/v1/mails/list",
                headers=_mail_headers(),
                json=list_payload,
                timeout=10,
            )
            resp_data = resp.json()
        except Exception as e:
            print(f"<{mask_account(self.account_name)}> 获取邮件列表失败: {e}")
            return False

        if resp_data.get("code") != 0:
            print(f"<{mask_account(self.account_name)}> 邮件列表返回异常: {resp_data}")
            return False

        mails = resp_data.get("data", {}).get("mails", [])
        unclaimed = [m for m in mails if not m.get("claimed", True)]

        if not unclaimed:
            print(f"<{mask_account(self.account_name)}> 没有未领取的邮件")
            return True

        # 打印未领取邮件信息
        print(f"<{mask_account(self.account_name)}> 找到 {len(unclaimed)} 封未领取邮件:")
        for m in unclaimed:
            print(f"  📧 {m.get('mailTitle', '无标题')}")

        # 2. 批量领取
        mail_ids = [m["mailId"] for m in unclaimed]
        receive_payload = {
            "mailIds": mail_ids,
            "userId": user_id,
            "clientData": client_data,
        }
        try:
            resp2 = http_requests.post(
                f"{mail_base_url}/Capybara/api/v1/mails/reward/receive",
                headers=_mail_headers(),
                json=receive_payload,
                timeout=10,
            )
            recv_data = resp2.json()
        except Exception as e:
            print(f"<{mask_account(self.account_name)}> 领取邮件失败: {e}")
            return False

        if recv_data.get("code") != 0:
            print(f"<{mask_account(self.account_name)}> 邮件领取返回异常: {recv_data}")
            return False

        rewards = recv_data.get("data", {}).get("rewards", [])
        success_count = sum(1 for r in rewards if r.get("code") == 0)
        print(f"<{mask_account(self.account_name)}> 成功领取 {success_count}/{len(unclaimed)} 封邮件奖励")
        return True

    def claim_activity_ads(self):
        """动态获取活动广告并领取（9d2c获取 → a52c领取）"""
        self.ac_manager.fetch_activity_info(self.account_name)
        adlist = self.ac_manager.get_account(self.account_name, 'adlist') or []
        if not adlist:
            print(f"<{mask_account(self.account_name)}> 没有可领取的活动广告")
            return False
        print(f"<{mask_account(self.account_name)}> 活动广告: {len(adlist)}条")
        for ad in adlist:
            req = {
                "ads": f"活动广告{ad['activity_id']}-{ad['sub_id']}",
                "times": ad['times'],
                "hexstringheader": "a52c",
                "request_body_i2": ad['activity_id'],
                "request_body_i3": ad['sub_id'],
            }
            print(f"<{mask_account(self.account_name)}> {req['ads']} x{ad['times']}")
            self.ac_manager.do_common_request(self.account_name, req, showres=self.showres)
        return True

    def mangheji_gacha(self):
        reqs = [
            {"ads":"盲盒机礼包","hexstringheader":"a52c","times":2,"request_body_i2":202512227,'request_body_i3':3010},
            {"ads":"盲盒机礼包","hexstringheader":"a52c","times":2,"request_body_i2":202512227,'request_body_i3':3020},
        ]
        self.ac_manager.do_common_request_list(self.account_name, reqs, showres=self.showres)

        """盲盒机抽奖"""
        reqs = [
            {"ads": "盲盒机抽奖","times": 1,"hexstringheader": "c92c","request_body_i2": 1,"request_body_i3": 107},
            {"ads": "盲盒机抽奖","times": 1,"hexstringheader": "c92c","request_body_i2": 1,"request_body_i3": 108},
            {"ads": "盲盒机抽奖","times": 1,"hexstringheader": "c92c","request_body_i2": 1,"request_body_i3": 107},
            {"ads": "盲盒机抽奖","times": 1,"hexstringheader": "c92c","request_body_i2": 1,"request_body_i3": 108},
        ]
        for req in reqs:
            res = self.ac_manager.do_common_request(self.account_name, req, showres=self.showres)
            if not res or len(res) <= 20:
                print(f"<{mask_account(self.account_name)}> 盲盒机抽奖无响应")
                # return False
            else:
                from .item_names import ITEM_NAMES
                resp = kpbl_pb2.da_mangheji_gacha_response()
                resp.ParseFromString(res[6:])
                if resp.result and resp.result.items:
                    print(f"<{mask_account(self.account_name)}> 盲盒机获得:")
                    for item in resp.result.items:
                        name = ITEM_NAMES.get(item.itemid, f"type:{item.itemid}")
                        print(f"  {name} x{item.itemcount}")
        return True

    # ── 冒险助手 ──
    MXZS_CLAIM_IDS = list(range(1, 14))

    def mxzs(self):
        """冒险助手：领取奖励(1~13)"""
        an = self.account_name
        for cid in self.MXZS_CLAIM_IDS:
            res = self.ac_manager.do_common_request(an, {"ads": f"冒险助手-{cid}", "hexstringheader": "9b65", "times": 1, "request_body_i2": cid}, showres=self.showres)
            if len(res)<20:
                print(f"<{mask_account(self.account_name)}> 冒险助手-{cid} error")
