"""
深渊管理模块
处理深渊挑战相关功能
"""

import logging
import time
import random
from .kpbltools import mask_account, ACManager
from .configs import sy_item_dict, sy_target_dict, sy_level_dict
from . import kpbl_pb2
import json
import sys


class ShenyuanManager:
    def __init__(self, account_name, minrare=7, level=51, bio=1):
        self.account_name = account_name
        self.ac_manager = ACManager(account_name)
        self.turn = 0
        self.showres = 0
        self.minrare = minrare
        self.level = level
        self.bio = bio
        # 创建logger
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        self.logger = logging.getLogger(f"[sy][{mask_account(account_name)}]")
        
    def select_skill_4b51(self, skilllist):  # skilllist = [[charalev, skill_pos], [charalev, skill_pos], ...]
        for skill in skilllist:
            # 创建syskill对象
            syskill_obj = kpbl_pb2.syskill()
            syskill_obj.i1 = skill[0]  # charalev
            syskill_obj.i2.i1 = skill[1]  # skill_pos
            req_config_skill = {"ads": "sy-select_skill_4b51","hexstringheader": "4b51", "request_body_i4": syskill_obj.SerializeToString(),"requestbodytype": "request_body_for_sy_skill"}
            # print(f"<{mask_account(self.account_name)}> 深渊-选择技能-4b51: {req_config_skill}")
            self.ac_manager.do_common_request(self.account_name, req_config_skill, showres=self.showres)

    def fight_4951(self, level, levelid, wave, MonsterCfgId, BefExpLv, BefExp):
        req_config_3 = {"ads": "sy-fight_4951","hexstringheader": "4951",
        "request_body_i2": "{\"DungeonId\":"+str(level)+",\"LevelId\":"+str(levelid)+",\"WaveIndex\":"+str(wave)+",\"LogId\":\"\",\"LogData\":\"\",\"BefPlayerHp\":1440473816,\"BefMountHp\":[648213217,576189527,648213217],\"BefRevive\":0,\"AftPlayerHp\":0,\"AftMountHp\":[],\"AftRevive\":0,\"Round\":0,\"BefLifeGazeRevive\":0,\"AftLifeGazeRevive\":0,\"MonsterCfgId\":"+str(MonsterCfgId)+",\"BefExpLv\":"+str(BefExpLv)+",\"AftExpLv\":0,\"BefExp\":"+str(BefExp)+",\"AftExp\":0,\"Seed\":0,\"ClientVersion\":\"750\",\"MaxChapterId\":164,\"TotalDropExp\":0,\"TotalWave\":0,\"CanUseRound\":0}", 'requestbodytype':'request_qh'}
        res = self.ac_manager.do_common_request(self.account_name, req_config_3, showres=self.showres)
        battleresult = kpbl_pb2.response_for_sy_battle()
        battleresult.ParseFromString(res[6:])

        return battleresult

    def select_levelid_4751(self, levelid):
        req_config_select_levelid = {"ads": "sy-select_levelid_4751","hexstringheader": "4751","request_body_i2": levelid}
        res = self.ac_manager.do_common_request(self.account_name, req_config_select_levelid, showres=self.showres)
        selectresult = kpbl_pb2.response_for_sy_selectlevelid()
        selectresult.ParseFromString(res[6:])
        return selectresult

    def abort_5551(self):
        req_config_abort = {"ads": "sy-abort_5551","hexstringheader": "5551"}
        self.ac_manager.do_common_request(self.account_name, req_config_abort, showres=self.showres)

    def enter_4351(self):
        req_config_shenyuan = {"ads": "sy-enter_4351","hexstringheader": "4351","request_body_i2": self.level, "request_body_i3": self.bio}
        resbin = self.ac_manager.do_common_request(self.account_name, req_config_shenyuan, showres=self.showres)
        response_for_sy_enter = kpbl_pb2.response_for_sy_enter()
        response_for_sy_enter.ParseFromString(resbin[6:])
        levelidlist = []
        for levelid in response_for_sy_enter.levelid:
            levelidlist.append(levelid)
        return levelidlist

    def get_levelid_4d51(self):
        req_config_get_levelid = {"ads": "sy-get_levelid_4d51","hexstringheader": "4d51"}
        resbin = self.ac_manager.do_common_request(self.account_name, req_config_get_levelid, showres=self.showres)
        if not resbin:
            return None
        response_for_sy_enter = kpbl_pb2.response_for_sy_enter()
        response_for_sy_enter.ParseFromString(resbin[6:])
        levelidlist = []
        for levelid in response_for_sy_enter.levelid:
            levelidlist.append(levelid)
        return levelidlist

    def istargetdrop(self, drops, target_rare, target_itemid, turn):
        if drops:
            for drop in drops:
                if drop.itemid in sy_item_dict and drop.itemid!=117:
                    # self.logger.info(f"turn:{turn} [{drop.itemid}] {sy_item_dict.get(drop.itemid)}: {drop.itemcount}")
                
                    # 检查itemid的第三位是否为6
                    itemid_str = str(drop.itemid)
                    if itemid_str[2] in target_rare or drop.itemid in target_itemid:
                        # self.logger.warning(f"turn:{turn} 🚨 发现第三位为{target_rare}的物品: [{drop.itemid}]{itemid_str}")
                        return True
        return False

    def final_drop(self, drops):
        self.logger.info(f"turn:{self.turn} FINAL DROP:")
        if drops:
            for drop in drops:
                # if drop.itemid in sy_item_dict:
                if drop.itemid!=117 and  drop.itemid in sy_item_dict:
                    self.logger.info(f"[{drop.itemid}] {sy_item_dict.get(drop.itemid)}: {drop.itemcount}")
                    
    def level_have_box(self, levelid):
        if 'box' in sy_level_dict.get(levelid, ''):
            return True
        return False

    def do_select_level(self, levelidlist):
        if len(levelidlist) == 1:
            return levelidlist[0]
        # 有box 选box
        for levelid in levelidlist:
            if 'box' in sy_level_dict.get(levelid, ''):
                return levelid
        
        have1or2=0
        # 没有box 且第一位为3或4，返回第一个
        for levelid in levelidlist:
            if str(levelid)[0] in ['1','2','3']:
                have1or2+=1
        if have1or2==0:
            return levelidlist[0]

        levelid_options = ""
        for i, level_id in enumerate(levelidlist, 1):
            levelid_options += f"\n{i}.{level_id}: {sy_level_dict.get(level_id, f'unknown level ({level_id})')} "
            # print(f"<{mask_account(self.account_name)}> sy-levelid: {i}.{level_id}: {sy_level_dict.get(level_id, f'unknown level ({level_id})')}")
            
        # 如果没有box且没有unknown，返回第一个
        if 'box' not in levelid_options and 'unknown' not in levelid_options:
            return levelidlist[0]
        return levelidlist[0]

    def doshenyuan(self):
        self.turn = 0
        # 根据输入构建目标物品ID过滤列表
        target_rare = [str(self.minrare)]  # 默认值
        target_itemid = []
        self.logger.info(f'prepare target rare: {target_rare}, target itemid:')
        for itemid in sy_target_dict:
            if itemid not in self.ac_manager.get_account(self.account_name, 'baoshi'):
                target_itemid.append(itemid)
                self.logger.info(f'[-] 未有 {itemid} : {sy_item_dict.get(itemid, f"unknown item ({itemid})")}')
            else:
                self.logger.info(f'[√] 已有 {itemid} : {sy_item_dict.get(itemid, f"unknown item ({itemid})")} ')
        if self.minrare:
            try:
                min_rare = int(self.minrare)
                target_rare = [str(i) for i in range(min_rare, 8)]  # 包含从输入值到6的所有级别
            except ValueError:
                self.logger.error(f"输入无效，使用默认值6")
        self.logger.info(f"稀有度: {target_rare}")
        self.logger.info(f"层数: {self.level}")
        self.logger.info(f"倍数: {self.bio}")
        while True:
            self.turn += 1
            sys.stdout.write(f"\rlevel: {self.level} - now try: {self.turn}   ")
            sys.stdout.flush()
            # self.logger.info(f"sy-turn {self.turn}")
            
            self.abort_5551()
            levelidlist = self.enter_4351()
            
            BefExpLv = 1
            BefExp = 0
            drops = None
            done = False
            while not done:
                if len(levelidlist) == 1:
                    done = True
                    if not self.istargetdrop(drops, target_rare, target_itemid, self.turn):
                        break
                    else:
                        self.logger.info("final step go")
                
                levelid = self.do_select_level(levelidlist)
                if not self.level_have_box(levelid) and not self.istargetdrop(drops, target_rare, target_itemid, self.turn):
                    done = True
                    break
                selectresult = self.select_levelid_4751(levelid)
                monsterlist = [monster.monid for monster in selectresult.linfo.monsters]
                if selectresult.linfo.boss and selectresult.linfo.boss.monid and selectresult.linfo.boss.monid!=0:
                    monsterlist.append(selectresult.linfo.boss.monid)
                
                wave=0
                for monsterid in monsterlist:
                    try:
                        battleresult = self.fight_4951(self.level, levelid=levelid, wave=wave, MonsterCfgId=monsterid, BefExpLv=BefExpLv, BefExp=BefExp)
                        AftExpLv = json.loads(battleresult.battleinfo)['AftExpLv']
                        BefExp = json.loads(battleresult.battleinfo)['AftExp']
                        while AftExpLv > BefExpLv:
                            BefExpLv+=1
                            self.select_skill_4b51([[BefExpLv, 3]])
                        wave += 1
                        drops = battleresult.drops
                    except Exception as e:
                        self.logger.error(f"战斗出错: {e}")
                        break
                
                if not done:
                    levelidlist = self.get_levelid_4d51()
                    if not levelidlist:
                        self.logger.warning(f"turn:{self.turn} maybe battle failed")
                        break
                else:
                    self.final_drop(drops)
                    self.logger.info(f"trun:{self.turn} finish")
                    break