"""
种花管理模块
处理种花相关功能
"""

import logging
import time
import threading
from .kpbltools import ACManager, mask_account
from . import kpbl_pb2
from tqdm import tqdm
import binascii
class ZHManager:
    """
    种花 种蛋活动
    """
    def __init__(self, account_name, showres=0):
        self.account_name = account_name
        self.ac_manager = ACManager(account_name)
        self.logger = logging.getLogger(f"ZHManager{account_name}")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.StreamHandler())
        self.showres = showres

        self.threshold_for_sell_all = 0.99
        self.threshold_for_sell_once = 0.96
        self.showres = showres
        # 创建logger
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        self.logger = logging.getLogger(f"[zh][{mask_account(account_name)}]")
        
        # 定义植物类型的最高价值字典
        self.topvalue_dict = {
            3111: 225,
            3112: 225,
            3113: 675,
            3114: 675,
            3115: 135,
            3116: 405,
            3011: 225,
            3012: 225,
            3013: 675,
            3014: 675,
            3015: 135,
            3016: 405,
        }
        
    def sell(self, plant_type, memid, count=1):
        """
        执行卖出操作
        
        Args:
            plant_type: 植物类型
            count: 数量
            memid: 会员ID
        """
        if memid == -1:
            request_body = {"ads": "卖出-self","times": 1,"hexstringheader": "6334", "request_body_i2": plant_type, "request_body_i3": count}
        else:
            request_body = {"ads": "卖出-guildmember","times": 1,"hexstringheader": "6334", "request_body_i2": plant_type, "request_body_i3": count, "request_body_i4": memid}
        
        return self.ac_manager.do_common_request(self.account_name, request_body, showres=self.showres)
    
    def show_sell_result(self, rev):
        """
        显示卖出结果
        """
        rev_length = len(rev) if rev else 0
        
        # 当返回值长度小于20时，认为已经卖出成功或没有更多可卖出的植物
        if rev_length < 20:
            self.logger.info("<20, finish")
            return True
        else:
            self.logger.info(">20, sell done")
            return False
    
    def do_shouhuo_and_plant(self):
        """
        执行收货功能和种植功能，从01到10(十六进制)循环执行
        """
        self.logger.info("开始执行收货和种植操作...")
        
        # 十六进制序列: 01, 02, 03, 04, 05, 06, 07, 08, 09, 0a, 0b, 0c, 0d, 0e, 0f, 10
        hex_values = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '0a', '0b', '0c', '0d', '0e', '0f', '10']
        
        # 构建所有收货请求
        shouhuo_configs = []
        zhongzhi_configs = []
        for hex_value in hex_values:
            binary_field_id = binascii.unhexlify(hex_value)
            shouhuo_configs.append({"ads": f"收货-{hex_value}","times": 1,"hexstringheader": "5f34", "request_body_i2": binary_field_id, "requestbodytype":"request_sh"})
            zhongzhi_configs.append({"ads": f"种花-{hex_value}","times": 1,"hexstringheader": "5b34", "request_body_i2": binary_field_id, "request_body_i3": 3000, "requestbodytype":"request_zz"})

        # 一次性完成所有收货
        self.logger.info("批量收货...")
        self.ac_manager.do_common_request_list(self.account_name, shouhuo_configs, showres=self.showres)

        # 一次性完成所有种植
        self.logger.info("批量种植...")
        self.ac_manager.do_common_request_list(self.account_name, zhongzhi_configs, showres=self.showres)

        self.logger.info("收货和种植操作完成")
        return True
    
    def hd_zhonghua_sell(self):
        """
        活动种花功能：执行run hdzh命令获取数据，然后按照dec.py中的逻辑找出推荐卖出的植物
        """
        self.logger.info(f"current threshold for sell all: {self.threshold_for_sell_all}, once: {self.threshold_for_sell_once}")
        
        # 执行run hdzh命令获取数据
        config_get_price = {"ads": "price","times": 1,"hexstringheader": "6734", "savetofile":"proto_hd_zhonghua", "tag":"hdzh"}
        res = self.ac_manager.do_common_request(self.account_name, config_get_price, showres=self.showres)
        
        if not res:
            self.logger.warning("cannot get game data, skip")
            return
        
        data = res
        # 跳过前8个字节
        if len(data) > 0:
            data = data[6:]
            
            # 使用plant_response解析数据
            plant_resp = kpbl_pb2.plant_response()
            plant_resp.ParseFromString(data)
            
            # 打印解析结果
            self.logger.info("-" * 40)
            
            # 创建一个字典来跟踪每种植物类型的最高价格
            highest_plants = {}  # 格式: {plant_type: (plant, source)}
            
            # 处理个人植物信息
            for plant in plant_resp.myplant:
                plant_type = plant.planttype
                if (plant_type not in highest_plants or 
                    plant.plantprice > highest_plants[plant_type][0].plantprice):
                    highest_plants[plant_type] = (plant, "self")
            
            # 处理公会植物信息
            for guild_plant in plant_resp.guildplant:
                for plant in guild_plant.myplant:
                    plant_type = plant.planttype
                    if (plant_type not in highest_plants or 
                        plant.plantprice > highest_plants[plant_type][0].plantprice):
                        # 使用实际的会员ID作为来源，但进行脱敏
                        member_id = guild_plant.field1.memid if hasattr(guild_plant, 'field1') and hasattr(guild_plant.field1, 'memid') else "unknown id"
                        highest_plants[plant_type] = (plant, f"guild member:{member_id}")
            
            # 打印所有类型中的最高价格植物，并标识推荐卖出的植物
            self.logger.info("all plant info (each type highest price):")
            
            for plant_type, (plant, source) in highest_plants.items():
                if plant_type not in self.topvalue_dict:
                    self.logger.warning(f"未知植物类型 {plant_type}，跳过")
                    continue
                # 计算价格比例
                price_ratio = plant.plantprice / self.topvalue_dict[plant_type]
                
                # 添加高价值提示
                sell_mark = ""
                if price_ratio >= self.threshold_for_sell_once:
                    sell_mark = "【recommend sell】"
                baginfo = self.ac_manager.get_account(self.account_name,attribute_name='baginfo')
                if plant_type in baginfo:
                    plantcount = baginfo[plant_type]
                else:
                    plantcount = 0
                self.logger.info(f"{plant_type}({plantcount}), P: {plant.plantprice}/{self.topvalue_dict[plant_type]}({price_ratio*100:.1f}%), {source} {sell_mark}")
                
                # 如果价格比例达到阈值，直接执行卖出操作
                if price_ratio >= self.threshold_for_sell_once:
                    # 从来源字符串提取会员ID
                    memid = 0  # 默认值
                    if source == "self":
                        memid = -1
                    elif "guild member:" in source:
                        try:
                            # 从已脱敏的字符串中获取原始ID需要特殊处理
                            if "unknown id" in source:
                                memid = 0
                            else:
                                # 从guild_plant中重新获取会员ID
                                for guild_plant in plant_resp.guildplant:
                                    for p in guild_plant.myplant:
                                        if p.planttype == plant_type and p.plantprice == plant.plantprice:
                                            memid = guild_plant.field1.memid
                                            break
                        except:
                            memid = 0
                    
                    # 执行卖出操作
                    if price_ratio >= self.threshold_for_sell_all:  # 价格比例大于等于阈值时循环卖出
                        self.logger.info(f"auto sell high value plant type {plant_type} (price ratio: {price_ratio*100:.1f}%)...")
                        attempt = 1
                        while True:
                            try:
                                self.logger.info(f"attempt #{attempt}: sell plant type {plant_type}...")
                                rev = self.sell(plant_type, memid)
                                if self.show_sell_result(rev):
                                    break
                                attempt += 1
                                # 防止无限循环，设置最大尝试次数
                                if attempt > 30:
                                    self.logger.warning(f"reach max attempt times, stop sell plant type {plant_type}")
                                    break
                            except Exception as e:
                                self.logger.error(f"卖出过程中出错: {str(e)}")
                                break
                    elif price_ratio >= self.threshold_for_sell_once:
                        # 普通推荐卖出（90%-99%之间的价格）只卖出一次
                        try:
                            self.logger.info(f"auto sell plant type {plant_type} (price ratio: {price_ratio*100:.1f}%)...")
                            rev = self.sell(plant_type, memid)
                            self.show_sell_result(rev)
                        except Exception as e:
                            self.logger.error(f"卖出过程中出错: {str(e)}")
            
            self.logger.info("-" * 40)
    
    def auto_monitor(self, interval_minutes=15):
        """
        自动执行活动种花功能：每指定分钟执行一次hd_zhonghua_sell
        
        Args:
            interval_minutes: 间隔分钟数，默认15分钟
        """
        self.logger.info(f"start auto hdzh monitor, check every {interval_minutes} minutes (Ctrl+C to exit)...")
        timesleep = 60 * interval_minutes
        
        while True:
            self.logger.info(f" execute hdzh monitor...")
            self.ac_manager.login(self.account_name)
            self.do_shouhuo_and_plant()
            self.hd_zhonghua_sell()

            # 显示下次执行时间
            next_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + timesleep))
            self.logger.info(f"all processing complete, next execute time: {next_time}, waiting...")
            
            # 等待指定的时间
            time.sleep(timesleep)
