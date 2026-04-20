"""
统一命令注册表
所有命令在此处定义一次，单账号执行、gg批量、gg seq、gg pipeline run 都从此处查找。
"""

from dataclasses import dataclass, field
from typing import Callable, Optional, List


@dataclass
class CommandDef:
    name: str                                          # 主名称
    desc: str = ""                                     # 帮助描述
    category: str = ""                                 # 帮助分类
    usage: str = ""                                    # 参数说明
    aliases: List[str] = field(default_factory=list)   # 别名
    execute: Optional[Callable] = None                 # (account_name, args, **kw) -> bool
    batch_default_args: Optional[List[str]] = None     # 批量模式默认参数
    batch_execute: Optional[Callable] = None           # (mgr, start_from) -> None  自定义批量逻辑
    batchable: bool = True                             # 是否支持 gg 批量
    guild_only: bool = False                           # 仅公会批量命令


# ── 执行函数 ────────────────────────────────────────────

def _execute_ac(account_name, args, **kw):
    if len(args) < 1:
        print("错误: ac 命令需要额外参数: [顺位] (0=塔, 1~4=顺位)")
        return False
    from .ac_manager import ACChallengeManager
    shunwei = int(args[0])
    maxtry = 20 if len(args) < 2 else int(args[1])
    ac = kw.get('ac_manager')
    mgr = ACChallengeManager(account_name, ac_manager=ac)
    if shunwei == 0:
        ac0_tower = mgr.ac_manager.get_account(account_name, 'ac0_tower_level') or 100101
        todo = (ac0_tower // 100 + 1) * 100 + 1 if ac0_tower % 10 == 0 else ac0_tower + 1
        print(f"从登录数据读取ac0已通关: {ac0_tower}，下一关: {todo}，最大尝试: {maxtry}")
        mgr.auto_challenge_with_progress(account_name, 0, todo, maxtry)
    else:
        if shunwei not in [1, 2, 3, 4]:
            print(f"错误: 不支持的顺位 {shunwei}，支持的顺位: 0, 1, 2, 3, 4")
            return False
        cleared = mgr.ac_manager.get_account(account_name, f'ac{shunwei}_cleared') or 0
        todo = cleared + 1
        print(f"从登录数据读取ac{shunwei}已通关: {cleared}，下一关: {todo}，最大尝试: {maxtry}")
        mgr.auto_challenge_with_progress_field(account_name, shunwei, f'ac{shunwei}_cleared', todo, maxtry)
    return True


def _execute_sy(account_name, args, **kw):
    minrare = int(args[0]) if len(args) > 0 else 7
    level = int(args[1]) if len(args) > 1 else 51
    bio = int(args[2]) if len(args) > 2 else 1
    print(f"深渊挑战参数: 目标稀有度={minrare}, 层数={level}, 倍数={bio}")
    from .shenyuan_manager import ShenyuanManager
    return ShenyuanManager(account_name, minrare=minrare, level=level, bio=bio).doshenyuan()


def _execute_yl(account_name, args, **kw):
    bio = 20
    level = None
    times = int(args[0]) if len(args) > 0 else 1
    print(f"游历参数: 倍数={bio}, 等级={level if level else '从账户获取'}")
    from .yl_manager import YLManager
    ac = kw.get('ac_manager')
    return YLManager(account_name, delay=0, showres=0, ac_manager=ac).do_youli_with_params(bio, level, times, 0)


def _execute_ylxyx(account_name, args, **kw):
    bio = 20
    level = None
    times = int(args[0]) if len(args) > 0 else 1
    print(f"游历参数: 倍数={bio}, 等级={level if level else '从账户获取'}")
    from .yl_manager import YLManager
    ac = kw.get('ac_manager')
    return YLManager(account_name, delay=0, showres=0, ac_manager=ac).do_youli_with_params(bio, level, times, 1)


def _execute_xyx(account_name, args, **kw):
    from .yl_manager import YLManager
    showres = kw.get('showres', 0)
    delay = kw.get('delay', 0)
    ac = kw.get('ac_manager')
    YLManager(account_name, showres=showres, delay=delay, ac_manager=ac).xyx_all()
    return True


def _execute_dapop(account_name, args, **kw):
    from .da_manager import DAManager
    showres = kw.get('showres', 1)
    delay = kw.get('delay', 0.5)
    ac = kw.get('ac_manager')
    DAManager(account_name, showres=showres, delay=delay, ac_manager=ac).claim_popup_deals()
    return True


def _execute_da(account_name, args, **kw):
    print("开始执行日常任务...")
    from .da_manager import DAManager
    showres = kw.get('showres', 0)
    delay = kw.get('delay', 0)
    ac = kw.get('ac_manager')
    return DAManager(account_name, showres=showres, delay=delay, ac_manager=ac).execute_daily()


def _execute_defda(account_name, args, **kw):
    from .da_manager import DAManager
    showres = kw.get('showres', 0)
    delay = kw.get('delay', 0)
    ac = kw.get('ac_manager')
    return DAManager(account_name, showres=showres, delay=delay, ac_manager=ac).dodefaultdailyquest()


def _execute_fl(account_name, args, **kw):
    from .da_manager import DAManager
    showres = kw.get('showres', 1)
    delay = kw.get('delay', 0)
    ac = kw.get('ac_manager')
    DAManager(account_name, showres=showres, delay=delay, ac_manager=ac).day_first_login()
    return True


def _execute_flfull(account_name, args, **kw):
    from .da_manager import DAManager
    showres = kw.get('showres', 1)
    delay = kw.get('delay', 0)
    ac = kw.get('ac_manager')
    DAManager(account_name, showres=showres, delay=delay, ac_manager=ac).day_first_login_full()
    return True


def _execute_mr(account_name, args, **kw):
    from .da_manager import DAManager
    showres = kw.get('showres', 0)
    delay = kw.get('delay', 0)
    ac = kw.get('ac_manager')
    return DAManager(account_name, showres=showres, delay=delay, ac_manager=ac).receive_mail()


def _execute_mxzs(account_name, args, **kw):
    from .da_manager import DAManager
    showres = kw.get('showres', 0)
    delay = kw.get('delay', 0)
    ac = kw.get('ac_manager')
    DAManager(account_name, showres=showres, delay=delay, ac_manager=ac).mxzs()
    return True


def _execute_ndrwlq(account_name, args, **kw):
    from .rzsg_manager import RZSGManager
    showres = kw.get('showres', 0)
    delay = kw.get('delay', 0)
    ac = kw.get('ac_manager')
    rzsg = RZSGManager(account_name, showres=showres, delay=delay, ac_manager=ac)
    rzsg.kpblzd()
    rzsg.gacha_n()
    rzsg.licheng()
    giftcount = rzsg.zengsong('default')
    print(f"礼物数量：{giftcount}")
    return True


def _execute_jq(account_name, args, **kw):
    level = int(args[0]) if len(args) >= 1 else 0
    from .story_battle import StoryBattleManager
    showres = kw.get('showres', 0)
    delay = kw.get('delay', 0)
    ac = kw.get('ac_manager')
    sbm = StoryBattleManager(account_name, showres=showres, delay=delay, ac_manager=ac)
    _do_jq_auto(sbm, account_name, level)
    return True


def _do_jq_auto(story_battle_manager, account_name, level):
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


def _execute_tf(account_name, args, **kw):
    from .story_battle import StoryBattleManager
    showres = kw.get('showres', 0)
    delay = kw.get('delay', 0)
    ac = kw.get('ac_manager')
    sbm = StoryBattleManager(account_name, showres=showres, delay=delay, ac_manager=ac)
    sbm.dotfn()
    return True


def _execute_tfn(account_name, args, **kw):
    from .story_battle import StoryBattleManager
    showres = kw.get('showres', 0)
    delay = kw.get('delay', 0)
    ac = kw.get('ac_manager')
    StoryBattleManager(account_name, showres=showres, delay=delay, ac_manager=ac).dotfn()
    return True


def _execute_pvp(account_name, args, **kw):
    from .da_manager import DAManager
    da = DAManager(account_name, showres=1, delay=0)
    da.dopvpinit()
    for _ in range(5):
        da.dopvp()
    return True


def _execute_sd(account_name, args, **kw):
    if len(args) < 1:
        print("错误: sd 命令需要额外参数: [序号] [次数=1]")
        return False
    dungeonType = int(args[0])
    times = 1 if len(args) < 2 else int(args[1])
    from .da_manager import DAManager
    da = DAManager(account_name)
    cleared = da.ac_manager.get_account(account_name, f'ac{dungeonType}_cleared') or 0
    level = cleared if cleared > 0 else 0
    print(f"从登录数据读取ac{dungeonType}已通关: {cleared}")
    print(f"扫荡参数: 副本序号={dungeonType}, 层数={level}, 次数={times}")
    return da.saodang(dungeonType, level, times)


def _execute_dy(account_name, args, **kw):
    if len(args) < 2:
        print("错误: dy 命令需要额外参数: [区域] [次数] [中止策略]")
        return False
    field = int(args[0])
    times = int(args[1])
    consider_abort = int(args[2]) if len(args) > 2 else 0
    print(f"钓鱼参数: 区域={field}, 次数={times}, 中止策略={consider_abort}")
    from .dy_manager import DYManager
    return DYManager(account_name, delay=0).execute_fishing(field, times, consider_abort)


def _execute_wk(account_name, args, **kw):
    print("开始执行挖矿...")
    from .wk_manager import WKManager
    return WKManager(account_name).start_mining(False)


def _execute_yb(account_name, args, **kw):
    if len(args) < 2:
        print("错误: yb 命令需要额外参数: [x] [y]")
        return False
    x, y = int(args[0]), int(args[1])
    print(f"月饼狂欢参数: x={x}, y={y}")
    from .hd_ybkh_manager import HdYbkhManager
    return HdYbkhManager(account_name, 1).tap(x, y)


def _execute_ybzt(account_name, args, **kw):
    print("查询月饼狂欢活动状态...")
    from .hd_ybkh_manager import HdYbkhManager
    return HdYbkhManager(account_name, 1).status()


def _execute_cc(account_name, args, **kw):
    from .da_manager import DAManager
    return DAManager(account_name).yjcc()


def _execute_rzsg(account_name, args, **kw):
    from .rzsg_manager import RZSGManager
    return RZSGManager(account_name).do_activity_boss()


def _execute_rzsgb(account_name, args, **kw):
    print("开始执行活动boss...")
    from .rzsg_manager import RZSGManager
    return RZSGManager(account_name).do_activity_boss()


def _execute_rzsgc(account_name, args, **kw):
    from .rzsg_manager import RZSGManager
    RZSGManager(account_name, showres=1, delay=0).buy_coin()
    return True


def _execute_hdzhloop(account_name, args, **kw):
    from .zh_manager import ZHManager
    ZHManager(account_name).auto_monitor(15)
    return True


def _execute_hdds(account_name, args, **kw):
    boxids = []
    if len(args) == 0:
        boxids = list(range(1, 16))
        print(f"未指定箱子ID，默认监控所有箱子: {boxids}")
    elif len(args) == 1 and ',' in args[0]:
        boxids = [int(x.strip()) for x in args[0].split(',')]
    else:
        boxids = [int(x) for x in args]
    print(f"开始监控箱子: {boxids}")
    from .hd_dashang_manager import HDDashang
    HDDashang(account_name).monitor(boxids, 60)
    return True


def _execute_hddsck(account_name, args, **kw):
    if len(args) < 2:
        print("错误: hddsck 命令需要额外参数: [boxid] [boxseq] [bio]")
        return False
    boxid = int(args[0])
    boxseq = int(args[1])
    bio = int(args[2]) if len(args) > 2 else 1
    from .hd_dashang_manager import HDDashang
    HDDashang(account_name).dogacha(boxid, boxseq, bio)
    return True


def _execute_gl(account_name, args, **kw):
    duration = None
    if len(args) > 0:
        try:
            duration = int(args[0])
            print(f"监听时长设置为: {duration} 秒")
        except ValueError:
            print("警告: 无效的时长参数，将持续监听")
    print("开始监听宝石副本组队消息...")
    from .gem_team_manager import GemTeamManager
    GemTeamManager(account_name).start_monitoring(duration)
    return True


def _execute_glauto(account_nameA, args, **kw):
    import time as _time
    times = 10
    while times > 0:
        print(f"times:{times}/10")
        account_nameB = args[0] if len(args) > 0 else "default"
        from .gem_team_manager import GemTeamManager
        level = int(args[1]) if len(args) > 1 else 1
        gm_A = GemTeamManager(account_nameA, level=level, showres=0)
        gm_A.fangqi_battle()
        gm_B = GemTeamManager(account_nameB, level=level, showres=0)
        gm_B.fangqi_battle()
        roomid = gm_A.create_and_invite(gm_B.ac_manager.get_account(account_nameB, "charaid"), level)
        if not roomid:
            return False
        if not gm_B.join(roomid):
            return False
        _time.sleep(1)
        gm_A.start()
        _time.sleep(1)
        gm_B.start()
        nowstep = 0
        while nowstep < 4:
            print(f"step:{nowstep}")
            nowstep += 1
            gm_B.update_step_and_check(nowstep)
            if nowstep >= 3:
                gm_A.fangqi_battle()
            else:
                gm_A.update_step_and_check(nowstep)
        gm_A.fangqi_battle()
        gm_B.finish_battle()
        times -= 1
    return True


def _execute_glauto2(account_nameA, args, **kw):
    import time as _time
    times = int(args[2]) if len(args) > 2 else 10
    while times > 0:
        print(f"times:{times}/{times}")
        account_nameB = args[0] if len(args) > 0 else "default"
        from .gem_team_manager import GemTeamManager
        level = int(args[1]) if len(args) > 1 else 1
        gm_A = GemTeamManager(account_nameA, level=level, showres=0, delay=0)
        gm_A.fangqi_battle()
        gm_B = GemTeamManager(account_nameB, level=level, showres=0, delay=0)
        gm_B.fangqi_battle()
        roomid = gm_A.create_and_invite(gm_B.ac_manager.get_account(account_nameB, "charaid"), level)
        if not roomid:
            return False
        if not gm_B.join(roomid):
            return False
        _time.sleep(1)
        gm_A.start()
        _time.sleep(1)
        gm_B.start()
        nowstep = 0
        while nowstep < 4:
            print(f"step:{nowstep}")
            nowstep += 1
            gm_B.update_step_and_check(nowstep)
            gm_A.update_step_and_check(nowstep)
        gm_A.finish_battle()
        gm_B.finish_battle()
        times -= 1
    return True


def _execute_login(account_name, args, **kw):
    from .kpbltools import ACManager, mask_account
    ACManager(account_name)
    print(f"账号 {mask_account(account_name)} 登录成功")
    return True


def _execute_py(account_name, args, **kw):
    from .py_manager import PeiyuManager
    return bool(PeiyuManager(account_name).run_interactive())


def _execute_knjf(account_name, args, **kw):
    from .kn_manager import KNManager
    kn = KNManager(account_name, isFangZhu=True)
    kn.create_and_invite(10141237)
    input("[FZ]回车开始")
    kn.start()
    kn.update_battle_round()
    kn.finish_battle()
    return True


def _execute_knjoin(account_name, args, **kw):
    from .kn_manager import KNManager
    kn = KNManager(account_name, isFangZhu=False)
    roomid = input("[DY]输入房间ID:")
    kn.join(roomid)
    input("[DY]回车开始")
    kn.start()
    kn.update_battle_round()
    kn.finish_battle()
    return True


def _execute_knauto(account_name, args, **kw):
    import time as _time
    from .kn_manager import KNManager
    duiyuan = args[0]
    level = int(args[1]) if len(args) > 1 else 0
    times = int(args[2]) if len(args) > 2 else 1
    kn_fz = KNManager(account_name, isFangZhu=True)
    kn_dy = KNManager(duiyuan, isFangZhu=False)

    def check_full(lv):
        t1, cap, c1 = kn_fz.get_weekly_stat(lv)
        t2, cap, c2 = kn_dy.get_weekly_stat(lv)
        cnt = max(c1, c2)
        print(f"target_level_cap:{cap}, target_level_count:{cnt}")
        if cap - cnt < 150:
            print(f"目标关卡{lv}已满，退出")
            return True
        return False

    total = times
    while times > 0 and not check_full(level):
        print(f"now:{total - times + 1}, left:{times - 1}")
        roomid = kn_fz.create_and_invite(10141237, usedefinelevel=level)
        kn_dy.join(roomid)
        kn_fz.start(bio=3)
        _time.sleep(3)
        kn_dy.start()
        totalstep = kn_fz.get_total_step()
        nowstep = 0
        while nowstep < totalstep:
            nowstep += 1
            w0, w1 = kn_fz.update_step_and_check(nowstep)
            w0, w1 = kn_dy.update_step_and_check(nowstep)
            print(f"\rstep:{nowstep}/{totalstep}, waveindex0:{w0}, waveindex1:{w1}", end="")
        kn_dy.finish_battle()
        kn_fz.finish_battle()
        times -= 1
    return True


def _execute_knauto3(account_name, args, **kw):
    from .kn_manager import KNManager
    level = int(args[0]) if len(args) > 0 else 0
    times = int(args[1]) if len(args) > 1 else 1
    kn_fz = KNManager(account_name, isFangZhu=True)

    def check_full(lv):
        total, cap, cnt = kn_fz.get_weekly_stat(lv)
        print(f"target_level_cap:{cap}, target_level_count:{cnt}")
        if cap - cnt < 150:
            print(f"目标关卡{lv}已满，退出")
            return True
        return False

    total = times
    while times > 0 and not check_full(level):
        print(f"now:{total - times + 1}, left:{times - 1}")
        kn_fz.create_solo(usedefinelevel=level)
        kn_fz.start(bio=3)
        totalstep = kn_fz.get_total_step()
        nowstep = 0
        while nowstep < totalstep:
            nowstep += 1
            w0, w1 = kn_fz.update_step_and_check(nowstep)
            print(f"\rstep:{nowstep}/{totalstep}, waveindex0:{w0}", end="")
        print()
        kn_fz.finish_battle()
        times -= 1
    return True


def _execute_wdh(account_name, args, **kw):
    from .da_manager import DAManager
    target = int(args[0]) if len(args) > 0 else 10611937
    DAManager(account_name, showres=1).dowdh(target)
    return True


def _execute_oi(account_name, args, **kw):
    from .da_manager import DAManager
    da = DAManager(account_name, showres=0, delay=0)
    print("3358412: 书箱子")
    print(da.ac_manager.baginfo_str)
    itemid = int(args[0]) if len(args) > 0 else 3358412
    count = int(args[1]) if len(args) > 1 else 99
    if count == 99:
        while True:
            if not da.useitem(itemid, 99):
                break
            print("使用书箱子")
    else:
        da.useitem(int(args[0]), count)
    return True


def _execute_dz(account_name, args, **kw):
    from .da_manager import DAManager
    return DAManager(account_name).wddh_dz()


def _execute_wddhyx(account_name, args, **kw):
    from .da_manager import DAManager
    da = DAManager(account_name)
    for _ in range(10):
        da.wddh_yuxuan()
    return True


def _execute_zn(account_name, args, **kw):
    from .da_manager import DAManager
    return DAManager(account_name).zn_sell()


def _execute_zng(account_name, args, **kw):
    from .kpbltools import ACManager
    ac_mgr = ACManager(account_name, showres=0, delay=0)
    server_id_now = ac_mgr.get_account(account_name, "server_id") or 401106
    while True:
        server_id_now += 1
        print(f"正在处理{account_name}, 服务器ID: {server_id_now}")
        ac_mgr.update_account(account_name, "server_id", server_id_now)
        ac_mgr.save_accounts()
        from .da_manager import DAManager
        da = DAManager(account_name, delay=0, showres=0)
        if da.ac_manager.get_account(account_name, "gqxx") < 5:
            import main
            main.run_new_account(account_name)
        da.execute_daily_tasks_nowk()
        from .story_battle import StoryBattleManager
        sbm = StoryBattleManager(account_name, delay=0, showres=0)
        sbm.dotfqh()
        from .ac_manager import ACChallengeManager
        ac = ACChallengeManager(account_name, delay=0)
        i = 4
        while i > 0:
            ac.execute_one_time(account_name, 1, 1)
            sbm.dotfqh()
            ac.execute_one_time(account_name, 2, 1)
            i -= 1
        if ac.ac_manager.get_account(account_name, "tl") > 99:
            from .yl_manager import YLManager
            YLManager(account_name).do_youli_with_params(20, 5)
        da.zn_quest()
        if da.zn_refresh() == True:
            return True


def _execute_sdgm(account_name, args, **kw):
    from .da_manager import DAManager
    return DAManager(account_name, showres=0, delay=0).sdgm()


def _execute_ggl(account_name, args, **kw):
    from .da_manager import DAManager
    DAManager(account_name).ggl()
    return True

def _execute_mhj(account_name, args, **kw):
    from .da_manager import DAManager
    ac = kw.get('ac_manager')
    dm = DAManager(account_name, ac_manager=ac)
    return dm.mangheji_gacha()


def _execute_hd20260330(account_name, args, **kw):
    from .rzsg_manager import RZSGManager
    showres = kw.get('showres', 0)
    delay = kw.get('delay', 0)
    ac = kw.get('ac_manager')
    RZSGManager(account_name, showres=showres, delay=delay, ac_manager=ac).hd20260330()
    return True


def _execute_yxkc(account_name, args, **kw):
    level = int(args[0]) if len(args) > 0 else 1
    print(f"开始执行异星矿场，关卡: {level}")
    from .yxkc_manager import YXKCManager
    return YXKCManager(account_name, showres=1, delay=0).do_battle(level)


def _execute_dc(account_name, args, **kw):
    times = int(args[0]) if len(args) > 0 else 3
    print(f"开始执行地牢自动战斗 x{times}...")
    from .dungeon_manager import DungeonManager
    showres = kw.get('showres', 0)
    delay = kw.get('delay', 0.5)
    ac = kw.get('ac_manager')
    total_boss = 0
    for i in range(times):
        print(f"\n===== 地牢第 {i+1}/{times} 次 =====")
        total_boss += DungeonManager(account_name, showres=showres, delay=delay, ac_manager=ac).auto_battle()
    print(f"\n地牢完成: {times}次, 总Boss通过={total_boss}")
    return True


def _execute_kpkpj(account_name, args, **kw):
    from .da_manager import DAManager
    return DAManager(account_name).kpkpj()


def _execute_jl(account_name, args, **kw):
    if args:
        if args[0] == 'gh':
            from .trade_manager import TradeManager
            from .item_names import ITEM_NAMES
            trade_xh = TradeManager('xh')
            print("正在获取公会船信息...")
            resp = trade_xh.getghinfo()
            if not resp or not resp.boats:
                print("没有找到公会船信息")
                return True
            valid_boats = [b for b in resp.boats if b.start_time > 0]
            if not valid_boats:
                print("当前没有起航的公会船")
                return True
            print(f"找到 {len(valid_boats)} 艘有效的公会船")
            trade = TradeManager(account_name)
            baginfo_before = trade.ac_manager.get_account(account_name, 'baginfo') or {}
            for boat in valid_boats:
                print(f"尝试攻击公会船 ID: {boat.boatpara1}, 公会 ID: {boat.boatpara4}")
                trade.attack_guild_ship(boat.boatpara1, boat.boatpara4)
            trade.ac_manager.login(account_name)
            baginfo_after = trade.ac_manager.get_account(account_name, 'baginfo') or {}
            def _bag_count(v):
                return v['count'] if isinstance(v, dict) else v
            diff = {ITEM_NAMES.get(k, k): _bag_count(baginfo_after.get(k, 0)) - _bag_count(baginfo_before.get(k, 0))
                    for k in set(baginfo_before) | set(baginfo_after)
                    if _bag_count(baginfo_after.get(k, 0)) != _bag_count(baginfo_before.get(k, 0))}
            if diff:
                print(f"背包变化: {diff}")
        elif args[0] == 'sd':
            from .trade_manager import TradeManager
            from .item_names import ITEM_NAMES
            guild_only = False
            if len(args) > 1 and args[1] == 'gh':
                guild_only = True
                times = int(args[2]) if len(args) > 2 else 20
            else:
                times = int(args[1]) if len(args) > 1 else 20
            target = 'xh'
            trade_xh = TradeManager(target)
            seen_ids = set()
            results = []

            def do_search():
                print("正在搜索符合条件的船只...")
                new_results = trade_xh.getboat(times, guild_only=guild_only, seen_ids=seen_ids)
                results.extend(new_results)
                results.sort(key=lambda x: x[0])

            TARGET_IDS = {5605} | set(range(1386000, 1386101))

            def _calc_prob(total, target, pick=3):
                """P(至少1个目标) = 1 - C(N-T,pick)/C(N,pick)"""
                if total < pick or target <= 0:
                    return 0.0
                from math import comb
                miss = total - target
                if miss < pick:
                    return 1.0
                return 1.0 - comb(miss, pick) / comb(total, pick)

            def show_results():
                if not results:
                    print("没有找到符合条件的船只")
                    return
                print(f"\n找到 {len(results)} 艘符合条件的船：")
                print("-" * 60)
                for idx, (slotslen, max_135, max_59, max_5604, boat, is_guild, guild_slots) in enumerate(results):
                    tag = "🏰" if is_guild else "  "
                    # 过滤guild_slots: 只保留含目标物品的船舱
                    filtered_slots = []
                    target_count = 0
                    if is_guild and guild_slots:
                        for s in guild_slots:
                            matched = [it for it in s['items'] if isinstance(it, dict) and it['id'] in TARGET_IDS]
                            target_count += len(matched)
                            if matched:
                                filtered_slots.append((s, matched))
                    if not filtered_slots and is_guild:
                        continue  # 公会船无匹配物品，跳过
                    prob = _calc_prob(slotslen, target_count)
                    print(f"  {tag}[{idx}] slots:{slotslen} 目标:{target_count} 概率:{prob:.0%} | 功勋币:{max_135} 武装令牌:{max_59} 武装宝箱:{max_5604}")
                    for s, matched in filtered_slots:
                        texts = ', '.join(it['text'] for it in matched)
                        print(f"        ⭐舱{s['slotid']}(稀有{s['rarity']}): {texts}")
                print("-" * 60)

            do_search()
            show_results()
            if not results:
                return True
            print("输入编号攻击，c 继续搜索，q 退出")
            trade = TradeManager(account_name)
            while True:
                choice = input(">>> ").strip()
                if choice.lower() == 'q':
                    print("退出手动劫掠")
                    break
                if choice.lower() == 'c':
                    do_search()
                    show_results()
                    print("输入编号攻击，c 继续搜索，q 退出")
                    continue
                try:
                    idx = int(choice)
                    if idx < 0 or idx >= len(results):
                        print(f"无效编号，请输入 0-{len(results) - 1}")
                        continue
                except ValueError:
                    print("请输入数字编号、c 继续搜索或 q 退出")
                    continue
                _, _, _, _, boat, is_guild, _ = results[idx]
                baginfo_before = trade.ac_manager.get_account(account_name, 'baginfo') or {}
                if is_guild:
                    trade.attack_guild_ship(boat.boatpara1, boat.boatpara4)
                else:
                    trade.attack(boat)
                trade.ac_manager.login(account_name)
                baginfo_after = trade.ac_manager.get_account(account_name, 'baginfo') or {}
                def _bag_count(v):
                    return v['count'] if isinstance(v, dict) else v
                diff = {ITEM_NAMES.get(k, k): _bag_count(baginfo_after.get(k, 0)) - _bag_count(baginfo_before.get(k, 0))
                        for k in set(baginfo_before) | set(baginfo_after)
                        if _bag_count(baginfo_after.get(k, 0)) != _bag_count(baginfo_before.get(k, 0))}
                print(f"变化: {diff}")
    else:
        from .da_manager import DAManager
        DAManager(account_name).dodailyjl()
    return True


def _execute_nc(account_name, args, **kw):
    from .nuanchun_manager import NuanChunManager
    NuanChunManager(account_name, delay=0, showres=1).doncxh()
    return True


def _execute_ncloop(account_name, args, **kw):
    from .kpbltools import ACManager
    from .nuanchun_manager import NuanChunManager
    ac = ACManager(account_name, showres=0, delay=0, skip_login=True)
    server_id = ac.get_account(account_name, 'server_id') or 401000
    while True:
        server_id += 1
        print(f"\n=== 服务器 {server_id} ===")
        ac.update_account(account_name, 'server_id', server_id)
        ac.save_accounts()
        nc = NuanChunManager(account_name, delay=0, showres=0)
        item_count = nc.doncxh()
        if item_count is not None and item_count >= 20:
            print(f"\n=== 财神帽已达 {item_count} >= 20，停止 ===")
            break
    return True


def _execute_rn(account_name, args, **kw):
    import main
    if len(args) >= 2 and args[0] == 'srv':
        from .kpbltools import ACManager
        import json
        import threading
        orig = ACManager(account_name, showres=0, delay=0, skip_login=True)
        orig_account = orig.get_account(account_name)
        base_fields = {f: orig_account[f] for f in ['s1', 'udid', 'acstr'] if f in orig_account}
        start_server = int(args[1])
        total = int(args[2]) if len(args) > 2 else 200
        num_threads = int(args[3]) if len(args) > 3 else 2
        end_server = start_server + total
        print(f"启动 {num_threads} 个线程，服务器范围: {start_server} ~ {end_server - 1}")
        counter = {'next': start_server}
        lock = threading.Lock()

        def worker(tid):
            alias = f"{account_name}_rn{tid}"
            alias_file = f"ac_{alias}.json"
            while True:
                with lock:
                    sid = counter['next']
                    if sid >= end_server:
                        break
                    counter['next'] += 1
                print(f"\n=== [线程{tid}] 服务器 {sid} ({sid - start_server + 1}/{total}) ===")
                data = dict(base_fields)
                data['server_id'] = sid
                with open(alias_file, 'w') as f:
                    json.dump({alias: data}, f, indent=4)
                try:
                    main.run_new_account_sample(alias)
                except Exception as e:
                    print(f"[线程{tid}] 服务器 {sid} 执行失败: {e}")

        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        print(f"\n=== 全部完成: {start_server} ~ {end_server - 1} ===")
    else:
        main.run_new_account(account_name)
    return True


def _execute_rns(account_name, args, **kw):
    import main
    main.run_new_account_sample(account_name)
    return True


def _execute_ghxs(account_name, args, **kw):
    from .ghxs_manager import GHXSManager
    ghxs = GHXSManager(account_name)
    resp = ghxs.query()
    if resp:
        type_counts = {}
        for task in resp.task_entries:
            tid = task.task_type_id
            type_counts[tid] = type_counts.get(tid, 0) + 1
        print(f"公会悬赏任务数: {len(resp.task_entries)}")
        for tid, count in type_counts.items():
            name = ghxs.format_task_type(tid)
            label = f"{name}({tid})" if name else str(tid)
            print(f"  {label} x{count}")
    else:
        print("查询公会悬赏失败")
    return True


def _execute_sl(account_name, args, **kw):
    import main
    from .kpbltools import ACManager
    account_file = f'ac_{account_name}.json'
    temp = ACManager(account_name, accounts_file=account_file, showres=0, delay=0, skip_login=True)
    new_name = temp.createaccount(account_file)
    if new_name is None:
        print("创建新账号失败")
        return False
    print(f"成功创建新账号: {new_name}")
    new_file = f'ac_{new_name}.json'
    ac_new = ACManager(new_name, accounts_file=new_file, showres=0, delay=0)
    server_id_now = ac_new.get_account(new_name, "server_id") or 401106
    giftcount = 0
    target = args[0] if len(args) > 0 else None
    target_list = ["default", 'mini'] if not target else [target]
    from .rzsg_manager import RZSGManager
    for target_account in target_list:
        rzsg_target = RZSGManager(target_account, showres=0, delay=0)
        print(f'进入dnaloop, from{server_id_now}')
        while not rzsg_target.check_gift_receive_count():
            server_id_now += 1
            print(f"正在处理{new_name}, 服务器ID: {server_id_now}, 已送出礼物: {giftcount}")
            ac_new.update_account(new_name, "server_id", server_id_now)
            ac_new.save_accounts()
            giftcount += main.one_loop(new_name, target_account)
            print(f"礼物数量：{giftcount}")
    return True


def _execute_rzsg2(account_name, args, **kw):
    import main
    from .kpbltools import ACManager
    ac_mgr = ACManager(account_name, showres=0, delay=0)
    server_id_now = ac_mgr.get_account(account_name, "server_id") or 401106
    giftcount = 0
    target = args[0] if len(args) > 0 else None
    target_list = ["default"] if not target else [target]
    from .rzsg_manager import RZSGManager
    for target_account in target_list:
        rzsg_target = RZSGManager(target_account, showres=0, delay=0)
        print(f'进入dnaloop, from{server_id_now}')
        while not rzsg_target.check_gift_receive_count():
            server_id_now += 1
            print(f"正在处理{account_name}, 服务器ID: {server_id_now}, 已送出礼物: {giftcount}")
            ac_mgr.update_account(account_name, "server_id", server_id_now)
            ac_mgr.save_accounts()
            giftcount += main.one_loop(account_name, target_account)
            print(f"礼物数量：{giftcount}")
    return True


# 批量专用：donate 单账号执行
def _execute_donate_single(account_name, args, **kw):
    from .kpbltools import ACManager
    showres = kw.get('showres', 0)
    delay = kw.get('delay', 0)
    ac = ACManager(account_name, showres=showres, delay=delay)
    ac.do_common_request_list(account_name, [{"ads": "工会捐献5", "times": 5, "hexstringheader": "2977"}], showres=1)
    return True


def _execute_kg(account_name, args, **kw):
    from .kg_manager import KGManager
    from .da_manager import DAManager
    ac = kw.get('ac_manager')
    DAManager(account_name, ac_manager=ac).petegggacha(2)
    KGManager(account_name, ac_manager=ac).run()
    return True


# 批量专用的自定义 batch_execute：fl 需要每个账号间 sleep 60 秒
def _batch_fl(mgr, start_from):
    import time as _time
    from .da_manager import DAManager
    def _fl(ac, name):
        DAManager(name, showres=mgr.showres, delay=mgr.delay).day_first_login()
        _time.sleep(60)
    mgr._for_each_account(_fl, "每日首登", start_from=start_from)


def _batch_flfull(mgr, start_from):
    import time as _time
    from .da_manager import DAManager
    def _fl(ac, name):
        DAManager(name, showres=mgr.showres, delay=mgr.delay).day_first_login_full()
        _time.sleep(60)
    mgr._for_each_account(_fl, "每日首登(完整)", start_from=start_from)


# ── 命令注册表 ──────────────────────────────────────────

COMMANDS = [
    # ── 挑战 / 战斗 ──
    CommandDef(name="ac",  desc="自动挑战", category="挑战/战斗", usage="[顺位] [最大尝试次数=20]", execute=_execute_ac),
    CommandDef(name="sy",  desc="深渊挑战", category="挑战/战斗", usage="[稀有度=7] [层数=51] [倍数=1]", execute=_execute_sy, batchable=False),
    CommandDef(name="jq",  desc="剧情战斗自动推图", category="挑战/战斗", execute=_execute_jq),
    CommandDef(name="pvp", desc="PVP对战", category="挑战/战斗", execute=_execute_pvp, batchable=False),
    CommandDef(name="sd",  desc="扫荡副本", category="挑战/战斗", usage="[副本序号] [次数=1]", execute=_execute_sd, batchable=False),

    # ── 日常 / 资源 ──
    CommandDef(name="dapop", desc="特惠弹框领取", category="日常/资源", execute=_execute_dapop),
    CommandDef(name="da",    desc="日常任务",   category="日常/资源", execute=_execute_da),
    CommandDef(name="defda", desc="默认日常任务", category="日常/资源", execute=_execute_defda),
    CommandDef(name="fl",    desc="首登奖励",   category="日常/资源", execute=_execute_fl, batch_execute=_batch_fl),
    CommandDef(name="flfull", desc="首登奖励(完整)", category="日常/资源", execute=_execute_flfull, batch_execute=_batch_flfull),
    CommandDef(name="yl",    desc="游历",       category="日常/资源", usage="[倍数=1] [等级]", execute=_execute_yl, batch_default_args=["20"]),
    CommandDef(name="ylxyx", desc="游历+幸运星", category="日常/资源", execute=_execute_ylxyx, batch_default_args=["20"]),
    CommandDef(name="xyx",   desc="幸运星",     category="日常/资源", execute=_execute_xyx),
    CommandDef(name="wk",    desc="挖矿",       category="日常/资源", execute=_execute_wk, batchable=False),
    CommandDef(name="dy",    desc="钓鱼",       category="日常/资源", usage="[区域] [次数] [中止策略=0]", execute=_execute_dy, batchable=False),
    CommandDef(name="cc",    desc="一键传承",   category="日常/资源", execute=_execute_cc, batchable=False),
    CommandDef(name="tf",    desc="天赋强化",   category="日常/资源", execute=_execute_tf),
    CommandDef(name="tfn",   desc="天赋强化(新版)", category="日常/资源", execute=_execute_tfn),
    CommandDef(name="py",    desc="培育 (交互式)", category="日常/资源", execute=_execute_py, batchable=False),
    CommandDef(name="oi",    desc="使用物品",   category="日常/资源", usage="[物品ID] [数量=1]", execute=_execute_oi, batchable=False),
    CommandDef(name="login", desc="仅登录",     category="日常/资源", execute=_execute_login, batchable=False),
    CommandDef(name="mr",    desc="邮件领取",   category="日常/资源", execute=_execute_mr),
    CommandDef(name="mxzs",  desc="冒险助手",   category="日常/资源", execute=_execute_mxzs),
    CommandDef(name="ndrwlq", desc="扭蛋任务领取", category="日常/资源", execute=_execute_ndrwlq),

    # ── 活动 / 限时 ──
    CommandDef(name="rzsg",  desc="日常送礼",   category="活动/限时", usage="[目标账号]", execute=_execute_rzsg2, batchable=False),
    CommandDef(name="sl",    desc="创建新账号并送礼", category="活动/限时", execute=_execute_sl, batchable=False),
    CommandDef(name="rzsgb", desc="活动boss",   category="活动/限时", execute=_execute_rzsgb, batchable=False),
    CommandDef(name="rzsgc", desc="购买活动币", category="活动/限时", execute=_execute_rzsgc, batchable=False),
    CommandDef(name="yb",    desc="月饼狂欢",   category="活动/限时", usage="[x] [y]", execute=_execute_yb, batchable=False),
    CommandDef(name="ybzt",  desc="月饼狂欢状态查询", category="活动/限时", execute=_execute_ybzt, batchable=False),
    CommandDef(name="hdzhloop", desc="种花循环监控", category="活动/限时", execute=_execute_hdzhloop, batchable=False),
    CommandDef(name="hdds",  desc="打赏箱子监控", category="活动/限时", usage="[boxids]", execute=_execute_hdds, batchable=False),
    CommandDef(name="hddsck", desc="打赏单次抽奖", category="活动/限时", usage="[boxid] [boxseq] [bio=1]", execute=_execute_hddsck, batchable=False),
    CommandDef(name="kpkpj", desc="卡皮卡皮机", category="活动/限时", execute=_execute_kpkpj, batchable=False),
    CommandDef(name="zn",    desc="周年庆出售", category="活动/限时", execute=_execute_zn, batchable=False),
    CommandDef(name="zng",   desc="周年庆跨服", category="活动/限时", execute=_execute_zng, batchable=False),
    CommandDef(name="ggl",   desc="公会挂历",   category="活动/限时", execute=_execute_ggl, batchable=False),
    CommandDef(name="mhj",   desc="盲盒机拿币&抽奖", category="活动/限时", execute=_execute_mhj),
    CommandDef(name="hd20260330", desc="奇妙马戏团", category="活动/限时", execute=_execute_hd20260330),
    CommandDef(name="jl",    desc="劫掠",       category="活动/限时", execute=_execute_jl, batchable=False),
    CommandDef(name="nc",    desc="暖春",       category="活动/限时", execute=_execute_nc, batchable=False),
    CommandDef(name="ncloop", desc="暖春循环",  category="活动/限时", execute=_execute_ncloop, batchable=False),
    CommandDef(name="kg",    desc="公会考古",   category="活动/限时", execute=_execute_kg),

    # ── 组队 / 副本 ──
    CommandDef(name="gl",     desc="宝石副本组队监听", category="组队/副本", usage="[时长(秒)]", execute=_execute_gl, batchable=False),
    CommandDef(name="glauto", desc="宝石副本自动双人(房主放弃)", category="组队/副本", execute=_execute_glauto, batchable=False),
    CommandDef(name="glauto2", desc="宝石副本自动双人(房主不放弃)", category="组队/副本", execute=_execute_glauto2, batchable=False),
    CommandDef(name="knjf",   desc="困难本建房", category="组队/副本", execute=_execute_knjf, batchable=False),
    CommandDef(name="knjoin", desc="困难本加入", category="组队/副本", execute=_execute_knjoin, batchable=False),
    CommandDef(name="knauto", desc="困难本自动双人", category="组队/副本", execute=_execute_knauto, batchable=False),
    CommandDef(name="knauto3", desc="困难本单人自动", category="组队/副本", execute=_execute_knauto3, batchable=False),

    # ── 武道 / 其他 ──
    CommandDef(name="wdh",   desc="武道大会挑战", category="武道/其他", usage="[目标ID=10611937]", execute=_execute_wdh, batchable=False),
    CommandDef(name="dz",    desc="武道大会点赞", category="武道/其他", execute=_execute_dz, batchable=False),
    CommandDef(name="wddhyx", desc="武道大会预选", category="武道/其他", execute=_execute_wddhyx, batchable=False),
    CommandDef(name="sdgm",  desc="扫荡购买",   category="武道/其他", execute=_execute_sdgm, batchable=False),
    CommandDef(name="yxkc",  desc="异星矿场",   category="武道/其他", usage="[关卡=1]", execute=_execute_yxkc, batchable=False),
    CommandDef(name="dc",    desc="地牢自动战斗", category="挑战/战斗", execute=_execute_dc, batchable=True),
    CommandDef(name="rn",    desc="新账号(批量)", category="武道/其他", execute=_execute_rn, batchable=False),
    CommandDef(name="rns",   desc="新账号(样本)", category="武道/其他", execute=_execute_rns, batchable=False),
    CommandDef(name="ghxs",  desc="公会悬赏查询", category="武道/其他", execute=_execute_ghxs, batchable=False),

    # ── 公会批量专属（guild_only） ──
    CommandDef(name="jz", desc="捐献", aliases=["d"], execute=_execute_donate_single, guild_only=True),
    CommandDef(name="status", desc="收集状态", aliases=["s"], guild_only=True,
              batch_execute=lambda mgr, start_from: mgr.batch_status(start_from=start_from)),
    CommandDef(name="join", desc="加入公会", aliases=["j"], guild_only=True,
              batch_execute=lambda mgr, start_from: mgr.batch_join(start_from=start_from)),
    CommandDef(name="approve", desc="批准申请", guild_only=True,
              batch_execute=lambda mgr, start_from: mgr.batch_approve()),
    CommandDef(name="check", desc="检查成员", guild_only=True,
              batch_execute=lambda mgr, start_from: mgr.batch_check()),
    CommandDef(name="k", desc="踢出成员", guild_only=True,
              batch_execute=lambda mgr, start_from: mgr.batch_kickoff()),
    CommandDef(name="info", desc="公会信息", aliases=["i"], guild_only=True,
              batch_execute=lambda mgr, start_from: mgr.batch_info()),
    CommandDef(name="daily", desc="捐献+扫荡", guild_only=True,
              batch_execute=lambda mgr, start_from: mgr.batch_daily()),
    CommandDef(name="init", desc="初始化小号", guild_only=True,
              batch_execute=None),  # 需要 init_func，在 handle_guild_batch_command 中特殊处理
    CommandDef(name="xsacp", desc="悬赏接受", guild_only=True,
              batch_execute=lambda mgr, start_from: mgr.batch_acp(start_from=start_from)),
    CommandDef(name="xsacpb", desc="悬赏接受后放弃", guild_only=True,
              batch_execute=lambda mgr, start_from: mgr.batch_acpb(start_from=start_from)),
    CommandDef(name="zscp", desc="赠送船票", guild_only=True,
              batch_execute=lambda mgr, start_from: mgr.batch_zs_cp(start_from=start_from)),
]

# ── 查找索引 ────────────────────────────────────────────

_COMMAND_MAP = {}

def _build_map():
    for cmd in COMMANDS:
        _COMMAND_MAP[cmd.name] = cmd
        for alias in cmd.aliases:
            _COMMAND_MAP[alias] = cmd

_build_map()


def get_command(name: str) -> Optional[CommandDef]:
    return _COMMAND_MAP.get(name)


def get_batchable_names() -> list:
    """返回所有可批量执行的命令名（含别名）"""
    return [name for name, cmd in _COMMAND_MAP.items() if cmd.batchable]
