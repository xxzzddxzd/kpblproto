import logging
import binascii
import json
from . import kpbl_pb2
from .kpbltools import ACManager, mask_account

class KNManager:
#  困难本

    level = 111
    nowstep = 0
    request_config = {
        "放弃":{"hexstringheader": "7133", "ads": "放弃", "times": 1},
        "检查":{"hexstringheader": "6133", "ads": "检查", "times": 1},
        "建房":{"hexstringheader": "6333", "ads": "建房", "times": 1, "request_body_i2": level,},
        "邀请":{"hexstringheader": "6333", "ads": "邀请", "times": 1, "requestbodytype": "request_body_for_kn_invite", "request_body_i2": level, "request_body_i3": "string:target_user_id","request_body_i5": 1},
        # "737d":{"hexstringheader": "737d", "ads": "737d", "times": 1},
        "选择关卡":{"hexstringheader": "7d33", "ads": "选择关卡", "times": 1, "request_body_i2": level,},
        
        "开始":{"hexstringheader": "6d33", "ads": "开始", "times": 1, "request_body_i2": 3, "request_body_i3": 1},
        "关卡信息":{"hexstringheader": "5f33", "ads": "关卡信息", "times": 1},
        "动作":{"hexstringheader": "7333", "ads": "动作", "times": 1, "request_body_i2":  "{\"SelectSkillIndex\":0,\"RefreshNum\":0,\"ActionBehavior\":0,\"RoundSelectSkill\":\"2\"}",},
        # SelectSkillIndex 战斗后技能
        # ActionBehavior  宝箱技能
        # RoundSelectSkill 战斗前技能
        # 选择技能 {"1,3|1,2"}
        "回合":{"hexstringheader": "7533", "ads": "回合", "times": 1, "request_body_i2": nowstep,},

        "结算":{"hexstringheader": "7133", "ads": "结算", "times": 1, "request_body_i2": level,},

        "每周统计":{"hexstringheader": "7b33", "ads": "每周统计", "times": 1},

        "加入":{"hexstringheader": "6533", "ads": "加入", "times": 1, "request_body_i2": "string:roomid", "request_body_i3": 1, 'requestbodytype': 'request_qh'},

    }

    def get_ac_mask(self):
        return mask_account(self.account_name)

    def __init__(self, account_name, isFangZhu = False, showres = 0):
        self.ac_manager = ACManager(account_name)
        self.I8_VALUE = self.ac_manager.I8_VALUE
        self.account_name = account_name
        self.level = self.ac_manager.get_account(self.account_name, 'kunnan')
        self.showres = showres

    def create_and_invite(self, target_user, usedefinelevel = 0):
        self.ac_manager.do_common_request(self.account_name,self.request_config["放弃"],showres=self.showres)

        # inp = input(f"当前等级{self.level}，输入等级或当前等级+1？(num/enter=+1)")
        # if inp == "":
        #     self.level += 1
        # else:
        #     self.level = int(inp)
        if usedefinelevel:
            self.level = usedefinelevel
        # else:
        #     self.level = 1
        print(f"[{self.get_ac_mask()}] target level:{self.level}")
        request_config = self.request_config["建房"]
        request_config["request_body_i2"] = self.level
        # print(request_config)
        res = self.ac_manager.do_common_request(self.account_name,request_config,showres=self.showres)
        create_resp = kpbl_pb2.kn_create_response()
        create_resp.ParseFromString(res[6:])
        # print(create_resp.rd.roomid)
        # input(f"点击邀请 ")
        self.invite(int(target_user))
        # print(self.get_gqxx())
        return create_resp.rd.roomid

    def create_solo(self, usedefinelevel=0):
        """单人建房，不邀请队友"""
        self.ac_manager.do_common_request(self.account_name,self.request_config["放弃"],showres=self.showres)
        if usedefinelevel:
            self.level = usedefinelevel
        print(f"[{self.get_ac_mask()}] solo target level:{self.level}")
        request_config = self.request_config["建房"]
        request_config["request_body_i2"] = self.level
        res = self.ac_manager.do_common_request(self.account_name,request_config,showres=self.showres)
        create_resp = kpbl_pb2.kn_create_response()
        create_resp.ParseFromString(res[6:])
        return create_resp.rd.roomid


    def invite(self, target_user_id):
        request_config = self.request_config["邀请"]
        request_config["request_body_i2"] = self.level
        request_config["request_body_i3"] = target_user_id
        # print(request_config)
        self.ac_manager.do_common_request(self.account_name,request_config,showres=self.showres)

    def start(self, bio=1):
        request_config = self.request_config["开始"]
        request_config["request_body_i3"] = bio
        self.ac_manager.do_common_request(self.account_name,request_config,showres=self.showres)
        # print(self.get_gqxx())
        
    def join(self, roomid):
        self.ac_manager.do_common_request(self.account_name,self.request_config["放弃"],showres=self.showres)
        request_config = self.request_config["加入"]
        request_config["request_body_i2"] = f"{str(roomid)}"
        self.ac_manager.do_common_request(self.account_name,request_config,showres=self.showres)
        # print(self.get_gqxx())


    def get_gqxx(self):
        res = self.ac_manager.do_common_request(self.account_name,self.request_config['关卡信息'],showres=self.showres)
        gqxx_resp = kpbl_pb2.kn_gqxx_response()
        gqxx_resp.ParseFromString(res[6:])
        return gqxx_resp

    def update_battle_round(self):
        totalstep = self.get_total_step()
        while self.nowstep < totalstep:
            self.nowstep += 1
            step = input(f"[{self.get_ac_mask()}] 输入步骤，回车使用nowstep:{self.nowstep}/{totalstep}")
            if step == "":
                step = self.nowstep
            self.update_step_and_check(step)
    
    def finish_battle(self):
        self.request_config['结算']['request_body_i2'] = self.level
        self.ac_manager.do_common_request(self.account_name,self.request_config['结算'],showres=self.showres)
        
            

    def update_step_and_check(self, step):
        self.request_config['回合']['request_body_i2'] = int(step)
        self.ac_manager.do_common_request(self.account_name,self.request_config['回合'],showres=self.showres)
        res = self.ac_manager.do_common_request(self.account_name,self.request_config['检查'],showres=self.showres)
        check_resp = kpbl_pb2.kn_round_check_response()
        check_resp.ParseFromString(res[6:])
        waveindex0 = json.loads( check_resp.bi.players[0].detail)['WaveIndex']
        waveindex1 = json.loads( check_resp.bi.players[1].detail)['WaveIndex'] if len(check_resp.bi.players) > 1 else None
        # print(f"waveindex0:{waveindex0}, waveindex1:{waveindex1}")
        self.level = check_resp.bi.level
        return waveindex0, waveindex1

    def get_total_step(self):
        res = self.ac_manager.do_common_request(self.account_name,self.request_config['关卡信息'],showres=self.showres)
        gqxx_resp = kpbl_pb2.kn_gqxx_response()
        gqxx_resp.ParseFromString(res[6:])
        return len(gqxx_resp.gqinfo.steps)
    
    def get_weekly_stat(self, target_level):
        res = self.ac_manager.do_common_request(self.account_name,self.request_config['每周统计'],showres=self.showres)
        weekly_stat_resp = kpbl_pb2.kn_weekly_stat_response()
        weekly_stat_resp.ParseFromString(res[6:])
        total = 0
        target_level_cap = 500 +  int(target_level/10)*100
        target_level_count = 0
        for gq in weekly_stat_resp.gqs:
            total += gq.count
            if gq.level == target_level:
                target_level_count = gq.count
        print(f"<{self.get_ac_mask()}> total:{total}, target_level_cap:{target_level_cap}, target_level_count:{target_level_count}")
        return total, target_level_cap, target_level_count