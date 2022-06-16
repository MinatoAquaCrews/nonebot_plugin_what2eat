from pathlib import Path
from typing import List, Dict, Union
from nonebot import logger
from pydantic.errors import PathError
from .config import what2eat_config, save_json
try:
    import ujson as json
except ModuleNotFoundError:
    import json
  
def do_compatible(new_eating_json: Path, new_greeting_json: Path) -> None:
    '''
        v0.3.0 is compatible with configure json file of version 0.2.x, but will be deprecated in next version
        Rename old file(data.json) to eating.json, greating.json(that's a wrong word) to greetings.json
        Replace old keys(eating) with new keys(count)
    '''
    logger.warning("v0.3.0 is compatible with configure json file of version 0.2.x, but will be deprecated in next version")
    
    old_data_json: Path = what2eat_config.what2eat_path / "data.json"
    
    if not old_data_json.exists():
        logger.info(f"Old data.json doesn't exist, ignored: {old_data_json}")
    else:
        # Rename
        res = old_data_json.rename(new_eating_json)
        if not res.exists():
            logger.warning(f"Create json files of new version failed!")
            raise PathError
        else:
            with new_eating_json.open("r", encoding="utf-8") as f:
                # Change key value
                _f: Dict[str, Union[List[str], Dict[str, Union[Dict[str, List[int]], List[str]]]]] = json.load(f)
                _f["count"] = _f.pop("eating")
            
            save_json(new_eating_json, _f)
    
    old_greating_json: Path = what2eat_config.what2eat_path / "greating.json"
    
    if not old_greating_json.exists():
        logger.info(f"Old greating.json doesn't exist, ignored: {old_greating_json}")
    else:
        # Rename
        res = old_greating_json.rename(new_greeting_json)
        if not res.exists():
            logger.warning(f"Create json files of new version failed!")
            raise PathError

__all__ = [
    do_compatible
]