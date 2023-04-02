from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

import httpx
from nonebot import get_driver, logger
from pydantic import BaseModel, Extra

from .utils import Meals, save_json

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


async def eating_check() -> None:
    '''
        Get the latest eating.json from repo.
        If it's newer than local, get the union set of "basic_food".
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

        # Merge "basic_food"
        else:
            with eating_json.open("r", encoding="utf-8") as f:
                _local = json.load(f)

                # For version below 0.3.6, there's no key of "version", set default 0
                cur_version = _local.get("version", 0)

                if not _local.get("basic_food", False):
                    _local.update({"basic_food": []})

                if not _local.get("group_food", False):
                    _local.update({"group_food": {}})

                if not _local.get("count", False):
                    _local.update({"count": {}})

                # Merge "basic_food" when there is a newer version
                if version > cur_version:
                    _local.update({"version": version})

                    local_basic_food: List[str] = _local.get("basic_food", [])
                    newer_basic_food: List[str] = response.get(
                        "basic_food", [])
                    merged_basic_food: List[str] = list(
                        set(local_basic_food).union(set(newer_basic_food)))

                    _local.update({"basic_food": merged_basic_food})

            save_json(eating_json, _local)

        if version > cur_version:
            logger.info(
                f"Updated eating.json, version: {cur_version} -> {version}")


async def drinks_check() -> None:
    '''
        Get the latest drinks.json from repo.
        If it's newer than local, get the union set of each keys in drinks.json
    '''
    drinks_json: Path = what2eat_config.what2eat_path / "drinks.json"
    cur_version: float = 0

    if what2eat_config.what2eat_auto_update:
        response = await download_url("drinks.json")
    else:
        response = None

    if response is None:
        if not drinks_json.exists():
            logger.warning("What2eat text resource missing! Please check!")
            raise ResourceError("Missing necessary resource: drinks.json!")

    else:
        try:
            version: float = response["version"]
        except KeyError:
            logger.warning(
                "What2eat text resource downloaded incompletely! Please check!")
            raise DownloadError

        # Update when there is a newer version
        if version > cur_version:
            if not drinks_json.exists():
                save_json(drinks_json, response)
            else:
                with drinks_json.open("r", encoding="utf-8") as f:
                    _local: Dict[str, Union[float, List[str]]] = json.load(f)

                    # Merge keys
                    local_branches: List[str] = _local.keys()
                    newer_branches: List[str] = response.keys()
                    merged_branches: List[str] = list(
                        set(local_branches).union(set(newer_branches)))

                    # Merge each of drink branches
                    for branch in merged_branches:
                        if branch == "version":
                            _local.update({branch: response[branch]})
                            continue

                        if branch in _local:
                            # Branch in local and in repo, merge drinking list
                            if branch in response:
                                local_drinks: List[str] = _local.get(
                                    branch, [])
                                newer_drinks: List[str] = response.get(
                                    branch, [])
                                merged_drinks: List[str] = list(
                                    set(local_drinks).union(set(newer_drinks)))

                                _local.update({branch: merged_drinks})
                        else:
                            # Branch but in local, update it
                            _local.update({branch: response[branch]})

                save_json(drinks_json, _local)

            logger.info(
                f"Updated drinks.json, version: {cur_version} -> {version}")


async def greetings_check() -> None:
    '''
        Check greetings.json and its keys
        If doesn't exist, try to download. Otherwise, check its keys.
        greetings.json will NOT auto check for update.
    '''
    greetings_json: Path = what2eat_config.what2eat_path / "greetings.json"

    if not greetings_json.exists():
        response = await download_url("greetings.json")

        if response is None:
            logger.warning("What2eat text resource missing! Please check!")
            raise ResourceError("Missing necessary resource: greetings.json!")
        else:
            save_json(greetings_json, response)
            logger.info(f"Downloaded greetings.json from repo")
    else:
        # Exists then check the keys
        with greetings_json.open("r", encoding="utf-8") as f:
            _local: Dict[str, Union[List[str], Dict[str, bool]]] = json.load(f)

            for meal in Meals:
                if not _local.get(meal.value[0], False):
                    _local.update({meal.value[0]: []})

            if not _local.get("groups_id", False):
                _local.update({"groups_id": {}})

            # Always update "groups_id" if greeting_groups_id is not empty
            if len(what2eat_config.greeting_groups_id) > 0:
                for gid in what2eat_config.greeting_groups_id:
                    _local["groups_id"].update({gid: True})

        save_json(greetings_json, _local)


@driver.on_startup
async def what2eat_check() -> None:
    if not what2eat_config.what2eat_path.exists():
        what2eat_config.what2eat_path.mkdir(parents=True, exist_ok=True)

    if not (what2eat_config.what2eat_path / "img").exists():
        (what2eat_config.what2eat_path / "img").mkdir(parents=True, exist_ok=True)

    await eating_check()
    await drinks_check()
    await greetings_check()
