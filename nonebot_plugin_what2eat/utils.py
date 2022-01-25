from nonebot.adapters.cqhttp import GroupMessageEvent, MessageSegment
import random
from pathlib import Path
from typing import Optional
import nonebot
from enum import Enum
import os

try:
    import ujson as json
except ModuleNotFoundError:
    import json

SUPERUSERS = nonebot.get_driver().config.superusers
_WHAT2EAT_PATH = nonebot.get_driver().config.what2eat_path
DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "resource")
WHAT2EAT_PATH = DEFAULT_PATH if not _WHAT2EAT_PATH else _WHAT2EAT_PATH
_EATING_LIMIT = nonebot.get_driver().config.eating_limit
EATING_LIMIT = 6 if not _EATING_LIMIT else _EATING_LIMIT

'''
    Reserved for next version
'''
class Meals(Enum):
    BREAKFAST   = "_breakfast"
    LUNCH       = "_lunch"
    DINNER      = "_dinner"
    SNACK       = "_midnight_snack"

class EatingManager:

    def __init__(self, file_path: Optional[Path]):
        self._data = {}
        if not file_path:
            file = Path(WHAT2EAT_PATH) / "data.json"
        else:
            file = file_path / "data.json"
        
        self.file = file
        if file.exists():
            with open(file, "r", encoding="utf-8") as f:
                self._data = json.load(f)

        self._init_json()

    def _init_json(self) -> None:
        # 建议["basic_food"]初始非空
        if "basic_food" not in self._data.keys():
            self._data["basic_food"] = []
        if "group_food" not in self._data.keys():
            self._data["group_food"] = {}
        if "eating" not in self._data.keys():
            self._data["eating"] = {}
    
    def _init_data(self, event: GroupMessageEvent) -> None:
        '''
            初始化用户信息
        '''
        user_id = str(event.user_id)
        group_id = str(event.group_id)
        
        if group_id not in self._data["group_food"].keys():
            self._data["group_food"][group_id] = []
        if group_id not in self._data["eating"].keys():
            self._data["eating"][group_id] = {}
        if user_id not in self._data["eating"][group_id].keys():
            self._data["eating"][group_id][user_id] = 0

    def get2eat(self, event: GroupMessageEvent) -> str:
        '''
            今天吃什么
        '''
        user_id = str(event.user_id)
        group_id = str(event.group_id)

        self._init_data(event)
        if not self.eating_check(event):
            return random.choice(
                [
                    "你今天已经吃得够多了！",
                    "吃这么多的吗？",
                    "害搁这吃呢？不工作的吗？",
                    "再吃肚子就要爆炸咯~"
                ]
            )
        else:
            # 菜单全为空，建议避免["basic_food"]为空
            if len(self._data["basic_food"]) == 0 and len(self._data["group_food"][group_id]) == 0:
                return "还没有菜单呢，就先饿着肚子吧，请[添加 菜名]🤤"
            
            food_list = self._data["basic_food"].copy()
            if len(self._data["group_food"][group_id]) > 0:
                food_list.extend(self._data["group_food"][group_id])

            msg = "建议" + random.choice(food_list)
            self._data["eating"][group_id][user_id] += 1
            self.save()

            return msg
    
    '''
        检查菜品是否存在
        1:  存在于基础菜单
        2:  存在于群菜单
        0:  不存在
    '''
    def food_exists(self, _food_: str) -> int:
        for food in self._data["basic_food"]:
            if food == _food_:
                return 1

        for group_id in self._data["group_food"]:
            for food in self._data["group_food"][group_id]:
                if food == _food_:
                    return 2
        
        return 0

    '''
        检查是否吃饱
    '''
    def eating_check(self, event: GroupMessageEvent) -> bool:
        user_id = str(event.user_id)
        group_id = str(event.group_id)
        return False if self._data["eating"][group_id][user_id] >= EATING_LIMIT else True

    '''
        添加至群菜单中 GROUP_ADMIN | GROUP_OWNER 权限
    '''
    def add_group_food(self, new_food: str, event: GroupMessageEvent) -> str:
        group_id = str(event.group_id)

        status = self.food_exists(new_food)
        if status == 1:
            return f"{new_food} 已在基础菜单中~"
        elif status == 2:
            return f"{new_food} 已在群特色菜单中~"

        self._data["group_food"][group_id].append(new_food)
        self.save()
        return f"{new_food} 已加入群特色菜单~"

    '''
        添加至基础菜单 SUPERUSER 权限
    '''
    def add_basic_food(self, new_food: str) -> str:
        status = self.food_exists(new_food)
        if status == 1:
            return f"{new_food} 已在基础菜单中~"
        elif status == 2:
            return f"{new_food} 已在群特色菜单中~"

        self._data["basic_food"].append(new_food)
        self.save()
        return f"{new_food} 已加入基础菜单~"

    '''
        从基础菜单移除 SUPERUSER 权限
        从群菜单中移除 GROUP_ADMIN | GROUP_OWNER 权限
    '''
    def remove_food(self, food_to_remove: str, event: GroupMessageEvent) -> str:
        user_id = str(event.user_id)
        group_id = str(event.group_id)
        
        status = self.food_exists(food_to_remove)
        if not status:
            return f"{food_to_remove} 不在菜单中哦~"

        # 在群菜单
        if status == 2:
            self._data["group_food"][group_id].remove(food_to_remove)
            self.save()
            return f"{food_to_remove} 已从群菜单中删除~"
        # 在基础菜单
        else:
            if user_id not in SUPERUSERS:
                return f"{food_to_remove} 在基础菜单中，非超管不可操作哦~"
            else:
                self._data["basic_food"].remove(food_to_remove)
                self.save()
                return f"{food_to_remove} 已从基础菜单中删除~"    

    def reset_eating(self) -> None:
        '''
            重置三餐eating times
        '''
        for group_id in self._data["eating"].keys():
            for user_id in self._data["eating"][group_id].keys():
                self._data["eating"][group_id][user_id] = 0
        
        self.save()

    def save(self) -> None:
        '''
            保存数据
        '''
        with open(self.file, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, ensure_ascii=False, indent=4)

    def show_menu(self, event: GroupMessageEvent, show_basic: bool) -> str:
        group_id = str(event.group_id)
        msg = []
        
        if len(self._data["group_food"][group_id]) > 0:
            msg += MessageSegment.text("---群特色菜单---\n")
            for food in self._data["group_food"][group_id]:
                msg += MessageSegment.text(f"{food}\n")

        if len(self._data["basic_food"]) > 0 and show_basic:
            msg += MessageSegment.text("---基础菜单---\n")
            for food in self._data["basic_food"]:
                msg += MessageSegment.text(f"{food}\n")
        
        if show_basic:
            return msg if len(msg) > 0 else "还没有菜单呢，请[添加 菜名]🤤"
        else:
            return msg if len(msg) > 0 else "没有群特色菜单，请[添加 菜名]🤤"

eating_manager = EatingManager(Path(WHAT2EAT_PATH))