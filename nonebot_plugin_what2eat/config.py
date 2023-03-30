from pathlib import Path
from pydantic import BaseModel, Extra
from typing import List, Dict, Set, Union, Any, Optional
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
    what2eat_auto_update: bool = False


driver = get_driver()
what2eat_config: PluginConfig = PluginConfig.parse_obj(driver.config.dict())


class ResourceError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class DownloadError(Exception):
    pass


async def download_url(name: str) -> Optional[Dict[str, Any]]:
    url: str = "https://raw.fgit.ml/MinatoAquaCrews/nonebot_plugin_what2eat/master/nonebot_plugin_what2eat/resource/" + name

    async with httpx.AsyncClient() as client:
        for i in range(3):
            try:
                response = await client.get(url)
                if response.status_code != 200:
                    continue

                return response.json()

            except Exception:
                logger.warning(
                    f"Error occured when downloading {url}, retry: {i+1}/3")

    logger.warning("Abort downloading")
    return None


@driver.on_startup
async def what2eat_check() -> None:
    if not what2eat_config.what2eat_path.exists():
        what2eat_config.what2eat_path.mkdir(parents=True, exist_ok=True)

    if not (what2eat_config.what2eat_path / "img").exists():
        (what2eat_config.what2eat_path / "img").mkdir(parents=True, exist_ok=True)

    '''
        Get the latest eating.json from repo.
        If it's newer than local,
        TODO get the union set of "basic_food".
    '''
    eating_json: Path = what2eat_config.what2eat_path / "eating.json"

    cur_version: float = 0
    if what2eat_config.what2eat_auto_update:
        response = await download_url("eating.json")
    else:
        response = None

    if response is None:
        if not eating_json.exists():
            logger.warning("What2eat text resource missing! Please check!")
            raise ResourceError("Missing necessary resource: eating.json!")

    else:
        # Get the latest eating.json from repo and local data exists, check the keys then merge
        try:
            version: float = response["version"]
        except KeyError:
            logger.warning(
                "What2eat text resource downloaded incompletely! Please check!")
            raise DownloadError

        # Get the latest eating.json from repo but local data doesn't exist, save
        if not eating_json.exists():
            save_json(eating_json, response)

        else:
            with eating_json.open("r", encoding="utf-8") as f:
                _f = json.load(f)
                
                # For version below 0.3.6, there's no key of "version"
                cur_version: float = _f.get("version", 0)
                
                if not _f.get("basic_food", False):
                    _f.update({"basic_food": []})

                if not _f.get("group_food", False):
                    _f.update({"group_food": {}})

                if not _f.get("count", False):
                    _f.update({"count": {}})

                # Update "basic_food" when there is a newer version
                if version > cur_version:
                    _f.update({"basic_food": response.get("basic_food", [])})
            
            save_json(eating_json, _f)
        
        if version > cur_version:
            logger.info(f"Updated eating.json, version: {cur_version} -> {version}")

    '''
        Get the latest drinks.json from repo.
        If it's newer than local, overwrite it.
        TODO Get the union set of drinks.json
    '''
    drinks_json: Path = what2eat_config.what2eat_path / "drinks.json"
    
    cur_version = 0
    if what2eat_config.what2eat_auto_update:
        response = await download_url("drinks.json")
    else:
        response = None
    
    if response is None:
        if not drinks_json.exists():
            logger.warning("What2eat text resource missing! Please check!")
            raise ResourceError("Missing necessary resource: drinks.json!")

    elif not drinks_json.exists():
        save_json(drinks_json, response)
    else:
        try:
            version = response["version"]
        except KeyError:
            logger.warning(
                "What2eat text resource downloaded incompletely! Please check!")
            raise DownloadError

        # Update when there is a newer version
        if version > cur_version:
            save_json(drinks_json, _f)
            logger.info(f"Updated drinks.json, version: {cur_version} -> {version}")

    '''
        Check greetings.json and its keys
        If doesn't exist, try to download. Otherwise, check its keys.
        greetings.json will NOT auto check for update.
    '''
    greetings_json: Path = what2eat_config.what2eat_path / "greetings.json"
    
    if not greetings_json.exists():
        response = download_url("greetings.json")
        
        if response is None:
            logger.warning("What2eat text resource missing! Please check!")
            raise ResourceError("Missing necessary resource: greetings.json!")
        else:
            save_json(greetings_json, response)
            logger.info(f"Downloaded greetings.json from repo")
    
    else:
        # Exists then check the keys
        with greetings_json.open("r", encoding="utf-8") as f:
            _f: Dict[str, Union[List[str], Dict[str, bool]]] = json.load(f)

            for meal in Meals:
                if not _f.get(meal.value[0], False):
                    _f.update({meal.value[0]: []})

            if not _f.get("groups_id", False):
                _f.update({"groups_id": {}})
            
            # Always update "groups_id" if greeting_groups_id is not empty
            if len(what2eat_config.greeting_groups_id) > 0:
                for gid in what2eat_config.greeting_groups_id:
                    _f["groups_id"].update({gid: True})

        save_json(greetings_json, _f)
