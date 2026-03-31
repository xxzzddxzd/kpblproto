"""
异星矿场管理模块
处理游戏中的异星矿场场景玩法
"""

import logging
from .kpbltools import ACManager, mask_account
from . import kpbl_pb2


class YXKCManager:
    """异星矿场管理器"""
    
    def __init__(self, account_name, showres=0, delay=0.5):
        """
        初始化异星矿场管理器
        
        Args:
            account_name: 账户名称
            showres: 是否显示响应，默认0不显示
            delay: 请求延迟，默认0.5秒
        """
        self.account_name = account_name
        self.ac_manager = ACManager(account_name, showres=showres, delay=delay)
        self.showres = showres
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        self.logger = logging.getLogger(f"[yxkc][{mask_account(account_name)}]")
    
    def step(self, stepid):
        """
        执行步骤
        
        Args:
            stepid: 步骤ID
            
        Returns:
            响应数据
            
        Raises:
            Exception: 响应长度小于20时抛出异常
        """
        req_config = {
            "ads": "异星矿场-步骤",
            "times": 1,
            "hexstringheader": "f755",
            "request_body_i2": stepid
        }
        self.logger.info(f"执行步骤: {stepid}")
        response = self.ac_manager.do_common_request(self.account_name, req_config, showres=self.showres)
        if not response or len(response) < 20:
            raise Exception(f"步骤 {stepid} 执行失败，响应长度不足")
        return response
    
    def select_skill(self):
        """
        选择技能
        
        Returns:
            响应数据
            
        Raises:
            Exception: 响应长度小于20时抛出异常
        """
        req_config = {
            "ads": "异星矿场-选择技能",
            "times": 1,
            "hexstringheader": "f955",
            "request_body_i2": "{\"SelectSkillIndex\":0,\"RefreshNum\":0,\"ActionBehavior\":0,\"RoundSelectSkill\":\"3|3\"}",
            "requestbodytype": "request_qh"
        }
        self.logger.info("选择技能")
        response = self.ac_manager.do_common_request(self.account_name, req_config, showres=self.showres)
        if not response or len(response) < 20:
            raise Exception("选择技能失败，响应长度不足")
        return response
    
    def start_battle(self, level):
        """
        开始战斗
        
        Args:
            level: 关卡ID
            
        Returns:
            响应数据
            
        Raises:
            Exception: 响应长度小于20时抛出异常
        """
        req_config = {
            "ads": "异星矿场-开始战斗",
            "times": 1,
            "hexstringheader": "f355",
            "request_body_i2": level
        }
        self.logger.info(f"开始战斗，关卡: {level}")
        response = self.ac_manager.do_common_request(self.account_name, req_config, showres=self.showres)
        if not response or len(response) < 20:
            raise Exception(f"开始战斗失败，关卡 {level}，响应长度不足")
        return response
    
    def finish_battle(self):
        """
        战斗结束
        
        Returns:
            响应数据
            
        Raises:
            Exception: 响应长度小于20时抛出异常
        """
        req_config = {
            "ads": "异星矿场-战斗结束",
            "times": 1,
            "hexstringheader": "f555"
        }
        self.logger.info("战斗结束")
        response = self.ac_manager.do_common_request(self.account_name, req_config, showres=self.showres)
        if not response or len(response) < 20:
            raise Exception("战斗结束失败，响应长度不足")
        return response
    
    def parse_total_step(self, response):
        """
        从start_battle响应中解析总步数
        使用 protobuf 解析，steps 的数量即为 total_step
        
        Args:
            response: start_battle的响应数据
            
        Returns:
            int: 总步数
        """
        if not response or len(response) <= 6:
            return 0
        
        try:
            data = response[6:]  # 跳过前6字节
            battle_resp = kpbl_pb2.yxkc_battle_start_response()
            battle_resp.ParseFromString(data)
            
            total_step = len(battle_resp.info.steps)
            return total_step
        except Exception as e:
            self.logger.error(f"解析总步数失败: {e}")
        
        return 0
    
    def do_battle(self, levelid):
        """
        执行完整战斗流程（单人模式）
        
        Args:
            levelid: 关卡ID
            
        Returns:
            bool: 是否成功
        """
        try:
            self.logger.info(f"开始异星矿场战斗流程，关卡: {levelid}")
            
            # 1. 开始战斗
            res = self.start_battle(levelid)
            
            # 2. 从响应解析总步数
            total_step = self.parse_total_step(res)
            if total_step == 0:
                self.logger.error("解析总步数失败")
                return False
            self.logger.info(f"总步数: {total_step}")
            
            # 3. 循环执行步骤
            nowstep = 0
            while nowstep < total_step:
                nowstep += 1
                self.logger.info(f"执行步骤: {nowstep}/{total_step}")
                self.step(nowstep)
                if nowstep < total_step:  # 最后一个step不选择技能
                    self.select_skill()
            
            # 4. 战斗结束
            self.finish_battle()
            
            self.logger.info("异星矿场战斗流程完成")
            return True
        except Exception as e:
            self.logger.error(f"异星矿场战斗流程失败: {e}")
            return False
