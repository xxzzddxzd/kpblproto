import json
import binascii
import requests
import hashlib
import time
import os
import sys
import re
import random
from tqdm import tqdm
from . import kpbl_pb2

# 彩色终端输出
class Colors:
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    PURPLE = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    PINK = '\033[95m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'
    
    @staticmethod
    def colorize(text, color):
        """用指定颜色包装文本"""
        return f"{color}{text}{Colors.RESET}"
    
    @staticmethod
    def sss(text="SSS"):
        """将SSS标记为彩色"""
        return Colors.colorize(text, Colors.BRIGHT_MAGENTA + Colors.BOLD)

# 基础工具函数
def mask_sensitive_info(info, keep_start=2, keep_end=2):
    """
    对敏感信息进行脱敏处理
    
    Args:
        info: 待脱敏的信息
        keep_start: 保留开头的字符数
        keep_end: 保留结尾的字符数
    
    Returns:
        脱敏后的信息
    """
    if not info or not isinstance(info, str):
        return str(info)
    
    info_str = str(info)
    info_len = len(info_str)
    
    if info_len <= keep_start + keep_end:
        return info_str
    
    masked_part = '*' * (info_len - keep_start - keep_end)
    return info_str[:keep_start] + masked_part + info_str[-keep_end:]


def mask_account(account_name):
    """脱敏账号名称"""
    return mask_sensitive_info(account_name, 2, 1)


def fixdata(data):
    """
    将非标准格式的JSON字符串（如游戏数据）转换为标准JSON并解析
    
    Args:
        data: 需要转换的数据字符串
        
    Returns:
        转换后的Python字典对象
    """
    # 移除前后可能的引号和多余空格
    data = data.strip()
    if data.startswith("'") and data.endswith("'"):
        data = data[1:-1].strip()
    elif data.startswith('"') and data.endswith('"'):
        data = data[1:-1].strip()
    
    # 将数据转换为有效的JSON格式
    # 1. 处理键值对，为键名添加双引号
    
    # 匹配键名并添加双引号
    data = re.sub(r'([a-zA-Z0-9_]+)(\s*:)', r'"\1"\2', data)
    
    # 2. 处理字符串值，确保使用双引号
    # 寻找未用引号包裹的值（如True、False、字符串等）
    data = re.sub(r':\s*(True|False)', lambda m: ': ' + m.group(1).lower(), data)
    data = re.sub(r':\s*([a-zA-Z][a-zA-Z0-9_]*)', r': "\1"', data)
    
    # 3. 处理花括号和方括号的格式
    data = data.replace("'", '"')  # 将所有单引号替换为双引号
    
    try:
        # 尝试解析JSON
        parsed_data = json.loads(data)
        return parsed_data
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        print(f"转换后的数据: {data}")
        # 返回原始数据，以便调用者进行进一步处理
        return {"error": "解析失败", "data": data}


class ACManager:
    """
    账户管理器 - 负责处理账户数据、登录和请求
    """
    # 类变量定义
    I8_VALUE = 925
    VERSION = "1.7.5"
    I11_VALUE = 123
    server_id = 0
    
    def __init__(self, account=None, accounts_file=None, delay=0.5, showres=0, skip_login=False):
        """
        初始化账户管理器
        
        Args:
            account: 账户名称
            accounts_file: 账户数据文件的路径
            delay: 请求延迟
            showres: 是否显示响应
            skip_login: 是否跳过登录（用于创建新账号的场景）
        """
        # 如果proto文件存在，解析并更新类变量
        self._parse_proto_file()
        
        if not account:
            raise ValueError("必须指定一个账户")
        self.delay = delay
        self.account_name = account
        if not accounts_file:
            default_file = f'ac_{account}.json'
            if os.path.exists(default_file):
                accounts_file = default_file
            else:
                # 在 ac_*/ 子目录中查找 {account}.json
                import glob
                candidates = glob.glob(f'ac_*/{account}.json')
                accounts_file = candidates[0] if candidates else default_file
        self.accounts_file = accounts_file
        self.accounts = {}
        self.loaded = False
        self.load_accounts()
        self.showres = showres

        if account and not skip_login:
            account_data = self.get_account(account)
            self.server_id = account_data['server_id'] if account_data and 'server_id' in account_data else 0
            # if self.check_login_status(account):
            #     print(f"<{self.mask_account(account)}:{self.server_id}> 复用登录态")
            # else:
            self.login(account)
    
    def _parse_proto_file(self):
        """
        解析proto文件并更新类变量
        如果proto文件存在，使用protobuf解析，提取字段8、10、11的值
        """
        proto_file = 'proto'
        
        # 检查proto文件是否存在
        if not os.path.exists(proto_file):
            return
        
        try:
            # 读取proto文件（跳过前4个字节）
            with open(proto_file, 'rb') as f:
                # 跳过前4个字节
                f.read(4)
                # 读取剩余数据
                proto_data = f.read()
            
            # 使用request_body_for_sy_skill消息结构解析
            # 该消息包含requester1 r1=1，其中包含了i8=8, ver=10, i11=11
            request_msg = kpbl_pb2.request_body_pure()
            request_msg.ParseFromString(proto_data)
            
            # 提取requester1中的字段
            # proto3中r1是嵌套消息，直接访问
            r1 = request_msg.r1
            
            # 提取字段8（i8）- proto3中int32默认值为0，如果非0则说明有值
            if r1.i8 != 0:
                ACManager.I8_VALUE = r1.i8
            
            # 提取字段10（ver）- proto3中string默认值为空字符串
            if r1.ver:
                ACManager.VERSION = r1.ver
            
            # 提取字段11（i11）- proto3中int32默认值为0
            if r1.i11 != 0:
                ACManager.I11_VALUE = r1.i11
                
        except Exception as e:
            print(f"警告: 解析proto文件时出错: {e}")
    
    def load_accounts(self):
        """加载账户数据文件"""
        try:
            with open(self.accounts_file, 'r') as f:
                self.accounts = json.load(f)
            

            
            self.loaded = True
            # print(f"成功加载 {len(self.accounts)} 个账户")
            return True
        except FileNotFoundError:
            print(f"错误: 找不到账户文件 {self.accounts_file}")
            return False
        except json.JSONDecodeError:
            print(f"错误: 账户文件 {self.accounts_file} 格式不正确")
            return False

    
    def get_account(self, account_name, attribute_name=None):
        """
        获取指定账户的数据
        
        Args:
            account_name: 账户名称
            attribute_name: 可选，指定获取账户的特定属性
            
        Returns:
            dict: 如果attribute_name为None，返回整个账户数据
            any: 如果指定了attribute_name，返回该属性值
            None: 如果账户不存在或属性不存在
        """
        if not self.loaded:
            if not self.load_accounts():
                return None
        
        account = self.accounts.get(account_name)
        
        if account is None:
            return None
            
        if attribute_name is not None:
            return account.get(attribute_name)
            
        return account
    
    def getItemIdByType(self, item_type):
        """根据物品type查找物品id"""
        baginfo = self.get_account(self.account_name, 'baginfo')
        # item_type = str(item_type)
        if baginfo and item_type in baginfo:
            return baginfo[item_type]['id'], int(baginfo[item_type]['count'])
        return None, 0
        

    def openBox(self, box_type=71, count=50):
        """开箱子，box_type: 71~75，count: 开箱数量"""
        box_id, box_count = self.getItemIdByType(box_type)
        if box_id:
            print(f"<{self.mask_account(self.account_name)}> 开箱子: type={box_type}, id={box_id}, count={count}/{box_count}")
            req_config = {"ads": f"开箱子_{box_type}", "times": 1, "hexstringheader": "074f", "request_body_i2": box_id, "request_body_i3": count}
            self.do_common_request(self.account_name, req_config, showres=0)
        else:
            print(f"<{self.mask_account(self.account_name)}> 未找到type={box_type}的箱子物品")
        
        

    def get_status_code(self, response_bytes):
        status_code_response = kpbl_pb2.status_code_response()
        status_code_response.ParseFromString(response_bytes[6:])
        return status_code_response.status_code
    
    def save_accounts(self):
        """保存账户数据到文件"""
        try:
            # 创建一个新字典，只包含指定的字段
            filtered_accounts = {}
            for account_name, account_data in self.accounts.items():
                filtered_account = {}
                # 只保存指定的字段
                for field in ['s1', 'udid', 'server_id', 'acstr', 'py_session', 'encbody', 'i5_adsid1',
                              'daily_activity', 'weekly_activity', 'diamond', 'coin', 'tl',
                              'charaname', 'charaid', 'status_time', 'kunnan', 'gqxx']:
                    if field in account_data:
                        filtered_account[field] = account_data[field]
                filtered_accounts[account_name] = filtered_account
            
            with open(self.accounts_file, 'w') as f:
                json.dump(filtered_accounts, f, indent=4)
            # print(f"成功保存 {len(self.accounts)} 个账户到 {self.accounts_file}")
            
            # 保存完成后，重新执行init的逻辑
            current_accounts = self.accounts.copy()  # 保存当前内存中的完整账户数据
            self.accounts = {}
            self.loaded = False
            self.load_accounts()  # 重新加载账户数据
            self.server_id = self.get_account(account_name)['server_id']
            
            # 恢复完整的账户数据，但保留从文件中加载的基本字段
            for account_name in self.accounts:
                if account_name in current_accounts:
                    # 保持文件中加载的基本字段不变
                    basic_fields = {field: self.accounts[account_name][field] 
                                   for field in ['s1', 'udid', 'server_id', 'acstr'] 
                                   if field in self.accounts[account_name]}
                    
                    # 恢复其他字段
                    self.accounts[account_name] = current_accounts[account_name]
                    
                    # 确保基本字段使用文件中的值
                    for field, value in basic_fields.items():
                        self.accounts[account_name][field] = value
            
            return True
        except Exception as e:
            print(f"保存账户数据时出错: {str(e)}")
            return False
    
    def update_account(self, account_name, key, value):
        """
        更新账户的特定数据
        
        Args:
            account_name: 账户名称
            key: 要更新的键
            value: 新值
        
        Returns:
            bool: 是否成功更新
        """
        if not self.loaded:
            if not self.load_accounts():
                return False
        
        if account_name not in self.accounts:
            print(f"错误: 账户 '{account_name}' 不存在")
            return False
        
        self.accounts[account_name][key] = value
        return True
    
    def createaccount(self, account_file=None):
        """
        创建一个新账户，将其保存到以新账号命名的文件中，并执行登录
        
        Args:
            account_file: 已废弃，保留用于兼容性，新账号总是保存到ac_{新账号名}.json
        
        Returns:
            str: 新创建的账户名称
        """
        import uuid as uuid_module
        
        # 生成新的UUID
        new_uuid = str(uuid_module.uuid4()).upper()
        
        # 使用UUID的第一个部分作为账户名
        account_name = new_uuid.split('-')[0]
        
        # 创建新账户数据
        new_account = {
            "udid": new_uuid,
        }
        
        # 新账号使用自己的账户文件
        new_account_file = f'ac_{account_name}.json'
        
        # 创建只包含新账号的字典
        accounts = {account_name: new_account}
        
        try:
            with open(new_account_file, 'w') as f:
                json.dump(accounts, f, indent=4)
            print(f"已将新账户'{account_name}'保存到{new_account_file}")
        except Exception as e:
            print(f"保存{new_account_file}时出错: {e}")
            return None
        
        # 创建新的ACManager实例来登录新账号
        # 使用新账号的文件
        new_ac_manager = ACManager(account_name, accounts_file=new_account_file, showres=0, delay=0)
        
        # 登录新账户（通过新的manager，它会自动登录）
        # loginrequest = {"ads":"login","times":1,"hexstringheader":"7527","request_body_i2":2,"request_body_i5":"com.habby.capybara"}
        # new_ac_manager.do_common_request(account_name, loginrequest, showres=0)

        new_ac_manager.update_account(account_name, "server_id", 401000)
        new_ac_manager.save_accounts()
        return account_name
    
    def check_account_ready(self, account_name):
        """
        检查账户是否已准备好执行请求（已加载，且具有必要信息）
        
        Args:
            account_name: 账户名称
            
        Returns:
            bool: 账户是否准备好
        """
        # 检查账户是否已加载
        if not self.loaded:
            print("账户数据未加载")
            return False
        
        # 检查账户是否存在
        if account_name not in self.accounts:
            print(f"账户 '{account_name}' 不存在")
            return False
        
        account = self.accounts[account_name]
        
        # 检查必要的账户信息是否存在
        required_fields = ['udid']
        for field in required_fields:
            if field not in account:
                print(f"账户 '{account_name}' 缺少必要信息: {field}")
                return False
        
        return True
    
    def check_login_status(self, account_name):
        """
        检查账户是否已登录（具有encbody, i5_adsid1, server_id）
        
        Args:
            account_name: 账户名称
            
        Returns:
            bool: 账户是否已登录
        """
        if not self.check_account_ready(account_name):
            return False
        
        account = self.accounts[account_name]
        login_fields = ['encbody', 'i5_adsid1', 'server_id']
        
        for field in login_fields:
            if field not in account:
                # print(f"账户 '{account_name}' 未登录，缺少字段: {field}")
                return False
        
        return True
    
    def common_header_requester1(self, account):
        """
        创建通用的请求头
        
        Args:
            account: 账户数据
            
        Returns:
            requester1: 请求头对象
        """
        # 创建一个 requester1 对象
        requester = kpbl_pb2.requester1()
        if "s1" in account:
            requester.s1 = account.get("s1")
        requester.i2 = 1
        requester.udid = account["udid"]
        if "encbody" in account:
            requester.encbody = account["encbody"]
        
        # 自增 i5_adsid1 并设置
        if "i5_adsid1" in account:
            account["i5_adsid1"] += 1
        else:
            account["i5_adsid1"] = 1
        requester.i5_adsid1 = account.get("i5_adsid1")
        
        if "server_id" in account:
            requester.server_id = account.get("server_id")
        requester.lang = "ChineseSimplified"
        requester.i8 = self.I8_VALUE
        requester.ver = self.VERSION
        requester.i11 = self.I11_VALUE
        return requester
    

    def create_request_body(self, account_name, hexstringheader, request_body_i2=None, 
                          request_body_i3=None, request_body_i4=None, request_body_i5=None,  request_body_i6=None,
                          request_body_i7=None, request_body_i9=None, request_body_i36=None, requestbodytype='request_body'):
        """
        创建请求体
        
        Args:
            account_name: 账户名称
            hexstringheader: 十六进制请求头
            request_body_i2: i2参数
            request_body_i3: i3参数
            request_body_i4: i4参数
            request_body_i5: i5参数
            request_body_i7: i7参数
            requestbodytype: 请求体类型
            
        Returns:
            bytes: 请求体数据
        """
        # 获取账户数据
        account = self.get_account(account_name)
        if not account:
            raise ValueError(f"账号 {account_name} 未找到")
        
        # 创建请求者对象
        requester = self.common_header_requester1(account)
        
        # 根据请求类型创建请求体
        if requestbodytype == 'request_body_for_stringi3':
            request_body = kpbl_pb2.request_body_for_stringi3()
        elif requestbodytype == 'request_body_for_mfssth':
            request_body = kpbl_pb2.request_body_for_mfssth()
        elif requestbodytype == 'request_body_for_dilao':
            request_body = kpbl_pb2.request_body_for_dilao()
        elif requestbodytype == 'request_body_for_geren':
            request_body = kpbl_pb2.request_body_for_geren()
        elif requestbodytype == 'request_sh':
            request_body = kpbl_pb2.request_sh()
        elif requestbodytype == 'request_zz':
            request_body = kpbl_pb2.request_zz()
        elif requestbodytype == 'request_body_for_sd':
            request_body = kpbl_pb2.request_body_for_sd()
        elif requestbodytype == 'miner_tap_request':
            request_body = kpbl_pb2.miner_tap_request()
        elif requestbodytype == 'request_body_tzzt':
            request_body = kpbl_pb2.request_body_tzzt()
        elif requestbodytype == 'request_login':
            request_body = kpbl_pb2.request_login()
        elif requestbodytype == 'request_body_for_jqfinish':
            request_body = kpbl_pb2.request_body_for_jqfinish()
        elif requestbodytype == 'request_body_q11':
            request_body = kpbl_pb2.request_body_q11()
        elif requestbodytype == 'request_body_long64i4':
            request_body = kpbl_pb2.request_body_long64i4()
        elif requestbodytype == 'request_qh':
            request_body = kpbl_pb2.request_qh()
        elif requestbodytype == 'request_body_for_jqupdate':
            request_body = kpbl_pb2.request_body_for_jqupdate()
        elif requestbodytype == 'request_body_for_sy_skill':
            request_body = kpbl_pb2.request_body_for_sy_skill()
        elif requestbodytype == 'request_body_allint':
            request_body = kpbl_pb2.request_body_allint()
        elif requestbodytype == 'request_body_allint1':
            request_body = kpbl_pb2.request_body_allint1()
        elif requestbodytype == 'request_body_for_kn_invite':
            request_body = kpbl_pb2.request_body_for_kn_invite()
        elif requestbodytype == 'request_body_for_nickname':
            request_body = kpbl_pb2.request_body_for_nickname()
        else:
            request_body = kpbl_pb2.request_body()
        
        # 设置请求者对象
        request_body.r1.CopyFrom(requester)
        
        # 特殊处理登录请求
        if requestbodytype == 'request_login':
            request_body.r1.ClearField("encbody")
            # request_body.r1.ClearField("server_id")
            request_body.r1.i5_adsid1 = 2
        
        # 设置其他参数
        if request_body_i2:
            request_body.i2 = request_body_i2
        if request_body_i3:
            request_body.i3 = request_body_i3
        if request_body_i4:
            request_body.i4 = request_body_i4
        if request_body_i5:
            # 调试信息：打印类型信息
            # print(f"调试: request_body类型: {type(request_body)}")
            # print(f"调试: request_body_i5类型: {type(request_body_i5)}, 值: {request_body_i5}")
            # try:
            #     print(f"调试: request_body.i5字段类型: {type(request_body.i5)}")
            # except Exception as e:
            #     print(f"调试: 无法获取i5字段类型: {e}")
            # print(f"request_body_i5: {request_body_i5}, {request_body}")
            request_body.i5 = request_body_i5
        if request_body_i6:
            request_body.i6 = request_body_i6
        if request_body_i7:
            request_body.i7 = request_body_i7
        if request_body_i9:
            request_body.i9 = request_body_i9
        if request_body_i36:
            request_body.i36 = request_body_i36
        
        # 序列化请求体
        serialized_data = request_body.SerializeToString()
        
        # 转换并拼接头部
        header_binary = binascii.unhexlify(hexstringheader)[:2]
        len_hex = len(serialized_data)
        
        # 使用小端序（低字节在前）
        len_bytes = bytes([len_hex & 0xFF, (len_hex >> 8) & 0xFF])
        
        combined_data = header_binary + len_bytes + serialized_data
        
        return combined_data
    
    def calcsha(self, data):
        """
        计算SHA-256哈希值
        
        Args:
            data: 待哈希的数据
            
        Returns:
            str: 十六进制格式的哈希值
        """
        sha256_hash = hashlib.sha256()
        sha256_hash.update(data)
        sha256_hex = sha256_hash.hexdigest().upper()
        return sha256_hex
    
    def mask_account(self, account_name):
        """
        脱敏账户名称，保留前两个和最后一个字符
        
        Args:
            account_name: 账户名称
            
        Returns:
            str: 脱敏后的账户名称
        """
        if not account_name or not isinstance(account_name, str):
            return str(account_name)
        
        info_str = str(account_name)
        info_len = len(info_str)
        
        keep_start = 2
        keep_end = 1
        
        if info_len <= keep_start + keep_end:
            return info_str
        
        masked_part = '*' * (info_len - keep_start - keep_end)
        return info_str[:keep_start] + masked_part + info_str[-keep_end:]
    
    def format_number(self, number):
        """
        将数字格式化为科学显示法，使用K、M、B、T单位
        
        Args:
            number: 要格式化的数字
            
        Returns:
            str: 格式化后的字符串
        """
        if number < 1000:
            return str(number)
        elif number < 1000000:
            return f"{number/1000:.1f}K"
        elif number < 1000000000:
            return f"{number/1000000:.1f}M"
        elif number < 1000000000000:
            return f"{number/1000000000:.1f}B"
        else:
            return f"{number/1000000000000:.1f}T"
    
    def dxxtype(self, binary_data):
        if len(binary_data) >= 2:
            byte1 = binary_data[0]
            byte2 = binary_data[1]
            # 调换字节顺序并转为十进制
            return str((byte2 << 8) | byte1)
        else:
            return "0"

    def send_binary_data(self, account_name, binary_data, times=1, describe="", showres=1):
        """
        发送二进制数据到服务器
        
        Args:
            account_name: 账户名称
            binary_data: 二进制数据
            times: 重复次数
            describe: 描述
            showres: 是否显示响应
            
        Returns:
            response: 响应对象
        """

            
        url = "https://prod.advrpg.com/"
        tosign = b'6F80DA08742462C12D7C9598B464E8020' + binary_data
        headers = {
            "Host": "prod.advrpg.com",
            "X-Unity-Version": "2022.3.49f1",
            "Accept": "*/*",
            "DxxVersion": "1",
            "DxxCheck": self.calcsha(tosign),
            "Accept-Language": "zh-cn",
            "Accept-Encoding": "gzip, deflate, br",
            "DxxTime": "0",
            "Content-Type": "application/octet-stream",
            "User-Agent": "capybara/15 CFNetwork/1209 Darwin/20.2.0",
            "DxxType": self.dxxtype(binary_data),
            "Content-Length": str(len(binary_data)),
            "Connection": "keep-alive"
        }
        
        max_retries = 3  # 最大重试次数
        retry_delay = 2  # 重试间隔(秒)
        
        response = None
        
        # while times > 0:
        for retry in range(max_retries):
            try:
                response = requests.post(url, headers=headers, data=binary_data, timeout=10)
                if showres:
                    print(f"<{self.mask_account(account_name)}:{self.server_id}> [{describe}:{times} left]Response body: {response.content}")
                times -= 1
                time.sleep(self.delay)  # 请求间增加短暂延迟
                break  # 成功则跳出重试循环
            except (requests.exceptions.SSLError, requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                if retry < max_retries - 1:
                    print(f"<{self.mask_account(account_name)}:{self.server_id}> 连接/超时错误，{retry+1}/{max_retries}次重试")
                    time.sleep(retry_delay )  # 指数退避
                else:
                    print(f"<{self.mask_account(account_name)}:{self.server_id}> 请求失败，达到最大重试次数: {e}")
                    if times > 0:
                        times -= 1  # 即使失败也减少剩余次数
            except Exception as e:
                print(f"<{self.mask_account(account_name)}:{self.server_id}> 未知错误: {e}")
                if times > 0:
                    times -= 1
                break
        
        return response
    
    def login(self, account_name, showloginres = 0):
        """
        执行登录操作
        
        Args:
            account_name: 账户名称
            
        Returns:
            bool: 是否登录成功
        """
        if self.showres:
            print(f"<{self.mask_account(account_name)}:{self.server_id}> 正在登录...")
            print(f"<{self.mask_account(account_name)}:{self.server_id}> VERSION: {self.VERSION}, I8_VALUE: {self.I8_VALUE}, I11_VALUE: {self.I11_VALUE}")

        
        # 检查账户是否准备好
        if not self.check_account_ready(account_name):
            print(f"<{self.mask_account(account_name)}:{self.server_id}> 账户未准备好，无法登录")
            return False
        
        # 设置初始化 i5_adsid1
        self.update_account(account_name, "i5_adsid1", 1)
        
        # 构建登录请求
        login_config = {
            "ads": "login",
            "hexstringheader": '7527',
            "times": 1,
            "requestbodytype": "request_login",
            "request_body_i2": 2,
            "request_body_i5": "com.habby.capybara"
        }
        
        # 添加可选参数
        if 'acstr' in self.accounts[account_name]:
            login_config["request_body_i3"] = self.accounts[account_name]['acstr']
        
        # 发送登录请求
        res = self.do_common_request(account_name, login_config, showres=showloginres)
        
        # 检查请求是否成功
        if not res:
            print(f"<{self.mask_account(account_name)}:{self.server_id}> 登录失败，没有收到响应")
            return False
        
        # 解析登录响应
        if len(res) > 6:
            try:
                # 从第6个字节开始提取数据
                login_data = res[6:]
                
                # 使用response_login结构解析数据
                login_resp = kpbl_pb2.response_login()
                login_resp.ParseFromString(login_data)


                
                open(f'res/response_login_{account_name}', 'wb').write(login_data)                
                # 更新账户信息
                self.update_account(account_name, 'encbody', login_resp.encbody)
                self.update_account(account_name, 'i5_adsid1', login_resp.reqid)
                # self.update_account(account_name, 'server_id', login_resp.serverid)
                self.update_account(account_name, 'coin', login_resp.ci.coin)
                self.update_account(account_name, 'diamon', login_resp.ci.diamon)
                self.update_account(account_name, 'charauuid', login_resp.charauuid)
                self.update_account(account_name, 'charaid', login_resp.charaid)
                self.update_account(account_name, 'charaname', login_resp.f17.charaname)
                self.update_account(account_name, 'kunnan', login_resp.kunnan)
                
                # 解析AC通关进度
                # ac0 挑战之塔: field 27 = 100000 + 已通关关卡号，默认100101(未通关)
                ac0_val = login_resp.ac0_tower_level
                self.update_account(account_name, 'ac0_tower_level', ac0_val if ac0_val else 100101)
                # ac1~4 顺位副本: field 40 repeated {dungeonType, level}，默认0(未通关)
                ac_levels = {}
                for d in login_resp.ac_dungeon_level:
                    ac_levels[d.dungeonType] = d.level
                for i in range(1, 5):
                    self.update_account(account_name, f'ac{i}_cleared', ac_levels.get(i, 0))
                
                self.update_account(account_name, 'ylifid', login_resp.ylif.id)
                self.update_account(account_name, 'zhanli', login_resp.f17.zhanli)

                for zyinfo in login_resp.zyinfo:
                    if zyinfo.type == 9:
                        self.update_account(account_name, 'tl', zyinfo.count)

                # 处理背包物品信息
                bag_items = {}
                bag_str_parts = []
                
                # 尝试从 bi 字段获取背包信息
                if hasattr(login_resp, 'bi') and login_resp.bi:
                    try:
                        # bi 是一个 repeated 类型的字段，直接遍历
                        for item in login_resp.bi:
                            if hasattr(item, 'type'):
                                bag_items[item.type] = {'id': item.id, 'count': item.count}
                                bag_str_parts.append(f"{item.type}:{item.count}")
                            
                        if bag_items:
                            self.update_account(account_name, 'baginfo', bag_items)
                        self.baginfo_str = ' | '.join(bag_str_parts)
                            
                    except Exception as e:
                        print(f"<{self.mask_account(account_name)}:{self.server_id}> 处理背包信息时出错: {str(e)}")
                # print(f"<{self.mask_account(account_name)}:{self.server_id}> 背包信息: {bag_items}")
                
                # 解析关卡信息
                max_gqh = max([gq.gqh for gq in login_resp.gqxxinfo]) if login_resp.gqxxinfo else 0
                self.update_account(account_name, 'gqxx', max_gqh)
                # 解析获取seasonid
                if hasattr(login_resp, 'hdinfo') and hasattr(login_resp.hdinfo, 'hdinfo1') and hasattr(login_resp.hdinfo.hdinfo1, 'seasoninfo'):
                    seasonid = login_resp.hdinfo.hdinfo1.seasoninfo.seasonid
                    self.update_account(account_name, 'seasonid', seasonid)
                
                if hasattr(login_resp, 'hdinfo') and hasattr(login_resp.hdinfo, 'hdinfo1') and hasattr(login_resp.hdinfo.hdinfo1, 'adinfo'):
                    adlist = []
                    for hd in login_resp.hdinfo.hdinfo1.adinfo:
                        adid = hd.adsid
                        for adsub in hd.subadslist:
                            adlist.append({adid: adsub.adssubid})
                    self.update_account(account_name, 'adlist', adlist)


                print(f"<{self.mask_account(account_name)}:{self.server_id}> 名: {login_resp.f17.charaname}/战: {self.format_number(login_resp.f17.zhanli)}/关: {max_gqh}/钱: {self.format_number(login_resp.ci.coin)}/钻: {self.format_number(login_resp.ci.diamon)}/体: {self.get_account(account_name, 'tl')}")

                # 解析宠物信息
                # if hasattr(login_resp, 'pets') and login_resp.pets:
                if hasattr(login_resp, 'field19') and login_resp.field19 and login_resp.field19.field19_8:
                    # 创建宠物信息列表
                    pets_info = []
                    for pet in login_resp.field19.field19_8.petinfo:
                        # 将宠物信息添加到列表，包括技能和数值
                        # 从第一套方案(fangan[0])中获取技能数据
                        skillsold = ''
                        valuesold = ''
                        if pet.fangan and len(pet.fangan) > 0:
                            fa = pet.fangan[0]
                            skillsold = binascii.hexlify(fa.skillsold).decode('utf-8') if fa.skillsold else ''
                            valuesold = binascii.hexlify(fa.valuesold).decode('utf-8') if fa.valuesold else ''
                        pet_data = {
                            'id': pet.id,
                            'type': pet.type,
                            'level': pet.level,
                            'position': pet.position,
                            'skillsold': skillsold,
                            'valuesold': valuesold
                        }
                        pets_info.append(pet_data)
                    
                    # 将宠物信息更新到账户数据中
                    self.update_account(account_name, 'pets', pets_info)
                
                cc_dict_raw = {}
                if hasattr(login_resp, 'field19') and login_resp.field19 and login_resp.field19.field19_8:
                    for cc in login_resp.field19.field19_8.cc.ccxl:
                        for cc_cell in cc.ccs:
                            cc_dict_raw[str(cc_cell.id)] = cc_cell.jd
                
                # 精简传承信息：
                # 1. 对于前2位相同的，只保留第3位最大的系列
                # 2. 在保留的系列中，第5位分组(1-4和5-7)，每组保留第5位最大的
                
                # 第一步：找出每个前2位中第3位最大的
                max_third_digit = {}
                for cc_id in cc_dict_raw.keys():
                    prefix2 = cc_id[:2]  # 前2位
                    third_digit = int(cc_id[2])  # 第3位
                    
                    if prefix2 not in max_third_digit or third_digit > max_third_digit[prefix2]:
                        max_third_digit[prefix2] = third_digit
                
                # 第二步：只处理第3位等于最大值的记录
                cc_simplified_dict = {}
                for cc_id, cc_jd in cc_dict_raw.items():
                    prefix2 = cc_id[:2]  # 前2位
                    third_digit = int(cc_id[2])  # 第3位
                    
                    # 跳过第3位不是最大的记录
                    if third_digit != max_third_digit[prefix2]:
                        continue
                    
                    # 前3位作为前缀（例如 '103'）
                    cc_prefix = cc_id[:3]
                    # 第5位数字（例如 '5'）
                    cc_fifth = int(cc_id[4])
                    
                    # 根据第5位数字确定分组：1-4为组1，5-7为组2
                    if 1 <= cc_fifth <= 4:
                        group = 'g1'
                    elif 5 <= cc_fifth <= 7:
                        group = 'g2'
                    else:
                        continue  # 跳过不在范围内的
                    
                    # 使用前缀+组作为key
                    key = f"{cc_prefix}_{group}"
                    
                    # 如果这个key还没记录，或者当前的第5位数字更大，则更新
                    if key not in cc_simplified_dict or cc_fifth > cc_simplified_dict[key]['fifth']:
                        cc_simplified_dict[key] = {
                            'id': cc_id,
                            'jd': cc_jd,
                            'fifth': cc_fifth
                        }
                
                # 构建精简后的字典 {id: jd}
                cc_final = {info['id']: info['jd'] for info in cc_simplified_dict.values()}
                
                self.update_account(account_name, 'cc', cc_final)

                baoshi_list = []
                eq_list = []
                # 解析装备和宝石信息
                if hasattr(login_resp, 'eq') and login_resp.eq:
                    for eq in login_resp.eq:
                        eq_list.append({'eq_uid': eq.eq_uid, 'eq_level': eq.eq_level})
                        if hasattr(eq, 'baoshi'):
                            for baoshi in eq.baoshi:
                                baoshi_list.append(baoshi.baoshiid)
                for item in login_resp.bi:
                    if str(item.type)[:3] in ['816', '817', '815']:
                        baoshi_list.append(item.type)
                self.update_account(account_name, 'baoshi', baoshi_list)
                self.update_account(account_name, 'eq_list', eq_list)

                return True
                
            except Exception as e:
                print(f"<{self.mask_account(account_name)}:{self.server_id}> 解析登录响应出错: {str(e)}")
                # 打印原始数据用于调试
                hex_data = binascii.hexlify(res).decode()
                print(f"原始数据: {hex_data[:60]}...")
                return False
        else:
            print(f"<{self.mask_account(account_name)}:{self.server_id}> 登录响应数据不足")
            return False
    
    def fetch_activity_info(self, account_name):
        """获取活动信息（9d2c），解析活动ID和过期时间，存入account"""
        config = {
            "ads": "活动信息",
            "times": 1,
            "hexstringheader": "9d2c",
        }
        res = self.do_common_request(account_name, config, showres=0)
        if res and len(res) > 20:
            try:
                resp = kpbl_pb2.acmanager_activity_info_response()
                resp.ParseFromString(res[6:])
                activity_info = {}
                for act in resp.activities:
                    if act.activity_id:
                        activity_info[act.activity_id] = act.expire_time
                self.update_account(account_name, 'activity_info', activity_info)
                print(f"<{self.mask_account(account_name)}> 活动信息: {len(activity_info)}个活动")
                return activity_info
            except Exception as e:
                print(f"<{self.mask_account(account_name)}> 解析活动信息出错: {e}")
                return {}
        return {}
    
    def do_request_by_binary(self, account_name, hexstringheader, binary_data, showres=1):
        """
        执行二进制数据请求
        """
        # 检查账户是否准备好
        if not self.check_account_ready(account_name):
            print(f"<{self.mask_account(account_name)}:{self.server_id}> 账户未准备好，无法执行请求")
            return None
        
        # 创建请求体
        account = self.get_account(account_name)
        if not account:
            raise ValueError(f"账号 {account_name} 未找到")
        
        # 创建请求者对象

        request_body = kpbl_pb2.request_body_for_jqupdate()
        request_body.CopyFrom(binary_data)
        request_body.r1.CopyFrom(self.common_header_requester1(account))
        request_body_binary = request_body.SerializeToString()
        

        # 转换并拼接头部
        header_binary = binascii.unhexlify(hexstringheader)[:2]
        len_hex = len(request_body_binary)
        
        # 使用小端序（低字节在前）
        len_bytes = bytes([len_hex & 0xFF, (len_hex >> 8) & 0xFF])
        
        request_body_binary = header_binary + len_bytes + request_body_binary
        
    
        open(f'req/request_jq', 'wb').write(request_body_binary)
        # 发送请求
        res = self.send_binary_data(
            account_name=account_name,
            binary_data=request_body_binary,
            times=1, # 废弃
            describe="jq_update",
            showres=showres
        )
        
        # 检查返回值
        if not res:
            print(f"<{self.mask_account(account_name)}:{self.server_id}> 请求失败，没有收到响应")
            return None
        
        # 检查错误消息
        if 'body length invalid' in res.text:
            print(f"<{self.mask_account(account_name)}:{self.server_id}> 请求失败，body length invalid")
            return None
        
        # # 如果需要保存到文件
        # if "savetofile" in request_config:
        #     with open(request_config.get("savetofile"), 'wb') as f:
        #         f.write(res.content)
        
        return res.content

    def do_common_request(self, account_name, request_config, showres=1):
        """
        执行通用请求，自动检查登录状态
        
        Args:
            account_name: 账户名称
            request_config: 请求配置
            showres: 是否显示响应
            
        Returns:
            bytes: 响应内容
        """
        # 特殊处理登录请求
        is_login_request = request_config.get("requestbodytype") == "request_login"
        
        # 检查账户是否准备好
        if not self.check_account_ready(account_name):
            print(f"<{self.mask_account(account_name)}:{self.server_id}> 账户未准备好，无法执行请求")
            return None
        
        # 非登录请求需要检查登录状态
        if not is_login_request and not self.check_login_status(account_name):
            print(f"<{self.mask_account(account_name)}:{self.server_id}> 账户未登录，尝试自动登录...")
            if not self.login(account_name):
                print(f"<{self.mask_account(account_name)}:{self.server_id}> 自动登录失败，无法执行请求")
                return None
        
        times = request_config.get("times", 1)
        self._relogin_attempted = False
        # 检查当前路径下有没有req和res目录，没有则新建
        if not os.path.exists('req'):
            os.makedirs('req')
        if not os.path.exists('res'):
            os.makedirs('res')
        
        while times > 0:
            times -= 1
            # 创建请求体
            try:
                # binary_data = self.create_request_body_new(account_name, request_config)
                binary_data = self.create_request_body(
                    account_name=account_name, 
                    hexstringheader=request_config.get("hexstringheader").replace(' ', ''),
                    request_body_i2=request_config.get("request_body_i2", None),
                    request_body_i3=request_config.get("request_body_i3", None),
                    request_body_i4=request_config.get("request_body_i4", None),
                    request_body_i5=request_config.get("request_body_i5", None),
                    request_body_i6=request_config.get("request_body_i6", None),
                    request_body_i7=request_config.get("request_body_i7", None),
                    request_body_i9=request_config.get("request_body_i9", None),
                    request_body_i36=request_config.get("request_body_i36", None),
                    requestbodytype=request_config.get("requestbodytype", None)
                )
            except Exception as e:
                print(f"<{self.mask_account(account_name)}:{self.server_id}> 创建请求体时出错: {str(e)}")
                print(f"request_config: {request_config}")
                raise e
                return None
            
            open(f'req/request_{request_config.get("ads")}', 'wb').write(binary_data)
            # 发送请求
            res = self.send_binary_data(
                account_name=account_name,
                binary_data=binary_data,
                times=request_config.get("times", 1), # 废弃
                describe=request_config.get("ads", "请求"),
                showres=showres
            )
            
            # 检查返回值
            if not res:
                print(f"<{self.mask_account(account_name)}:{self.server_id}> 请求失败，没有收到响应 request_config: {request_config}")
                return None
            
            # 检查错误消息
            if 'body length invalid' in res.text:
                if not is_login_request and not self._relogin_attempted:
                    print(f"<{self.mask_account(account_name)}:{self.server_id}> 登录态可能过期，重新登录...")
                    self._relogin_attempted = True
                    # 清除旧session，重新登录
                    self.accounts[account_name].pop('encbody', None)
                    if self.login(account_name):
                        times += 1  # 恢复次数，让本次请求重试
                        continue
                print(f"<{self.mask_account(account_name)}:{self.server_id}> 请求失败，body length invalid")
                return None
            open(f'res/response_{request_config.get("ads")}', 'wb').write(res.content)
        

        
        return res.content
    
    def do_common_request_list(self, account_name, request_configs, showres=1):
        """
        并发执行多个通用请求
        
        Args:
            account_name: 账户名称
            request_configs: 请求配置列表
            showres: 是否显示响应
            
        Returns:
            1: 所有请求完成后返回1
        """
        import threading
        
        threads = []
        for config in request_configs:
            times = config.get('times', 1)
            single_config = dict(config)
            single_config['times'] = 1
            for _ in range(times):
                t = threading.Thread(target=self.do_common_request, args=(account_name, dict(single_config), showres))
                threads.append(t)
                t.start()
        for t in threads:
            t.join()
        
        return 1
    
    def get_all_account_names(self):
        """
        获取所有账户名称
        
        Returns:
            list: 账户名称列表
        """
        if not self.loaded:
            if not self.load_accounts():
                return []
        
        return list(self.accounts.keys())

    def item_type_name(self, type_id):
        """
        获取物品类型名称
        
        Args:
            type_id: 物品类型ID
            
        Returns:
            str: 物品类型名称
        """
        type_names = {
            24: "金币",
            60: "道具",
            62: "武器",
            # 可以添加更多类型
        }
        return type_names.get(type_id, f"未知类型({type_id})")
    
    def format_item_info(self, item):
        """
        格式化物品信息
        
        Args:
            item: 物品数据
            
        Returns:
            str: 格式化的物品信息
        """
        type_name = self.item_type_name(item.get('type', 0))
        return f"ID:{item['id']} - {type_name} x {item.get('count', 1)}"

    # def item_open(self, account_name, item_id):
    #     """
    #     打开物品
    #     """
    #     config = {"ads":"item_open","times":1,"hexstringheader":"d72b","request_body_i2": item_id, "request_body_i3": 1, "request_body_i4": 1 }
    #     self.do_common_request(account_name,config,showres=self.showres)

# 测试代码
if __name__ == "__main__":
    # 创建账户管理器
    ac_manager = ACManager()
    
    # 获取所有账户
    accounts = ac_manager.get_all_account_names()
    print(f"可用账户: {accounts}")
    
    # 如果提供了命令行参数，则执行特定操作
    if len(sys.argv) > 2:
        account_name = sys.argv[1]
        command = sys.argv[2]
        
        if account_name in accounts or account_name == "all":
            # 处理"all"参数
            account_list = accounts if account_name == "all" else [account_name]
            
            for current_account in account_list:
                print(f"\n处理账户: {ac_manager.mask_account(current_account)}")
                
                # 登录
                if not ac_manager.login(current_account):
                    print(f"账户 {ac_manager.mask_account(current_account)} 登录失败，跳过")
                    continue
                
                # 执行命令
                if command == "test":
                    print(f"测试账户 {ac_manager.mask_account(current_account)} 成功")
        else:
            print(f"账户 {account_name} 不存在")
    else:
        print("用法: python send_new.py [账户名|all] [命令]")
