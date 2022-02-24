import os
from pydantic import BaseModel
from typing import List

class PluginConfig(BaseModel):
    use_preset_menu: bool = False
    use_preset_greating: bool = False
    superusers: List = []
    what2eat_path: str = os.path.join(os.path.dirname(__file__), "resource")
    eating_limit: int = 5
    groups_id: List = []
    
    class Config:
        extra = "ignore"