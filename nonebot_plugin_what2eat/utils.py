from nonebot.adapters.cqhttp import GroupMessageEvent
import random
from pathlib import Path
from typing import Optional, Union, List, Dict
import nonebot

try:
    import ujson as json
except ModuleNotFoundError:
    import json

_WHAT2EAT_PATH = nonebot.get_driver().config.what2eat_path
DEFAULT_PATH = "./data/what2eat"
WHAT2EAT_PATH = DEFAULT_PATH if not _WHAT2EAT_PATH else _WHAT2EAT_PATH
_EATING_LIMIT = nonebot.get_driver().config.eating_limit
EATING_LIMIT = 5 if not _EATING_LIMIT else _EATING_LIMIT

class EatingManager:

    def __init__(self, file: Optional[Path]):
        self._data = {}
        if not file:
            file = Path(WHAT2EAT_PATH) / "data.json"
        
        self.file = file
        if file.exists():
            with open(file, "r", encoding="utf-8") as f:
                self._data = json.load(f)
    
    def _init_data(self, event: GroupMessageEvent):
        '''
            初始化用户信息
        '''
        user_id = str(event.user_id)
        if "eating_times" not in self._data.keys():
            self._data["eating_times"] = {}

        if user_id not in self._data["eating_times"].keys():
            self._data["eating_times"][user_id] = 0

    def get2eat(self, user_id: str, event: GroupMessageEvent) -> str:
        '''
            Bot给出建议
        '''
        self._init_data(event)
        if not self.eat_limit_check(user_id):
            return random.choice(
                [
                    "你今天已经吃得够多了！",
                    "吃这么多的吗？",
                    "害搁这吃呢？不工作的吗？"
                ]
            )
        else:
            result = "建议" + random.choice(self._data["food"])
            self._data["eating_times"][user_id] = self._data["eating_times"][user_id] + 1
            self.save()

            return result

    def eat_limit_check(self, user_id: str) -> bool:
        '''
            检查是否达到询问上限
        '''
        return False if self._data["eating_times"][user_id] >= EATING_LIMIT else True

    def add_food(self, new_food: str) -> str:
        for food in self._data["food"]:
            if food == new_food:
                return f"{new_food}已经在菜单中了~"
        
        self._data["food"].append(new_food)
        self.save()
        return f"{new_food}已加入菜单~"
    
    def remove_food(self, food_to_remove: str) -> str:
        for food in self._data["food"]:
            if food == food_to_remove:
                self._data["food"].remove(food_to_remove)
                self.save()
                return f"{food_to_remove}已从菜单中删除~"
        
        return f"{food_to_remove}不在菜单中哦~"

    def reset_eating_times(self):
        '''
            重置三餐eating_limit
        '''
        for user_id in self._data["eating_times"].keys():
            self._data["eating_times"][user_id] = 0
        
        self.save()

    def save(self):
        '''
            保存数据
        '''
        with open(self.file, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, ensure_ascii=False, indent=4)

eating_manager = EatingManager(Path(WHAT2EAT_PATH) / "data.json")