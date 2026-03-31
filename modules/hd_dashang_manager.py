"""
活动打赏管理模块
处理活动打赏监控相关功能
"""

import logging
import time
import threading
from . import kpbl_pb2
from .kpbltools import ACManager


class HDDashang:
    def __init__(self, account_name):
        self.account_name = account_name
        self.ac_manager = ACManager(account_name)
        self.logger = logging.getLogger(f"HDDashang_{account_name}")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.StreamHandler())
        
        # 重构数据管理结构 - 所有boxid内余量的数据表
        self.box_data_table = {}  # 格式: {box_key: {'current': box_data, 'previous': box_data, 'history': []}}
        
        self.running = False
        self.threads = []
        self.change_history = {}  # 存储变化历史，格式: {key: change_info}，永久保存
        self.temp_change_display = {}  # 临时显示变化，格式: {key: {'change': str, 'remaining_cycles': int}}
        self.current_cycle = 0  # 当前刷新周期
        self.current_results = {}  # 存储当前周期的所有结果，用于比较最低cost
        self.ever_seen_boxes = set()  # 记录曾经出现过的box，用于保留归零的box
        self.initial_values = {}  # 存储初始值，用于计算累计变化
        
        # 第三区域：已清空箱子的永久记录
        self.emptied_boxes_history = []  # 存储已清空箱子的完整状态，永久保存
        self.last_change_times = {}  # 记录每个box最后一次余量变化的时间
        
        # 独立线程刷新控制 - 重构版本
        self.boxid_threads = {}  # 每个boxid的监控线程
        self.boxid_refresh_intervals = {}  # 每个boxid的当前刷新间隔
        self.boxid_last_change_time = {}  # 每个boxid最后一次变化的时间
        self.boxid_no_change_count = {}  # 每个boxid连续无变化次数
        self.boxid_last_refresh_time = {}  # 每个boxid最后一次刷新的时间
        self.boxid_current_results = {}  # 每个boxid的最新结果
        self.boxid_stop_flags = {}  # 每个boxid的停止标志
        self.boxid_refresh_count = {}  # 每个boxid的总刷新次数
        self.base_refresh_interval = 60  # 基础刷新间隔（无变化时）
        self.active_refresh_interval = 3  # 活跃刷新间隔（有变化时）
        self.change_timeout = 60  # 1分钟内无变化则恢复初始间隔
        
        # 数据同步锁
        import threading
        self.data_lock = threading.Lock()
        
        # Box名称映射
        self.box_names = {
            1: "妖刀",
            2: "妖刀核心", 
            3: "鹿",
            4: "鹿核心",
            5: "椰子",
            6: "轩辕核心",
            7: "坐骑核心A",
            8: "坐骑核心B",
            9: "神器核心A",
            10: "神器核心B",
            11: "藏品",
            12: "烙印",
            13: "武器",
            14: "装备",
            15: "传承"
        }
        self.box_coin_config = {
            "box_1_4":{0:0,
1:0,
2:200,
3:0,
4:100,
5:0,
6:40,
-1:500},

"box_5_11":{0:0,
1:0,
2:120,
3:0,
4:60,
5:0,
6:30,
-1:400,},


"box_12_15":{0:0,
1:0,
2:80,
3:0,
4:40,
5:0,
6:10,
-1:200,},
        }
    
    def monitor_single_box(self, boxid, page=1):
        """监控单个boxid"""
        request_config = {
            "ads":"box monitor","times":1,"hexstringheader":"6d42",
            "request_body_i2":int(boxid),
            "request_body_i3":page,
        }
        try:
            res = self.ac_manager.do_common_request(self.account_name, request_config, showres=0)
            return self.resana(res)
        except Exception as e:
            self.logger.error(f"监控 boxid {boxid} 时出错: {e}")
            return []
    
    def monitor_boxid_thread(self, boxid, start_delay=0):
        """独立线程监控单个boxid"""
        import time
        import threading
        
        # 初始延迟，避免所有线程同时执行
        if start_delay > 0:
            self.logger.info(f"Box{boxid} 等待 {start_delay} 秒后开始监控")
            time.sleep(start_delay)
        
        # 初始化该boxid的状态
        with self.data_lock:
            self.boxid_refresh_intervals[boxid] = self.base_refresh_interval
            self.boxid_last_change_time[boxid] = time.time()
            self.boxid_last_refresh_time[boxid] = time.time()
            self.boxid_no_change_count[boxid] = 0
            self.boxid_current_results[boxid] = []
            self.boxid_stop_flags[boxid] = False
            self.boxid_refresh_count[boxid] = 0  # 初始化刷新次数
        
        self.logger.info(f"启动 boxid {boxid} 独立监控线程")
        
        while not self.boxid_stop_flags.get(boxid, False) and self.running:
            current_time = time.time()
            
            try:
                # 获取数据（支持多页）
                page1_results = self.monitor_single_box(boxid, page=1)
                
                # 检查第一页是否有 Aleft > 0 的箱子
                has_aleft_in_page1 = any(result.get('Aleft', 0) > 0 for result in page1_results)
                
                if not has_aleft_in_page1:
                    # 如果第一页没有 Aleft，尝试获取第二页
                    try:
                        page2_results = self.monitor_single_box(boxid, page=2)
                        combined_results = page1_results + page2_results
                    except Exception:
                        combined_results = page1_results
                else:
                    combined_results = page1_results
                
                # 检测变化并更新刷新间隔
                has_change = False
                with self.data_lock:
                    old_results = self.boxid_current_results.get(boxid, [])
                    
                    # 比较数据是否有变化
                    if old_results:
                        # 创建对比字典
                        old_dict = {f"{r['boxid']}-{r['boxseq']}": r for r in old_results}
                        new_dict = {f"{r['boxid']}-{r['boxseq']}": r for r in combined_results}
                        
                        for key, new_result in new_dict.items():
                            if key in old_dict:
                                old_result = old_dict[key]
                                if (new_result['left'] != old_result['left'] or 
                                    new_result['Aleft'] != old_result['Aleft']):
                                    has_change = True
                                    break
                    
                    # 更新数据
                    self.boxid_current_results[boxid] = combined_results
                    self.boxid_last_refresh_time[boxid] = current_time
                    self.boxid_refresh_count[boxid] += 1  # 增加刷新次数
                    
                    # 更新刷新间隔
                    if has_change:
                        self.boxid_refresh_intervals[boxid] = self.active_refresh_interval
                        self.boxid_last_change_time[boxid] = current_time
                        self.boxid_no_change_count[boxid] = 0
                        self.logger.debug(f"Box{boxid} 检测到变化，刷新间隔降至 {self.active_refresh_interval}秒")
                    else:
                        self.boxid_no_change_count[boxid] += 1
                        last_change_time = self.boxid_last_change_time.get(boxid, current_time)
                        
                        # 如果超过60秒没有变化，恢复到基础间隔
                        if current_time - last_change_time >= self.change_timeout:
                            if self.boxid_refresh_intervals[boxid] != self.base_refresh_interval:
                                self.boxid_refresh_intervals[boxid] = self.base_refresh_interval
                                self.logger.debug(f"Box{boxid} 超过{self.change_timeout}秒无变化，恢复基础刷新间隔 {self.base_refresh_interval}秒")
                
            except Exception as e:
                self.logger.error(f"Box{boxid} 监控线程出错: {e}")
            
            # 按照当前刷新间隔休眠
            refresh_interval = self.boxid_refresh_intervals.get(boxid, self.base_refresh_interval)
            time.sleep(refresh_interval)
        
        self.logger.info(f"Box{boxid} 监控线程已停止")
    
    def monitor(self, boxids, refresh_interval):
        """
        使用独立线程监控多个boxid - 重构版本
        每个boxid都有独立的刷新控制逻辑
        """
        import threading
        import time
        import sys
        import os
        
        # 处理单个boxid的情况
        if isinstance(boxids, (int, str)):
            boxids = [boxids]
        
        # 设置基础刷新间隔
        self.base_refresh_interval = refresh_interval
        self.running = True
        
        self.logger.info(f"开始独立线程监控 boxids: {boxids}, 基础刷新间隔: {refresh_interval}秒")
        
        # 启动每个boxid的独立监控线程，每个线程间隔2秒启动
        for i, boxid in enumerate(boxids):
            start_delay = i * 2  # 每个线程延迟2秒启动
            thread = threading.Thread(target=self.monitor_boxid_thread, args=(boxid, start_delay))
            thread.daemon = True
            thread.start()
            self.boxid_threads[boxid] = thread
            self.logger.info(f"启动Box{boxid}线程，延迟{start_delay}秒")
        
        # 清屏确保显示格式不受影响
        os.system('clear' if os.name == 'posix' else 'cls')
        
        try:
            cycle_count = 0
            
            while self.running:
                cycle_count += 1
                current_time = time.strftime('%H:%M:%S')
                
                # 收集所有线程的最新数据
                all_current_results = {}
                with self.data_lock:
                    for boxid in boxids:
                        box_results = self.boxid_current_results.get(boxid, [])
                        for result in box_results:
                            all_current_results[f"{result['boxid']}-{result['boxseq']}"] = result
                
                # 更新当前结果用于过滤
                self.current_results = all_current_results
                
                # 更新box数据表以计算变化量
                self.update_box_data_table(all_current_results)
                
                # 应用过滤条件
                filtered_results = self.filter_results_by_conditions(boxids)
                
                # 重新绘制整个界面
                self.render_screen(boxids, filtered_results, cycle_count, current_time, 0)
                
                # 界面每秒更新一次以显示动态倒计时
                time.sleep(1)
                
        except KeyboardInterrupt:
            print(f"\n监控已停止 (共刷新 {cycle_count} 次)")
            self.stop_monitor()
    
    def render_screen(self, boxids, filtered_results, cycle_count, current_time, refresh_interval):
        """重新渲染整个屏幕"""
        import os
        
        # 清屏
        os.system('clear' if os.name == 'posix' else 'cls')
        
        # 打印数据 - 分两个区域显示
        
        # 区域A：含Aleft的box
        print("=== 含Aleft区域 ===")
        has_aleft_data = False
        for i, boxid in enumerate(boxids):
            aleft_boxes = filtered_results['aleft'].get(boxid, [])
            if aleft_boxes:
                has_aleft_data = True
                for result in aleft_boxes:
                    print(self.format_with_progress(result))
        
        if not has_aleft_data:
            print("暂无含Aleft的箱子")
        
        print()
        print("=== 硬币性价比最高区域 ===")
        
        # 区域B：硬币性价比最高的box
        has_coins_data = False
        for i, boxid in enumerate(boxids):
            coins_boxes = filtered_results['coins'].get(boxid, [])
            if coins_boxes:
                has_coins_data = True
                for result in coins_boxes:
                    print(self.format_with_progress(result))
        
        if not has_coins_data:
            print("暂无硬币数据")
        
        # 第三区域：已清空箱子的永久记录
        print()
        print("=== 已清空箱子记录 ===")
        if self.emptied_boxes_history:
            # 按清空时间倒序显示（最新的在前）
            sorted_emptied = sorted(self.emptied_boxes_history, key=lambda x: x['emptied_timestamp'], reverse=True)
            for record in sorted_emptied:
                self.render_emptied_box(record)
        else:
            print("暂无已清空的箱子")
    

    
    def render_emptied_box(self, record):
        """渲染已清空箱子的记录，除了进度条以外都展示"""
        # 获取box名称
        box_name = self.box_names.get(record['boxid'], f"Box{record['boxid']}")
        
        # 格式化硬币信息
        total_coins = record.get('total_coins', 0)
        coins_per_cost = record.get('coins_per_cost', 0)
        cost_before = record.get('cost_before', 0)
        
        if cost_before == 0:
            if total_coins > 0:
                coin_info = f"({total_coins}c，∞per)"
            else:
                coin_info = "(0c，∞per)"
        elif total_coins > 0:
            coin_info = f"({total_coins}c，{coins_per_cost:.1f}per)"
        else:
            coin_info = ""
        
        # 检查是否含有Aleft，决定Box字体颜色
        has_aleft = record.get('aleft_before', 0) > 0
        if has_aleft:
            box_prefix = f"\033[31mBox{record['boxid']:2d}\033[0m"  # 红色Box
        else:
            box_prefix = f"Box{record['boxid']:2d}"  # 普通颜色
        
        # 格式化显示：不包含进度条，其他信息都保留
        emptied_info = f"{box_prefix}-{record['boxseq']:02d}: {record['left_before']:3d}→0 "
        emptied_info += f"c:{cost_before:4d} {coin_info} [{box_name}] (清空于{record['emptied_time']})"
        
        print(emptied_info)

    def create_progress_bar(self, current, max_val, width=30):
        """创建进度条"""
        if max_val == 0:
            return "░" * width
        
        progress = current / max_val
        filled = int(progress * width)
        bar = "█" * filled + "░" * (width - filled)
        return bar
    
    def find_min_cost_by_boxid(self, target_boxid):
        """找出指定boxid中的最低cost值（排除cost=0）"""
        min_cost = float('inf')
        for key, result in self.current_results.items():
            if result['boxid'] == target_boxid and result['cost'] > 0:
                min_cost = min(min_cost, result['cost'])
        return min_cost if min_cost != float('inf') else None
    
    def find_max_coins_per_cost_global(self):
        """找出全局硬币性价比最高的值"""
        max_coins_per_cost = 0
        for key, result in self.current_results.items():
            if result.get('coins_per_cost', 0) > max_coins_per_cost:
                max_coins_per_cost = result['coins_per_cost']
        return max_coins_per_cost if max_coins_per_cost > 0 else None
    

    
    def filter_results_by_conditions(self, boxids):
        """
        重构的过滤方法，分为两个区域：
        区域A：含Aleft的box（余量最少的一个 + 余量小于80%的）
        区域B：各box中硬币性价比最高的（包括归零后的持久显示）
        """
        aleft_results = {}  # 上区域：含Aleft的
        coins_results = {}  # 下区域：性价比最高的
        
        for boxid in boxids:
            # 获取该boxid的所有结果
            box_results = []
            for key, result in self.current_results.items():
                if result['boxid'] == boxid:
                    box_results.append(result)
            
            if not box_results:
                aleft_results[boxid] = []
                coins_results[boxid] = []
                continue
            
            # 区域A：含Aleft的box处理
            has_aleft_results = [r for r in box_results if r['Aleft'] > 0]
            a_boxes = []
            
            if has_aleft_results:
                # 1. 余量最少的一个（含Aleft的）
                min_left_with_aleft = min(has_aleft_results, key=lambda x: x['left'])
                a_boxes.append(min_left_with_aleft)
                
                # 2. 余量小于80%的（含Aleft的）
                under_80_with_aleft = [
                    r for r in has_aleft_results 
                    if (r.get('left', 0) / max(r.get('items_total', r.get('left', 1)), 1)) < 0.8
                ]
                for box in under_80_with_aleft:
                    if box not in a_boxes:
                        a_boxes.append(box)
            
            # 区域B：硬币性价比最高的box处理
            b_boxes = []
            if box_results:
                max_coins_per_cost_box = max(box_results, key=lambda x: x.get('coins_per_cost', 0))
                b_boxes.append(max_coins_per_cost_box)
                
                # 为每个boxid添加当前余量最小的box
                non_zero_boxes = [r for r in box_results if r.get('left', 0) > 0]
                if non_zero_boxes:
                    min_left_box = min(non_zero_boxes, key=lambda x: x.get('left', float('inf')))
                    if min_left_box not in b_boxes:
                        b_boxes.append(min_left_box)
            
            # 添加曾经出现过但现在归零的箱子（硬币行持久显示）
            for result in box_results:
                result_key = f"{result['boxid']}-{result['boxseq']}"
                if result_key in self.ever_seen_boxes and result.get('left', 0) == 0:
                    # 如果该box有硬币价值，添加到B区域
                    if result.get('total_coins', 0) > 0 and result not in b_boxes:
                        b_boxes.append(result)
            
            # 排序
            a_boxes.sort(key=lambda x: x['cost'])
            b_boxes.sort(key=lambda x: x['cost'])
            
            aleft_results[boxid] = a_boxes
            coins_results[boxid] = b_boxes
        
        return {'aleft': aleft_results, 'coins': coins_results}

    def format_with_progress(self, result):
        """格式化显示结果，包含进度条"""
        key = f"{result['boxid']}-{result['boxseq']}"
        
        # 记录初始值（第一次出现时）
        if key not in self.initial_values:
            self.initial_values[key] = {
                'left': result['left'],
                'Aleft': result['Aleft']
            }
        
        # 计算变化量
        current_change_parts = []  # 当次变化
        cumulative_change_parts = []  # 累计变化
        
        # 使用新的box_data_table获取previous数据
        if key in self.box_data_table and self.box_data_table[key]['previous']:
            prev = self.box_data_table[key]['previous']
            left_change = result['left'] - prev['left']
            aleft_change = result['Aleft'] - prev['Aleft']
            
            # 计算累计变化
            initial = self.initial_values[key]
            left_cumulative = result['left'] - initial['left']
            aleft_cumulative = result['Aleft'] - initial['Aleft']
            
            # 当次变化
            if left_change != 0:
                arrow = "↓" if left_change < 0 else "↑"
                if left_change < 0:
                    current_change_parts.append(f"\033[31m{arrow}{abs(left_change)}\033[0m")  # 红色
                else:
                    current_change_parts.append(f"\033[32m{arrow}{abs(left_change)}\033[0m")  # 绿色
            
            if aleft_change != 0:
                arrow = "↓" if aleft_change < 0 else "↑"
                if aleft_change < 0:
                    current_change_parts.append(f"\033[31mA{arrow}{abs(aleft_change)}\033[0m")  # 红色
                else:
                    current_change_parts.append(f"\033[32mA{arrow}{abs(aleft_change)}\033[0m")  # 绿色
            
            # 累计变化
            if left_cumulative != 0:
                arrow = "↓" if left_cumulative < 0 else "↑"
                if left_cumulative < 0:
                    cumulative_change_parts.append(f"{arrow}{abs(left_cumulative)}")
                else:
                    cumulative_change_parts.append(f"{arrow}{abs(left_cumulative)}")
            
            if aleft_cumulative != 0:
                arrow = "↓" if aleft_cumulative < 0 else "↑"
                if aleft_cumulative < 0:
                    cumulative_change_parts.append(f"A{arrow}{abs(aleft_cumulative)}")
                else:
                    cumulative_change_parts.append(f"A{arrow}{abs(aleft_cumulative)}")
            
            # 新的变化显示逻辑：
            # 格式：↓2 ( ↓2 / ↓41 )
            # - 括号前：最后一次变化，只显示5次刷新
            # - 括号内：最后一次变化 / 总变化，持久显示
            
            # 如果有当次变化，更新变化信息
            if current_change_parts:
                recent_change = " ".join(current_change_parts)
                
                # 保存到历史记录（括号内显示用）
                if key not in self.change_history:
                    self.change_history[key] = {}
                self.change_history[key]['last_change'] = recent_change
                
                # 设置临时显示（括号前显示用，5次刷新后消失）
                self.temp_change_display[key] = {
                    'change': recent_change,
                    'remaining_cycles': 5
                }
            
            # 始终更新累计变化信息
            if cumulative_change_parts:
                cumulative_change = " ".join(cumulative_change_parts)
                if key not in self.change_history:
                    self.change_history[key] = {}
                self.change_history[key]['total_change'] = cumulative_change
        
        # 更新临时显示的倒计时
        if key in self.temp_change_display:
            self.temp_change_display[key]['remaining_cycles'] -= 1
            if self.temp_change_display[key]['remaining_cycles'] <= 0:
                del self.temp_change_display[key]
        
        # 获取当前应该显示的变化信息
        display_change_info = ""
        
        # 括号前的临时显示（5次刷新后消失）
        temp_display = ""
        if key in self.temp_change_display:
            temp_display = self.temp_change_display[key]['change']
        
        # 括号内的持久显示
        persistent_display = ""
        if key in self.change_history:
            history = self.change_history[key]
            last_change = history.get('last_change', '')
            total_change = history.get('total_change', '')
            
            if last_change and total_change:
                persistent_display = f"({last_change} / {total_change})"
            elif last_change:
                persistent_display = f"({last_change})"
            elif total_change:
                persistent_display = f"({total_change})"
        
        # 组合显示：临时显示 + 持久显示
        if temp_display and persistent_display:
            display_change_info = f" {temp_display} {persistent_display}"
        elif temp_display:
            display_change_info = f" {temp_display}"
        elif persistent_display:
            display_change_info = f" {persistent_display}"
        
        # 历史数据更新已在update_box_data_table中处理，这里不需要重复
        
        # 使用当前box自己的items_total作为最大值
        max_left = result.get('items_total', result['left'])
        
        progress_bar = self.create_progress_bar(result['left'], max_left, 15)  # 缩短到15字符
        progress_percent = (result['left'] / max_left) * 100 if max_left > 0 else 0
        
        # 百分比显示：低于30%时显示为红色
        if progress_percent < 30:
            percent_display = f"\033[31m({progress_percent:5.1f}%)\033[0m"  # 红色
        else:
            percent_display = f"({progress_percent:5.1f}%)"
        
        # 检查是否是该boxid中cost最低的（排除cost=0）
        min_cost = self.find_min_cost_by_boxid(result['boxid'])
        is_min_cost = (min_cost is not None and result['cost'] == min_cost and result['cost'] > 0)
        
        # 检查是否是全局硬币性价比最高的
        max_coins_per_cost = self.find_max_coins_per_cost_global()
        is_max_coins_per_cost = (max_coins_per_cost is not None and 
                                result.get('coins_per_cost', 0) == max_coins_per_cost and 
                                result.get('coins_per_cost', 0) > 0)
        
        # 格式化cost显示（最低cost显示为绿色），包含硬币信息
        total_coins = result.get('total_coins', 0)
        coins_per_cost = result.get('coins_per_cost', 0)
        
        # 硬币信息格式：总硬币数/每cost硬币数
        # 全局性价比最高显示黄色，高性价比(≥40)显示为红色
        # 对于cost=0的情况，显示总硬币数和"∞"作为性价比
        if result['cost'] == 0:
            if total_coins > 0:
                coin_info = f"({total_coins}c，∞per)"
            else:
                coin_info = "(0c，∞per)"
        elif total_coins > 0:
            coin_base = f"({total_coins}c，{coins_per_cost:.1f}per)"
            if is_max_coins_per_cost:
                coin_info = f"\033[33m{coin_base}\033[0m"  # 黄色：全局性价比最高
            elif coins_per_cost >= 40:
                coin_info = f"\033[31m{coin_base}\033[0m"  # 红色：高性价比
            else:
                coin_info = coin_base
        else:
            coin_info = ""
        
        if is_min_cost:
            cost_display = f"\033[32mc:{result['cost']:4d}\033[0m {coin_info}"  # 绿色cost
        else:
            cost_display = f"c:{result['cost']:4d} {coin_info}"
        
        # 获取box名称
        box_name = self.box_names.get(result['boxid'], f"Box{result['boxid']}")
        
        # 计算距离下次刷新的秒数和总刷新次数
        import time
        current_time = time.time()
        boxid = result['boxid']
        refresh_interval = self.boxid_refresh_intervals.get(boxid, self.base_refresh_interval)
        last_refresh_time = self.boxid_last_refresh_time.get(boxid, current_time)
        time_since_last_refresh = current_time - last_refresh_time
        time_until_next_refresh = max(0, refresh_interval - time_since_last_refresh)
        seconds_until_next = int(time_until_next_refresh)
        total_refresh_count = self.boxid_refresh_count.get(boxid, 0)
        
        # 获取最后一次余量变化时间
        key = f"{result['boxid']}-{result['boxseq']}"
        last_change_time = self.last_change_times.get(key, None)
        if last_change_time:
            last_change_str = time.strftime('%H:%M:%S', time.localtime(last_change_time))
            time_suffix = f"，{last_change_str}"
        else:
            time_suffix = ""
        
        # 检查该box是否含有Aleft，决定Box字体颜色
        has_aleft = result['Aleft'] > 0
        if has_aleft:
            box_prefix = f"\033[31mBox{result['boxid']:2d}\033[0m"  # 红色Box
        else:
            box_prefix = f"Box{result['boxid']:2d}"  # 普通颜色
        
        # 格式化显示 - 将名称和倒计时秒数放在最后，保持进度条对齐，boxid固定2位宽度
        base_info = f"{box_prefix}-{result['boxseq']:02d}: [{progress_bar}] {result['left']:3d}/{max_left} {percent_display} "
        base_info += f"{cost_display}{display_change_info} [{box_name}] ({seconds_until_next}s，{total_refresh_count}{time_suffix})"
        
        return base_info
    

    
    def record_emptied_box(self, box_data, emptied_time):
        """记录被清空的箱子到第三区域"""
        import time
        
        # 创建清空记录
        emptied_record = {
            'boxid': box_data['boxid'],
            'boxseq': box_data['boxseq'],
            'left_before': box_data['left'],
            'aleft_before': box_data['Aleft'],
            'total_coins': box_data.get('total_coins', 0),
            'coins_per_cost': box_data.get('coins_per_cost', 0),
            'cost_before': box_data.get('cost', 0),
            'emptied_time': time.strftime('%H:%M:%S', time.localtime(emptied_time)),
            'emptied_timestamp': emptied_time
        }
        
        # 检查是否已存在相同的记录，避免重复
        box_key = f"{box_data['boxid']}-{box_data['boxseq']}"
        existing_record = None
        for record in self.emptied_boxes_history:
            if (record['boxid'] == box_data['boxid'] and 
                record['boxseq'] == box_data['boxseq']):
                existing_record = record
                break
        
        if existing_record:
            # 更新现有记录
            existing_record.update(emptied_record)
        else:
            # 添加新记录
            self.emptied_boxes_history.append(emptied_record)
        
        # 保留最近50个清空记录
        if len(self.emptied_boxes_history) > 50:
            self.emptied_boxes_history = self.emptied_boxes_history[-50:]
        
        self.logger.info(f"记录Box{box_data['boxid']}-{box_data['boxseq']:02d}清空状态")

    def stop_monitor(self):
        """停止所有监控线程"""
        self.running = False
        
        # 停止所有boxid线程
        with self.data_lock:
            for boxid in self.boxid_stop_flags:
                self.boxid_stop_flags[boxid] = True
        
        # 等待所有线程结束
        for boxid, thread in self.boxid_threads.items():
            if thread.is_alive():
                thread.join(timeout=2)
                if thread.is_alive():
                    self.logger.warning(f"Box{boxid} 线程未能正常停止")
        
        self.logger.info("所有监控线程已停止")
    
    def update_box_data_table(self, current_results):
        """更新余量数据表"""
        import time
        current_time = time.time()
        
        for key, result in current_results.items():
            if key not in self.box_data_table:
                # 初始化box数据
                self.box_data_table[key] = {
                    'current': result.copy(),
                    'previous': None,
                    'history': [],
                    'first_seen': current_time
                }
            else:
                # 更新数据
                self.box_data_table[key]['previous'] = self.box_data_table[key]['current'].copy()
                self.box_data_table[key]['current'] = result.copy()
                
                # 记录历史变化
                if self.box_data_table[key]['previous']:
                    prev = self.box_data_table[key]['previous']
                    if (result['left'] != prev['left'] or result['Aleft'] != prev['Aleft']):
                        change_record = {
                            'time': current_time,
                            'left_change': result['left'] - prev['left'],
                            'aleft_change': result['Aleft'] - prev['Aleft'],
                            'left_before': prev['left'],
                            'left_after': result['left'],
                            'aleft_before': prev['Aleft'],
                            'aleft_after': result['Aleft']
                        }
                        self.box_data_table[key]['history'].append(change_record)
                        
                        # 更新最后变化时间
                        self.last_change_times[key] = current_time
                        
                        # 检查是否有箱子被清空（从有余量变为0）
                        if prev['left'] > 0 and result['left'] == 0:
                            self.record_emptied_box(prev, current_time)
                        
                        # 保留最近100次变化记录
                        if len(self.box_data_table[key]['history']) > 100:
                            self.box_data_table[key]['history'] = self.box_data_table[key]['history'][-100:]

    def detect_changes_and_update_intervals(self, current_results):
        """检测变化并更新刷新间隔 - 改进版本"""
        import time
        current_time = time.time()
        
        # 先更新数据表
        self.update_box_data_table(current_results)
        
        # 按boxid分组检测变化
        boxid_changes = {}
        for key, result in current_results.items():
            boxid = result['boxid']
            if boxid not in boxid_changes:
                boxid_changes[boxid] = False
            
            # 初始化该boxid的刷新间隔和无变化计数
            if boxid not in self.boxid_refresh_intervals:
                self.boxid_refresh_intervals[boxid] = self.base_refresh_interval
            if boxid not in self.boxid_no_change_count:
                self.boxid_no_change_count[boxid] = 0
            
            # 检查是否有变化
            if key in self.box_data_table and self.box_data_table[key]['previous']:
                prev = self.box_data_table[key]['previous']
                current = self.box_data_table[key]['current']
                if (current['left'] != prev['left'] or current['Aleft'] != prev['Aleft']):
                    boxid_changes[boxid] = True
        
        # 更新各boxid的刷新间隔
        for boxid, has_change in boxid_changes.items():
            # 确保所有字典都包含该boxid
            if boxid not in self.boxid_refresh_intervals:
                self.boxid_refresh_intervals[boxid] = self.base_refresh_interval
            if boxid not in self.boxid_no_change_count:
                self.boxid_no_change_count[boxid] = 0
            if boxid not in self.boxid_last_change_time:
                self.boxid_last_change_time[boxid] = current_time
            if boxid not in self.boxid_last_refresh_time:
                self.boxid_last_refresh_time[boxid] = current_time
                
            if has_change:
                # 有变化，降低到活跃刷新间隔
                self.boxid_refresh_intervals[boxid] = self.active_refresh_interval
                self.boxid_last_change_time[boxid] = current_time
                self.boxid_no_change_count[boxid] = 0
                self.logger.debug(f"Box{boxid} 检测到变化，刷新间隔降至 {self.active_refresh_interval}秒")
            else:
                # 无变化，累加无变化次数
                self.boxid_no_change_count[boxid] += 1
                last_change_time = self.boxid_last_change_time.get(boxid, current_time)
                
                # 如果超过60秒没有变化，恢复到基础间隔
                if current_time - last_change_time >= self.change_timeout:
                    if self.boxid_refresh_intervals[boxid] != self.base_refresh_interval:
                        self.boxid_refresh_intervals[boxid] = self.base_refresh_interval
                        self.logger.debug(f"Box{boxid} 超过{self.change_timeout}秒无变化，恢复基础刷新间隔 {self.base_refresh_interval}秒")
    
    def calculate_coins(self, boxid, items):
        """计算箱子中的硬币总数"""
        # 根据boxid确定使用哪个配置
        if boxid in [1, 2, 3, 4]:
            coin_config = self.box_coin_config["box_1_4"]
            config_name = "box_1_4"
        elif boxid in [5, 6, 7, 8, 9, 10, 11]:
            coin_config = self.box_coin_config["box_5_11"]
            config_name = "box_5_11"
        elif boxid in [12, 13, 14, 15]:
            coin_config = self.box_coin_config["box_12_15"]
            config_name = "box_12_15"
        else:
            return 0  # 未配置的boxid返回0
        
        total_coins = 0
        debug_info = []
        
        for item in items:
            # item.itemid对应硬币类型，item.itemcount对应数量
            if item.itemid in coin_config:
                coins_per_item = coin_config[item.itemid]
                item_coins = item.itemcount * coins_per_item
                total_coins += item_coins
                debug_info.append(f"itemid={item.itemid}: {item.itemcount}x{coins_per_item}={item_coins}")
            else:
                debug_info.append(f"itemid={item.itemid}: 未匹配(count={item.itemcount})")
        
        # 调试输出
        # print(f"Box{boxid} 硬币计算调试:")
        # print(f"  配置: {config_name}")
        # print(f"  配置内容: {coin_config}")
        # for info in debug_info:
        #     print(f"  {info}")
        # print(f"  总硬币数: {total_coins}")
        # print()
        
        return total_coins
    
    def resana(self, res):
        data = res[6:]
        hd_dashang_huanxiang_resp = kpbl_pb2.hd_dashang_huanxiang_response()
        hd_dashang_huanxiang_resp.ParseFromString(data)
        
        boxid = hd_dashang_huanxiang_resp.boxid
        all_results = []  # 存储所有有效的box
        current_boxes = set()  # 当前存在的box
        boxcost = 3 if boxid in [1,2,3,4] else 2 if boxid in [5,6,7,8,9,10,11] else 1
        boxs = hd_dashang_huanxiang_resp.boxs
        
        # 收集当前所有box（包括Aleft=0的）
        for box in boxs:
            left = 0
            Aleft = 0
            items_total = 0
            
            # 计算left和Aleft
            for item in box.items:
                left += item.itemcount
                if item.itemid == 0:
                    Aleft = item.itemcount
            
            # 获取items_total - 这是一个repeated item列表，需要求和
            if hasattr(box, 'items_total') and box.items_total:
                items_total = sum(item.itemcount for item in box.items_total)
            else:
                # 如果没有items_total字段，使用left作为默认值
                items_total = left if left > 0 else 200  # 归零时给一个默认最大值
            
            box_key = f"{box.boxid}-{box.boxseq}"
            current_boxes.add(box_key)
            
            # 计算硬币数量
            total_coins = self.calculate_coins(box.boxid, box.items)
            
            # 记录曾经出现过的box（含Aleft或含硬币的）
            if Aleft > 0 or total_coins > 0:
                self.ever_seen_boxes.add(box_key)
            
            # 包含所有box：有余量的箱子都包含，以便后续过滤找到性价比最高的
            if left > 0 or (box_key in self.ever_seen_boxes):
                percentage = (left / items_total) * 100 if items_total > 0 else 0
                
                # 计算性价比（每cost对应多少硬币）
                coins_per_cost = total_coins / (boxcost * left) if (boxcost * left) > 0 else 0
                
                result = {
                    "boxid": box.boxid, 
                    "boxseq": box.boxseq, 
                    "left": left, 
                    "Aleft": Aleft, 
                    "cost": boxcost * left,
                    "items_total": items_total,
                    "percentage": percentage,
                    "is_zero": Aleft == 0,  # 标记是否为归零状态
                    "total_coins": total_coins,  # 箱子总硬币数
                    "coins_per_cost": coins_per_cost  # 每cost对应硬币数
                }
                all_results.append(result)
        
        # 新的过滤逻辑：
        # 1. 至少一个含有A的箱子（余量最少的）
        # 2. 每个boxid中性价比最高的箱子（每cost硬币数最多的）
        # 3. 显示所有余量小于80%的
        # 4. 排序：含A的在上，失去A的或归零的在下
        
        filtered_results = []
        
        # 分类results  
        has_A_results = [r for r in all_results if r['Aleft'] > 0]  # 含有A的
        under_80_results = [r for r in all_results if r['percentage'] <= 80]  # 小于80%的
        lost_A_or_zero_results = [r for r in all_results if r['is_zero']]  # 失去A的或归零的
        
        # 1. 确保至少有一个含有A的箱子（余量最少的）
        if has_A_results:
            min_A_result = min(has_A_results, key=lambda x: x['left'])
            filtered_results.append(min_A_result)
        
        # 2. 确保显示该boxid中性价比最高的箱子（每cost硬币数最多的）
        if all_results:
            max_coins_per_cost_result = max(all_results, key=lambda x: x['coins_per_cost'])
            if max_coins_per_cost_result not in filtered_results:
                filtered_results.append(max_coins_per_cost_result)
        
        # 3. 添加所有余量小于80%的（排除已选择的）
        for result in under_80_results:
            if result not in filtered_results:
                filtered_results.append(result)
        
        # 4. 添加失去A的或归零的箱子（排在下面）
        for result in lost_A_or_zero_results:
            if result not in filtered_results:
                filtered_results.append(result)
        
        # 排序：含A的在前，其他在后
        filtered_results.sort(key=lambda x: (x['Aleft'] == 0, x['cost']))
        
        # 移除临时字段，保持原有格式
        for result in filtered_results:
            result.pop('percentage', None)
            result.pop('is_zero', None)
        
        return filtered_results
    
    def dogacha(self, boxid, boxseq, bio=1):
        request_config_get_left = {
            "ads":"box left","times":1,"hexstringheader":"6b42",
            "request_body_i2":boxid,
            "request_body_i3":boxseq,
        }
        res = self.ac_manager.do_common_request(self.account_name, request_config_get_left, showres=0)
        data = res[6:]
        hd_dashang_huanxiang_resp = kpbl_pb2.hd_dashang_huanxiang_response()
        hd_dashang_huanxiang_resp.ParseFromString(data)
        print(hd_dashang_huanxiang_resp)
        boxid = hd_dashang_huanxiang_resp.boxid

        left = 0
        Aleft = 0
        items_total = 0
        
        # 计算left和Aleft
        for item in hd_dashang_huanxiang_resp.boxs[0].items:
            left += item.itemcount
            # if item.itemid == 0:
                # Aleft = item.itemcount
        # print(Aleft)
        # if Aleft > 0:
        request_config_do_gacha = {
            "ads":"box gacha","times":1,"hexstringheader":"6f42",
            "request_body_i2":boxid,
            "request_body_i3":boxseq,
            "request_body_i5":left-1,
            "request_body_i6":1, "requestbodytype":"request_body_allint"
        }
        print(request_config_do_gacha)
        res = self.ac_manager.do_common_request(self.account_name, request_config_do_gacha, showres=0)
        print(res)

    # def dogacha(self, boxid, boxseq, bio=1):
    #     request_config_get_left = {
    #         "ads":"box left","times":1,"hexstringheader":"6b42",
    #         "request_body_i2":boxid,
    #         "request_body_i3":boxseq,
    #     }
    #     res = self.ac_manager.do_common_request(self.account_name, request_config_get_left, showres=0)
    #     data = res[6:]
    #     hd_dashang_huanxiang_resp = kpbl_pb2.hd_dashang_huanxiang_response()
    #     hd_dashang_huanxiang_resp.ParseFromString(data)
        
    #     boxid = hd_dashang_huanxiang_resp.boxid

    #     left = 0
    #     Aleft = 0
    #     items_total = 0
        
    #     # 计算left和Aleft
    #     for item in hd_dashang_huanxiang_resp.boxs[0].items:
    #         left += item.itemcount
    #         if item.itemid == 0:
    #             Aleft = item.itemcount
    #     # print(res)
    #     if Aleft > 0:
    #         request_config_do_gacha = {
    #             "ads":"box gacha","times":1,"hexstringheader":"6f42",
    #             "request_body_i2":boxid,
    #             "request_body_i3":boxseq,
    #             "request_body_i5":left-1,
    #             "request_body_i6":1, "requestbodytype":"request_body_allint"
    #         }
    #         print(request_config_do_gacha)
    #         res = self.ac_manager.do_common_request(self.account_name, request_config_do_gacha, showres=0)
    #         print(res)