"""
扫荡管理模块
处理游戏中的扫荡功能
"""

import logging
from .kpbltools import ACManager, mask_account


class SDManager:
    """扫荡管理器"""
    
    def __init__(self, account_name):
        self.account_name = account_name
        self.ac_manager = ACManager(account_name)
        self.logger = logging.getLogger(f"SDManager_{account_name}")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.StreamHandler())
        
        # 副本层数上限配置
        self.levelcap = {
            '1': 100,
            '2': 100, 
            '3': 50,
            '4': 100
        }
    
    def saodang(self, dungeonType, level, times):
        """
        执行扫荡功能
        
        Args:
            dungeonType: 副本类型ID
            level: 层数，如果为0则使用默认上限
            times: 扫荡次数
        """
        print(f"<{mask_account(self.account_name)}> 开始执行副本ID {dungeonType}：{level} 的扫荡，次数：{times}")
        
        # 确定实际层数
        actual_level = self.levelcap[str(dungeonType)] if level == 0 else level
        print(f"{dungeonType} {actual_level} {str(self.ac_manager.I8_VALUE)}")
        # 配置扫荡请求参数
        config = {
            "ads": f"扫荡-副本{dungeonType}",
            "times": times,  # 每次请求只发送一次
            "request_body_i2": dungeonType,
            "request_body_i3": actual_level,  # 层数
            "request_body_i4": 1,  
            "request_body_i5": str(self.ac_manager.I8_VALUE),
            "hexstringheader": "9530",
        }
        
        self.ac_manager.do_common_request(self.account_name, config, showres=0)
        print(f"<{mask_account(self.account_name)}> 副本{dungeonType}扫荡完成")
    
    def execute_saodang(self, dungeonType, level=0, times=1):
        """
        执行扫荡的接口方法，与main.py兼容
        
        Args:
            dungeonType: 副本类型ID  
            level: 层数，如果为0则使用默认上限
            times: 扫荡次数
        """
        try:
            self.saodang(dungeonType, level, times)
            return True
        except Exception as e:
            print(f"<{mask_account(self.account_name)}> 扫荡执行失败: {e}")
            return False
    
    def get_level_cap(self, dungeonType):
        """
        获取指定副本类型的层数上限
        
        Args:
            dungeonType: 副本类型ID
            
        Returns:
            int: 层数上限
        """
        return self.levelcap.get(str(dungeonType), 100)
    
    def batch_saodang(self, saodang_list):
        """
        批量执行扫荡
        
        Args:
            saodang_list: 扫荡列表，每个元素是(dungeonType, level, times)元组
        """
        success_count = 0
        total_count = len(saodang_list)
        
        print(f"<{mask_account(self.account_name)}> 开始批量扫荡，共{total_count}个任务")
        
        for i, (dungeonType, level, times) in enumerate(saodang_list, 1):
            print(f"<{mask_account(self.account_name)}> 执行第{i}/{total_count}个扫荡任务")
            
            if self.execute_saodang(dungeonType, level, times):
                success_count += 1
            else:
                print(f"<{mask_account(self.account_name)}> 第{i}个扫荡任务失败")
        
        print(f"<{mask_account(self.account_name)}> 批量扫荡完成，成功: {success_count}/{total_count}")
        return success_count == total_count