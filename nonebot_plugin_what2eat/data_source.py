from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, PrivateMessageEvent, MessageSegment
from nonebot.adapters.onebot.v11 import ActionFailed
from nonebot import get_bot, logger
import random
from pathlib import Path
from enum import Enum
from typing import Optional, Union, List, Dict, Tuple
from .config import Meals, what2eat_config
from .utils import save_json, load_json, do_compatible
try:
    import ujson as json
except ModuleNotFoundError:
    import json
    
class FoodLoc(Enum):
    IN_BASIC = "In_Basic"
    IN_GROUP = "In_Group"
    NOT_EXISTS = "Not_Exists"

class EatingManager:
    def __init__(self):
        self._eating: Dict[str, Union[List[str], Dict[str, Union[Dict[str, List[int]], List[str]]]]] = {}
        self._greetings: Dict[str, Union[List[str], Dict[str, bool]]] = {}
        
        self._eating_json: Path = what2eat_config.what2eat_path / "eating.json"
        self._greetings_json: Path = what2eat_config.what2eat_path / "greetings.json"
        '''
            Compatible work will be deprecated in next version
        '''
        do_compatible(self._eating_json, self._greetings_json)
    
    def _init_data(self, gid: str, uid: Optional[str]) -> None:
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
        self._eating = load_json(self._eating_json)
        self._init_data(gid, uid)
            
        if isinstance(event, PrivateMessageEvent):
            if len(self._eating["basic_food"]) > 0:
                return MessageSegment.text("建议") + MessageSegment.text(random.choice(self._eating["basic_food"]))
            else:
                return MessageSegment.text("还没有菜单呢，就先饿着肚子吧，请[添加 菜名]🤤")
            
        uid = str(event.user_id)
        gid = str(event.group_id)
        food_list: List[str] = []
        
        # Check whether is full of stomach
        if self._eating["count"][gid][uid] >= what2eat_config.eating_limit:
            save_json(self._eating_json, self._eating)
            return random.choice(
                [
                    "你今天已经吃得够多了！",
                    "吃这么多的吗？",
                    "害搁这吃呢？不工作的吗？",
                    "再吃肚子就要爆炸咯~",
                    "你是米虫吗？今天碳水要爆炸啦！"
                ]
            )
        else:
            # basic_food and group_food both are EMPTY
            if len(self._eating["basic_food"]) == 0 and len(self._eating["group_food"][gid]) == 0:
                return MessageSegment.text("还没有菜单呢，就先饿着肚子吧，请[添加 菜名]🤤")
            
            food_list = self._eating["basic_food"].copy()
            if len(self._eating["group_food"][gid]) > 0:
                food_list.extend(self._eating["group_food"][gid])

            # Even a food maybe in basic AND group menu, probability of it is doubled
            msg = MessageSegment.text("建议") + MessageSegment.text(random.choice(food_list))
            self._eating["count"][gid][uid] += 1
            save_json(self._eating_json, self._eating)

            return msg

    def _is_food_exists(self, _food: str, gid: Optional[str]) -> FoodLoc:
        '''
            检查菜品是否存在于某个群组
        '''
        for food in self._eating["basic_food"]:
            if food == _food:
                return FoodLoc.IN_BASIC
            
        if isinstance(gid, str):
            if gid in self._eating["group_food"]:
                for food in self._eating["group_food"][gid]:
                    if food == _food:
                        return FoodLoc.IN_GROUP
        
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
        elif status == FoodLoc.IN_GROUP:
            # If food in group menu, move it to basic menu from all groups'. Check all groups' menu.
            self._food_group2basic(new_food)
        else:
            self._eating["basic_food"].append(new_food)
            msg = f"{new_food} 已加入基础菜单~"
        
        save_json(self._eating_json, self._eating)
        return MessageSegment.text(msg)

    def _food_group2basic(self, _food_to_move: str) -> None:
        for gid in self._eating["group_food"]:
            if self._is_food_exists(_food_to_move, gid) == FoodLoc.IN_GROUP:
                self._eating["group_food"][gid].remove(_food_to_move)
        
        self._eating["basic_food"].append(_food_to_move)

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

    # ------------------------- Menu -------------------------
    def show_group_menu(self, gid: str) -> MessageSegment:
        msg: str = ""
        self._eating = load_json(self._eating_json)
        self._init_data(gid)
        save_json(self._eating_json, self._eating)
            
        if len(self._eating["group_food"][gid]) > 0:
            msg += f"---群特色菜单---"
            for food in self._eating["group_food"][gid]:
                msg += f"\n{food}"
            
            return MessageSegment.text(msg)
        
        return MessageSegment.text("还没有群特色菜单呢，请[添加 菜名]🤤")

    def show_basic_menu(self) -> MessageSegment:
        msg: str = ""
        self._eating = load_json(self._eating_json)

        if len(self._eating["basic_food"]) > 0:
            msg += f"---基础菜单---"
            for food in self._eating["basic_food"]:
                msg += f"\n{food}"
            
            return MessageSegment.text(msg)
        
        return MessageSegment.text("还没有基础菜单呢，请[添加 菜名]🤤")

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
        else:
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
                        await bot.send_group_msg(group_id=int(gid), message=msg)
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
    
class DrinkingManager:
    def __init__(self):
        self._eating_json: Path = what2eat_config.what2eat_path / "eating.json"
        # Only save the drinking esource data, but csave ounting data in eating.json
        self._drinking_json: Path = what2eat_config.what2eat_path / "drinking.json"
    
    def get2drink(self) -> MessageSegment:
        '''
            今天喝什么，目前仅概括性地描述如何选择一款具体的饮品，未包括次数的统计
        '''
        self._drinking = load_json(self._drinking_json)
        msg: str = ""
        
        # 1. Pick one drink
        branch, drink = self._pick_one_drink()
        
        cup: str = random.choice(self._drinking[branch]["cup"])
        sugar_level: str = random.choice(self._drinking[branch]["sugar_level"])
        
        ice_level: str = self._pick_ice_level(branch, drink)
        ingredients: List[str] = self._pick_ingredients() # length is 1 to 3
        
        msg = f"不如来杯{cup}{sugar_level}{ice_level}{drink}，加"
        
        if len(ingredients) == 1:
            msg += f"{ingredients[0]}吧！"
        elif len(ingredients) == 2:
            msg += f"{ingredients[0]}和{ingredients[1]}吧！"
        else:
            msg += f"{ingredients[0]}、{ingredients[1]}和{ingredients[2]}吧！"
        
        return MessageSegment.text(msg)

    def _pick_one_drink(self) -> Tuple[str, str]:
        branch: str = random.choice(list(self._drinking.keys()))
        drinks: List[str] = []
        for item in self._drinking[branch]["drinks"]:
            drinks.append(self._drinking[branch]["drinks"][item])
        
        drink = random.choice(drinks)
        return branch, drink
        
    def _pick_ice_level(self, _branch: str, _drink: str) -> str:
        pass
    
    def _pick_ingredients(self) -> List[str]:
        pass
    

eating_manager = EatingManager()      
drinking_manager = DrinkingManager()    

__all__ = [
    eating_manager, drinking_manager
]