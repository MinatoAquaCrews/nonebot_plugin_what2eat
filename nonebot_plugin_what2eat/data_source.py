import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from nonebot import Bot, get_bot, get_driver, logger
from nonebot.adapters.onebot.v11 import (ActionFailed, GroupMessageEvent,
                                         Message, MessageSegment,
                                         PrivateMessageEvent)

from .config import what2eat_config
from .utils import *


class EatingManager:
    def __init__(self):
        self._eating: Dict[str, Union[List[str], Dict[str,
                                                      Union[Dict[str, List[int]], List[str]]]]] = {}
        self._greetings: Dict[str, Union[List[str], Dict[str, bool]]] = {}

        self._eating_json: Path = what2eat_config.what2eat_path / "eating.json"
        self._greetings_json: Path = what2eat_config.what2eat_path / "greetings.json"
        self._drinks_json: Path = what2eat_config.what2eat_path / "drinks.json"
        self._img_dir: Path = what2eat_config.what2eat_path / "img"

    def _init_data(self, gid: str, uid: Optional[str] = None) -> None:
        '''
            初始化用户信息
        '''
        if gid not in self._eating["group_food"]:
            self._eating["group_food"][gid] = []
        if gid not in self._eating["count"]:
            self._eating["count"][gid] = {}

        if isinstance(uid, str):
            if uid not in self._eating["count"][gid]:
                self._eating["count"][gid][uid] = 0

    def get2eat(self, event: Union[PrivateMessageEvent, GroupMessageEvent]) -> Tuple[Message, MessageSegment]:
        '''
            今天吃什么
        '''
        # Deal with private message event FIRST
        if isinstance(event, PrivateMessageEvent):
            if len(self._eating["basic_food"]) > 0:
                return MessageSegment.text("建议") + Message(random.choice(self._eating["basic_food"]))
            else:
                return MessageSegment.text("还没有菜单呢，就先饿着肚子吧，请[添加 菜名]🤤")

        uid: str = str(event.user_id)
        gid: str = str(event.group_id)
        food_list: List[str] = []

        self._eating = load_json(self._eating_json)
        self._init_data(gid, uid)

        # Check whether is full of stomach
        if self._eating["count"][gid][uid] >= what2eat_config.eating_limit:
            save_json(self._eating_json, self._eating)
            return MessageSegment.text(random.choice(EatingEnough_List))
        else:
            # basic_food and group_food both are EMPTY
            if len(self._eating["basic_food"]) == 0 and len(self._eating["group_food"][gid]) == 0:
                return MessageSegment.text("还没有菜单呢，就先饿着肚子吧，请[添加 菜名]🤤")

            food_list = self._eating["basic_food"].copy()

            # 取并集
            if len(self._eating["group_food"][gid]) > 0:
                food_list = list(set(food_list).union(
                    set(self._eating["group_food"][gid])))

            msg = MessageSegment.text("建议") + Message(random.choice(food_list))
            self._eating["count"][gid][uid] += 1
            save_json(self._eating_json, self._eating)

            return msg

    def get2drink(self, event: Union[PrivateMessageEvent, GroupMessageEvent]) -> MessageSegment:
        '''
            今天喝什么
        '''
        # Deal with private message event first
        if isinstance(event, PrivateMessageEvent):
            _branch, _drink = self.pick_one_drink()
            return MessageSegment.text(random.choice(
                [
                    f"不如来杯 {_branch} 的 {_drink} 吧！",
                    f"去 {_branch} 整杯 {_drink} 吧！",
                    f"{_branch} 的 {_drink} 如何？",
                    f"{_branch} 的 {_drink}，好喝绝绝子！"
                ]
            )
            )

        uid: str = str(event.user_id)
        gid: str = str(event.group_id)

        self._eating = load_json(self._eating_json)
        self._init_data(gid, uid)

        # Check whether is full of stomach
        if self._eating["count"][gid][uid] >= what2eat_config.eating_limit:
            save_json(self._eating_json, self._eating)
            return MessageSegment.text(random.choice(DrinkingEnough_List))
        else:
            _branch, _drink = self.pick_one_drink()
            self._eating["count"][gid][uid] += 1
            save_json(self._eating_json, self._eating)

            return MessageSegment.text(random.choice(
                [
                    f"不如来杯 {_branch} 的 {_drink} 吧！",
                    f"去 {_branch} 整杯 {_drink} 吧！",
                    f"{_branch} 的 {_drink} 如何？",
                    f"{_branch} 的 {_drink}，好喝绝绝子！"
                ]
            )
            )

    def _is_food_exists(self, _food: str, _search: SearchLoc, gid: Optional[str] = None) -> Tuple[FoodLoc, str]:
        '''
            检查菜品是否存在于某个群组/全局，优先检测是否在群组，返回菜品所在区域及其全称；
            - gid = None, 搜索群组
            - _search: IN_BASIC, IN_GROUP or IN_GLOBAL（全局指本群与基础菜单）

            群组添加菜品: gid=str, _search=IN_GLOBAL
            优先检测群组是否匹配，返回：
            IN_BASIC, IN_GROUP, NOT_EXISTS

            基础添加菜品: gid=None, _search=IN_BASIC
            仅检测基础菜单是否存在，返回：
            IN_BASIC, NOT_EXISTS

            群组移除菜品: gid=str, _search=IN_GLOBAL
            全局检测，返回：IN_BASIC, IN_GROUP, NOT_EXISTS

            Notes:
            1. 添加时，文字与图片一一对应才认为是相同的菜品
            2. 移除时，移除文字匹配的第一个；若配图也被移除，同时移除配图相同的其余菜品（即使在基础菜单中）
        '''
        if _search == SearchLoc.IN_GROUP or _search == SearchLoc.IN_GLOBAL:
            if isinstance(gid, str):
                if gid in self._eating["group_food"]:
                    for food in self._eating["group_food"][gid]:
                        # food is the full name or _food matches the food name before CQ code
                        if _food == food or _food == food.split("[CQ:image")[0]:
                            return FoodLoc.IN_GROUP, food

                    if _search == SearchLoc.IN_GROUP:
                        return FoodLoc.NOT_EXISTS, ""

        if _search == SearchLoc.IN_BASIC or _search == SearchLoc.IN_GLOBAL:
            for food in self._eating["basic_food"]:
                if _food == food or _food == food.split("[CQ:image")[0]:
                    return FoodLoc.IN_BASIC, food

            return FoodLoc.NOT_EXISTS, ""

    def add_group_food(self, event: GroupMessageEvent, new_food: str) -> str:
        '''
            添加至群菜单
        '''
        uid: str = str(event.user_id)
        gid: str = str(event.group_id)
        msg: str = ""

        self._eating = load_json(self._eating_json)
        self._init_data(gid, uid)
        status, _ = self._is_food_exists(
            new_food, SearchLoc.IN_GLOBAL, gid)  # new food may include cq

        if status == FoodLoc.IN_BASIC:
            msg = f"已在基础菜单中~"
        elif status == FoodLoc.IN_GROUP:
            msg = f"已在群特色菜单中~"
        else:
            # If image included, save it, return the path in string
            self._eating["group_food"][gid].append(new_food)
            msg = f"已加入群特色菜单~"

        save_json(self._eating_json, self._eating)
        return msg

    def add_basic_food(self, new_food: str) -> str:
        '''
            添加至基础菜单
        '''
        self._eating = load_json(self._eating_json)
        msg: str = ""
        status, _ = self._is_food_exists(
            new_food, SearchLoc.IN_BASIC, None)  # new food may include cq

        if status == FoodLoc.IN_BASIC:
            msg = f"已在基础菜单中~"
        else:
            # Even food is in groups' menu, it won't be affected when to pick
            self._eating["basic_food"].append(new_food)
            msg = f"已加入基础菜单~"

        save_json(self._eating_json, self._eating)
        return msg

    def remove_food(self, event: GroupMessageEvent, food_to_remove: str) -> str:
        '''
            从基础菜单移除，需SUPERUSER 权限（群聊与私聊）
            从群菜单中移除，需GROUP_ADMIN | GROUP_OWNER 权限
            移除时，移除文字匹配的第一个；若配图也被移除，同时移除配图相同的其余菜品（即使在基础菜单中）
        '''
        uid: str = str(event.user_id)
        gid: str = str(event.group_id)
        msg: str = ""
        res: bool = True

        self._eating = load_json(self._eating_json)
        self._init_data(gid, uid)
        status, food_fullname = self._is_food_exists(
            food_to_remove, SearchLoc.IN_GLOBAL, gid)   # food_to_remove dosen't include cq

        if status == FoodLoc.IN_GROUP:
            self._eating["group_food"][gid].remove(food_fullname)
            # Return the food name user input instead of full name
            msg = f"{food_to_remove} 已从群菜单中删除~"
        elif status == FoodLoc.IN_BASIC:
            if uid not in get_driver().config.superusers:
                msg = f"{food_to_remove} 在基础菜单中，非超管不可操作哦~"
            else:
                self._eating["basic_food"].remove(food_fullname)
                msg = f"{food_to_remove} 已从基础菜单中删除~"
        else:
            msg = f"{food_to_remove} 不在菜单中哦~"

        # If an image included, unlink it
        if "[CQ:image" in food_fullname:
            res = delete_cq_image(food_fullname)
            if res:
                _deleted: Path = get_cq_image_path(food_fullname)
                # Search all the foods with cq image path
                _flag: bool = self._remove_food_matched(_deleted)

                if _flag:
                    msg += f"\n相同配图的其他菜品一并被移除"

            if not res:
                msg += "\n但配图删除出错，图片可能不存在"

        save_json(self._eating_json, self._eating)
        return msg

    def _remove_food_matched(self, _deleted: str) -> bool:
        '''
            Remove all the foods with the same image path
            Return whether other images removed
        '''
        _flag: bool = False
        for food in self._eating["basic_food"]:
            if _deleted in food:
                self._eating["basic_food"].remove(food)
                _flag = True

        for gid in self._eating["group_food"]:
            for food in self._eating["group_food"][gid]:
                if _deleted in food:
                    self._eating["group_food"][gid].remove(food)
                    _flag = True

        return _flag

    def reset_count(self) -> None:
        '''
            Reset eating times in every eating time
        '''
        self._eating = load_json(self._eating_json)

        for gid in self._eating["count"]:
            for uid in self._eating["count"][gid]:
                self._eating["count"][gid][uid] = 0

        save_json(self._eating_json, self._eating)

    def pick_one_drink(self) -> Tuple[str, str]:
        _drinks: Dict[str, List[str]] = load_json(self._drinks_json)
        _branch: str = random.choice(list(_drinks))
        _drink: str = random.choice(_drinks[_branch])

        return _branch, _drink

    # ------------------------- Menu -------------------------
    def show_group_menu(self, gid: str) -> Tuple[bool, Union[Message, MessageSegment]]:
        msg: str = ""
        food_with_img: int = 0
        self._eating = load_json(self._eating_json)
        self._init_data(gid)
        save_json(self._eating_json, self._eating)

        if len(self._eating["group_food"][gid]) > 0:
            msg += f"---群特色菜单---"
            for food in self._eating["group_food"][gid]:
                msg += f"\n{food}"
                if "[CQ:image" in food:
                    food_with_img += 1

            return len(self._eating["group_food"][gid]) > 20 or (food_with_img > 4 and len(self._eating["group_food"][gid]) > 15), Message(msg)

        return 0, MessageSegment.text("还没有群特色菜单呢，请[添加 菜名]🤤")

    def show_basic_menu(self) -> Tuple[bool, Union[Message, MessageSegment]]:
        msg: str = ""
        food_with_img: int = 0
        self._eating = load_json(self._eating_json)

        if len(self._eating["basic_food"]) > 0:
            msg += f"---基础菜单---"
            for food in self._eating["basic_food"]:
                msg += f"\n{food}"
                if "[CQ:image" in food:
                    food_with_img += 1

            return len(self._eating["basic_food"]) > 20 or (food_with_img > 4 and len(self._eating["basic_food"]) > 15), Message(msg)

        return 0, MessageSegment.text("还没有基础菜单呢，请[添加 菜名]🤤")

    # ------------------------- Greetings -------------------------
    def update_greeting_status(self, gid: str, new_state: bool) -> None:
        '''
            Turn on/off greeting tips in group
        '''
        self._greetings = load_json(self._greetings_json)

        if new_state:
            self._greetings["groups_id"].update({gid: True})
        else:
            if gid in self._greetings["groups_id"]:
                self._greetings["groups_id"].pop(gid)

        save_json(self._greetings_json, self._greetings)

    def which_meals(self, input_cn: str) -> Optional[Meals]:
        '''
            Judge which meals user's input indicated
        '''
        for meal in Meals:
            if input_cn in meal.value:
                return meal

        return None

    def add_greeting(self, meal: Meals, greeting: str) -> MessageSegment:
        '''
            添加某一时段问候语
        '''
        self._greetings = load_json(self._greetings_json)
        self._greetings[meal.value[0]].append(greeting)
        save_json(self._greetings_json, self._greetings)

        return MessageSegment.text(f"{greeting} 已加入 {meal.value[1]} 问候~")

    def show_greetings(self, meal: Meals) -> MessageSegment:
        '''
            展示某一时段问候语并标号
            等待用户输入标号，调用 remove_greeting 删除
        '''
        self._greetings = load_json(self._greetings_json)
        msg: str = ""
        i: int = 1

        for greeting in self._greetings[meal.value[0]]:
            if i < len(self._greetings[meal.value[0]]):
                msg += f"{i}-{greeting}\n"
            else:
                msg += f"{i}-{greeting}"

            i += 1

        return MessageSegment.text(msg)

    def remove_greeting(self, meal: Meals, index: int) -> MessageSegment:
        '''
            删除某一时段问候语
        '''
        self._greetings = load_json(self._greetings_json)

        if index > len(self._greetings[meal.value[0]]):
            return MessageSegment.text("输入序号不合法")
        else:
            # Get the popped greeting to show
            greeting = self._greetings[meal.value[0]].pop(index-1)
            save_json(self._greetings_json, self._greetings)

        return MessageSegment.text(f"{greeting} 已从 {meal.value[1]} 问候中移除~")

    async def do_greeting(self, meal: Meals) -> None:
        try:
            bot: Bot = get_bot()
        except Exception as e:
            logger.warning(f"获取Bot失败：{e}")
            return

        self._greetings = load_json(self._greetings_json)
        msg = self._get_greeting(meal)

        if isinstance(msg, MessageSegment) and bool(self._greetings["groups_id"]) > 0:
            for gid in self._greetings["groups_id"]:
                try:
                    await bot.call_api("send_group_msg", group_id=int(gid), message=msg)
                except ActionFailed as e:
                    logger.warning(f"发送群 {gid} 失败：{e}")

            logger.info(f"已群发{meal.value[1]}提醒")

    def _get_greeting(self, meal: Meals) -> Optional[MessageSegment]:
        '''
            Get a greeting, return None if empty
        '''
        if meal.value[0] in self._greetings:
            if len(self._greetings.get(meal.value[0])) > 0:
                greetings: List[str] = self._greetings.get(meal.value[0])
                return MessageSegment.text(random.choice(greetings))

        return None


eating_manager = EatingManager()
