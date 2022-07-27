from pathlib import Path
from typing import Any
from enum import Enum
try:
    import ujson as json
except ModuleNotFoundError:
    import json

class Meals(Enum):
    BREAKFAST = ["breakfast", "早餐", "早饭"]
    LUNCH = ["lunch", "午餐", "午饭", "中餐"]
    SNACK = ["snack", "摸鱼", "下午茶", "饮茶"]
    DINNER = ["dinner", "晚餐", "晚饭"]
    MIDNIGHT = ["midnight", "夜宵", "宵夜"]
    
class FoodLoc(Enum):
    IN_BASIC = "In_Basic"
    IN_GROUP = "In_Group"
    NOT_EXISTS = "Not_Exists"
       
def save_json(_file: Path, _data: Any) -> None:
    with open(_file, 'w', encoding='utf-8') as f:
        json.dump(_data, f, ensure_ascii=False, indent=4)
  
def load_json(_file: Path) -> Any:
    with open(_file, 'r', encoding='utf-8') as f:
        return json.load(f)

__all__ = [
    Meals, FoodLoc, save_json, load_json
]