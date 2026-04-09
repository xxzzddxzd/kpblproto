"""
剧情战斗模块
重构自老代码中的dojq函数，专门处理剧情关卡战斗
"""

import binascii
from . import kpbl_pb2
from .kpbltools import ACManager, mask_account


def sth(hexstring):
    """将16进制字符串转换为二进制数据（从老代码移植）"""
    return binascii.unhexlify(hexstring.replace(" ", ""))


class StoryBattleManager:
    """剧情战斗管理器，专门处理dojq（剧情）战斗逻辑"""
    
    def __init__(self, account_name, showres=0, delay=0.5, ac_manager=None):
        self.account_name = account_name
        self.showres = showres
        self.ac_manager = ac_manager or ACManager(account_name, delay=delay, showres=showres)
        # return self.ac_manager.get_account(account_name, 'gqxx')
    
    def _get_hardcoded_battle_data(self):
        """获取硬编码的战斗数据（从老代码原样移植）"""
        return binascii.unhexlify(
            '0b2b33040a920310011a2445433630304634342d454631362d343933302d384537322d3535323737'
            '4546324432393622c002594e5152'
            '4662514f397770425a70417244626865666e71567a46356950774a66717341744f7573432b6f6539'
            '35463573476746344e4a62466c556832702b51662f59616c4b527765735466384d6b4745615a624c'
            '4e415067457944523045685941574a537463756f494a5575582b5a4c57674430363459337a505631'
            '72752f655737663250373134593442466c644b415576436f446153337a65474d3647467631585a73'
            '4d714d454c59537974526f355430367675765a786e32526c326431364d6758554971557433392f53'
            '3032364e553364483355756c467173544256674464327339705873715270707633346d3732596435'
            '4d4b636e33724e6a794c5455484a4e4d746872436d696a597074356962575a61574d686d55796972'
            '79526a6a37707547736d63482f3772443357395564767442556e7254745430514a4b797528c96330'
            'e0c7183a114368696e65736553696d706c696669656440ea055206312e352e313458521001183c22'
            '2041747461636b253d39377c446566656e6365253d32327c48504d6178253d32382a2dcf8f06dddd'
            '06fc9106ff9106fb9106839206c7a907ae8d068192068f8e06fd9106f38e06ce8f06ba8d06969106'
            '32015a38d7054a03373436528b040a090801120508023a01000a04080212000a04080312000a0408'
            '0412000a04080512000a04080612000a07080712033a01000a04080812000a08080912043a020000'
            '0a07080a12033a01000a07080b12033a01000a04080c12000a04080d12000a04080e12000a07080f'
            '12033a01000a07081012033a01000a04081112000a04081212000a07081312033a01000a07081412'
            '033a01000a07081512033a01000a04081612000a04081712000a07081812033a01000a0808191204'
            '3a0200000a06081a120218010a04081b12000a04081c12000a07081d12033a01000a07081e12033a'
            '01000a07081f12033a01000a07082012033a01000a04082112000a04082212000a07082312033a01'
            '000a07082412033a01000a04082512000a04082612000a07082712033a01000a0a0828120610023a'
            '0200000a090829120530013a01000a07082a12033a01000a04082b12000a04082c12000a06082d12'
            '0228020a08082e12043a0200000a04082f12000a04083012000a04083112000a07083212033a0100'
            '0a07083312033a01000a04083412000a04083512000a07083612033a01000a07083712033a01000a'
            '04083812000a04083912000a07083a12033a01000a07083b12033a01001206080212020802120608'
            '03120208021204080412001204080512001206080612020801120608071202080112060808120208'
            '0212060809120208011206080a12020802a2022d7b224265664c69666547617a6552657669766522'
            '3a302c224166744c69666547617a65526576697665223a307d'
        )
    

    def donewaccount(self):
        # req_configs = [
        #     {"ads":"q1","times":1,"hexstringheader":"c12b"},
        #     {"ads":"q2","times":1,"hexstringheader":"9b2c"},
        #     {"ads":"q3","times":1,"hexstringheader":"9d2c"},
        #     {"ads":"q4","times":1,"hexstringheader":"e935"},
        #     {"ads":"q5","times":1,"hexstringheader":"9575"},
        #     {"ads":"q6","times":1,"hexstringheader":"dd2b"},
        #     {"ads":"q7","times":1,"hexstringheader":"9f27"},
        #     {"ads":"q7","times":1,"hexstringheader":"0529"},
        #     {"ads":"q8","times":1,"hexstringheader":"f177"},
        #     {"ads":"q9","times":1,"hexstringheader":"4d4f"},
        #     {"ads":"q10","times":1,"hexstringheader":"8330"}, # 94
        #     {"ads":"q7","times":1,"hexstringheader":"8d27"},

            
        #     {"ads":"q21","times":1,"hexstringheader":"4151"}, # 94
        # ]
        # for config in req_configs:
        #     self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)        
        # self.execute_story_battle(1)
        req_configs =[
            # {"ads":"培养-宠物蛋3次","request_body_i2":11,"hexstringheader":"f14e","times":3},
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
            {"ads":"签到","times":1,"hexstringheader":"ef2c"},
            {"ads":"免费10体力","times":1,"hexstringheader":"a527"},

        ]

        for config in req_configs:
            self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        # level = 2
        # while level<4:
        #     self.execute_story_battle(level)
        #     level+=1
        # self.execute_story_battle(4)
        # self.execute_story_battle(5)


    def dotfqh(self):
        # config_qh = [
        #     {"ads":"tsAttack","times":10,"hexstringheader":"7f30 ", 'request_body_i2':"Attack", "request_body_i3":level, 'requestbodytype':'request_qh'}, 
        #     {"ads":"tsHPMax","times":10,"hexstringheader":"7f30 ", 'request_body_i2':"HPMax", "request_body_i3":level, 'requestbodytype':'request_qh'}, 
        #     {"ads":"tsDefence","times":10,"hexstringheader":"7f30 ", 'request_body_i2':"Defence", "request_body_i3":level, 'requestbodytype':'request_qh'},         
        # ]
        todo = {
            "Attack":0,
            "HPMax":0,
            "Defence":0
        }
        next_todo = {
            "Attack":0,
            "HPMax":0,
            "Defence":0
        }
        config = {"ads":"tsDefence","times":1,"hexstringheader":"7f30 ", 'request_body_i2':"Defence", "request_body_i3":1, 'requestbodytype':'request_qh'}
        res = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        if not res:
            return 0
        tfqh_resp = kpbl_pb2.tfqh_response()
        tfqh_resp.ParseFromString(res[6:])
        level = tfqh_resp.tf.level
        # print(tfqh_resp)
        for tfxq in tfqh_resp.tf.tfxq:
            todo[tfxq.tfms] = tfxq.tfdj
        # print(todo)
        # input('sss')
        if level < 34:
            cap = 10
        else:
            cap = 15
        for key in todo:
            while todo[key]<cap:
                config = {"ads":key,"times":1,"hexstringheader":"7f30 ", 'request_body_i2':key, "request_body_i3":level, 'requestbodytype':'request_qh'}
                rev = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
                tfqh_resp = kpbl_pb2.tfqh_response()
                tfqh_resp.ParseFromString(rev[6:])
                # print(tfqh_resp)
                for tfxq in tfqh_resp.tf.tfxq:
                    next_todo[tfxq.tfms] = tfxq.tfdj
                
                # 对比 todo 和next_todo，若完全一样，则返回0
                if todo[key] == next_todo[key]:
                    print('未变化，无money')
                    return 0
                todo = next_todo
                next_todo = {
                    "Attack":0,
                    "HPMax":0,
                    "Defence":0
                }


        return 1
        

    def execute_story_battle(self, level):
        """
        执行剧情战斗（完全按照老代码dojq函数重构）
        
        Args:
            level: 关卡等级
            
        Returns:
            bool: 战斗是否成功
        """
        if level == 0:
            level = self.ac_manager.get_account(self.account_name, 'gqxx') + 1
        if self.showres:
            print(f"<{mask_account(self.account_name)}> 开始剧情战斗 - 关卡 {level}")
        
        try:
            # 步骤1: 开始战斗（原样复制老代码逻辑）
            battle_start = {"ads": "战斗开始", "times": 1, "hexstringheader": "212b", "request_body_i2": level}
            res = self.ac_manager.do_common_request(self.account_name, battle_start, showres=self.showres)
            
            if len(res) < 100:
                if self.showres:
                    print(f"战斗开始失败{level}")
                code = self.ac_manager.get_status_code(res)
                if code == 132:
                    print(f"无体力")
                else:
                    print(res)
                return False
            
            # 步骤2: 解析战斗响应
            battle_response = kpbl_pb2.battle_response()
            battle_response.ParseFromString(res[6:])
            max_turn = battle_response.turns[-1].round_number
            
            if self.showres:
                print(f"  战斗回合数: {max_turn}")
            
            # 步骤3: 构建战斗更新数据
            savedfile = self._get_hardcoded_battle_data()
            battle_update = kpbl_pb2.request_body_for_jqupdate()
            battle_update.ParseFromString(savedfile[4:])
            battle_update.i2 = level
            battle_update.i3 = max_turn
            battle_update.i4 = 'Attack%=597|Defence%=520|HPMax%=580'
            
            # 步骤4: 发送战斗更新请求（完全按照老代码）
            self.ac_manager.do_request_by_binary(self.account_name, savedfile[:2].hex(), battle_update, showres=self.showres)
            
            # 步骤5: 发送战斗结束请求（完全按照老代码）
            battle_end = {
                "ads": "战斗结束",
                "times": 1,
                "hexstringheader": "232b",
                "request_body_i2": level,
                "request_body_i3": max_turn,
                "request_body_i4": 1,
                "request_body_i7": sth('969106a48d06a58d06a78d06aa8d06ad8d06b19006b28d06b29006b38d06b39006b49006b68d06b78d06b88d06c29306c39306c49306cd8f06ce8f06d08f06d78f06dd9206de9206f99106fa9106fb9106fc9106fd9106b4db06b7db06dddd06dedd06e0dd06e7dd06ede006eee00689e0068ae0068be0068ce0068de006819206868e068b8e068c8e068d8e068e8e068f8e06908e06918e06928e06999106c79306c89306d28f06d58f0695dc0696dc069adc069bdc069cdc069ddc069edc069fdc06a0dc06a1dc06a2dc06829206ff9106d68f068392069b9106e98e06eb8e06ec8e06f28e06f38e06f48e06f58e06f68e06'),
                "requestbodytype": "request_body_for_jqfinish"
            }
            
            # 使用 docommonrequest 的等价方法
            battle_end_res = self.ac_manager.do_common_request(self.account_name, battle_end, showres=self.showres)
            battle_end_resp = kpbl_pb2.battle_end_response()
            battle_end_resp.ParseFromString(battle_end_res[6:])
            if battle_end_resp.update_gqxx > level:
                if self.showres:
                    print(f"✓ 剧情战斗执行完成 - 下一个关卡 {battle_end_resp.update_gqxx}")
                # return True
            else:
                if self.showres:
                    print(f"✗ 剧情战斗失败 - 关卡 {battle_end_resp.update_gqxx}")
            return battle_end_resp.update_gqxx
            # return False
            
        except Exception as e:
            if self.showres:
                print(f"✗ 剧情战斗失败 - 关卡 {level}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def execute_xjtz_zs(self): # 星级挑战钻石获取
        config = {"ads":f"星级挑战钻石获取","times":1,"hexstringheader":"272b", 'request_body_i2':1}
        self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
    
    def execute_zjbx(self, level, step): # 章节宝箱获取
        config = {"ads":f"章节宝箱获取","times":1,"hexstringheader":"fd2a", 'request_body_i2':level, 'request_body_i3':step}
        self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)

    def execute_zjbx_list(self, levelnboxlist): # 章节宝箱获取
        req_list = []
        for unit in levelnboxlist:
            config = {"ads":f"章节宝箱获取","times":1,"hexstringheader":"fd2a", 'request_body_i2':unit[0], 'request_body_i3':unit[1]}
            req_list.append(config)
        self.ac_manager.do_common_request_list(self.account_name, req_list, showres=self.showres)

    def execute_story_sequence(self, start_level=2, end_level=5):
        """
        执行完整的剧情序列
        
        Args:
            start_level: 起始关卡
            end_level: 结束关卡
            
        Returns:
            bool: 所有剧情关卡是否成功
        """
        if self.showres:
            print(f"\n=== 开始剧情序列: {start_level}-{end_level} 关卡 ===")
        
        success_count = 0
        total_count = end_level - start_level + 1
        
        for level in range(start_level, end_level + 1):
            if self.execute_story_battle(level):
                success_count += 1
            import time
            time.sleep(1)  # 战斗间隔
        
        if self.showres:
            print(f"=== 剧情序列完成: {success_count}/{total_count} ===")
        return success_count == total_count
    


    def _analyze_battle_result(self, response_data, level):
        """
        分析战斗结束响应，提取通过/未通过标识
        
        基于重新对比分析 response_战斗结束_win 和 response_战斗结束_lose：
        - 胜利：末尾字段 7: 3，且包含复杂的字段7结构（含子字段）
        - 失败：末尾字段 7: 2，无复杂字段7结构
        
        Args:
            response_data: 战斗结束响应的二进制数据
            level: 关卡等级
            
        Returns:
            dict: 包含success(bool)和status(str)的结果字典
        """
        try:
            if not response_data or len(response_data) < 10:
                return {"success": False, "status": "响应数据不完整"}
            
            # 跳过头部6字节，分析protobuf数据
            data = response_data[6:]
            
            # 胜利的特征：
            # 1. 末尾有字段7=3 (编码为 0x38 0x03)
            # 2. 数据更长（胜利响应382字节 vs 失败响应326字节）
            # 3. 包含复杂的字段7结构
            
            battle_result = None
            
            # 检查末尾字段7的值
            if data.endswith(b'\x38\x03'):  # 字段7=3，表示胜利
                battle_result = "win"
            elif data.endswith(b'\x38\x02'):  # 字段7=2，表示失败
                battle_result = "lose"
            else:
                # 检查数据中是否存在字段7=3的模式
                if b'\x38\x03' in data:
                    battle_result = "win"
                elif b'\x38\x02' in data:
                    battle_result = "lose"
                else:
                    # 基于数据长度的启发式判断
                    # 胜利响应通常更长（包含更多奖励信息）
                    if len(data) > 350:  # 胜利响应约382字节，失败约326字节
                        battle_result = "win"
                    elif len(data) < 330:
                        battle_result = "lose"  
                    else:
                        # 检查是否包含复杂字段7结构的特征
                        # 胜利响应包含字段7的子结构
                        if b'\x3a' in data:  # 字段7的子字段标识
                            battle_result = "win"
                        else:
                            battle_result = "lose"
            
            if battle_result == "win":
                return {"success": True, "status": "(胜利)"}
            elif battle_result == "lose":
                return {"success": False, "status": "(失败)"}
            else:
                # 默认认为成功，保持与老代码一致
                return {"success": True, "status": "(完成)"}
                
        except Exception as e:
            if self.showres:
                print(f"分析战斗结果时出错: {e}")
            # 出错时默认认为成功，保持与老代码一致
            return {"success": True, "status": "(未知结果)"}



