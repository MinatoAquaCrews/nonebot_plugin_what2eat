from nonebot.adapters.onebot.v11 import Message, MessageEvent, GroupMessageEvent, PrivateMessageEvent, MessageSegment
from nonebot.adapters.onebot.v11 import ActionFailed
from nonebot import get_bot, logger
import random
from pathlib import Path
from typing import Optional, Union, List, Dict, Tuple
from .utils import *
from .config import what2eat_config

class EatingManager:
    def __init__(self):
        self._eating: Dict[str, Union[List[str], Dict[str, Union[Dict[str, List[int]], List[str]]]]] = {}
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

    def get2eat(self, event: MessageEvent) -> Tuple[Message, MessageSegment]:
        '''
            今天吃什么
        '''
        # Deal with private message event FIRST
        if isinstance(event, PrivateMessageEvent):
            if len(self._eating["basic_food"]) > 0:
                return MessageSegment.text("建议") + Message(random.choice(self._eating["basic_food"]))
            else:
                return MessageSegment.text("还没有菜单呢，就先饿着肚子吧，请[添加 菜名]🤤")
            
        uid = str(event.user_id)
        gid = str(event.group_id)
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
                food_list = list(set(food_list).union(set(self._eating["group_food"][gid])))

            msg = MessageSegment.text("建议") + Message(random.choice(food_list))
            self._eating["count"][gid][uid] += 1
            save_json(self._eating_json, self._eating)

            return msg
        
    def get2drink(self, event: MessageEvent) -> MessageSegment:
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
        
        uid = str(event.user_id)
        gid = str(event.group_id)
        
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

    def _is_food_exists(self, _food: str, gid: Optional[str] = None) -> Tuple[FoodLoc, str]:
        '''
            检查菜品是否存在于某个群组，优先检测是否在群组，优先移除
            若遇到多个匹配（一个纯文字匹配，一个CQ码前文字完全匹配），只返回第一个
        '''
        if isinstance(gid, str):
            if gid in self._eating["group_food"]:
                for food in self._eating["group_food"][gid]:
                    # food is the full name or _food matches the food name before CQ code
                    if _food == food or _food == food.split("[CQ:image")[0]:
                        return FoodLoc.IN_GROUP, food
        
        for food in self._eating["basic_food"]:
            if _food == food or _food == food.split("[CQ:image")[0]:
                return FoodLoc.IN_BASIC, food
        
        return FoodLoc.NOT_EXISTS, ""

    def add_group_food(self, event: GroupMessageEvent, new_food: str) -> str:
        '''
            添加至群菜单
        '''
        uid = str(event.user_id)
        gid = str(event.group_id)
        msg: str = ""

        self._eating = load_json(self._eating_json)
        self._init_data(gid, uid)
        status, _ = self._is_food_exists(new_food, gid)
        
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
        status, _ = self._is_food_exists(new_food)
        
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
        '''
        uid = str(event.user_id)
        gid = str(event.group_id)
        msg: str = ""
        res: bool = True
        
        self._eating = load_json(self._eating_json)
        self._init_data(gid, uid)
        status, food_fullname = self._is_food_exists(food_to_remove, gid)

        if status == FoodLoc.IN_GROUP:
            self._eating["group_food"][gid].remove(food_fullname)
            # Return the food name user input instead of full name
            msg = f"{food_to_remove} 已从群菜单中删除~"
        elif status == FoodLoc.IN_BASIC:
            if uid not in what2eat_config.superusers:
                msg = f"{food_to_remove} 在基础菜单中，非超管不可操作哦~"
            else:
                self._eating["basic_food"].remove(food_fullname)
                msg = f"{food_to_remove} 已从基础菜单中删除~"
        else:
            msg = f"{food_to_remove} 不在菜单中哦~"
            
        # If an image included, unlink it
        if "[CQ:image" in food_fullname:
            res = delete_cq_image(food_fullname)
            if not res:
                msg += "\n但配图删除出错，图片可能不存在"
        
        save_json(self._eating_json, self._eating)
        return msg
    
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
        _branch = random.choice(list(_drinks))
        _drink = random.choice(_drinks[_branch])
        
        return _branch, _drink

    # ------------------------- Menu -------------------------
    def show_group_menu(self, gid: str) -> Tuple[bool, Union[Message, MessageSegment]]:
        msg: str = ""
        self._eating = load_json(self._eating_json)
        self._init_data(gid)
        save_json(self._eating_json, self._eating)
            
        if len(self._eating["group_food"][gid]) > 0:
            msg += f"---群特色菜单---"
            for food in self._eating["group_food"][gid]:
                msg += f"\n{food}"
            
            return len(self._eating["group_food"][gid]) > 20, Message(msg)
        
        return 0, MessageSegment.text("还没有群特色菜单呢，请[添加 菜名]🤤")

    def show_basic_menu(self) -> Tuple[bool, Union[Message, MessageSegment]]:
        msg: str = ""
        self._eating = load_json(self._eating_json)

        if len(self._eating["basic_food"]) > 0:
            msg += f"---基础菜单---"
            for food in self._eating["basic_food"]:
                msg += f"\n{food}"
            
            return len(self._eating["basic_food"]) > 20, Message(msg)
        
        return 0, MessageSegment.text("还没有基础菜单呢，请[添加 菜名]🤤")

    # ------------------------- Greetings -------------------------
    def update_groups_on(self, gid: str, new_state: bool) -> None:
        '''
            Turn on/off greeting tips in group
        '''
        self._greetings = load_json(self._greetings_json)
        
        if new_state:
            if gid not in self._greetings["groups_id"]:
                self._greetings["groups_id"].update({gid: True})
        else:
            if gid in self._greetings["groups_id"]:
                self._greetings["groups_id"].update({gid: False})
        
        save_json(self._greetings_json, self._greetings)
        
    def which_meals(self, input_cn: str) -> Union[Meals, None]:
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
        bot = get_bot()
        self._greetings = load_json(self._greetings_json)
        msg = self._get_greeting(meal)
        
        if isinstance(msg, MessageSegment) and bool(self._greetings["groups_id"]) > 0:
            for gid in self._greetings["groups_id"]:
                if self._greetings["groups_id"].get(gid, False):
                    try:
                        await bot.call_api("send_group_msg", group_id=int(gid), message=msg)
                    except ActionFailed as e:
                        logger.warning(f"发送群 {gid} 失败：{e}")
    
    def _get_greeting(self, meal: Meals) -> Union[MessageSegment, None]:
        '''
            Get greeting, return None if empty
        ''' 
        if meal.value[0] in self._greetings:
            if len(self._greetings.get(meal.value[0])) > 0:
                greetings: List[str] = self._greetings.get(meal.value[0])
                return MessageSegment.text(random.choice(greetings))
        
        return None

eating_manager = EatingManager()      

__all__ = [
    eating_manager
]