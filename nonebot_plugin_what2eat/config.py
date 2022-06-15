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
    use_preset_menu: bool = True
    use_preset_greetings: bool = True
    eating_limit: int = 5
    greeting_groups_id: Set[str] = set() # e.g. {"123456", "654321"} or ["123456", "654321"]
    superusers : Set[str] = set()
    
class Meals(Enum):
    BREAKFAST   = "breakfast"
    LUNCH       = "lunch"
    SNACK       = "snack"
    DINNER      = "dinner"
    MIDNIGHT    = "midnight"
    
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
    _data = {}
    if _name == "eating.json":
        _data["basic_food"] = []
        _data["group_food"] = {}
        _data["count"] = {}
        save_json(_file, _data)
    else:
        for meal in Meals:
            if meal not in _data:
                _data[meal] = []
        
        _data["groups_id"] = {}
        save_json(_file, _data)
               
async def download_file(_url: str, _file: Path, _name: str) -> None:
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
        Check the path
        Generate the groups id saved in eating.json
        If needed, download the preset menu and greetings
    '''
    if not what2eat_config.what2eat_path.exists():
        what2eat_config.what2eat_path.mkdir(parents=True, exist_ok=True)

    _url = "https://raw.fastgit.org/MinatoAquaCrews/nonebot_plugin_what2eat/beta/nonebot_plugin_what2eat/resource/"
    
    '''
        If eating.json doesn't exist or eating.json exists but f.get["basic_food"] doesn't exist and USE_PRESET_MENU is True, download
        If USE_PRESET_MENU is False, break
    '''
    eating_json_path: Path = what2eat_config.what2eat_path / "eating.json"
    
    if what2eat_config.use_preset_menu:
        if not eating_json_path.exists():
            await download_file(_url, eating_json_path, "eating.json")
        else:
            with eating_json_path.open("r", encoding="utf-8") as f:
                _f: Dict[str, Union[List[str], Dict[str, Union[Dict[str, List[int]], List[str]]]]] = json.load(f)
                if not _f.get("basic_food", False):
                    await download_file(_url, eating_json_path, "eating.json")
    
    '''
        If greetings.json doesn't exist or greetings.json exists but ... ALL doesn't exist and USE_PRESET_greetings is True, download
        If USE_PRESET_greetings is False, break
    '''
    greetings_json_path: Path = what2eat_config.what2eat_path / "greetings.json"
    
    if what2eat_config.use_preset_greetings:
        if not greetings_json_path.exists():
            await download_file(_url, greetings_json_path, "greetings.json")    
        else:
            with greetings_json_path.open("r", encoding="utf-8") as f:
                _f: Dict[str, Union[List[str], Dict[str, bool]]] = json.load(f)
                if not _f.get("breakfast", False) or not _f.get("lunch", False) or \
                    not _f.get("snack", False) or not _f.get("dinner", False) or \
                        not _f.get("midnight", False):
                    await download_file(_url, greetings_json_path, "greetings.json")    
    
    # Save groups id in greetings.json if len > 0
    if len(what2eat_config.greeting_groups_id) > 0:
        with greetings_json_path.open("r", encoding="utf-8") as f:
            _f: Dict[str, Union[List[str], Dict[str, bool]]] = json.load(f)
            
            # Update the default groups
            for gid in what2eat_config.greeting_groups_id:
                _f["groups_id"].update({gid: True})
                
            json.dump(_f, f, ensure_ascii=False, indent=4)

__all__ = [
    Meals, what2eat_config
]