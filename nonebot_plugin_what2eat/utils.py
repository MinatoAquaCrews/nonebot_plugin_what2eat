from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageSegment
from nonebot import logger
import nonebot
import random
from pathlib import Path
from typing import Optional, List
from enum import Enum
from .download import get_preset
from .config import PluginConfig
try:
    import ujson as json
except ModuleNotFoundError:
    import json

global_config = nonebot.get_driver().config
config: PluginConfig = PluginConfig.parse_obj(global_config.dict())

class Meals(Enum):
    BREAKFAST   = "breakfast"
    LUNCH       = "lunch"
    SNACK       = "snack"
    DINNER      = "dinner"
    MIDNIGHT    = "midnight"

class EatingManager:

    def __init__(self, path: Optional[Path]):
        self.greating_enbale = True
        self._data = {}
        self._greating = {}
        if not path:
            data_file = Path(config.what2eat_path) / "data.json"
            greating_file = Path(config.what2eat_path) / "greating.json"
        else:
            data_file = path / "data.json"
            greating_file = path / "greating.json"
        
        self.data_file = data_file
        self.greating_file = greating_file
        if not data_file.exists():
            if config.use_preset_menu:
                logger.info("Downloading preset what2eat menu resource...")
                get_preset(data_file, "MENU")
            else:
                with open(data_file, "w", encoding="utf-8") as f:
                    f.write(json.dumps(dict()))
                    f.close()

        if data_file.exists():
            with open(data_file, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        
        if not greating_file.exists():
            if config.use_preset_greating:
                logger.info("Downloading preset what2eat greating resource...")
                get_preset(greating_file, "GREATING")
            else:
                with open(greating_file, "w", encoding="utf-8") as f:
                    f.write(json.dumps(dict()))
                    f.close()

        if greating_file.exists():
            with open(greating_file, "r", encoding="utf-8") as f:
                self._greating = json.load(f)

        self._init_json()

    def _init_json(self) -> None:
        if "basic_food" not in self._data.keys():
            self._data["basic_food"] = []
        if "group_food" not in self._data.keys():
            self._data["group_food"] = {}
        if "eating" not in self._data.keys():
            self._data["eating"] = {}
        
        for meal in Meals:
            if meal.value not in self._greating.keys():
                self._greating[meal.value] = []
    
    def _init_data(self, group_id: str, user_id: str) -> None:
        '''
            初始化用户信息
        '''
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

        self._init_data(group_id, user_id)
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
        return False if self._data["eating"][group_id][user_id] >= config.eating_limit else True

    '''
        添加至群菜单中 GROUP_ADMIN | GROUP_OWNER 权限
    '''
    def add_group_food(self, new_food: str, event: GroupMessageEvent) -> str:
        user_id = str(event.user_id)
        group_id = str(event.group_id)

        self._init_data(group_id, user_id)
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
        
        self._init_data(group_id, user_id)
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
            if user_id not in config.superusers:
                return f"{food_to_remove} 在基础菜单中，非超管不可操作哦~"
            else:
                self._data["basic_food"].remove(food_to_remove)
                self.save()
                return f"{food_to_remove} 已从基础菜单中删除~"    

    def reset_eating(self) -> None:
        '''
            重置三餐 eating times
        '''
        for group_id in self._data["eating"].keys():
            for user_id in self._data["eating"][group_id].keys():
                self._data["eating"][group_id][user_id] = 0
        
        self.save()

    def save(self) -> None:
        '''
            保存数据
        '''
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, ensure_ascii=False, indent=4)
        
        with open(self.greating_file, 'w', encoding='utf-8') as f:
            json.dump(self._greating, f, ensure_ascii=False, indent=4)

    def show_group_menu(self, event: GroupMessageEvent) -> str:
        user_id = str(event.user_id)
        group_id = str(event.group_id)
        msg = []
        
        self._init_data(group_id, user_id)
        if len(self._data["group_food"][group_id]) > 0:
            msg += MessageSegment.text("---群特色菜单---\n")
            for food in self._data["group_food"][group_id]:
                msg += MessageSegment.text(f"{food}\n")
        
        return msg if len(msg) > 0 else "还没有群特色菜单呢，请[添加 菜名]~"

    def show_basic_menu(self) -> str:
        msg = []

        if len(self._data["basic_food"]) > 0:
            msg += MessageSegment.text("---基础菜单---\n")
            for food in self._data["basic_food"]:
                msg += MessageSegment.text(f"{food}\n")
        
        return msg if len(msg) > 0 else "还没有基础菜单呢，请[添加 菜名]~"

    '''
        干饭/摸鱼小助手：获取问候语，问候语为空返回None
    '''
    def get2greating(self, meal: Meals) -> Optional[str]:
        if len(self._greating.get(meal.value)) > 0:
            greatings = self._greating[meal.value]
            return random.choice(greatings)
        else:
            return None

    '''
        添加某一时段问候语
    '''
    def add_greating(self, args: List) -> str:
        if args[0] == "早餐":
            meal = Meals.BREAKFAST.value
        elif args[0] == "中餐":
            meal = Meals.LUNCH.value
        elif args[0] == "摸鱼" or args[0] == "饮茶":
            meal = Meals.SNACK.value
        elif args[0] == "晚餐":
            meal = Meals.DINNER.value
        elif args[0] == "夜宵":
            meal = Meals.MIDNIGHT.value
        else:
            return f"请检查输入参数{args[0]}是否正确~"
            
        greating = args[1]
        self._greating[meal].append(greating)
        self.save()

        return f"{greating} 已加入 {args[0]} 问候~"

    '''
        删除某一时段最新的问候语
    '''
    def remove_greating(self, arg: str) -> str:
        if arg == "早餐":
            meal = Meals.BREAKFAST.value
        elif arg == "中餐":
            meal = Meals.LUNCH.value
        elif arg == "摸鱼" or arg == "饮茶":
            meal = Meals.SNACK.value
        elif arg == "晚餐":
            meal = Meals.DINNER.value
        elif arg == "夜宵":
            meal = Meals.MIDNIGHT.value
        else:
            return f"请检查输入参数{arg}是否正确~"
        
        greating = self._greating[meal].pop()
        self.save()

        return f"{greating} 已从 {arg} 问候中移除~"


eating_manager = EatingManager(Path(config.what2eat_path))