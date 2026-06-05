"""
宝石副本组队管理模块
处理游戏中的宝石副本组队功能，监听聊天群组中的组队消息
"""

import json
import time
import logging
import requests
from .kpbltools import ACManager, mask_account
import modules.kpbl_pb2 as kpbl_pb2


class GemTeamManager:
    """宝石副本组队管理器"""
    
    def __init__(self, account_name, showres = 0, level = 0, delay = 0.1, ac_manager=None):
        self.account_name = account_name
        self.ac_manager = ac_manager or ACManager(account_name, delay=delay, showres=showres)
        self.showres = showres
        self.delay = delay
        self.logger = logging.getLogger(f"GemTeamManager_{account_name}")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.StreamHandler())
        
        
        self.level = 350 + level
        self.target_dungeon_id = 14
        # 宝石副本操作配置 - 沿用KN管理器的配置，调整为宝石副本
        self.gem_dungeon_config = {
            "建房": {"hexstringheader": "3f75", "ads": "建房", "times": 1, "request_body_i2": self.level, "request_body_i6": self.target_dungeon_id, "requestbodytype": "request_body_allint"},
            "邀请":{"hexstringheader": "3f75", "ads": "邀请", "times": 1, "requestbodytype": "request_body_for_kn_invite", "request_body_i2": self.level, "request_body_i3": "string:target_user_id","request_body_i5": 1, "request_body_i6": self.target_dungeon_id},
            "关卡信息": {"hexstringheader": "3175", "ads": "关卡信息", "times": 1, "request_body_i2": self.target_dungeon_id},
            # "开始": {"hexstringheader": "3775", "ads": "开始", "times": 1, "request_body_i2": self.target_dungeon_id},
            "开始": {"hexstringheader": "3575", "ads": "开始", "times": 1, "request_body_i2": self.target_dungeon_id, "request_body_i3": 3},
            "加入": {"hexstringheader": "4175", "ads": "加入", "times": 1, "requestbodytype": "request_qh", "request_body_i2": "string:roomid","request_body_i3": self.target_dungeon_id},
            # "关卡信息": {"hexstringheader": "5f33", "ads": "关卡信息", "times": 1},
            "回合": {"hexstringheader": "3d75", "ads": "回合", "times": 1, "request_body_i2": 0, "request_body_i3": self.target_dungeon_id},
            "结算": {"hexstringheader": "3975", "ads": "结算", "times": 1, "request_body_i2": self.target_dungeon_id},
            "检查":{"hexstringheader": "3375", "ads": "检查", "times": 1, "request_body_i2": self.target_dungeon_id},
            "放弃":{"hexstringheader": "3975", "ads": "放弃", "times": 1, "request_body_i2": self.target_dungeon_id},
        }
        
        # 副本状态
        self.current_level = 0
        self.current_step = 0
    
    
    def join(self, roomid):
        # self.ac_manager.do_common_request(self.account_name,self.request_config["放弃"],showres=self.showres)
        request_config = self.gem_dungeon_config["加入"]
        request_config["request_body_i2"] = f"{str(roomid)}"
        # print(request_config)
        return len(self.ac_manager.do_common_request(self.account_name,request_config,showres=self.showres)) > 20
        # print(self.get_gqxx())


    def start(self):
        request_config = self.gem_dungeon_config["开始"]
        self.ac_manager.do_common_request(self.account_name,request_config,showres=self.showres)    

    def get_total_step(self):
        res = self.ac_manager.do_common_request(self.account_name,self.gem_dungeon_config['关卡信息'],showres=self.showres)
        gqxx_resp = kpbl_pb2.kn_gqxx_response()
        gqxx_resp.ParseFromString(res[6:])
        return len(gqxx_resp.gqinfo.steps)
    
    def update_step_and_check(self, step):
        request_config = self.gem_dungeon_config['回合']
        request_config['request_body_i2'] = int(step)
        self.ac_manager.do_common_request(self.account_name,request_config,showres=self.showres)
        # res = self.ac_manager.do_common_request(self.account_name,self.gem_dungeon_config['关卡信息'],showres=self.showres)
        # check_resp = kpbl_pb2.kn_round_check_response()
        # check_resp.ParseFromString(res[6:])
        # print(check_resp)
        # waveindex0 = json.loads( check_resp.bi.players[0].detail)['WaveIndex']
        # waveindex1 = json.loads( check_resp.bi.players[1].detail)['WaveIndex']
        # # print(f"waveindex0:{waveindex0}, waveindex1:{waveindex1}")
        # self.level = check_resp.bi.level
        # return waveindex0, waveindex1
    
    def finish_battle(self):
        self.gem_dungeon_config['结算']['request_body_i2'] = self.level
        self.ac_manager.do_common_request(self.account_name,self.gem_dungeon_config['结算'],showres=self.showres)
 
    def fangqi_battle(self): # 放弃战斗
        self.ac_manager.do_common_request(self.account_name,self.gem_dungeon_config['放弃'],showres=self.showres)
 

    def get_gqxx(self):
        res = self.ac_manager.do_common_request(self.account_name,self.gem_dungeon_config['关卡信息'],showres=self.showres)
        gqxx_resp = kpbl_pb2.kn_gqxx_response()
        gqxx_resp.ParseFromString(res[6:])
        return gqxx_resp
        
        
    def get_ac_mask(self):
        return mask_account(self.account_name)
    
    def create_and_invite(self, target_user, usedefinelevel = 1):
        # self.ac_manager.do_common_request(self.account_name,self.request_config["放弃"],showres=self.showres)

        # inp = input(f"当前等级{self.level}，输入等级或当前等级+1？(num/enter=+1)")
        # if inp == "":
        #     self.level += 1
        # else:
        #     self.level = int(inp)
        if usedefinelevel:
            self.level = 350 + usedefinelevel
        # else:
        #     self.level = 1
        print(f"[{self.get_ac_mask()}] target level:{self.level}")
        request_config = self.gem_dungeon_config["建房"]
        request_config["request_body_i2"] = self.level
        request_config["request_body_i6"] = self.target_dungeon_id
        # print(request_config)
        res = self.ac_manager.do_common_request(self.account_name,request_config,showres=self.showres)
        if len(res) < 16:
            print(f"[{self.get_ac_mask()}] 建房失败")
            return None
        create_resp = kpbl_pb2.kn_create_response()
        create_resp.ParseFromString(res[6:])
        # print(create_resp.rd.roomid)
        # input(f"点击邀请 ")
        self.invite(int(target_user))
        # print(self.get_gqxx())
        print(f"[{self.get_ac_mask()}] 建房成功，房间ID: {create_resp.rd.roomid}")
        return create_resp.rd.roomid


    def invite(self, target_user_id):
        request_config = self.gem_dungeon_config["邀请"]
        request_config["request_body_i2"] = self.level
        request_config["request_body_i3"] = target_user_id
        # print(request_config)
        rev = self.ac_manager.do_common_request(self.account_name,request_config,showres=self.showres)


def run_gem_auto2(account_name_a, account_name_b="default", level=1, times=10, showres=0, delay=0, ac_manager_a=None, ac_manager_b=None):
    """房主不放弃的宝石副本自动双人流程，等价于 glauto2。"""
    times = int(times)
    level = int(level)
    if times <= 0:
        return True

    gm_a = GemTeamManager(account_name_a, level=level, showres=showres, delay=delay, ac_manager=ac_manager_a)
    gm_b = GemTeamManager(account_name_b, level=level, showres=showres, delay=delay, ac_manager=ac_manager_b)
    target_charaid = gm_b.ac_manager.get_account(account_name_b, "charaid")

    for idx in range(1, times + 1):
        print(f"times:{idx}/{times}")
        gm_a.fangqi_battle()
        gm_b.fangqi_battle()
        roomid = gm_a.create_and_invite(target_charaid, level)
        if not roomid:
            return False
        if not gm_b.join(roomid):
            return False

        time.sleep(1)
        gm_a.start()
        time.sleep(1)
        gm_b.start()

        nowstep = 0
        while nowstep < 4:
            print(f"step:{nowstep}")
            nowstep += 1
            gm_b.update_step_and_check(nowstep)
            gm_a.update_step_and_check(nowstep)
        gm_a.finish_battle()
        gm_b.finish_battle()
    return True
