"""
公会考古管理模块
处理公会考古活动：领取奖励、自动挖掘
"""

import binascii
import json
import time
from pathlib import Path
from . import kpbl_pb2
from .kpbltools import ACManager


class KGManager:
    """公会考古管理器"""

    # 锤子的背包物品类型
    HAMMER_TYPE = 151
    # e159 领奖档位 -> 所需今日挖矿任务积分。1-4 来自界面/实测，5-30 来自积分不足响应。
    REWARD_SCORE_THRESHOLDS = {
        1: 1000,
        2: 2500,
        3: 6500,
        4: 14500,
        5: 26500,
        6: 28000,
        7: 30250,
        8: 36250,
        9: 48250,
        10: 66250,
        11: 68250,
        12: 71250,
        13: 79250,
        14: 95250,
        15: 119250,
        16: 121750,
        17: 125500,
        18: 135500,
        19: 155500,
        20: 185500,
        21: 188000,
        22: 191750,
        23: 201750,
        24: 221750,
        25: 251750,
        26: 254250,
        27: 258000,
        28: 268000,
        29: 288000,
        30: 318000,
    }

    def __init__(self, account_name, ac_manager=None):
        self.account_name = account_name
        self.ac_manager = ac_manager or ACManager(account_name)

    def _build_and_send(self, hexstringheader, request_body):
        """构建带header的请求并发送"""
        serialized = request_body.SerializeToString()
        header = binascii.unhexlify(hexstringheader)[:2]
        length = len(serialized)
        len_bytes = bytes([length & 0xFF, (length >> 8) & 0xFF])
        binary_data = header + len_bytes + serialized
        return self.ac_manager.send_binary_data(
            self.account_name, binary_data, describe=hexstringheader, showres=0
        )

    def _make_requester(self):
        account = self.ac_manager.get_account(self.account_name)
        return self.ac_manager.common_header_requester1(account)

    def _parse_kg(self, res):
        """解析考古响应"""
        if not res or len(res) <= 20:
            return None
        resp = kpbl_pb2.kg_response()
        resp.ParseFromString(res[6:])
        return resp

    def query_kg(self):
        """d959: 查询考古状态"""
        config = {"ads": "考古查询", "times": 1, "hexstringheader": "d959"}
        res = self.ac_manager.do_common_request(self.account_name, config, showres=0)
        return self._parse_kg(res)

    def query_kg_raw(self, ads="考古查询"):
        """d959: 查询考古状态，返回原始响应。"""
        config = {"ads": ads, "times": 1, "hexstringheader": "d959"}
        return self.ac_manager.do_common_request(self.account_name, config, showres=0)

    def enter_kg(self):
        """1329: 进入考古页面，拉取入口/红点状态"""
        config = {"ads": "考古入口状态", "times": 1, "hexstringheader": "1329"}
        return self.ac_manager.do_common_request(self.account_name, config, showres=0)

    def dump_responses(self, out_dir="res", label=None):
        """保存考古入口和查询的原始响应，用于字段逆向。"""
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        label = label or f"{self.account_name}_{int(time.time())}"
        dumps = []
        for header, name, config in [
            ("1329", "enter", {"ads": f"{label}_kg_enter_1329", "times": 1, "hexstringheader": "1329"}),
            ("d959", "query", {"ads": f"{label}_kg_query_d959", "times": 1, "hexstringheader": "d959"}),
        ]:
            res = self.ac_manager.do_common_request(self.account_name, config, showres=0)
            if not res:
                print(f"  {header} {name}: 无响应")
                continue
            full_path = Path(out_dir) / f"{label}_{header}_{name}.bin"
            body_path = Path(out_dir) / f"{label}_{header}_{name}.body.bin"
            full_path.write_bytes(res)
            body_path.write_bytes(res[6:] if len(res) > 6 else b"")
            print(f"  {header} {name}: full={full_path} len={len(res)}, body={body_path} len={max(len(res) - 6, 0)}")
            if header == "d959":
                kg = self._parse_kg(res)
                if kg:
                    print(f"  d959 parsed: 挖矿任务积分={kg.mining_task_score}, field4={kg.field4}, field8={kg.field8}")
            dumps.append((header, name, str(full_path), str(body_path)))
        return dumps

    def claim_reward_response(self, tier, ads=None):
        """e159: 领取考古奖励，返回(status_code, raw_response)。"""
        config = {"ads": ads or f"考古领奖{tier}", "times": 1, "hexstringheader": "e159",
                  "request_body_i2": tier}
        res = self.ac_manager.do_common_request(self.account_name, config, showres=0)
        if not res or len(res) <= 6:
            return None, res
        sc = self.ac_manager.get_status_code(res)
        return sc, res

    def _classify_claim_response(self, status_code, res):
        """e159 成功包没有 status_code 字段，body 直接以 field2 奖励大包开始。"""
        body = res[6:] if res and len(res) > 6 else b""
        if body[:1] == b"\x12" or (status_code == 0 and len(body) > 20):
            return "success"
        if status_code == 114:
            return "already"
        if status_code == 103:
            return "insufficient"
        return "failed"

    def claim_reward_detail(self, tier, ads=None):
        """领取单档奖励，返回结构化结果。success 会实际发放奖励。"""
        sc, res = self.claim_reward_response(tier, ads=ads)
        result = self._classify_claim_response(sc, res)
        return {
            "tier": tier,
            "status_code": sc,
            "result": result,
            "response_len": len(res) if res else 0,
        }

    def claim_reward(self, tier):
        """e159: 领取考古奖励"""
        return self.claim_reward_detail(tier)["result"] == "success"

    def _today_key(self):
        return time.strftime("%Y-%m-%d", time.localtime())

    def _get_local_claimed_tiers(self, date_key):
        account = self.ac_manager.get_account(self.account_name) or {}
        if account.get("kg_reward_claimed_date") != date_key:
            return set()
        tiers = account.get("kg_reward_claimed_tiers") or []
        return {int(tier) for tier in tiers}

    def _save_local_claimed_tiers(self, date_key, tiers, score):
        """保留账号文件其他字段，只更新考古领奖状态。"""
        fields = {
            "kg_reward_claimed_date": date_key,
            "kg_reward_claimed_tiers": sorted(tiers),
            "kg_reward_claimed_score": score,
            "kg_reward_claimed_time": int(time.time()),
        }
        account = self.ac_manager.get_account(self.account_name)
        if account is not None:
            account.update(fields)

        accounts_file = getattr(self.ac_manager, "accounts_file", None)
        if not accounts_file:
            return
        path = Path(accounts_file)
        try:
            with path.open("r") as f:
                data = json.load(f)
            data.setdefault(self.account_name, {}).update(fields)
            with path.open("w") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"  保存考古领奖状态失败: {e}")

    def _eligible_reward_tiers(self, score):
        return [
            tier for tier, need in self.REWARD_SCORE_THRESHOLDS.items()
            if score >= need
        ]

    def scan_reward_claims(self, max_tier=30):
        """逐个尝试领奖并记录响应，用于逆向奖励领取状态。会实际领取可领奖励。"""
        label = int(time.time())
        before = self.query_kg()
        hammer_before = self.get_hammer_count()
        before_field4 = before.field4 if before else 0
        before_score = before.mining_task_score if before else 0
        before_field8 = before.field8 if before else 0
        print(f"== 奖励扫描开始: score={before_score}, field4={before_field4} ({bin(before_field4)}), field8={before_field8}, hammer={hammer_before} ==")

        successes = []
        date_key = self._today_key()
        local_claimed = self._get_local_claimed_tiers(date_key)
        local_changed = False
        for tier in range(max_tier + 1):
            ads = f"kg_rewardscan_{self.account_name}_{label}_tier{tier}"
            detail = self.claim_reward_detail(tier, ads=ads)
            sc = detail["status_code"]
            result = detail["result"]
            print(f"  tier {tier}: status={sc}, result={result}, len={detail['response_len']}")
            if tier > 0 and result in ("success", "already"):
                local_claimed.add(tier)
                local_changed = True
            if result != "success":
                continue

            after = self.query_kg()
            hammer_after = self.get_hammer_count()
            field4 = after.field4 if after else 0
            score = after.mining_task_score if after else 0
            field8 = after.field8 if after else 0
            changed = before_field4 ^ field4
            print(f"    成功: field4 {before_field4}->{field4} xor={changed} ({bin(changed)}), score={score}, field8={field8}, hammer {hammer_before}->{hammer_after}")
            successes.append({
                'tier': tier,
                'field4_before': before_field4,
                'field4_after': field4,
                'field4_xor': changed,
                'score': score,
                'field8': field8,
                'hammer_before': hammer_before,
                'hammer_after': hammer_after,
            })
            before_field4 = field4
            hammer_before = hammer_after

        if local_changed:
            self._save_local_claimed_tiers(date_key, local_claimed, before_score)

        final = self.query_kg()
        hammer_final = self.get_hammer_count()
        if final:
            print(f"== 奖励扫描结束: score={final.mining_task_score}, field4={final.field4} ({bin(final.field4)}), field8={final.field8}, hammer={hammer_final} ==")
        print(f"== 成功tier: {[s['tier'] for s in successes]} ==")
        return successes

    def dig(self, layer, x, y):
        """db59: 在指定层的(x,y)坐标挖掘"""
        req = kpbl_pb2.request_body_for_kg()
        req.r1.CopyFrom(self._make_requester())
        req.i2 = layer
        req.i3.x = x
        req.i3.y = y
        res = self._build_and_send("db59", req)
        if not res:
            return None
        return self._parse_kg(res.content)

    def query_board(self, layer):
        """db59: 查询指定层棋盘(不挖掘)"""
        config = {"ads": f"考古查询层{layer}", "times": 1, "hexstringheader": "db59",
                  "request_body_i2": layer}
        res = self.ac_manager.do_common_request(self.account_name, config, showres=0)
        return self._parse_kg(res)

    def claim_all_rewards(self):
        """领取当前积分可领取且今天未记录领取的奖励，返回成功领取的数量。"""
        kg = self.query_kg()
        score = kg.mining_task_score if kg else 0
        eligible = self._eligible_reward_tiers(score)
        date_key = self._today_key()
        local_claimed = self._get_local_claimed_tiers(date_key)
        pending = [tier for tier in eligible if tier not in local_claimed]

        print(f"  今日挖矿任务积分: {score}")
        if local_claimed:
            skipped = [tier for tier in eligible if tier in local_claimed]
            if skipped:
                print(f"  本地记录已领档位: {skipped}")
        if not pending:
            print("  没有新的可领取档位")
            return 0

        claimed = 0
        changed = False
        for tier in pending:
            need = self.REWARD_SCORE_THRESHOLDS.get(tier, 0)
            detail = self.claim_reward_detail(tier)
            result = detail["result"]
            status = detail["status_code"]
            if result == "success":
                claimed += 1
                local_claimed.add(tier)
                changed = True
                print(f"  领取奖励 tier {tier}({need}分) 成功")
            elif result == "already":
                local_claimed.add(tier)
                changed = True
                print(f"  奖励 tier {tier}({need}分) 服务端显示已领取，已记录")
            else:
                print(f"  奖励 tier {tier}({need}分) 未领取: status={status}, result={result}")

        if changed:
            self._save_local_claimed_tiers(date_key, local_claimed, score)
        return claimed

    def get_hammer_count(self):
        """登录刷新背包后，返回当前考古锤子数量"""
        self.ac_manager.login(self.account_name)
        baginfo = self.ac_manager.get_account(self.account_name, 'baginfo') or {}
        entry = baginfo.get(self.HAMMER_TYPE, 0)
        return entry.get('count', 0) if isinstance(entry, dict) else entry

    def print_status(self, label="考古状态"):
        """打印已解析出的考古棋盘和统计字段，用于观察任务积分/进度。"""
        kg = self.query_kg()
        if not kg:
            print(f"== {label}: 无法解析考古状态 ==")
            return None
        if kg.field4 or kg.mining_task_score or kg.field8:
            print(f"== {label}: 挖矿任务积分={kg.mining_task_score}, field4={kg.field4}, field8={kg.field8} ==")
        printed_stats = False
        for idx, board in enumerate((kg.boards.board1, kg.boards.board2), 1):
            if not board.board_id:
                continue
            layers = list(board.layers)
            print(f"== {label}: board{idx} id={board.board_id} {board.width}x{board.height} layers={layers} 已挖={len(board.dug_cells)} 宝物={self._treasure_progress_text(board)} ==")
            if board.stats:
                printed_stats = True
                stats = ", ".join(f"{s.stat_id}:{s.value}" + (f"/{s.variant}" if s.variant else "") for s in board.stats)
                print(f"  stats: {stats}")
        if not printed_stats:
            print("  未解析到考古任务积分/进度字段")
        return kg

    def status_snapshot(self, kg=None):
        """返回可比较的考古状态快照。"""
        kg = kg or self.query_kg()
        if not kg:
            return []
        snapshot = []
        if kg.field4 or kg.mining_task_score or kg.field8:
            snapshot.append({
                'top': 'kg',
                'field4': kg.field4,
                'mining_task_score': kg.mining_task_score,
                'field8': kg.field8,
            })
        for idx, board in enumerate((kg.boards.board1, kg.boards.board2), 1):
            if not board.board_id:
                continue
            snapshot.append({
                'board': idx,
                'board_id': board.board_id,
                'layers': list(board.layers),
                'dug': len(board.dug_cells),
                'items': len(board.items),
                'stats': [(s.stat_id, s.value, s.variant) for s in board.stats],
            })
        return snapshot

    def collect_info(self):
        """只进入考古、领取任务奖励并统计锤子数量，不抽蛋也不挖掘。"""
        print("== 考古信息: 进入考古 ==")
        self.enter_kg()
        print("== 考古信息: 领取任务奖励 ==")
        claimed = self.claim_all_rewards()
        hammer = self.get_hammer_count()
        print(f"== 考古信息: 领取 {claimed} 档, 锤子数量 = {hammer} ==")
        return hammer

    def get_undug_cells(self, board):
        """获取未挖掘的格子坐标列表"""
        dug_set = self._dug_set(board)
        undug = []
        for y in range(board.height):
            for x in range(board.width):
                if (x, y) not in dug_set:
                    undug.append((x, y))
        return undug

    def _dug_set(self, board):
        return {(dc.pos.x, dc.pos.y) for dc in board.dug_cells}

    def _board_key(self, board):
        return (board.board_id, tuple(board.layers), board.width, board.height)

    def _board_layer(self, board):
        return board.layers[0] if board.layers else 0

    def _treasure_progress(self, board):
        """返回(已发现宝物数, 当前层宝物总数)。stats 目前表现为本层宝物列表。"""
        found = len(board.items)
        total = len(board.stats) if board.stats else found
        return found, max(total, found)

    def _treasure_progress_text(self, board):
        found, total = self._treasure_progress(board)
        if total:
            return f"{found}/{total}"
        return str(found)

    def _is_layer_complete(self, board):
        found, total = self._treasure_progress(board)
        return total > 0 and found >= total and not self._incomplete_treasures(board)

    def _item_cells(self, item):
        return [(c.x, c.y) for c in item.cells]

    def _remaining_item_cells(self, board, item):
        dug = self._dug_set(board)
        cells = self._item_cells(item)
        return [cell for cell in cells if cell not in dug]

    def _covered_item_cells(self, board, item):
        dug = self._dug_set(board)
        return sum(1 for cell in self._item_cells(item) if cell in dug)

    def _incomplete_treasures(self, board):
        treasures = []
        for item in board.items:
            cells = self._item_cells(item)
            if not cells:
                continue
            remaining = self._remaining_item_cells(board, item)
            if remaining:
                treasures.append((item, remaining, len(cells) - len(remaining), len(cells)))
        return treasures

    def _treasure_label(self, item):
        suffix = f"/{item.variant}" if item.variant else ""
        return f"type={item.treasure_type}{suffix}"

    def _ordered_undug_cells(self, board):
        undug = self.get_undug_cells(board)
        dig_order = sorted(undug, key=lambda c: (c[1], c[0]))
        phase1 = [c for c in dig_order if (c[0] + c[1]) % 2 == 0]
        phase2 = [c for c in dig_order if (c[0] + c[1]) % 2 == 1]
        return undug, phase1 + phase2

    def print_board(self, board):
        """打印棋盘状态"""
        # 构建宝物地图
        treasure_map = {}
        for item in board.items:
            for c in item.cells:
                treasure_map[(c.x, c.y)] = item.treasure_type
        # 构建已挖掘集合
        dug_set = self._dug_set(board)
        completing_set = set()
        for dc in board.dug_cells:
            if dc.is_completing:
                completing_set.add((dc.pos.x, dc.pos.y))

        total = board.width * board.height
        dug_count = len(dug_set)
        print(f"  棋盘 {board.board_id} ({board.width}x{board.height}), 已挖 {dug_count}/{total}, 宝物 {self._treasure_progress_text(board)} 个")
        for y in range(board.height - 1, -1, -1):
            row = f"  y={y}: "
            for x in range(board.width):
                if (x, y) in dug_set:
                    if (x, y) in treasure_map:
                        t = treasure_map[(x, y)]
                        mark = f"{t}*" if (x, y) in completing_set else f"{t} "
                    else:
                        mark = "o "
                else:
                    mark = ". "
                row += mark
            print(row)
        print("       " + "".join(f"{x} " for x in range(board.width)))

    def dig_available(self, hammer=None):
        """使用当前锤子自动挖掘，不抽蛋、不领奖。"""
        if hammer is None:
            hammer = self.get_hammer_count()
        print(f"== 考古挖掘: 锤子数量 = {hammer} ==")
        if hammer <= 0:
            print("  没有锤子，结束")
            return 0

        print("== 自动挖掘 ==")
        kg = self.query_kg()
        if not kg or not kg.boards.board1.board_id:
            print("  无法获取考古数据")
            return 0

        board = kg.boards.board1
        layer = self._board_layer(board)
        if not layer:
            print("  无法获取层数")
            return 0

        dug_count = 0
        while hammer > 0:
            layer = self._board_layer(board)
            if not layer:
                print("  无法获取层数")
                break
            if self._is_layer_complete(board):
                print(f"  层 {layer} 宝物已全部发现 ({self._treasure_progress_text(board)})，先查询是否已切到新层")
                refreshed = self.query_kg()
                if refreshed and refreshed.boards.board1.board_id and self._board_key(refreshed.boards.board1) != self._board_key(board):
                    old_board = board
                    board = refreshed.boards.board1
                    print(f"  查询到新矿图: layer {self._board_layer(old_board)}->{self._board_layer(board)}, board {old_board.board_id}->{board.board_id}")
                    continue
                print("  未查询到新层，停止挖掘以避免继续消耗旧层空格")
                break

            incomplete = self._incomplete_treasures(board)
            if incomplete:
                self.print_board(board)
                summary = ", ".join(
                    f"{self._treasure_label(item)} {covered}/{total}"
                    for item, _, covered, total in incomplete
                )
                print(f"  优先补完已发现宝物: {summary}")
                replan = False
                stop_after_complete = False
                for item, remaining, covered, total in incomplete:
                    ordered_remaining = sorted(remaining, key=lambda c: (c[1], c[0]))
                    print(f"  补完 {self._treasure_label(item)} {covered}/{total}: {ordered_remaining}")
                    for x, y in ordered_remaining:
                        if hammer <= 0:
                            break
                        old_board = board
                        old_key = self._board_key(old_board)
                        old_found, old_total = self._treasure_progress(old_board)
                        result = self.dig(layer, x, y)
                        hammer -= 1
                        dug_count += 1
                        found_text = ""
                        if result and result.boards.board1.board_id:
                            new_board = result.boards.board1
                            new_key = self._board_key(new_board)
                            new_found, new_total = self._treasure_progress(new_board)
                            if new_found > old_found:
                                found_text = f", 发现宝物! ({old_found}/{old_total}->{new_found}/{new_total})"
                            board = new_board
                            if new_key != old_key:
                                print(f"  补挖宝物 ({x},{y}) 剩余锤子 {hammer}{found_text}")
                                print(f"  矿图已更新: layer {self._board_layer(old_board)}->{self._board_layer(new_board)}, board {old_board.board_id}->{new_board.board_id}，重新规划")
                                replan = True
                                break
                            if self._is_layer_complete(new_board):
                                print(f"  补挖宝物 ({x},{y}) 剩余锤子 {hammer}{found_text}")
                                print(f"  当前层宝物已全部挖完 ({self._treasure_progress_text(new_board)})，重新查询矿图")
                                refreshed = self.query_kg()
                                if refreshed and refreshed.boards.board1.board_id:
                                    refreshed_board = refreshed.boards.board1
                                    if self._board_key(refreshed_board) != new_key:
                                        board = refreshed_board
                                        print(f"  查询到新矿图: layer {self._board_layer(new_board)}->{self._board_layer(refreshed_board)}, board {new_board.board_id}->{refreshed_board.board_id}")
                                        replan = True
                                    else:
                                        stop_after_complete = True
                                else:
                                    stop_after_complete = True
                                break
                        print(f"  补挖宝物 ({x},{y}) 剩余锤子 {hammer}{found_text}")
                        time.sleep(0.3)
                    if replan or stop_after_complete or hammer <= 0:
                        break
                if stop_after_complete:
                    print("  未查询到新层，停止挖掘以避免继续消耗旧层空格")
                    break
                continue

            self.print_board(board)
            undug, ordered = self._ordered_undug_cells(board)
            print(f"  层 {layer}, 未挖 {len(undug)} 格, 宝物 {self._treasure_progress_text(board)}, 锤子 {hammer}")
            if not ordered:
                print("  当前层没有可挖格子，结束")
                break

            replan = False
            stop_after_complete = False
            for x, y in ordered:
                if hammer <= 0:
                    break
                old_board = board
                old_key = self._board_key(old_board)
                old_found, old_total = self._treasure_progress(old_board)
                result = self.dig(layer, x, y)
                hammer -= 1
                dug_count += 1
                found_text = ""
                if result and result.boards.board1.board_id:
                    new_board = result.boards.board1
                    new_key = self._board_key(new_board)
                    new_found, new_total = self._treasure_progress(new_board)
                    if new_found > old_found:
                        found_text = f", 发现宝物! ({old_found}/{old_total}->{new_found}/{new_total})"
                    board = new_board
                    if new_key != old_key:
                        print(f"  挖掘 ({x},{y}) 剩余锤子 {hammer}{found_text}")
                        print(f"  矿图已更新: layer {self._board_layer(old_board)}->{self._board_layer(new_board)}, board {old_board.board_id}->{new_board.board_id}，重新规划")
                        replan = True
                        break
                    if new_found > old_found and self._incomplete_treasures(new_board):
                        print(f"  挖掘 ({x},{y}) 剩余锤子 {hammer}{found_text}")
                        print("  新发现宝物尚未挖完，切换为补完宝物")
                        replan = True
                        break
                    if self._is_layer_complete(new_board):
                        print(f"  挖掘 ({x},{y}) 剩余锤子 {hammer}{found_text}")
                        print(f"  当前层宝物已全部挖完 ({self._treasure_progress_text(new_board)})，重新查询矿图")
                        refreshed = self.query_kg()
                        if refreshed and refreshed.boards.board1.board_id:
                            refreshed_board = refreshed.boards.board1
                            if self._board_key(refreshed_board) != new_key:
                                board = refreshed_board
                                print(f"  查询到新矿图: layer {self._board_layer(new_board)}->{self._board_layer(refreshed_board)}, board {new_board.board_id}->{refreshed_board.board_id}")
                                replan = True
                            else:
                                stop_after_complete = True
                        else:
                            stop_after_complete = True
                        break
                print(f"  挖掘 ({x},{y}) 剩余锤子 {hammer}{found_text}")
                time.sleep(0.3)
            if stop_after_complete:
                print("  未查询到新层，停止挖掘以避免继续消耗旧层空格")
                break
            if not replan:
                break

        print(f"== 完成: 共挖 {dug_count} 格 ==")
        self.print_board(board)
        return dug_count

    def run(self):
        """执行考古：进入页面 → 领取积分奖励 → 自动挖掘 → 结果汇报。"""

        print("== 步骤1: 进入考古 ==")
        self.enter_kg()
        before_kg = self.query_kg()
        score_before = before_kg.mining_task_score if before_kg else 0
        hammer_before = self.get_hammer_count()
        print(f"  初始积分={score_before}, 初始锤子={hammer_before}")

        print("== 步骤2: 领取积分奖励 ==")
        claimed = self.claim_all_rewards()
        hammer_after_claim = self.get_hammer_count()
        print(f"  已领取 {claimed} 档, 锤子 {hammer_before}->{hammer_after_claim}")

        print("== 步骤3: 自动挖掘 ==")
        dug_count = self.dig_available(hammer_after_claim)
        hammer_final = self.get_hammer_count()
        final_kg = self.query_kg()
        score_final = final_kg.mining_task_score if final_kg else score_before

        print("== 考古结果汇报 ==")
        print(f"  积分: {score_before}->{score_final}")
        print(f"  领奖: {claimed} 档")
        print(f"  锤子: {hammer_before}->{hammer_after_claim}->{hammer_final}")
        print(f"  挖掘: {dug_count} 格")
        return {
            "score_before": score_before,
            "score_final": score_final,
            "claimed": claimed,
            "hammer_before": hammer_before,
            "hammer_after_claim": hammer_after_claim,
            "hammer_final": hammer_final,
            "dug_count": dug_count,
        }
