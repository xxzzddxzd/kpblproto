"""
公会管理模块
处理游戏中的公会功能：加入、退出、捐献、批量管理
"""

import json
import logging
import random
from .kpbltools import ACManager, mask_account


class GuildManager:
    """公会管理器"""

    def __init__(self, account_name, showres=0, delay=0.5):
        self.account_name = account_name
        self.ac_manager = ACManager(account_name, showres=showres, delay=delay)
        self.logger = logging.getLogger(f"GuildManager_{account_name}")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.StreamHandler())
        self.showres = showres

    def join(self, guild_id=None):
        """申请加入公会"""
        config = {"ads": "加入公会", "times": 1, "hexstringheader": "a375"}
        if guild_id:
            config["request_body_i2"] = guild_id
        res = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        print(f"<{mask_account(self.account_name)}> 加入公会完成, res长度: {len(res)}")
        return len(res) > 20

    def approve(self, charaid):
        """同意加入公会"""
        config = {"ads": "同意加入公会", "times": 1, "hexstringheader": "ab75", "request_body_i2": charaid}
        res = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        print(f"<{mask_account(self.account_name)}> 同意加入公会完成, res长度: {len(res)}")
        return len(res) > 20

    def quit(self):
        """退出公会"""
        config = {"ads": "退出公会", "times": 1, "hexstringheader": "b175"}
        res = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        print(f"<{mask_account(self.account_name)}> 退出公会完成, res长度: {len(res)}")
        return len(res) > 20

    def donate(self):
        """工会捐献5"""
        config = {"ads": "工会捐献5", "times": 5, "hexstringheader": "2977"}
        res = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        print(f"<{mask_account(self.account_name)}> 工会捐献5完成, res长度: {len(res)}")
        return len(res) > 20

    def guild_info(self):
        """获取公会信息"""
        config = {"ads": "获取公会信息", "times": 1, "hexstringheader": "9575"}
        res = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        print(f"<{mask_account(self.account_name)}> 获取公会信息完成, res长度: {len(res)}")
        return res

    def nickname_re(self, new_name):
        """重命名角色"""
        config = {
            "ads": "改名", "times": 1, "hexstringheader": "8127",
            "request_body_i2": new_name, "request_body_i3": 1004, "request_body_i4": 2031,
            "requestbodytype": "request_body_for_nickname"
        }
        res = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        return res

    def kickoff(self, charaid):
        """踢出成员"""
        config = {"ads": "踢出成员", "times": 1, "hexstringheader": "af75", "request_body_i2": charaid}
        res = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        return res

    def get_daily_task_status(self):
        """查询日常任务面板，返回(日活, 周活) 或 None"""
        config = {"ads": "日常任务查询", "times": 1, "hexstringheader": "0529"}
        res = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        if not res or len(res) < 10:
            return None
        try:
            from . import kpbl_pb2
            resp = kpbl_pb2.daily_task_response()
            resp.ParseFromString(res[6:])
            return (resp.daily_activity, resp.weekly_activity)
        except Exception:
            pass
        # fallback: 尝试不跳过前6字节
        try:
            from . import kpbl_pb2
            resp = kpbl_pb2.daily_task_response()
            resp.ParseFromString(res)
            return (resp.daily_activity, resp.weekly_activity)
        except Exception:
            pass
        # 都解析不了，用decode_raw看看实际内容
        import subprocess, tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
            f.write(res)
            tmppath = f.name
        for skip in [6, 0, 4]:
            r = subprocess.run(f'dd bs=1 skip={skip} if={tmppath} 2>/dev/null | ./protoc --decode_raw',
                              shell=True, capture_output=True, text=True,
                              cwd='/Users/xuzhengda/Documents/workspace/kpbl/proto')
            if r.stdout.strip() and 'Failed' not in r.stdout:
                print(f"<{mask_account(self.account_name)}> 日常任务raw(skip={skip},len={len(res)}):\n{r.stdout.strip()[:500]}")
                # 尝试从raw输出提取日活/周活
                lines = r.stdout.strip().split('\n')
                vals = {}
                for line in lines:
                    s = line.strip()
                    for field_num in ['3', '4']:
                        if s == f'{field_num}: ' or s.startswith(f'{field_num}: '):
                            parts = s.split(': ', 1)
                            if len(parts) == 2 and parts[1].isdigit():
                                vals[field_num] = int(parts[1])
                if '3' in vals and '4' in vals:
                    return (vals['3'], vals['4'])
                break
        print(f"<{mask_account(self.account_name)}> 日常任务解析失败, res长度={len(res)}, 前20字节={res[:20].hex()}")
        return None


class GuildBatchManager:
    """公会批量管理器 — 以会长号为基准管理小号"""

    @staticmethod
    def guild_file(leader_account):
        return f'ac_{leader_account}_guild.json'

    @staticmethod
    def guild_dir(leader_account):
        """公会小号的账号文件存放目录"""
        return f'ac_{leader_account}'

    @staticmethod
    def guild_account_file(leader_account, account_name):
        """公会小号的账号文件路径"""
        return f'ac_{leader_account}/{account_name}.json'

    def __init__(self, leader_account, showres=0, delay=0.3):
        self.leader_account = leader_account
        self.accounts_file = self.guild_file(leader_account)
        self.accounts_dir = self.guild_dir(leader_account)
        self.showres = showres
        self.delay = delay
        self.guild_name = None  # 延迟获取
        self.guild_member_names = None  # 延迟获取
        import json
        with open(self.accounts_file, 'r') as f:
            self.guild_accounts = json.load(f)
        print(f"加载了 {len(self.guild_accounts)} 个公会小号 ({self.accounts_file})")

    def _get_guild_name(self):
        """获取公会名称（带缓存）"""
        if self.guild_name:
            return self.guild_name
        try:
            gm = GuildManager(self.leader_account, showres=0, delay=0)
            res = gm.guild_info()
            if res and len(res) > 20:
                from . import kpbl_pb2
                info = kpbl_pb2.guild_info_response()
                info.ParseFromString(res[6:])
                self.guild_name = info.guild_basic.guild_detail.guild_name
                return self.guild_name
        except Exception as e:
            print(f"获取公会名称失败: {e}")
        return None

    def _get_guild_member_names(self):
        """获取公会成员名称集合（带缓存），返回 set 或 None"""
        if self.guild_member_names is not None:
            return self.guild_member_names
        try:
            gm = GuildManager(self.leader_account, showres=0, delay=0)
            res = gm.guild_info()
            if res and len(res) > 20:
                from . import kpbl_pb2
                info = kpbl_pb2.guild_info_response()
                info.ParseFromString(res[6:])
                self.guild_member_names = {m.member_name for m in info.guild_basic.members}
                print(f"公会成员: {len(self.guild_member_names)}人")
                return self.guild_member_names
        except Exception as e:
            print(f"获取公会成员列表失败: {e}")
        return None

    def _is_guild_member(self, account_name):
        """判断账号是否属于公会成员（优先用charaname精确匹配，fallback到server_id后4位）"""
        members = self._get_guild_member_names()
        if members is None:
            return True  # 查询失败时不跳过
        # 优先用charaname精确匹配
        charaname = self.guild_accounts.get(account_name, {}).get('charaname', '')
        if charaname and charaname in members:
            return True
        # fallback: server_id后4位匹配
        sid = str(self.guild_accounts.get(account_name, {}).get('server_id', ''))
        sid_suffix = sid[-4:]
        for mname in members:
            if sid_suffix in mname:
                return True
        return False

    @staticmethod
    def _expected_name_prefix(guild_name, server_id):
        """生成期望的角色名前缀: {公会名前2字符}{server_id后4位}"""
        return f"{guild_name[:2]}{str(server_id)[-4:]}"

    @staticmethod
    def _gen_nickname(guild_name, server_id):
        """生成完整昵称: 前缀 + 3位随机字母"""
        import random, string
        prefix = GuildBatchManager._expected_name_prefix(guild_name, server_id)
        suffix = ''.join(random.choices(string.ascii_lowercase, k=3))
        return prefix + suffix

    # ── 静态工具 ──

    @staticmethod
    def gen_accounts(leader_account, count=30, start_server_id=None):
        """从会长号生成公会小号账号文件，自动跳过会长的server_id"""
        import json
        with open(f'ac_{leader_account}.json', 'r') as f:
            base = json.load(f)[leader_account]
        leader_sid = base['server_id']
        if not start_server_id:
            start_server_id = leader_sid + 1
        accounts = {}
        sid = start_server_id
        for i in range(1, count + 1):
            if sid == leader_sid:  # 跳过会长所在服务器
                sid += 1
            accounts[f"{leader_account}g{i}"] = {
                "udid": base["udid"],
                "server_id": sid, 
                # "acstr": base["acstr"],
                # "s1": base["s1"], 
            }
            sid += 1
        out_file = GuildBatchManager.guild_file(leader_account)
        with open(out_file, 'w') as f:
            json.dump(accounts, f, indent=4)
        sids = [a['server_id'] for a in accounts.values()]
        print(f"已生成 {count} 个账号到 {out_file}")
        print(f"server_id: {min(sids)}~{max(sids)} (跳过会长sid={leader_sid})")

    @staticmethod
    def show_overview(leader_account):
        """显示管理概览"""
        import json, os
        gf = GuildBatchManager.guild_file(leader_account)
        print(f"══════ 公会管理 ({leader_account}) ══════")
        if os.path.exists(gf):
            with open(gf, 'r') as f:
                accs = json.load(f)
            sids = [a['server_id'] for a in accs.values()]
            init_count = sum(1 for n in accs if os.path.exists(GuildBatchManager.guild_account_file(leader_account, n)))
            print(f"  账号文件: {gf}  |  小号: {len(accs)}  |  sid: {min(sids)}~{max(sids)}  |  已init: {init_count}/{len(accs)}")
        else:
            print(f"  ⚠ 尚未生成小号，请先执行: {leader_account} gg gen [数量]")
        for cmd, desc in [
            ("gen [数量] [起始sid]", "生成小号"), ("init [线程数]", "初始化+加入公会"),
            ("join/j [起始序号]", "加入公会"), ("approve", "批准待审核"),
            ("donate/d", "捐献"), ("daily", "日常(捐献+扫荡)"),
            ("da", "日常任务"), ("defda", "默认日常"),
            ("jq [起始序号]", "剧情战斗"),
            ("yl [起始序号]", "游历(固定20倍)"),
            ("tf [起始序号]", "天赋强化"),
            ("xyx [起始序号]", "幸运星"),
            ("run [起始序号]", "一条龙(按pipeline配置)"),
            ("seq [起始序号] cmd1,cmd2...", "顺序执行多个命令(逗号分隔)"),
            ("pipeline [set 任务列表]", "查看/设置pipeline配置"),
            ("check", "检查小号公会状态"), ("status/s", "收集日活/周活/钻石"),
            ("help", "详细帮助"),
        ]:
            print(f"  {cmd:26s} - {desc}")

    @staticmethod
    def show_help(leader_account):
        """显示详细帮助"""
        a = leader_account
        print(f"══════ 公会批量管理帮助 ══════")
        print(f"以会长号为基准，管理同账号不同服务器的小号组成公会。\n")
        print(f"首次建会: {a} gg gen → {a} gg init → {a} gg donate")
        print(f"日常维护: {a} gg daily / {a} gg da / {a} gg defda\n")
        print(f"gen 参数: {a} gg gen [数量] [起始sid]  (默认30个, sid从会长+1)")

    # ── 实例方法 ──

    @staticmethod
    def _fmt_zhanli(val):
        if val >= 1_000_000_000_000: return f"{val / 1_000_000_000_000:.2f}T"
        elif val >= 1_000_000_000: return f"{val / 1_000_000_000:.2f}B"
        elif val >= 1_000_000: return f"{val / 1_000_000:.2f}M"
        elif val >= 1_000: return f"{val / 1_000:.1f}K"
        return str(val)

    def batch_info(self, items=None):
        """显示公会信息，成员按名称排序，附带status数据。items: 要显示的物品type列表"""
        from . import kpbl_pb2
        gm = GuildManager(self.leader_account, showres=0, delay=0)
        res = gm.guild_info()
        if not res or len(res) < 20:
            print("获取公会信息失败")
            return False
        info = kpbl_pb2.guild_info_response()
        info.ParseFromString(res[6:])
        gd = info.guild_basic.guild_detail
        role_names = {1: "会长", 2: "副会长", 4: "成员"}
        # 加载status数据，按server_id建索引
        import time
        from datetime import datetime, timezone, timedelta
        now = time.time()
        beijing_tz = timezone(timedelta(hours=8))
        beijing_offset = 8 * 3600  # UTC+8
        day_start_offset = 8 * 3600  # 每天8点为起始
        # 当前北京时间对应的"逻辑日"起始时间戳（UTC）
        beijing_now = now + beijing_offset
        today_start_utc = (int(beijing_now - day_start_offset) // 86400) * 86400 + day_start_offset - beijing_offset
        # 按 charaname 建索引，精确匹配每个账号
        name_status = {}   # charaname -> (daily, weekly, diamond, coin, tl, status_time, is_today, account_key, baginfo)
        for name, acc in self.guild_accounts.items():
            charaname = acc.get('charaname', '')
            if not charaname:
                continue
            daily = acc.get('daily_activity')
            weekly = acc.get('weekly_activity')
            diamond = acc.get('diamond')
            coin = acc.get('coin', 0)
            tl = acc.get('tl', 0)
            status_time = acc.get('status_time', 0)
            baginfo = acc.get('baginfo', {})
            if daily is not None and status_time > 0:
                is_today = status_time >= today_start_utc
                name_status[charaname] = (daily, weekly, diamond, coin, tl, status_time, is_today, name, baginfo)

        print(f"══════ 公会信息 ══════")
        print(f"  名称: {gd.guild_name} (ID:{gd.guild_id})  Lv{gd.guild_level}")
        print(f"  成员: {gd.member_count}/{gd.max_members}  战力: {self._fmt_zhanli(gd.guild_zhanli)}  🔥{gd.weekly_donation}")
        # 按 guild_accounts 中的顺序排序：匹配到的按 json key 顺序，未匹配的排后面
        guild_order = {cn: idx for idx, cn in enumerate(
            acc.get('charaname', '') for acc in self.guild_accounts.values()
        ) if cn}
        members = sorted(info.guild_basic.members,
                         key=lambda m: guild_order.get(m.member_name, len(guild_order)))
        if members:
            has_status = bool(name_status)
            header = f"── 成员列表 ({len(members)}人)"
            if has_status:
                header += " [含status数据]"
            header += " ──"
            print(header)
            for m in members:
                role = role_names.get(m.role, f"?{m.role}")
                online = "🟢" if m.is_online else "  "
                line = f"  {online} [{role}] {m.member_name:20s} Lv{m.level:<4d} 战力:{self._fmt_zhanli(m.member_zhanli):>8s} 🔥{m.contribution}"
                matched = name_status.get(m.member_name)
                if matched:
                    d, w, dm, cn, tl, st_time, is_today, ac_key, baginfo = matched
                    line = f"  {online} [{role}] {m.member_name:20s} ({ac_key:6s}) Lv{m.level:<4d} 战力:{self._fmt_zhanli(m.member_zhanli):>8s} 🔥{m.contribution}"
                    line += f"  | 日:{d} 周:{w} 💎{dm} 💰{cn} 体:{tl}"
                    if items and baginfo:
                        item_parts = []
                        for tid in items:
                            entry = baginfo.get(str(tid)) or baginfo.get(tid)
                            if entry and isinstance(entry, dict):
                                item_parts.append(f"{tid}:{entry.get('count', 0)}")
                            elif entry:
                                item_parts.append(f"{tid}:{entry}")
                            else:
                                item_parts.append(f"{tid}:0")
                        if item_parts:
                            line += f"  | {' '.join(item_parts)}"
                    if is_today:
                        line += f" \033[32m✓\033[0m"
                    else:
                        dt_str = datetime.fromtimestamp(st_time, tz=beijing_tz).strftime('%m-%d %H:%M')
                        line += f" \033[31m{dt_str}\033[0m"
                print(line)
        ds = info.guild_activity.donate_status
        if ds.donate_count:
            print(f"  今日已捐: {ds.donate_count}次")
        return True

    def get_leader_guild_id(self):
        """查询会长的公会ID"""
        try:
            gm = GuildManager(self.leader_account, showres=0, delay=0)
            res = gm.guild_info()
            if res and len(res) > 20:
                from . import kpbl_pb2
                info = kpbl_pb2.guild_info_response()
                info.ParseFromString(res[6:])
                gid = info.guild_basic.guild_detail.guild_id
                print(f"会长公会ID: {gid}")
                return gid
        except Exception as e:
            print(f"查询公会ID失败: {e}")
        return None

    def _for_each_account(self, func, desc="操作", start_from=1, check_member=True):
        """遍历每个小号执行操作，start_from: 从第N个开始(1-based)"""
        import io, sys
        total = len(self.guild_accounts)
        success = 0
        skipped = 0
        for i, name in enumerate(self.guild_accounts.keys(), 1):
            if i < start_from:
                continue
            sid = self.guild_accounts[name]['server_id']
            if check_member and not self._is_guild_member(name):
                print(f"[{i}/{total}] {name} ({sid}) — 非公会成员，跳过")
                skipped += 1
                continue
            print(f"[{i}/{total}] {name} ({sid}) — {desc}")
            try:
                # 捕获输出检测风控
                old_stdout = sys.stdout
                captured = io.StringIO()
                sys.stdout = type('Tee', (), {'write': lambda s, x: (old_stdout.write(x), captured.write(x)), 'flush': lambda s: old_stdout.flush()})()
                ac = ACManager(name, accounts_file=self.accounts_file,
                              showres=self.showres, delay=self.delay)
                func(ac, name)
                sys.stdout = old_stdout
                if "没有收到响应" in captured.getvalue():
                    print(f"⛔ 检测到风控，在第 {i} 个账号停止。下次可用: gg {desc} {i}")
                    break
                success += 1
            except Exception as e:
                sys.stdout = old_stdout
                if "没有收到响应" in str(e):
                    print(f"⛔ 检测到风控，在第 {i} 个账号停止。下次可用: gg {desc} {i}")
                    break
                print(f"  ✗ {name} 失败: {e}")
        msg = f"完成 {desc}: {success}/{total} 成功"
        if skipped:
            msg += f" (跳过{skipped}个非成员)"
        print(msg)

    def batch_init(self, init_func, start_from=1):
        """批量初始化（顺序执行），流程：检查公会成员→检查关卡>=5→改名→加入公会"""
        import json, io, sys, os
        guild_id = self.get_leader_guild_id()
        guild_name = self._get_guild_name()
        names = list(self.guild_accounts.keys())
        total = len(names)
        # 确保子目录存在
        os.makedirs(self.accounts_dir, exist_ok=True)
        # 先检查公会成员，识别不在公会的账号
        members = self._get_guild_member_names()
        not_in_guild = [n for n in names if not self._is_guild_member(n)]
        in_guild_count = total - len(not_in_guild)
        print(f"公会成员: {in_guild_count}  不在公会: {len(not_in_guild)}")
        if not_in_guild:
            sids = [str(self.guild_accounts[n]['server_id']) for n in not_in_guild]
            print(f"需要init的账号: {', '.join(f'{n}({s})' for n, s in zip(not_in_guild, sids))}")
        else:
            print("所有账号均在公会中，无需init")
            return
        print(f"批量初始化 {len(not_in_guild)} 个小号" + (f"，从第{start_from}个开始" if start_from > 1 else ""))
        for idx, name in enumerate(names):
            if idx + 1 < start_from:
                continue
            sid = self.guild_accounts[name]['server_id']
            if self._is_guild_member(name):
                print(f"[{idx+1}/{total}] {name} (sid={sid}) — 已在公会，跳过")
                continue
            print(f"[{idx+1}/{total}] {name} (sid={sid})")
            ac_file = self.guild_account_file(self.leader_account, name)
            with open(ac_file, 'w') as af:
                json.dump({name: self.guild_accounts[name]}, af, indent=4)
            try:
                old_stdout = sys.stdout
                captured = io.StringIO()
                sys.stdout = type('Tee', (), {'write': lambda s, x: (old_stdout.write(x), captured.write(x)), 'flush': lambda s: old_stdout.flush()})()
                # 1. 登录检查关卡等级
                ac = ACManager(name, accounts_file=ac_file, showres=0, delay=0)
                gqxx = ac.get_account(name, 'gqxx') or 0
                if gqxx < 5:
                    print(f"  {name} 关:{gqxx} < 5，执行rns")
                    init_func(name)
                    ac = ACManager(name, accounts_file=ac_file, showres=0, delay=0)
                else:
                    print(f"  {name} 关:{gqxx} >= 5，跳过rns")
                # 2. 校验角色名称
                if guild_name:
                    charaname = ac.get_account(name, 'charaname') or ''
                    expected_prefix = self._expected_name_prefix(guild_name, sid)
                    if not charaname.startswith(expected_prefix):
                        new_name = self._gen_nickname(guild_name, sid)
                        print(f"  改名: {charaname} → {new_name}")
                        ac.do_common_request(name, {
                            "ads": "改名", "times": 1, "hexstringheader": "8127",
                            "request_body_i2": new_name, "request_body_i3": 1004, "request_body_i4": 2031,
                            "requestbodytype": "request_body_for_nickname"
                        }, showres=0)
                # 3. 加入公会
                if guild_id:
                    ac.do_common_request(name, {"ads": "加入公会", "times": 1, "hexstringheader": "a375", "request_body_i2": guild_id}, showres=0)
                    # 验证是否加入成功
                    from . import kpbl_pb2
                    res = ac.do_common_request(name, {"ads": "获取公会信息", "times": 1, "hexstringheader": "9575"}, showres=0)
                    if res and len(res) > 20:
                        info = kpbl_pb2.guild_info_response()
                        info.ParseFromString(res[6:])
                        gid = info.guild_basic.guild_detail.guild_id
                        if gid == guild_id:
                            print(f"  ✓ {name} 已加入公会")
                        else:
                            print(f"  ⚠ {name} 加入异常 (guild_id={gid})")
                    else:
                        print(f"  ⚠ {name} 未加入公会")
                else:
                    print(f"  ✓ {name}")
                sys.stdout = old_stdout
                if "没有收到响应" in captured.getvalue():
                    print(f"⛔ 检测到风控，在第 {idx+1} 个账号停止。下次可用: gg init {idx+1}")
                    break
            except Exception as e:
                sys.stdout = old_stdout
                if "没有收到响应" in str(e):
                    print(f"⛔ 检测到风控，在第 {idx+1} 个账号停止。下次可用: gg init {idx+1}")
                    break
                print(f"  ✗ {name}: {e}")
        print(f"批量初始化完成: {total} 个账号")

    def batch_join(self, start_from=1):
        """所有小号加入公会，使用会长的公会ID"""
        guild_id = self.get_leader_guild_id()
        if not guild_id:
            print("错误: 无法获取会长的公会ID，无法批量加入公会")
            return False
        def _join(ac, name):
            ac.do_common_request(name, {"ads": "加入公会", "times": 1, "hexstringheader": "a375", "request_body_i2": guild_id}, showres=self.showres)
        self._for_each_account(_join, f"加入公会 {guild_id}", start_from=start_from, check_member=False)
        return True

    def batch_donate(self):
        def _donate(ac, name):
            ac.do_common_request(name, {"ads": "工会捐献5", "times": 5, "hexstringheader": "2977"}, showres=self.showres)
        self._for_each_account(_donate, "捐献")

    def batch_zs_cp(self, start_from=1):
        """赠送船票：先用会长号任命船长，再遍历小号赠送船票"""
        from .trade_manager import TradeManager
        print(f"leader:{self.leader_account}")
        tm = TradeManager(self.leader_account)
        resp = tm.getghinfo()
        if not resp or not resp.boats:
            print("没有找到公会船信息")
            return False
        # 筛选未到达的船（候船中start_time=0 或 航行中end_time=0）
        valid_boats = [b for b in resp.boats if b.end_time == 0]
        if not valid_boats:
            print("当前没有可赠送船票的公会船")
            return False
        # 优先选候船中的船（start_time=0），其次选航行中的
        valid_boats.sort(key=lambda b: (b.start_time > 0, b.boatpara1))
        boat_id = valid_boats[0].boatpara1
        print(f"目标船 boatpara1={boat_id}，共 {len(valid_boats)} 艘未到达")
        # 任命会长为船长
        tm.assign_captain(boat_id)
        def _zs_cp(ac, name):
            id, count = ac.getItemIdByType(133)
            if not count or count<3:
                print(f"购买船票: {id}, {count}")
                req ={"ads":"船票购买(3)", "times":1, "hexstringheader":"6532", "request_body_i2":2, "request_body_i3":22100, "request_body_i4":3}
                print(len(ac.do_common_request(name, req, showres=self.showres))>20)
            req ={"ads":"上船", "times":1, "hexstringheader":"1962", "request_body_i2":int(boat_id), "request_body_i3":random.randint(21, 25)}
            print(len(ac.do_common_request(name, req, showres=1))>20)
            req ={"ads":"船票赠送", "times":1, "hexstringheader":"1b62", "request_body_i2":int(boat_id), "request_body_i3":3}
            print(len(ac.do_common_request(name, req, showres=1))>20)
        self._for_each_account(_zs_cp, "赠送船票", start_from=start_from)

    def batch_daily(self):
        """捐献+扫荡"""
        def _daily(ac, name):
            ac.do_common_request(name, {"ads": "工会捐献5", "times": 5, "hexstringheader": "2977"}, showres=self.showres)
            for dt in range(1, 5):
                kunnan = ac.get_account(name, 'kunnan') or 0
                cap = {1: 100, 2: 100, 3: 50, 4: 100}
                level = min(kunnan, cap[dt]) if kunnan > 0 else 1
                ac.do_common_request(name, {
                    "ads": f"扫荡-副本{dt}", "times": 4, "hexstringheader": "9530",
                    "request_body_i2": dt, "request_body_i3": level,
                    "request_body_i4": 1, "request_body_i5": str(ac.I8_VALUE),
                }, showres=self.showres)
        self._for_each_account(_daily, "日常(捐献+扫荡)")

    @staticmethod
    def pipeline_file(leader_account):
        return f'ac_{leader_account}_pipeline.json'

    @staticmethod
    def pipeline_config(leader_account, new_tasks=None):
        """查看或设置pipeline任务清单"""
        pf = GuildBatchManager.pipeline_file(leader_account)
        default_tasks = ['fl', 'da', 'defda']
        if new_tasks:
            with open(pf, 'w') as f:
                json.dump(new_tasks, f, indent=2, ensure_ascii=False)
            print(f"已保存pipeline配置到 {pf}: {new_tasks}")
            return new_tasks
        # 读取现有配置
        import os
        if os.path.exists(pf):
            with open(pf) as f:
                tasks = json.load(f)
            print(f"当前pipeline配置 ({pf}): {tasks}")
            print(f"gg p set {' '.join(tasks)}")
            return tasks
        print(f"无pipeline配置，使用默认: {default_tasks}")
        return default_tasks

    def _run_task(self, account_name, task):
        """执行单个任务，统一通过命令注册表分发"""
        from .command_registry import get_command
        parts = task.split()
        command = parts[0]
        command_args = parts[1:]

        cmd = get_command(command)
        if cmd is None:
            print(f"未知pipeline任务: {task}")
            return

        # pipeline 中 status 仍走旧逻辑（需要 _collect_account_status）
        if command in ('status', 's'):
            self._collect_account_status(account_name)
            return

        # 确保独立账号文件存在
        import os
        os.makedirs(self.accounts_dir, exist_ok=True)
        ac_file = self.guild_account_file(self.leader_account, account_name)
        if not os.path.exists(ac_file) and account_name in self.guild_accounts:
            with open(ac_file, 'w') as f:
                json.dump({account_name: self.guild_accounts[account_name]}, f, indent=4)

        cmd.execute(account_name, command_args, showres=self.showres, delay=self.delay)

    def _collect_account_status(self, name):
        """收集单个账号的日活/周活/钻石/金币/体力/角色名，保存到guild_accounts"""
        try:
            ac = ACManager(name, accounts_file=self.accounts_file,
                          showres=0, delay=self.delay)
            diamond = ac.get_account(name, 'diamon') or 0
            coin = ac.get_account(name, 'coin') or 0
            tl = ac.get_account(name, 'tl') or 0
            charaname = ac.get_account(name, 'charaname') or ''
            gm = GuildManager.__new__(GuildManager)
            gm.account_name = name
            gm.showres = 0
            gm.ac_manager = ac
            status = gm.get_daily_task_status()
            daily = status[0] if status else -1
            weekly = status[1] if status else -1
            if name in self.guild_accounts:
                import time
                self.guild_accounts[name]['daily_activity'] = daily
                self.guild_accounts[name]['weekly_activity'] = weekly
                self.guild_accounts[name]['diamond'] = diamond
                self.guild_accounts[name]['coin'] = coin
                self.guild_accounts[name]['tl'] = tl
                if charaname:
                    self.guild_accounts[name]['charaname'] = charaname
                self.guild_accounts[name]['status_time'] = int(time.time())
                baginfo = ac.get_account(name, 'baginfo')
                if baginfo:
                    self.guild_accounts[name]['baginfo'] = baginfo
            print(f"    日活:{daily} 周活:{weekly} 💎{diamond} 💰{coin} 体:{tl}")
            return (daily, weekly, diamond)
        except Exception as e:
            print(f"    status失败: {e}")
            return (-1, -1, 0)

    def batch_approve(self):
        """会长批准所有待审核"""
        leader_gm = GuildManager(self.leader_account, showres=self.showres, delay=self.delay)
        for name in self.guild_accounts.keys():
            try:
                ac = ACManager(name, accounts_file=self.accounts_file, showres=0, delay=self.delay)
                charaid = ac.get_account(name, 'charaid')
                if charaid:
                    print(f"批准 {name} (charaid={charaid})")
                    leader_gm.approve(charaid)
            except Exception as e:
                print(f"  ✗ {name} 失败: {e}")
        return True

    def batch_kickoff(self):
        """会长踢出所有非会长成员"""
        from . import kpbl_pb2
        leader_gm = GuildManager(self.leader_account, showres=0, delay=0)
        res = leader_gm.guild_info()
        if not res or len(res) < 20:
            print("获取公会信息失败")
            return False
        info = kpbl_pb2.guild_info_response()
        info.ParseFromString(res[6:])
        members = info.guild_basic.members
        kick_configs = []
        for m in members:
            if m.role == 1:  # 跳过会长
                continue
            print(f"踢出: {m.member_name} (id={m.member_id}, Lv{m.level})")
            kick_configs.append({"ads": "踢出成员", "times": 1, "hexstringheader": "af75", "request_body_i2": m.member_id})
        if kick_configs:
            leader_gm.ac_manager.do_common_request_list(self.leader_account, kick_configs, showres=0)
        print(f"已踢出 {len(kick_configs)} 人")
        return True

    def batch_check(self):
        """检查每个小号的公会状态"""
        from . import kpbl_pb2
        leader_guild_id = self.get_leader_guild_id()
        results = []
        total = len(self.guild_accounts)
        for i, name in enumerate(self.guild_accounts.keys(), 1):
            sid = self.guild_accounts[name]['server_id']
            try:
                ac = ACManager(name, accounts_file=self.accounts_file, showres=0, delay=0)
                config = {"ads": "获取公会信息", "times": 1, "hexstringheader": "9575"}
                res = ac.do_common_request(name, config, showres=0)
                if res and len(res) > 20:
                    info = kpbl_pb2.guild_info_response()
                    info.ParseFromString(res[6:])
                    gid = info.guild_basic.guild_detail.guild_id
                    if gid == leader_guild_id:
                        results.append((name, sid, "✓ 在会中", gid))
                    elif gid > 0:
                        results.append((name, sid, f"⚠ 在其他公会", gid))
                    else:
                        results.append((name, sid, "✗ 未加入", 0))
                else:
                    results.append((name, sid, "✗ 未加入", 0))
            except Exception as e:
                results.append((name, sid, f"✗ 错误: {e}", 0))
            if i % 10 == 0:
                print(f"已检查 {i}/{total}...")
        in_guild = sum(1 for r in results if r[2] == "✓ 在会中")
        not_in = sum(1 for r in results if "未加入" in r[2])
        other = total - in_guild - not_in
        print(f"\n══════ 公会状态检查 ══════")
        print(f"  会长公会ID: {leader_guild_id}")
        print(f"  在会中: {in_guild}  |  未加入: {not_in}  |  其他: {other}")
        if not_in > 0 or other > 0:
            print(f"── 异常账号 ──")
            for name, sid, status, gid in results:
                if status != "✓ 在会中":
                    print(f"  {name} (sid={sid}): {status}" + (f" (guild_id={gid})" if gid else ""))
        return results

    def batch_acp(self, start_from=1):
        """依次登录公会小号接受悬赏任务，成功后退出"""
        from .ghxs_manager import GHXSManager

        # 先用会长号 query 获取任务列表
        ghxs_leader = GHXSManager(self.leader_account, showres=self.showres)
        resp = ghxs_leader.query()
        if not resp or not resp.task_entries:
            print("查询公会悬赏失败或无任务")
            return False

        # 按 type_id 聚合，展示供选择
        type_tasks = {}
        for task in resp.task_entries:
            tid = task.task_type_id
            if tid not in type_tasks:
                type_tasks[tid] = []
            type_tasks[tid].append(task)

        tid_list = list(type_tasks.keys())
        print("可接受的悬赏任务:")
        for idx, tid in enumerate(tid_list):
            name = ghxs_leader.format_task_type(tid) or str(tid)
            print(f"  [{idx}] {name} x{len(type_tasks[tid])}")

        choice = input("选择任务编号: ").strip()
        try:
            chosen_tid = tid_list[int(choice)]
        except (ValueError, IndexError):
            print("无效编号")
            return False

        target_task = type_tasks[chosen_tid][0]
        task_uuid = target_task.task_uuid
        task_type_id = target_task.task_type_id
        name_str = ghxs_leader.format_task_type(task_type_id) or str(task_type_id)
        print(f"目标任务: {name_str} uuid={task_uuid}")

        # 遍历小号尝试接受
        total = len(self.guild_accounts)
        for i, acname in enumerate(self.guild_accounts.keys(), 1):
            if i < start_from:
                continue
            sid = self.guild_accounts[acname]['server_id']
            print(f"[{i}/{total}] {acname} ({sid}) — 接受悬赏")
            try:
                ghxs = GHXSManager(acname, delay=self.delay, showres=self.showres)
                if ghxs.accept(task_uuid, task_type_id):
                    print(f"  ✓ {acname} 接受成功")
                    return True
                else:
                    print(f"  ✗ {acname} 接受失败")
            except Exception as e:
                print(f"  ✗ {acname} 异常: {e}")
        print("所有账号均未能接受任务")
        return False

    def batch_status(self, start_from=1):
        """收集每个小号的日活、周活、钻石，保存到guild账号文件"""
        total = len(self.guild_accounts)
        results = []
        for i, name in enumerate(self.guild_accounts.keys(), 1):
            if i < start_from:
                continue
            sid = self.guild_accounts[name]['server_id']
            if not self._is_guild_member(name):
                print(f"  [{i}/{total}] {name} (sid={sid}) — 非公会成员，跳过")
                continue
            print(f"  [{i}/{total}] {name} (sid={sid})", end="")
            daily, weekly, diamond = self._collect_account_status(name)
            results.append((name, sid, daily, weekly, diamond))
        with open(self.accounts_file, 'w') as f:
            json.dump(self.guild_accounts, f, indent=4, ensure_ascii=False)
        valid = [r for r in results if r[2] >= 0]
        if valid:
            total_diamond = sum(r[4] for r in valid)
            avg_daily = sum(r[2] for r in valid) / len(valid)
            avg_weekly = sum(r[3] for r in valid) / len(valid)
            print(f"\n══════ 状态汇总 ({len(valid)}人) ══════")
            print(f"  日活平均: {avg_daily:.1f}  |  周活平均: {avg_weekly:.1f}  |  💎总计: {total_diamond}")
        print(f"已保存到 {self.accounts_file}")
        return results

    def batch_pipeline(self, start_from=1, sleep_seconds=10, task_list=None):
        """按配置或指定任务列表的流水线顺序为每个账号执行一系列操作"""
        import time, sys, os

        # 1. 获取任务列表
        if task_list is None:
            task_list = self.pipeline_config(self.leader_account)
        
        if not task_list:
            print("没有找到执行任务！")
            return False

        total = len(self.guild_accounts)
        accounts = list(self.guild_accounts.keys())
        dashboard = _PipelineDashboard(task_list, accounts, self.guild_accounts, sleep_seconds)

        overall_start = time.time()
        success_count = 0
        stopped = False

        def _save():
            with open(self.accounts_file, 'w') as f:
                json.dump(self.guild_accounts, f, indent=4, ensure_ascii=False)

        try:
            for i, name in enumerate(accounts, 1):
                if i < start_from:
                    continue
                sid = self.guild_accounts[name]['server_id']
                if not self._is_guild_member(name):
                    print(f"[{i}/{total}] {name} ({sid}) — 非公会成员，跳过")
                    continue
                account_start = time.time()
                dashboard.set_account(i, name, sid, overall_start)
                dashboard.render(overall_start, account_start, do_clear=True)

                all_ok = True
                for ti, task in enumerate(task_list):
                    dashboard.set_task(ti, overall_start, account_start)
                    dashboard.clear_log_area()
                    dashboard.update_header(overall_start, account_start)
                    print(f"  ▸ {task} ...", flush=True)
                    task_start = time.time()
                    try:
                        self._run_task(name, task)
                        dashboard.finish_task(ti, True, time.time() - task_start)
                        dashboard.update_header(overall_start, account_start)
                        print(f"  ✓ {task} ({_fmt_duration(time.time() - task_start)})")
                    except Exception as te:
                        import traceback
                        dashboard.finish_task(ti, False, time.time() - task_start)
                        dashboard.update_header(overall_start, account_start)
                        err_msg = str(te)
                        print(f"  ✗ {task} 失败: {err_msg}")
                        traceback.print_exc()
                        if "没有收到响应" in err_msg:
                            stopped = True
                            break
                        all_ok = False

                # 每个账号执行完后立即保存，防止 Ctrl+C 丢失数据
                _save()

                if stopped:
                    print(f"\n⛔ 检测到风控，在第 {i} 个账号停止。下次可用: gg run {i}")
                    break

                if all_ok:
                    success_count += 1

                # 账号间等待（通过header更新倒计时）
                if i < total and not stopped and sleep_seconds > 0:
                    for sec in range(sleep_seconds, 0, -1):
                        dashboard.update_header(overall_start, account_start, countdown=sec)
                        time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⚠ 用户中断，正在保存已完成的数据...")
            _save()
            dashboard.cleanup()
            print(f"已保存到 {self.accounts_file}")
            return

        # 清理滚动区域
        dashboard.cleanup()
        # 汇总
        elapsed = time.time() - overall_start
        processed = i - start_from + 1 if not stopped else i - start_from + 1
        print(f"\n{'='*50}")
        print(f"Pipeline 完成: {success_count}/{processed} 成功  总耗时: {_fmt_duration(elapsed)}")
        print(f"已保存到 {self.accounts_file}")
        print(f"{'='*50}")

class _PipelineDashboard:
    """Pipeline 终端 Dashboard - 使用ANSI滚动区域"""

    def __init__(self, task_list, accounts, guild_accounts, sleep_seconds):
        self.task_list = task_list
        self.accounts = accounts
        self.guild_accounts = guild_accounts
        self.sleep_seconds = sleep_seconds
        self.total = len(accounts)
        self.current_account_idx = 0
        self.current_account_name = ""
        self.current_sid = 0
        self.current_task_idx = -1
        self.task_states = [None] * len(task_list)
        self.task_durations = [0.0] * len(task_list)
        self.header_lines = 0

    def set_account(self, idx, name, sid, overall_start):
        self.current_account_idx = idx
        self.current_account_name = name
        self.current_sid = sid
        self.task_states = [None] * len(self.task_list)
        self.task_durations = [0.0] * len(self.task_list)
        self.current_task_idx = -1

    def set_task(self, task_idx, overall_start, account_start):
        self.current_task_idx = task_idx
        self.task_states[task_idx] = 'running'

    def finish_task(self, task_idx, success, duration):
        self.task_states[task_idx] = success
        self.task_durations[task_idx] = duration

    def _build_header(self, overall_start, account_start, countdown=0, warning=""):
        """构建header行列表"""
        import time, os
        elapsed_total = time.time() - overall_start
        elapsed_account = time.time() - account_start
        try:
            cols = os.get_terminal_size().columns
        except (ValueError, OSError):
            cols = 80
        w = min(cols, 60)
        lines = []
        lines.append(f"\033[36m{'═' * w}\033[0m")
        lines.append(f"\033[36m{'Pipeline':^{w}}\033[0m")
        lines.append(f"\033[36m{'═' * w}\033[0m")
        pct = (self.current_account_idx - 1) / self.total * 100 if self.total > 0 else 0
        lines.append(f" 总耗时: {_fmt_duration(elapsed_total)}  |  "
                     f"账号: [{self.current_account_idx}/{self.total}] "
                     f"{self.current_account_name} (sid={self.current_sid})")
        bar_width = min(w - 8, 40)
        filled = int(bar_width * pct / 100)
        lines.append(f" \033[32m{'█' * filled}{'░' * (bar_width - filled)}\033[0m {pct:.0f}%")
        timer_line = f" 账号耗时: {_fmt_duration(elapsed_account)}"
        if countdown > 0:
            timer_line += f"  |  \033[33m⏳ 等待 {countdown}秒\033[0m"
        lines.append(timer_line)
        if warning:
            lines.append(f" \033[31m{warning}\033[0m")
        lines.append(f"\033[90m{'─' * w}\033[0m 任务清单")
        for ti, task in enumerate(self.task_list):
            state = self.task_states[ti]
            if state is None:
                icon = "\033[90m⏳\033[0m"; suffix = ""
            elif state == 'running':
                icon = "\033[33m▶\033[0m"; suffix = ""
            elif state is True:
                icon = "\033[32m✓\033[0m"
                suffix = f" \033[90m({_fmt_duration(self.task_durations[ti])})\033[0m"
            else:
                icon = "\033[31m✗\033[0m"
                suffix = f" \033[90m({_fmt_duration(self.task_durations[ti])})\033[0m"
            lines.append(f"  {icon} {task}{suffix}")
        lines.append(f"\033[90m{'─' * w}\033[0m 日志")
        return lines

    def render(self, overall_start, account_start, countdown=0, warning="", do_clear=False):
        """渲染dashboard，do_clear时初始化滚动区域"""
        import sys, os
        lines = self._build_header(overall_start, account_start, countdown, warning)
        self.header_lines = len(lines)
        if do_clear:
            sys.stdout.write("\033[r")      # 重置滚动区域
            sys.stdout.write("\033[2J")     # 清屏
            sys.stdout.write("\033[H")      # 光标到顶部
            for line in lines:
                sys.stdout.write(f"{line}\n")
            try:
                rows = os.get_terminal_size().lines
            except (ValueError, OSError):
                rows = 24
            # 设置滚动区域: header之后到终端底部
            sys.stdout.write(f"\033[{self.header_lines + 1};{rows}r")
            # 光标移到滚动区域起始
            sys.stdout.write(f"\033[{self.header_lines + 1};1H")
            sys.stdout.flush()
        else:
            self.update_header(overall_start, account_start, countdown, warning)

    def update_header(self, overall_start, account_start, countdown=0, warning=""):
        """就地更新header，不影响日志滚动区"""
        import sys
        lines = self._build_header(overall_start, account_start, countdown, warning)
        sys.stdout.write("\033[s")  # 保存光标
        for i, line in enumerate(lines):
            sys.stdout.write(f"\033[{i+1};1H\033[2K{line}")
        sys.stdout.write("\033[u")  # 恢复光标
        sys.stdout.flush()

    def clear_log_area(self):
        """清空日志滚动区域"""
        import sys
        sys.stdout.write("\033[s")  # 保存光标
        sys.stdout.write(f"\033[{self.header_lines + 1};1H")  # 移到滚动区起始
        sys.stdout.write("\033[J")  # 清除到屏幕底部
        sys.stdout.write("\033[u")  # 恢复光标
        sys.stdout.flush()

    def cleanup(self):
        """重置滚动区域"""
        import sys
        sys.stdout.write("\033[r")
        sys.stdout.write(f"\033[999;1H\n")
        sys.stdout.flush()


def _fmt_duration(seconds):
    """格式化时长"""
    s = int(seconds)
    if s < 60:
        return f"{s}秒"
    m, s = divmod(s, 60)
    if m < 60:
        return f"{m}分{s:02d}秒"
    h, m = divmod(m, 60)
    return f"{h}时{m:02d}分{s:02d}秒"
