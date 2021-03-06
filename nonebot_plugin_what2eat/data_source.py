from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, PrivateMessageEvent, MessageSegment
from nonebot.adapters.onebot.v11 import ActionFailed
from nonebot import get_bot, logger
import random
from pathlib import Path
from typing import Optional, Union, List, Dict, Tuple
from .utils import save_json, load_json, Meals, FoodLoc
from .config import what2eat_config

class EatingManager:
    def __init__(self):
        self._eating: Dict[str, Union[List[str], Dict[str, Union[Dict[str, List[int]], List[str]]]]] = {}
        self._greetings: Dict[str, Union[List[str], Dict[str, bool]]] = {}
        
        self._eating_json: Path = what2eat_config.what2eat_path / "eating.json"
        self._greetings_json: Path = what2eat_config.what2eat_path / "greetings.json"
        self._drinks_json: Path = what2eat_config.what2eat_path / "drinks.json"
    
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

    def get2eat(self, event: MessageEvent) -> MessageSegment:
        '''
            今天吃什么
        '''
        uid = str(event.user_id)
        gid = str(event.group_id)
        food_list: List[str] = []
        
        self._eating = load_json(self._eating_json)
        self._init_data(gid, uid)
            
        if isinstance(event, PrivateMessageEvent):
            if len(self._eating["basic_food"]) > 0:
                return MessageSegment.text("建议") + MessageSegment.text(random.choice(self._eating["basic_food"]))
            else:
                return MessageSegment.text("还没有菜单呢，就先饿着肚子吧，请[添加 菜名]🤤")

        # Check whether is full of stomach
        if self._eating["count"][gid][uid] >= what2eat_config.eating_limit:
            save_json(self._eating_json, self._eating)
            return MessageSegment.text(random.choice(
                    [
                        "你今天已经吃得够多了！",
                        "吃这么多的吗？",
                        "害搁这吃呢？不工作的吗？",
                        "再吃肚子就要爆炸咯~",
                        "你是米虫吗？今天碳水要爆炸啦！"
                    ]
                )
            )
        else:
            # basic_food and group_food both are EMPTY
            if len(self._eating["basic_food"]) == 0 and len(self._eating["group_food"][gid]) == 0:
                return MessageSegment.text("还没有菜单呢，就先饿着肚子吧，请[添加 菜名]🤤")
            
            food_list = self._eating["basic_food"].copy()
            
            # 取并集
            if len(self._eating["group_food"][gid]) > 0:
                food_list = list(set(food_list).union(set(self._eating["group_food"][gid])))

            msg = MessageSegment.text("建议") + MessageSegment.text(random.choice(food_list))
            self._eating["count"][gid][uid] += 1
            save_json(self._eating_json, self._eating)

            return msg
        
    def get2drink(self, event: MessageEvent) -> MessageSegment:
        '''
            今天喝什么
        '''
        uid = str(event.user_id)
        gid = str(event.group_id)
        
        self._eating = load_json(self._eating_json)
        self._init_data(gid, uid)
            
        if isinstance(event, PrivateMessageEvent):
            _branch, _drink = self.pick_one_drink()
            return MessageSegment.text(f"不如来杯 {_branch} 的 {_drink} 吧！")

        # Check whether is full of stomach
        if self._eating["count"][gid][uid] >= what2eat_config.eating_limit:
            save_json(self._eating_json, self._eating)
            return MessageSegment.text(random.choice(
                    [
                        "你今天已经喝得够多了！",
                        "喝这么多的吗？",
                        "害搁这喝呢？不工作的吗？",
                        "再喝肚子就要爆炸咯~",
                        "你是水桶吗？今天糖分要超标啦！"
                    ]
                )
            )
        else:
            _branch, _drink = self.pick_one_drink()
            self._eating["count"][gid][uid] += 1
            save_json(self._eating_json, self._eating)

            return MessageSegment.text(random.choice(
                    [
                        f"不如来杯 {_branch} 的 {_drink} 吧！",
                        f"去 {_branch} 整杯 {_drink} 吧！",
                        f"{_branch} 的 {_drink} 如何？"
                    ]
                )
            )

    def _is_food_exists(self, _food: str, gid: Optional[str] = None) -> FoodLoc:
        '''
            检查菜品是否存在于某个群组
            优先检测是否在群组，优先移除
        ''' 
        if isinstance(gid, str):
            if gid in self._eating["group_food"]:
                if _food in self._eating["group_food"][gid]:
                    return FoodLoc.IN_GROUP
        
        if _food in self._eating["basic_food"]:
            return FoodLoc.IN_BASIC
        
        return FoodLoc.NOT_EXISTS

    def add_group_food(self, event: GroupMessageEvent, new_food: str) -> MessageSegment:
        '''
            添加至群菜单中 GROUP_ADMIN | GROUP_OWNER 权限
        '''
        uid = str(event.user_id)
        gid = str(event.group_id)
        msg: str = ""

        self._eating = load_json(self._eating_json)
        self._init_data(gid, uid)
        status: FoodLoc = self._is_food_exists(new_food, gid)
        
        if status == FoodLoc.IN_BASIC:
            msg = f"{new_food} 已在基础菜单中~"
        elif status == FoodLoc.IN_GROUP:
            msg = f"{new_food} 已在群特色菜单中~"
        else:
            self._eating["group_food"][gid].append(new_food)
            msg = f"{new_food} 已加入群特色菜单~"
        
        save_json(self._eating_json, self._eating)
        return MessageSegment.text(msg)

    def add_basic_food(self, new_food: str) -> MessageSegment:
        '''
            添加至基础菜单 SUPERUSER 权限
        '''
        self._eating = load_json(self._eating_json)
        msg: str = ""
        status: FoodLoc = self._is_food_exists(new_food)
        
        if status == FoodLoc.IN_BASIC:
            msg = f"{new_food} 已在基础菜单中~"
        else:
            # If food in group menu, move it to basic menu from all groups'. Check all groups' menu.
            self._eating["basic_food"].append(new_food)
            msg = f"{new_food} 已加入基础菜单~"

        save_json(self._eating_json, self._eating)
        return MessageSegment.text(msg)

    def remove_food(self, event: GroupMessageEvent, food_to_remove: str) -> MessageSegment:
        '''
            从基础菜单移除，需SUPERUSER 权限
            从群菜单中移除，需GROUP_ADMIN | GROUP_OWNER 权限
        '''
        uid = str(event.user_id)
        gid = str(event.group_id)
        msg: str = ""
        
        self._eating = load_json(self._eating_json)
        self._init_data(gid, uid)
        status: FoodLoc = self._is_food_exists(food_to_remove, gid)

        if status == FoodLoc.IN_GROUP:
            self._eating["group_food"][gid].remove(food_to_remove)
            msg = f"{food_to_remove} 已从群菜单中删除~"
        elif status == FoodLoc.IN_BASIC:
            if uid not in what2eat_config.superusers:
                msg = f"{food_to_remove} 在基础菜单中，非超管不可操作哦~"
            else:
                self._eating["basic_food"].remove(food_to_remove)
                msg = f"{food_to_remove} 已从基础菜单中删除~"
        else:
            msg = f"{food_to_remove} 不在菜单中哦~"
        
        save_json(self._eating_json, self._eating)
        return MessageSegment.text(msg)
    
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
        self._drinks: Dict[str, List[str]] = load_json(self._drinks_json)
        _branch = random.choice(list(self._drinks))
        _drink = random.choice(self._drinks[_branch])
        
        return _branch, _drink

    # ------------------------- Menu -------------------------
    def show_group_menu(self, gid: str) -> Tuple[int, MessageSegment]:
        msg: str = ""
        self._eating = load_json(self._eating_json)
        self._init_data(gid)
        save_json(self._eating_json, self._eating)
            
        if len(self._eating["group_food"][gid]) > 0:
            msg += f"---群特色菜单---"
            for food in self._eating["group_food"][gid]:
                msg += f"\n{food}"
            
            return len(self._eating["group_food"][gid]), MessageSegment.text(msg)
        
        return 0, MessageSegment.text("还没有群特色菜单呢，请[添加 菜名]🤤")

    def show_basic_menu(self) -> Tuple[int, MessageSegment]:
        msg: str = ""
        self._eating = load_json(self._eating_json)

        if len(self._eating["basic_food"]) > 0:
            msg += f"---基础菜单---"
            for food in self._eating["basic_food"]:
                msg += f"\n{food}"
            
            return len(self._eating["basic_food"]), MessageSegment.text(msg)
        
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