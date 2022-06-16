from pathlib import Path
from enum import Enum
from pydantic import BaseModel, Extra
from typing import List, Dict, Set, Union, Any
import httpx
from nonebot import get_driver
from nonebot import logger
try:
    import ujson as json
except ModuleNotFoundError:
    import json

class PluginConfig(BaseModel, extra=Extra.ignore):
    what2eat_path: Path = Path(__file__).parent / "resource"
    use_preset_menu: bool = False
    use_preset_greetings: bool = False
    eating_limit: int = 5
    greeting_groups_id: Set[str] = set()
    superusers: Set[str] = set()
    '''
        v0.3.0 is compatible with configure json file of version 0.2.x, but will be deprecated in next version
    '''
    use_compatible: bool = True
    
class Meals(Enum):
    BREAKFAST = ["breakfast", "早餐", "早饭"]
    LUNCH = ["lunch", "午餐", "午饭", "中餐"]
    SNACK = ["snack", "摸鱼", "下午茶", "饮茶"]
    DINNER = ["dinner", "晚餐", "晚饭"]
    MIDNIGHT = ["midnight", "夜宵", "宵夜"]
    
driver = get_driver()
what2eat_config: PluginConfig = PluginConfig.parse_obj(driver.config.dict())

class DownloadError(Exception):
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return self.msg
    
async def download_url(url: str) -> Union[Any, None]:
    async with httpx.AsyncClient() as client:
        for i in range(3):
            try:
                response = await client.get(url)
                if response.status_code != 200:
                    continue
                return response.json()
            except Exception as e:
                logger.warning(f"Error occured when downloading {url}, {i+1}/3: {e}")
    
    logger.warning(f"Abort downloading")
    return None

def save_json(_file: Path, _data: Any) -> None:
    with open(_file, 'w', encoding='utf-8') as f:
        json.dump(_data, f, ensure_ascii=False, indent=4)
        
def write_init_keys(_file: Path, _name: str) -> None:
    '''
        Write ALL the initial keys
    '''
    _data = {}
    if _name == "eating.json":
        _data["basic_food"] = []
        _data["group_food"] = {}
        _data["count"] = {}
        save_json(_file, _data)
    else:
        for meal in Meals:
            if meal not in _data:
                _data[meal.value[0]] = []
        
        _data["groups_id"] = {}
        save_json(_file, _data)
               
async def download_file(_file: Path, _name: str) -> None:
    _url = "https://raw.fastgit.org/MinatoAquaCrews/nonebot_plugin_what2eat/beta/nonebot_plugin_what2eat/resource/"
    url = _url + _name
    
    resp = await download_url(url)
    if resp is None:
        # Write initial keys in file when download failed
        write_init_keys(_file, _name)
        logger.info(f"Write inital keys in file {_name}")
    else:
        save_json(_file, resp)
        logger.info(f"Get file {_name} from repo")
        
@driver.on_startup
async def what2eat_check() -> None:
    '''
        Check the path, gnerate the groups id saved in eating.json
        If needed, download the preset menu and greetings
    '''
    if not what2eat_config.what2eat_path.exists():
        what2eat_config.what2eat_path.mkdir(parents=True, exist_ok=True)
    
    '''
        If eating.json doesn't exist or eating.json exists but f.get["basic_food"] doesn't exist and USE_PRESET_MENU is True, download
        If USE_PRESET_MENU is False, break
    '''
    eating_json: Path = what2eat_config.what2eat_path / "eating.json"
    if what2eat_config.use_preset_menu:
        if not eating_json.exists():
            await download_file(eating_json, "eating.json")
        else:
            # Exists then check the keys
            with eating_json.open("r", encoding="utf-8") as f:
                _f: Dict[str, Union[List[str], Dict[str, Union[Dict[str, List[int]], List[str]]]]] = json.load(f)
                if not _f.get("basic_food", False):
                    _f.update({"basic_food", []})
                
                if not _f.get("group_food", False):
                    _f.update({"group_food", {}})
                    
                if not _f.get("count", False):
                    _f.update({"count", {}})
                
            save_json(eating_json, _f)
    
    '''
        If greetings.json doesn't exist or greetings.json exists but ... ALL doesn't exist and USE_PRESET_greetings is True, download
        If USE_PRESET_greetings is False, break
    '''
    greetings_json: Path = what2eat_config.what2eat_path / "greetings.json"
    if what2eat_config.use_preset_greetings:
        if not greetings_json.exists():
            await download_file(greetings_json, "greetings.json")    
        else:
            # Exists then check the keys
            with greetings_json.open("r", encoding="utf-8") as f:
                _f: Dict[str, Union[List[str], Dict[str, bool]]] = json.load(f)
                for meal in Meals:
                    if _f.get(meal.value[0], False):
                        _f.update({meal.value[0], []})
                
                if not _f.get("groups_id", False):
                    _f["groups_id"] = {}
            
            save_json(greetings_json, _f)
    
    # Save groups id in greetings.json if len > 0
    if len(what2eat_config.greeting_groups_id) > 0:
        with greetings_json.open("r", encoding="utf-8") as f:
            _f: Dict[str, Union[List[str], Dict[str, bool]]] = json.load(f)
            
            # Update the default groups    
            if not _f.get("groups_id", False):
                _f["groups_id"] = {}
                        
            for gid in what2eat_config.greeting_groups_id:
                _f["groups_id"].update({gid: True})
        
        save_json(greetings_json, _f)

__all__ = [
    Meals, what2eat_config, save_json
]