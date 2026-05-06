"""
贸易管理模块
处理游戏中的贸易功能
"""

import logging
from .kpbltools import ACManager, mask_account
import modules.kpbl_pb2 as kpbl_pb2

class TradeManager:
    """贸易管理器"""

    GRC_TARGET_ITEM_ID = 135
    GRC_TARGET_ITEM_COUNT = 200
    GRC_SLOT_COUNT = 2
    
    def __init__(self, account_name, delay=0, showres=0, ac_manager=None):
        self.account_name = account_name
        self.ac_manager = ac_manager or ACManager(account_name, delay=delay, showres=showres)
        self.logger = logging.getLogger(f"TradeManager_{account_name}")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.StreamHandler())
        self.showres = showres

    def _parse_grc_response(self, res):
        if not res or len(res) <= 6:
            return None
        resp = kpbl_pb2.grc_personal_boat_response()
        resp.ParseFromString(res[6:])
        return resp

    def _grc_request(self, ads, header, slot_index=None):
        config = {"ads": ads, "times": 1, "hexstringheader": header}
        if slot_index is not None:
            config["request_body_i2"] = int(slot_index)
        res = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        return self._parse_grc_response(res)

    def _grc_cabins_from_response(self, resp):
        if not resp:
            return []
        cabins = list(resp.cabins)
        if resp.started_cabin.slot_index:
            cabins.append(resp.started_cabin)
        return cabins

    def _grc_cabin_from_response(self, resp, slot_index=None):
        cabins = self._grc_cabins_from_response(resp)
        if slot_index is None:
            return cabins[0] if cabins else None
        return next((cabin for cabin in cabins if cabin.slot_index == slot_index), None)

    def _grc_item_pairs(self, cabin):
        if not cabin:
            return []
        return [(item.item.itemid, item.item.itemcount) for item in cabin.items]

    def _grc_items_text(self, cabin):
        parts = []
        for item_id, count in self._grc_item_pairs(cabin):
            name = self.item_list.get(item_id, f"#{item_id}")
            parts.append(f"{name}×{count}")
        return ", ".join(parts) if parts else "空"

    def _grc_has_target(self, cabin):
        return any(
            item_id == self.GRC_TARGET_ITEM_ID and count >= self.GRC_TARGET_ITEM_COUNT
            for item_id, count in self._grc_item_pairs(cabin)
        )

    def _grc_print_cabin(self, cabin, prefix):
        if not cabin:
            print(f"{prefix}: 无船舱数据")
            return
        hit = "命中" if self._grc_has_target(cabin) else "未命中"
        print(
            f"{prefix}: 舱{cabin.slot_index} 稀有={cabin.rarity} "
            f"state={cabin.state} refresh_id={cabin.refresh_id} {hit} | {self._grc_items_text(cabin)}"
        )

    def claim_previous_grc_reward(self, slot_index):
        # TODO: 领取上一次个人船到达奖励。grc.chlz 未录到该请求，后续补充。
        return False

    def enter_grc_page(self):
        """进入开船入口和个人船页面，返回当前个人船页面响应。"""
        self._grc_request("开船入口", "0d62")
        resp = self._grc_request("个人船页面", "8162")
        cabins = self._grc_cabins_from_response(resp)
        if cabins:
            print(f"个人船页面: {len(cabins)} 个船舱")
            for cabin in cabins[:self.GRC_SLOT_COUNT]:
                self._grc_print_cabin(cabin, "  当前")
        else:
            print("个人船页面: 未解析到船舱")
        return resp

    def _grc_check_or_refresh_slot(self, slot_index, ads):
        resp = self._grc_request(ads, "7362", slot_index=slot_index)
        return self._grc_cabin_from_response(resp, slot_index=slot_index)

    def _grc_start_slot(self, slot_index):
        resp = self._grc_request(f"个人船开船{slot_index}", "7762", slot_index=slot_index)
        cabin = self._grc_cabin_from_response(resp, slot_index=slot_index)
        if cabin:
            self._grc_print_cabin(cabin, f"  开船结果")
            return True, cabin
        print(f"  舱{slot_index} 开船响应未解析到船舱")
        return False, None

    def _grc_prepare_slot(self, slot_index, max_refresh):
        self.claim_previous_grc_reward(slot_index)
        cabin = self._grc_check_or_refresh_slot(slot_index, f"个人船查看舱{slot_index}")
        self._grc_print_cabin(cabin, f"  查看")
        if self._grc_has_target(cabin):
            return cabin, 0

        for refresh_count in range(1, max_refresh + 1):
            cabin = self._grc_check_or_refresh_slot(slot_index, f"个人船刷新舱{slot_index}")
            self._grc_print_cabin(cabin, f"  刷新#{refresh_count}")
            if self._grc_has_target(cabin):
                return cabin, refresh_count

        print(f"  舱{slot_index} 达到最大刷新次数 {max_refresh}，仍未出现功勋币×{self.GRC_TARGET_ITEM_COUNT}")
        return None, max_refresh

    def run_grc(self, max_refresh=50):
        """个人船：两舱依次刷新到功勋币×200后开船。"""
        print("== 个人船刷新开船 ==")
        self.enter_grc_page()
        results = []
        for slot_index in range(1, self.GRC_SLOT_COUNT + 1):
            print(f"== 舱{slot_index}: 查看并刷新到功勋币×{self.GRC_TARGET_ITEM_COUNT} ==")
            cabin, refresh_count = self._grc_prepare_slot(slot_index, max_refresh)
            if not cabin:
                results.append({"slot": slot_index, "refresh": refresh_count, "started": False})
                continue
            print(f"== 舱{slot_index}: 条件满足，开船 ==")
            started, started_cabin = self._grc_start_slot(slot_index)
            results.append({
                "slot": slot_index,
                "refresh": refresh_count,
                "started": started,
                "items": self._grc_item_pairs(started_cabin or cabin),
            })

        print("== 个人船结果汇报 ==")
        for result in results:
            status = "已开船" if result["started"] else "未开船"
            print(f"  舱{result['slot']}: 刷新{result['refresh']}次, {status}")
        return all(result["started"] for result in results)
    
    def refresh(self):
        """刷新贸易数据"""
        config = {
            "ads": "贸易刷新",
            "times": 1,
            "request_body_i2": 1,
            "hexstringheader": "a961",
        }
        res = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        if len(res)>20:
            refresh_resp = kpbl_pb2.jielve_refreash_response()
            refresh_resp.ParseFromString(res[6:])
            # print(refresh_resp)
            return refresh_resp
        return 0

    def boatinfo(self, boat):
        """获取船只信息"""
        config = {
            "ads": "船只信息",
            "times": 1,
            "hexstringheader": "ab61",
            "request_body_i2":boat.boatpara2, # boatpara2
            "request_body_i3":boat.boatpara1, # boatpara1
            "request_body_i4":boat.boatpara4, # guild_id / boatpara4
            "request_body_i5":boat.boatpara5, # user_id
            "request_body_i6":boat.boatpara10, # boatpara10
            "requestbodytype": "request_body_allint1"
        }
        res = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        # print(res)
        if len(res)>20:
            boatinfo_resp = kpbl_pb2.jielve_boatinfo_response()
            boatinfo_resp.ParseFromString(res[6:])
            items = {}
            i = 0
            for slot in boatinfo_resp.i4.slots:
                # print(slot)
                if slot.hasjl == 1:
                    continue
                items[i] = {
                    "itemid": slot.item.itemid,
                    "itemcount": slot.item.itemcount,
                }
                i += 1
            max_135 = max((slot.item.itemcount for slot in boatinfo_resp.i4.slots if slot.item.itemid == 135 and slot.hasjl != 1), default=0)
            max_59 = max((slot.item.itemcount for slot in boatinfo_resp.i4.slots if slot.item.itemid == 59 and slot.hasjl != 1), default=0)
            max_5604 = max((slot.item.itemcount for slot in boatinfo_resp.i4.slots if slot.item.itemid == 5604 and slot.hasjl != 1), default=0)
            items_135 = [(slot.item.itemcount) for slot in boatinfo_resp.i4.slots if slot.item.itemid == 135 and slot.hasjl != 1]
            items_59 = [(slot.item.itemcount) for slot in boatinfo_resp.i4.slots if slot.item.itemid == 59 and slot.hasjl != 1]
            items_5604 = [(slot.item.itemcount) for slot in boatinfo_resp.i4.slots if slot.item.itemid == 5604 and slot.hasjl != 1]
            parts = []
            if items_135:
                parts.append(f"功勋币({len(items_135)}): {items_135}")
            if items_59:
                parts.append(f"武装令牌({len(items_59)}): {items_59}")
            if items_5604:
                parts.append(f"武装宝箱({len(items_5604)}): {items_5604}")
            if parts:
                print(f"{boat.boatpara5} slots:{len(items)} | " + " | ".join(parts))
            return len(items), max_135, max_59, max_5604
        return 0, 0, 0, 0

    def attack(self, boat):
        """攻击"""
        config = {
            "ads": "劫掠攻击",
            "times": 1,
            "request_body_i2": boat.boatpara1, # 2 
            "request_body_i3": boat.boatpara5, # 11500508
            "hexstringheader": "af61",
        }
        res = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        # print(f'atk: {len(res)}')
        # slots, max_135 = self.boatinfo(boat)

        return len(res)>20
    def attackbyid(self, boatid):
        """攻击"""
        config = {
            "ads": "劫掠攻击",
            "times": 1,
            "request_body_i2": 2, # 2
            "request_body_i3": boatid, # 11500508
            "hexstringheader": "af61",
        }
        res = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        # print(res)
        print(f'atk: {len(res)}')
        return len(res)>20

    def attack_guild_ship(self, boatpara1, boatpara4):
        """攻击公会船 (ad61)"""
        config = {
            "ads": "攻击公会船",
            "times": 1,
            "request_body_i2": int(boatpara1), #boat.boatpara1, #guild_boat_id
            "request_body_i3": int(boatpara4), # boat.boatpara4,    # guild_id
            "hexstringheader": "ad61",    # DxxType 25005
        }
        res = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        print(f'atk_guild_ship: {len(res)}')
        return len(res) > 20

    from .item_names import ITEM_NAMES as item_list

    def guild_boatinfo(self, boat):
        """获取公会船只信息（使用ab61，解析jielve_guild_boat_response）"""
        config = {
            "ads": "公会船信息",
            "times": 1,
            "hexstringheader": "ab61",
            "request_body_i2": boat.boatpara2,     # 1 (普通船是boatpara1)
            "request_body_i3": boat.boatpara1,     # guild_boat_id (普通船是boatpara2)
            "request_body_i4": boat.boatpara4,     # guild_id
            "request_body_i5": boat.boatpara5,     # user_id
            "requestbodytype": "request_body_allint1"
        }
        res = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        if len(res) > 20:
            resp = kpbl_pb2.jielve_guild_boat_response()
            resp.ParseFromString(res[6:])
            # 查找匹配的船只
            target_boat = None
            for b in resp.boats:
                if b.boatpara1 == boat.boatpara1:
                    target_boat = b
                    break
            if not target_boat:
                return 0, 0, 0, 0, []
            # 按船舱统计物品
            items_count = 0
            max_135 = 0
            max_59 = 0
            max_5604 = 0
            guild_slots = []  # 保存舱位详情
            for slot in target_boat.slots:
                rarity = slot.field4
                slot_items = []
                for item_container in slot.items:
                    if item_container.hasjl == 1:
                        continue
                    items_count += 1
                    item = item_container.item
                    name = self.item_list.get(item.itemid, f"#{item.itemid}")
                    slot_items.append({'id': item.itemid, 'text': f"{name}×{item.itemcount}"})
                    if item.itemid == 135:
                        max_135 = max(max_135, item.itemcount)
                    elif item.itemid == 59:
                        max_59 = max(max_59, item.itemcount)
                    elif item.itemid == 5604:
                        max_5604 = max(max_5604, item.itemcount)
                guild_slots.append({'rarity': rarity, 'slotid': slot.slotid, 'items': slot_items})
            return items_count, max_135, max_59, max_5604, guild_slots
        return 0, 0, 0, 0, []

    def getboat(self, maxtry, guild_only=False, seen_ids=None):
        results = []  # (slotslen, max_135, max_59, max_5604, boat, is_guild, guild_slots)
        if seen_ids is None:
            seen_ids = set()
        while maxtry >= 0:
            print(f"maxtry: {maxtry}")
            maxtry -= 1
            boats = self.refresh()
            for boat in boats.boats:
                # 公会船：rare==99，无条件加入
                if boat.rare == 99:
                    boat_key = f"guild_{boat.boatpara1}"
                    if boat_key in seen_ids:
                        continue
                    seen_ids.add(boat_key)
                    slotslen, max_135, max_59, max_5604, guild_slots = self.guild_boatinfo(boat)
                    # 需要有2个以上稀有度>=5的船舱
                    high_rarity_count = sum(1 for s in guild_slots if s['rarity'] >= 5)
                    if high_rarity_count >= 2:
                        results.append((slotslen, max_135, max_59, max_5604, boat, True, guild_slots))
                # 普通船
                elif not guild_only and boat.rare >= 4 and not boat.boathasjlcount and boat.boatpara5 not in seen_ids:
                    seen_ids.add(boat.boatpara5)
                    slotslen, max_135, max_59, max_5604 = self.boatinfo(boat)
                    if max_135 >= 200 or max_59 >= 200 or max_5604 >= 1:
                        results.append((slotslen, max_135, max_59, max_5604, boat, False, None))
        results.sort(key=lambda x: x[0])
        return results

    def getghinfo(self):
        config = {
            "ads": "公会信息",
            "times": 1,
            "hexstringheader": "0d62",    # DxxType 25005
        }
        res = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        if len(res) > 20:
            resp = kpbl_pb2.jielve_guild_boat_response()
            resp.ParseFromString(res[6:])
            return resp
        return None

    TARGET_ITEMS = {1386015, 1386016}
    TARGET_5605 = 5605

    def _count_boat_items(self, boat):
        """统计船上目标物品数量，返回 (1386015+1386016总数, 5605总数)"""
        count_1386 = 0
        count_5605 = 0
        for slot in boat.slots:
            for ic in slot.items:
                iid = ic.item.itemid
                if iid in self.TARGET_ITEMS:
                    count_1386 += ic.item.itemcount
                elif iid == self.TARGET_5605:
                    count_5605 += ic.item.itemcount
        return count_1386, count_5605

    def boat_refresh_until(self, max_tries=50, target_boat_id=None):
        """刷新公会船货物，直到 1386015+1386016 >= 3 且 5605 >= 3"""
        resp = self.getghinfo()
        if not resp or not resp.boats:
            print("无法获取公会船信息")
            return False
        # 找到目标船
        boat = None
        if target_boat_id:
            for b in resp.boats:
                if b.boatpara1 == target_boat_id:
                    boat = b
                    break
            if not boat:
                print(f"未找到目标船 {target_boat_id}")
                return False
        else:
            boat = resp.boats[0]
        boat_id = boat.boatpara1

        count_1386, count_5605 = self._count_boat_items(boat)
        print(f"  初始状态: 1386015+1386016={count_1386}, 5605={count_5605}")

        tries = 0
        while count_1386 < 3 or count_5605 < 3:
            if tries >= max_tries:
                print(f"  达到最大刷新次数 {max_tries}，停止")
                return False
            config = {
                "ads": "船货刷新",
                "times": 1,
                "hexstringheader": "1762",
                "request_body_i2": boat_id,
            }
            res = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
            tries += 1
            if not res or len(res) <= 20:
                print(f"  刷新失败，停止")
                return False
            resp = kpbl_pb2.jielve_guild_boat_response()
            resp.ParseFromString(res[6:])
            if not resp.boats:
                print(f"  刷新响应无船数据，停止")
                return False
            boat = next((b for b in resp.boats if b.boatpara1 == boat_id), resp.boats[0])
            count_1386, count_5605 = self._count_boat_items(boat)
            print(f"  刷新#{tries}: 1386015+1386016={count_1386}, 5605={count_5605}")

        print(f"  条件满足，共刷新 {tries} 次")
        return True

    def assign_captain(self, boat_id, member_charaid=None):
        """任命船长 (1d62): 会长指定某成员为船长，默认任命自己"""
        if member_charaid is None:
            member_charaid = self.ac_manager.get_account(self.account_name, 'charaid')
            if not member_charaid:
                print("未找到charaid，无法任命船长")
                return False
        config = {
            "ads": "任命船长",
            "times": 1,
            "hexstringheader": "1d62",
            "request_body_i2": int(boat_id),
            "request_body_i3": int(member_charaid),
        }
        res = self.ac_manager.do_common_request(self.account_name, config, showres=self.showres)
        ok = len(res) > 20
        print(f"任命船长: boat={boat_id}, captain={member_charaid}, {'成功' if ok else '失败'}")
        return ok
