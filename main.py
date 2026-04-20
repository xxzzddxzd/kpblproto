#!/usr/bin/env python3
"""
KPBL游戏工具主程序
使用重构后的模块化架构
"""

import sys
import os
import time
#

# 添加modules目录到路径
sys.path.append('modules')

from modules.kpbltools import mask_account


def print_usage():
    """从命令注册表自动生成帮助文本"""
    from modules.command_registry import COMMANDS
    print("用法: python main.py [账号] [命令] [参数...]")
    current_cat = None
    for cmd in COMMANDS:
        if cmd.guild_only:
            continue
        if cmd.category and cmd.category != current_cat:
            current_cat = cmd.category
            print(f"\n===== {current_cat} =====")
        usage = f" {cmd.usage}" if cmd.usage else ""
        aliases = f"/{'/'.join(cmd.aliases)}" if cmd.aliases else ""
        print(f"  {cmd.name}{aliases:8s}{usage:24s} - {cmd.desc}")
    print("\n===== 公会批量 (gg) =====")
    print("  gg [子命令]                - 公会批量操作")
    print("  gg run                     - 执行pipeline")
    print("  gg seq [起始] cmd1,cmd2... - 顺序执行")
    print("  gg pipeline set [任务...]  - 设置pipeline")


def run_new_account_sample(account_name):
    time_start = time.time()
    from modules import StoryBattleManager
    story_battle_manager = StoryBattleManager(account_name, delay=0, showres=0)
    story_battle_manager.execute_story_battle(1)
    story_battle_manager.execute_story_battle(2)
    story_battle_manager.execute_story_battle(3)
    # do_jq_auto(story_battle_manager, account_name, 0)
    print("step1, time pass:{}".format(time.time() - time_start))
    story_battle_manager.donewaccount()
    story_battle_manager.dotfqh()
    story_battle_manager.execute_story_battle(4)
    story_battle_manager.execute_story_battle(5)
    print("step2, time pass:{}".format(time.time() - time_start))
    story_battle_manager.execute_xjtz_zs()
    story_battle_manager.execute_zjbx_list([[1, 25],[1, 40],[1, 60],[2, 25],[2, 40],[2, 60],[3, 10],[3, 20],[3, 30],[4, 10],[4, 20],[4, 30],[5, 3],[5, 5]])
    print("step3, time pass:{}".format(time.time() - time_start))


def run_new_account(account_name):
    time_start = time.time()
    from modules import StoryBattleManager
    story_battle_manager = StoryBattleManager(account_name, delay=0, showres=0)
    story_battle_manager.execute_story_battle(1)
    story_battle_manager.execute_story_battle(2)
    story_battle_manager.execute_story_battle(3)
    print("step1, time pass:{}".format(time.time() - time_start))
    story_battle_manager.donewaccount()
    story_battle_manager.dotfqh()
    story_battle_manager.execute_story_battle(4)
    story_battle_manager.execute_story_battle(5)
    print("step2, time pass:{}".format(time.time() - time_start))
    story_battle_manager.execute_xjtz_zs()
    story_battle_manager.execute_zjbx(1, 25)
    story_battle_manager.execute_zjbx(1, 40)
    story_battle_manager.execute_zjbx(1, 60)
    story_battle_manager.execute_zjbx(2, 25)
    story_battle_manager.execute_zjbx(2, 40)
    story_battle_manager.execute_zjbx(2, 60)
    story_battle_manager.execute_zjbx(3, 10)
    story_battle_manager.execute_zjbx(3, 20)
    story_battle_manager.execute_zjbx(3, 30)
    story_battle_manager.execute_zjbx(4, 10)
    story_battle_manager.execute_zjbx(4, 20)
    story_battle_manager.execute_zjbx(4, 30)
    story_battle_manager.execute_zjbx(5, 3)
    story_battle_manager.execute_zjbx(5, 5)
    print("step3, time pass:{}".format(time.time() - time_start))
    print("step4, time pass:{}".format(time.time() - time_start))
    from modules import ACChallengeManager
    challenge_manager = ACChallengeManager(account_name, delay=0, showres=0)
    challenge_manager.buy_times(10)
    challenge_manager.buy_times(10)
    challenge_manager.auto_challenge_with_progress(account_name, 0, 100101)
    challenge_manager.auto_challenge_with_progress(account_name, 1, 1)
    challenge_manager.auto_challenge_with_progress(account_name, 1, 1)
    challenge_manager.auto_challenge_with_progress(account_name, 1, 1)
    challenge_manager.auto_challenge_with_progress(account_name, 1, 1)
    print("step5, time pass:{}".format(time.time() - time_start))
    from modules import DAManager
    da_manager = DAManager(account_name, showres=0, delay=0)
    da_manager.dobuypvp()
    da_manager.dobuypvp()
    da_manager.dobuypvp()
    da_manager.dopvpinit()
    print("step6, time pass:{}".format(time.time() - time_start))
    i = 20
    while i > 0:
        da_manager.dopvp()
        i -= 1


def one_loop(account_name, target_account):
    time_start = time.time()
    from modules import RZSGManager
    rzsg_manager = RZSGManager(account_name, showres=0, delay=0)
    if rzsg_manager.ac_manager.get_account(account_name, "gqxx") < 5:
        run_new_account(account_name)

    from modules import DAManager
    da_manager = DAManager(account_name)
    rzsg_manager.kpblzd()
    rzsg_manager.gacha_n()
    rzsg_manager.licheng()
    giftcount = rzsg_manager.zengsong(target_account)
    print(f"礼物数量：{giftcount}")

    total_time = time.time() - time_start
    print("总执行时间: {:.2f}秒".format(total_time))
    return giftcount if giftcount else 0


# do_jq_auto 保留供外部引用（command_registry 中已有自己的版本）
def do_jq_auto(story_battle_manager, account_name, level):
    while True:
        if level == 0:
            level = story_battle_manager.ac_manager.get_account(account_name, 'gqxx')
        print(f"当前关卡: {level}")
        new_level = story_battle_manager.execute_story_battle(level)
        if new_level is False:
            break
        print(f"下一个关卡: {new_level}")
        if new_level == level:
            break
        level = new_level


def test():
    import modules.kpbl_pb2 as kpbl_pb2
    """测试函数"""
    from modules import StoryBattleManager
    account_name = 'mini'
    story_battle_manager = StoryBattleManager(account_name, showres=0, delay=0)
    story_battle_manager.execute_xjtz_zs()
    story_battle_manager.execute_zjbx(1, 25)
    story_battle_manager.execute_zjbx(1, 40)
    story_battle_manager.execute_zjbx(1, 60)
    story_battle_manager.execute_zjbx(2, 25)
    story_battle_manager.execute_zjbx(2, 40)
    story_battle_manager.execute_zjbx(2, 60)
    story_battle_manager.execute_zjbx(3, 10)
    story_battle_manager.execute_zjbx(3, 20)
    story_battle_manager.execute_zjbx(3, 30)
    story_battle_manager.execute_zjbx(4, 10)
    story_battle_manager.execute_zjbx(4, 20)
    story_battle_manager.execute_zjbx(4, 30)
    story_battle_manager.execute_zjbx(5, 3)
    story_battle_manager.execute_zjbx(5, 5)


def handle_guild_command(account_name, args):
    """处理公会命令"""
    from modules import GuildManager
    sub = args[0] if len(args) > 0 else None
    if not sub:
        print("用法: g [子命令] [参数]")
        print("  join/j [公会ID]  - 加入公会")
        print("  quit             - 退出公会")
        print("  info/i           - 查看公会信息")
        print("  donate/d         - 工会捐献")
        print("  approve [角色ID] - 同意加入")
        return False
    guild_manager = GuildManager(account_name, showres=0, delay=0)
    if sub in ('join', 'j'):
        guild_id = int(args[1]) if len(args) > 1 else None
        if not guild_id:
            print("错误: join 命令需要公会编号，用法: g j [公会ID]")
            return False
        return guild_manager.join(guild_id)
    elif sub == 'quit':
        return guild_manager.quit()
    elif sub == 'approve':
        charaid = int(args[1]) if len(args) > 1 else None
        if not charaid:
            print("错误: approve 命令需要角色ID")
            return False
        return guild_manager.approve(charaid)
    elif sub in ('info', 'i'):
        res = guild_manager.guild_info()
        if not res or len(res) < 20:
            print("获取公会信息失败")
            return False
        from modules.kpbl_pb2 import guild_info_response
        def fmt_zhanli(val):
            if val >= 1_000_000_000_000:
                return f"{val / 1_000_000_000_000:.2f}T"
            elif val >= 1_000_000_000:
                return f"{val / 1_000_000_000:.2f}B"
            elif val >= 1_000_000:
                return f"{val / 1_000_000:.2f}M"
            return str(val)
        role_names = {1: "会长", 2: "副会长", 4: "成员"}
        info = guild_info_response()
        info.ParseFromString(res[6:])
        gd = info.guild_basic.guild_detail
        print(f"══════ 公会信息 ══════")
        print(f"  公会名称: {gd.guild_name}")
        print(f"  公会ID:   {gd.guild_id}")
        print(f"  等级:     Lv{gd.guild_level}")
        print(f"  成员:     {gd.member_count}/{gd.max_members}")
        print(f"  经验:     {gd.guild_exp}")
        print(f"  战力:     {fmt_zhanli(gd.guild_zhanli)}")
        print(f"  本周捐献: 🔥{gd.weekly_donation}")
        print(f"  会长:     {gd.leader_name} (ID:{gd.leader_id})")
        print(f"  服务器:   {gd.server_id}")
        if gd.guild_announcement:
            print(f"  公会宣言: {gd.guild_announcement}")
        members = sorted(info.guild_basic.members, key=lambda m: m.member_name)
        if members:
            print(f"── 成员列表 ({len(members)}人) ──")
            for m in members:
                role = role_names.get(m.role, f"未知({m.role})")
                online = "🟢" if m.is_online else "  "
                print(f"  {online} [{role}] {m.member_name} | Lv{m.level} | 战力:{fmt_zhanli(m.member_zhanli)} | 🔥{m.contribution}")
        ds = info.guild_activity.donate_status
        if ds.donate_count:
            print(f"── 捐献状态 ──")
            print(f"  今日已捐: {ds.donate_count}次")
        return True
    elif sub in ('donate', 'd'):
        return guild_manager.donate()
    else:
        print(f"未知的公会子命令: {sub}，可用: join/j, quit, info/i, donate/d, approve")
        return False


def handle_guild_batch_command(account_name, args):
    """处理公会批量命令 (gg)"""
    from modules import GuildBatchManager
    from modules.command_registry import get_command
    sub = args[0] if args else None
    if not sub:
        GuildBatchManager.show_overview(account_name)
        return False
    if sub == 'help':
        GuildBatchManager.show_help(account_name)
        return True
    if sub == 'gen':
        count = int(args[1]) if len(args) > 1 else 30
        start_sid = int(args[2]) if len(args) > 2 else None
        GuildBatchManager.gen_accounts(account_name, count, start_sid)
        return True
    if sub in ('pipeline', 'p'):
        if len(args) > 1 and args[1] == 'set':
            raw = args[2:]
            tasks = []
            i = 0
            while i < len(raw):
                if raw[i] in ('ac', 'sd'):
                    parts = [raw[i]]
                    while i + 1 < len(raw) and raw[i + 1].isdigit():
                        i += 1
                        parts.append(raw[i])
                    tasks.append(' '.join(parts))
                else:
                    tasks.append(raw[i])
                i += 1
            GuildBatchManager.pipeline_config(account_name, tasks)
        else:
            GuildBatchManager.pipeline_config(account_name)
        return True

    mgr = GuildBatchManager(account_name, showres=0, delay=0.3)
    start = int(args[1]) if len(args) > 1 and args[1].isdigit() else 1

    # seq: 需要消费所有外部参数
    if sub == 'seq':
        seq_args = " ".join(args[2:]).replace('，', ',')
        task_list = [t.strip() for t in seq_args.split(',') if t.strip()]
        if not task_list:
            print("错误: 缺少可执行的任务列表。使用方式: gg seq [起始序号] cmd1,cmd2...")
            return False
        return mgr.batch_pipeline(start_from=start, task_list=task_list)

    # run: 执行 pipeline
    if sub == 'run':
        return mgr.batch_pipeline(start_from=start)

    # init: 特殊处理，需要 run_new_account_sample 回调
    if sub == 'init':
        mgr.batch_init(run_new_account_sample, start_from=start)
        return True

    # 从注册表查找命令
    cmd = get_command(sub)
    if cmd is None or not cmd.batchable:
        print(f"未知的gg子命令: {sub}")
        print("可用: gen, init, join/j, approve, donate/d, daily, da, defda, jq, yl, tf, xyx, fl, mr, ndrwlq, check, k, i, status/s, run, xsacp, xsacpb, xsacpb3, zscp, pipeline")
        return False

    if cmd.batch_execute:
        # 有自定义批量逻辑
        if cmd.name == 'info':
            # 解析 items 参数: gg i 1508 1509 1510
            item_ids = [int(a) for a in args[1:] if a.isdigit()] or None
            mgr.batch_info(items=item_ids)
        else:
            cmd.batch_execute(mgr, start)
    else:
        # 通用路径：用 _for_each_account 包装 execute()
        batch_args = cmd.batch_default_args or []
        def _run(ac, name):
            cmd.execute(name, batch_args, showres=mgr.showres, delay=mgr.delay, ac_manager=ac)
        mgr._for_each_account(_run, cmd.desc or cmd.name, start_from=start)
    return True


def dispatch_command(account_name, command, command_args):
    """分发并执行命令，返回是否成功"""
    # 公会相关的 meta 命令保持特殊处理
    if command in ('gh', 'g', 'guild'):
        return handle_guild_command(account_name, command_args)
    if command == 'gg':
        return handle_guild_batch_command(account_name, command_args)

    from modules.command_registry import get_command
    cmd = get_command(command)
    if cmd is None:
        print(f"未知命令: {command}")
        return False
    if cmd.guild_only:
        print(f"命令 '{command}' 仅支持公会批量模式 (gg {command})")
        return False
    try:
        return cmd.execute(account_name, command_args)
    except Exception as e:
        import traceback
        print(f"执行命令 '{command}' 时发生错误: {e}")
        traceback.print_exc()
        return False


def main():

    if sys.argv[1] == "test":
        test()
        return
    """主函数"""
    if len(sys.argv) < 3:
        print_usage()
        sys.exit(1)

    account_name = sys.argv[1]
    command = sys.argv[2]
    command_args = sys.argv[3:] if len(sys.argv) > 3 else []

    print(f"\n--- 开始处理账号: {mask_account(account_name)} ---")
    print(f"执行命令: {command}")

    try:
        success = dispatch_command(account_name, command, command_args)

        if success:
            print(f"命令 '{command}' 在账号 {mask_account(account_name)} 上执行完毕。")
        else:
            print(f"命令 '{command}' 执行失败。")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(0)
    except Exception as e:
        import traceback
        print(f"处理账号 {mask_account(account_name)} 时发生错误: {e}")
        traceback.print_exc()
        sys.exit(1)

    print("\n--- 处理完毕 ---")


if __name__ == "__main__":
    main()


# ./protoc --python_out=modules/ kpbl.proto
# dd bs=1 skip=4 if=proto | ./protoc --decode_raw
# dd bs=1 skip=6 if=proto1 | ./protoc --decode_raw


# scp -r modules/  main.py  proto root@39.107.24.174:/root/kpbln
# rm -rf modules/__pycache__/ && scp -r modules/  main.py  proto root@79.99.78.80:/root/kpbln