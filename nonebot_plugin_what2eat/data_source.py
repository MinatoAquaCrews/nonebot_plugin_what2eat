from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, PrivateMessageEvent, MessageSegment
import random
from pathlib import Path
from enum import Enum
from typing import Optional, Union, List, Dict
from nonebot import logger
from .config import Meals, what2eat_config
from .utils import do_compatible
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
        self._init_ok: bool = False
        self._eating: Dict[str, Union[List[str], Dict[str, Union[Dict[str, List[int]], List[str]]]]] = {}
        self._greetings: Dict[str, Union[List[str], Dict[str, bool]]] = {}
        
        self._eating_json: Path = what2eat_config.what2eat_path / "eating.json"
        self._greetings_json: Path = what2eat_config.what2eat_path / "greetings.json"
        
        '''
            Compatible work will be deprecated in next version
        '''
        if what2eat_config.use_compatible:
            do_compatible(self._eating_json, self._greetings_json)
            logger.debug("Compatible work success!")
        
    def _init_json(self) -> None:
        self._init_ok = True
        with open(self._eating_json, 'r', encoding='utf-8') as f:
            self._eating = json.load(f)
            
        with open(self._greetings_json, 'r', encoding='utf-8') as f:
            self._greetings = json.load(f)
    
    def _init_data(self, gid: str, uid: str) -> None:
        '''
            初始化用户信息
        '''
        if not self._init_ok:
            self._init_json()
        if gid not in self._eating["group_food"]:
            self._eating["group_food"][gid] = []
        if gid not in self._eating["count"]:
            self._eating["count"][gid] = {}
        if uid not in self._eating["count"][gid]:
            self._eating["count"][gid][uid] = 0

    def get2eat(self, event: MessageEvent) -> MessageSegment:
        '''
            今天吃什么
        '''
        if not self._init_ok:
            self._init_json()
        if isinstance(event, PrivateMessageEvent):
            if len(self._eating["basic_food"]) == 0:
                return MessageSegment.text("还没有菜单呢，就先饿着肚子吧，请[添加 菜名]🤤")
            else:
                return MessageSegment.text("建议") + MessageSegment.text(random.choice(self._eating["basic_food"]))
            
        uid = str(event.user_id)
        gid = str(event.group_id)
        food_list: List[str] = []

        self._init_data(gid, uid)
        if not self.eating_check(gid, uid):
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
            self.save()

            return msg

    def is_food_exists(self, _food: str, gid: Optional[str]) -> FoodLoc:
        '''
            检查菜品是否存在
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

    def eating_check(self, gid: str, uid: str) -> bool:
        '''
            检查是否吃饱
        '''
        return False if self._eating["count"][gid][uid] >= what2eat_config.eating_limit else True

    def add_group_food(self, new_food: str, event: GroupMessageEvent) -> MessageSegment:
        '''
            添加至群菜单中 GROUP_ADMIN | GROUP_OWNER 权限
        '''
        uid = str(event.user_id)
        gid = str(event.group_id)
        msg: MessageSegment = ""

        self._init_data(gid, uid)
        status: FoodLoc = self.is_food_exists(new_food, gid)
        
        if status == FoodLoc.IN_BASIC:
            msg = MessageSegment.text(f"{new_food} 已在基础菜单中~")
        elif status == FoodLoc.IN_GROUP:
            msg = MessageSegment.text(f"{new_food} 已在群特色菜单中~")
        else:
            self._eating["group_food"][gid].append(new_food)
            self.save()
            msg = MessageSegment.text(f"{new_food} 已加入群特色菜单~")
        
        return msg

    def add_basic_food(self, new_food: str) -> MessageSegment:
        '''
            添加至基础菜单 SUPERUSER 权限
        '''
        status: FoodLoc = self.is_food_exists(new_food)
        
        if status == FoodLoc.IN_BASIC:
            msg = MessageSegment.text(f"{new_food} 已在基础菜单中~")
            
        elif status == FoodLoc.NOT_EXISTS:
            self._eating["basic_food"].append(new_food)
            self.save()
            msg = MessageSegment.text(f"{new_food} 已加入基础菜单~")
        
        return msg

    def remove_food(self, event: GroupMessageEvent, food_to_remove: str) -> MessageSegment:
        '''
            从基础菜单移除，需SUPERUSER 权限
            从群菜单中移除，需GROUP_ADMIN | GROUP_OWNER 权限
        '''
        uid = str(event.user_id)
        gid = str(event.group_id)
        msg: MessageSegment = ""
        
        self._init_data(gid, uid)
        status: FoodLoc = self.is_food_exists(food_to_remove, gid)

        if status == FoodLoc.IN_GROUP:
            self._eating["group_food"][gid].remove(food_to_remove)
            self.save()
            msg = MessageSegment.text(f"{food_to_remove} 已从群菜单中删除~")
            
        elif status == FoodLoc.IN_BASIC:
            if uid not in what2eat_config.superusers:
                msg = MessageSegment.text(f"{food_to_remove} 在基础菜单中，非超管不可操作哦~")
            else:
                self._eating["basic_food"].remove(food_to_remove)
                self.save()
                msg = MessageSegment.text(f"{food_to_remove} 已从基础菜单中删除~")   
        else:
            msg = MessageSegment.text(f"{food_to_remove} 不在菜单中哦~")
        
        return msg
    
    def reset_count(self) -> None:
        '''
            重置三餐 eating times
        '''
        for gid in self._eating["count"]:
            for uid in self._eating["count"][gid]:
                self._eating["count"][gid][uid] = 0
        
        self.save()

    # ------------------------- Menu -------------------------
    def show_group_menu(self, gid: str) -> MessageSegment:
        msg: MessageSegment = ""
        
        if gid not in self._eating["group_food"]:
            self._eating["group_food"][gid] = []
            
        if len(self._eating["group_food"][gid]) > 0:
            msg += MessageSegment.text("---群特色菜单---")
            for food in self._eating["group_food"][gid]:
                msg += MessageSegment.text(f"\n{food}")
            
            return msg
        
        return MessageSegment.text("还没有群特色菜单呢，请[添加 菜名]🤤")

    def show_basic_menu(self) -> MessageSegment:
        msg: MessageSegment = ""

        if len(self._eating["basic_food"]) > 0:
            msg += MessageSegment.text("---基础菜单---")
            for food in self._eating["basic_food"]:
                msg += MessageSegment.text(f"\n{food}")
            
            return msg
        
        return MessageSegment.text("还没有基础菜单呢，请[添加 菜名]🤤")

    # ------------------------- greetings -------------------------
    def is_groups_on(self, gid) -> bool:
        return self._greetings["groups_id"].get(gid, False)
        
    def update_groups_on(self, gid: str, new_state: bool) -> None:
        '''
            Turn on/off greeting tips in group
        '''
        if new_state:
            if gid not in self._greetings["groups_id"]:
                self._greetings["groups_id"].update({gid: True})
        else:
            if gid in self._greetings["groups_id"]:
                self._greetings["groups_id"].update({gid: False})
        
        self.save()
        
    def get_greeting(self, meal: Meals) -> Union[str, None]:
        '''
            干饭/摸鱼小助手: Get greeting, return None when empty
        '''
        if meal.value[0] in self._greetings:
            if len(self._greetings.get(meal.value[0])) > 0:
                greetings = self._greetings[meal.value[0]]
                return random.choice(greetings)
            else:
                return None
        
        return None
        
    def which_meals(self, input_cn: str) -> Union[Meals, None]:
        '''
            Judge which meals is user's input indicated
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
        self._greetings[meal.value[0]].append(greeting)
        self.save()

        return MessageSegment.text(f"{greeting} 已加入 {meal.value[1]} 问候~")
    
    def show_greetings(self, meal: Meals) -> MessageSegment:
        '''
            展示某一时段问候语并标号
            等待用户输入标号，调用 remove_greeting 删除
        '''
        msg: MessageSegment = ""
        i: int = 1
        for greeting in self._greetings[meal.value[0]]:
            if i < len(self._greetings[meal.value[0]]):
                msg += MessageSegment.text(f"{i}-{greeting}\n")
            else:
                msg += MessageSegment.text(f"{i}-{greeting}")
                
            i += 1
        
        return msg
            
    def remove_greeting(self, meal: Meals, index: int) -> MessageSegment:
        '''
            删除某一时段问候语
        '''
        if index > len(self._greetings[meal.value[0]]):
            return MessageSegment.text("输入序号不合法")
        else:
            greeting = self._greetings[meal.value[0]].pop(index-1)
            self.save()
        
        return MessageSegment.text(f"{greeting} 已从 {meal.value[1]} 问候中移除~")

    def save(self) -> None:
        '''
            保存数据
        '''
        with open(self._eating_json, 'w', encoding='utf-8') as f:
            json.dump(self._eating, f, ensure_ascii=False, indent=4)
        
        with open(self._greetings_json, 'w', encoding='utf-8') as f:
            json.dump(self._greetings, f, ensure_ascii=False, indent=4)

eating_manager = EatingManager()

__all__ = [
    eating_manager
]