"""
AC自动挑战管理模块
处理自动挑战功能，包括进度保存和续传
"""

import json
import os
import time
from . import kpbl_pb2
from .kpbltools import mask_account, fixdata, ACManager



class AutoClaimProgressManager:
    """AC进度管理器，负责保存和读取挑战进度"""
    
    def __init__(self, account_name):
        self.account_name = account_name
        self.progress_file = f"ac_progress_{account_name}.json"

    
    def save_progress(self, current_todo):
        """保存当前进度到文件"""
        next_todo = self._calculate_next_todo(current_todo)
        progress_data = {
            'account_name': self.account_name,
            'last_completed': current_todo,
            'next_todo': next_todo,
            'timestamp': time.time(),
            'time_str': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2, ensure_ascii=False)
            print(f"进度已保存：{current_todo} -> {next_todo}")
        except Exception as e:
            print(f"保存进度失败：{e}")
    
    def load_progress(self):
        """从文件读取进度"""
        if not os.path.exists(self.progress_file):
            return None
            
        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
            
            # 验证数据
            if progress_data.get('account_name') == self.account_name:
                return progress_data.get('next_todo')
            else:
                print(f"进度文件账号不匹配：{progress_data.get('account_name')} != {self.account_name}")
                return None
                
        except Exception as e:
            print(f"读取进度失败：{e}")
            return None
    
    def _calculate_next_todo(self, current_todo):
        """计算下一个todo值"""
        current_todo = int(current_todo)
        
        # 如果当前todo以10结尾（如19010），跳到下一个百位数的开始（如19101）
        if current_todo % 10 == 0:
            next_todo = (current_todo // 100 + 1) * 100 + 1
        else:
            # 否则简单地加1
            next_todo = current_todo + 1
        
        return next_todo
    
    def clear_progress(self):
        """清除进度文件"""
        if os.path.exists(self.progress_file):
            try:
                os.remove(self.progress_file)
                print(f"进度文件已清除：{self.progress_file}")
            except Exception as e:
                print(f"清除进度文件失败：{e}")


class ACChallengeManager:
    """AC挑战管理器，负责执行自动挑战逻辑"""
    
    def __init__(self, account_name, showres=0, delay=0.5):
        self.account_name = account_name
        self.ac_manager = ACManager(account_name, delay=delay, showres=showres)
        self.I8_VALUE = self.ac_manager.I8_VALUE
        self.showres = showres
    
    def claim_reward(self, todo,account_name): # 13110
        config = {"ads": "挑战塔奖励","times" : 1,"request_body_i2" : 1000 + int(str(todo)[:3]),"hexstringheader": "cb32",}
        self.ac_manager.do_common_request(account_name,config,showres=self.showres)
        config = {"ads": "挑战塔奖励","times" : 1,"request_body_i2" : 1000 + int(str(todo)[:-2]),"hexstringheader": "cb32",}
        self.ac_manager.do_common_request(account_name,config,showres=self.showres)

    def execute_one_time(self, account_name, shunwei, todo):
        """执行单次挑战"""
        self.execute_challenge(account_name, shunwei, todo)
        return True

    def execute_challenge(self, account_name, shunwei, todo, maxtry=20):
        """执行单次挑战"""
        # 已移除对send_ads.py的依赖，相关函数已在本文件中实现
        
        config_common = {
            "ads": f"副本{shunwei}",
            "times": 1,
            "request_body_i2": shunwei,
            "request_body_i3": todo,
            "request_body_i5": str(self.I8_VALUE),
            "hexstringheader": "9530"
        }
        
        if int(shunwei) == 0:  # 挑战之塔
            config_common = {
                "ads": f"挑战之塔",
                "times": 1,
                "request_body_i2": int(todo),
                "request_body_i3": str(self.I8_VALUE),
                "hexstringheader": "c932",
                "requestbodytype": "request_body_for_stringi3"
            }
        
        config = config_common
        minhp = -1
        
        # 如果是塔的10层结尾，先领取奖励（claim_reward需要纯level，去掉100000前缀）
        if int(shunwei) == 0 and int(todo) % 10 == 0:
            self.claim_reward(int(todo) - 100000, account_name)
        
        trycount = 0
        while trycount < maxtry:
            trycount += 1
            try:
                res = self.ac_manager.do_common_request(account_name, config, showres=self.showres)
            except Exception as e:
                print(f'{e}')
                continue
            
            # 将bytes对象转换为字符串
            res_text = res.decode('utf-8', errors='replace')
            a = res_text.split("ResultData")[1] if "ResultData" in res_text else ""
            a = a.replace("=", "")
            
            if len(a) < 100:
                print(f"len(a)<100 may not have stama or wrong level")
                return False
            
            if len(a) > 0:
                parsed_data = fixdata(a)
                
                # 检查敌人是否全部被击败
                all_enemies_defeated = True
                any_enemy_found = False
                
                for entry in parsed_data:
                    if entry.get('m_camp') == 'Enemy':
                        any_enemy_found = True
                        if entry.get('m_curHp', 0) > 0:
                            all_enemies_defeated = False
                
                # 检查我方主角是否被击败
                friendly_main_defeated = False
                for entry in parsed_data:
                    if entry.get('m_camp') == 'Friendly' and entry.get('m_isMainMember') == True:
                        if entry.get('m_curHp', 1) <= 0:
                            friendly_main_defeated = True
                            break
                
                # 胜利条件：敌人全部被击败 或 没有敌人
                if (all_enemies_defeated and any_enemy_found) or (not any_enemy_found):
                    print('done')
                    if int(shunwei) == 0 and int(todo) % 10 == 0:
                        self.claim_reward(int(todo) - 100000, account_name)
                    return True
                
                # 失败条件：我方主角被击败
                elif friendly_main_defeated:
                    print('战斗失败: 我方主角被击败，继续尝试...')
                
                enemylist = []
                for row in parsed_data:
                    if row['m_camp'] == 'Enemy':
                        lasthp = row['m_curHp']
                        minhp = lasthp if lasthp < minhp or minhp == -1 else minhp
                        maxhp = row['m_maxHp']
                        enemylist.append(row)
                
                print(f"\r<{mask_account(account_name)}> count:{trycount}/{maxtry}, minhp:({minhp/maxhp*100:.2f}%){minhp}, lasthp:({lasthp/maxhp*100:.2f}%){lasthp}", end='', flush=True)
        
        # 达到最大尝试次数
        print(f"\n达到最大尝试次数 {maxtry}，放弃关卡 {todo}")
        return False
    
    def auto_challenge_with_progress(self, account_name, shunwei, todo=None, maxtry=20):
        """带进度的自动挑战"""
        if todo is None:
            print("请指定关卡号")
            return
        
        current_todo = int(todo)
        
        # 对于挑战之塔，支持连续挑战
        if int(shunwei) == 0:
            while True:
                print(f"\n开始挑战关卡 {current_todo}")
                success = self.execute_challenge(account_name, shunwei, current_todo, maxtry)
                
                if success:
                    # 计算下一关
                    if current_todo % 10 == 0:
                        next_todo = (current_todo // 100 + 1) * 100 + 1
                    else:
                        next_todo = current_todo + 1
                    
                    if self.showres:
                        print(f"\n关卡{current_todo}完成，下一关卡{next_todo}")
                    current_todo = next_todo
                    
                    # 短暂暂停
                    time.sleep(1)
                else:
                    if self.showres:
                        print(f"\n关卡{current_todo}失败，停止挑战")
                    break
        else:
            # 非塔关卡，只执行一次
            success = self.execute_challenge(account_name, shunwei, current_todo, maxtry)
            if success:
                if self.showres:
                    print(f"\n关卡{current_todo}完成")
            else:
                if self.showres:
                    print(f"\n关卡{current_todo}失败")
    
    def set_account_level(self, account_name, level):
        """设置账号的 ac_level"""
        try:
            self.ac_manager.update_account(account_name, 'ac_level', int(level))
            self.ac_manager.save_accounts()
            if self.showres:
                print(f"已将账号 {mask_account(account_name)} 的 ac_level 设置为 {level}")
            return True
        except Exception as e:
            if self.showres:
                print(f"设置 ac_level 失败: {e}")
            return False
    
    def get_account_level(self, account_name):
        """获取账号的 ac_level"""
        return self.ac_manager.get_account(account_name, 'ac_level')
    
    def set_account_level_field(self, account_name, field_name, level):
        """设置账号的指定级别字段"""
        try:
            self.ac_manager.update_account(account_name, field_name, int(level))
            self.ac_manager.save_accounts()
            # 总是显示保存结果，不受showres影响
            print(f"已将账号 {mask_account(account_name)} 的 {field_name} 设置为 {level}")
            return True
        except Exception as e:
            # 总是显示错误信息
            print(f"设置 {field_name} 失败: {e}")
            return False
    
    def get_account_level_field(self, account_name, field_name):
        """获取账号的指定级别字段"""
        return self.ac_manager.get_account(account_name, field_name)
    
    def auto_challenge_with_progress_field(self, account_name, shunwei, field_name, todo, maxtry=20):
        """带进度保存的自动挑战（支持指定字段）"""
        current_todo = int(todo)
        
        if int(shunwei) == 0:
            # 挑战之塔，支持连续挑战
            while True:
                print(f"\n开始挑战关卡 {current_todo}")
                success = self.execute_challenge(account_name, shunwei, current_todo, maxtry)
                
                if success:
                    # 计算下一关
                    if current_todo % 10 == 0:
                        next_todo = (current_todo // 100 + 1) * 100 + 1
                    else:
                        next_todo = current_todo + 1
                    
                    print(f"\n关卡{current_todo}完成，下一关卡{next_todo}")
                    current_todo = next_todo
                    
                    # 短暂暂停
                    time.sleep(1)
                else:
                    print(f"\n关卡{current_todo}失败，停止挑战")
                    break
        else:
            # 其他顺位，支持连续挑战直到失败
            while True:
                print(f"\n开始挑战顺位{shunwei}关卡{current_todo}")
                success = self.execute_challenge(account_name, shunwei, current_todo, maxtry)
                
                if success:
                    # 成功，保存下一级别并继续挑战
                    next_todo = current_todo + 1
                    print(f"\n关卡{current_todo}完成，下一关卡{next_todo}")
                    current_todo = next_todo
                    
                    # 短暂暂停
                    time.sleep(1)
                else:
                    # 失败，停止挑战
                    print(f"\n关卡{current_todo}失败，停止挑战")
                    break

    def buy_times(self, times):
        """购买次数"""
        config = {"ads": "购买次数","times": 1,"hexstringheader": "d12b", 'request_body_i2':19, 'request_body_i3':times}
        self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)