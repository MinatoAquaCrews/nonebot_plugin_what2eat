from pathlib import Path
from pydantic import BaseModel, Extra
from typing import List, Dict, Set, Union, Any
from nonebot import get_driver, logger
from .utils import save_json, Meals
import httpx
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
    
driver = get_driver()
what2eat_config: PluginConfig = PluginConfig.parse_obj(driver.config.dict())

class DownloadError(Exception):
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return self.msg
    
async def download_url(url: str) -> Any:
    async with httpx.AsyncClient() as client:
        for i in range(3):
            try:
                response = await client.get(url)
                if response.status_code != 200:
                    continue
                return response.json()
            except Exception:
                logger.warning(f"Error occured when downloading {url}, retry: {i+1}/3")
    
    raise DownloadError(f"Reseource {url} download failed! Please check!")
               
async def download_file(_file: Path, _name: str) -> None:
    _url = "https://raw.fastgit.org/MinatoAquaCrews/nonebot_plugin_what2eat/beta/nonebot_plugin_what2eat/resource/"
    url = _url + _name
    
    resp = await download_url(url)
    save_json(_file, resp)
    
    logger.info(f"Get file {_name} from repo")
        
@driver.on_startup
async def what2eat_check() -> None:
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
            # check the keys
            with eating_json.open("r", encoding="utf-8") as f:
                _f: Dict[str, Union[List[str], Dict[str, Union[Dict[str, List[int]], List[str]]]]] = json.load(f)
                if not _f.get("basic_food", False):
                    _f.update({"basic_food": []})
                
                if not _f.get("group_food", False):
                    _f.update({"group_food": {}})
                    
                if not _f.get("count", False):
                    _f.update({"count": {}})
                
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
                        _f.update({meal.value[0]: []})
                
                if not _f.get("groups_id", False):
                    _f["groups_id"] = {}
            
            save_json(greetings_json, _f)
    
    drinking_json: Path = what2eat_config.what2eat_path / "drinks.json"
    if not drinking_json.exists():
        await download_file(drinking_json, "drinks.json")
    
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
    what2eat_config
]
