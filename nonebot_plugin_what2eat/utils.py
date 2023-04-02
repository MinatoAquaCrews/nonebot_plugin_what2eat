from enum import Enum
from pathlib import Path
from typing import Any, List, Optional

import aiofiles
import httpx
from nonebot import logger
from nonebot.adapters.onebot.v11 import Message, MessageSegment

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
    IN_BASIC = "In basic"
    IN_GROUP = "In group"
    NOT_EXISTS = "Not exists"


class SearchLoc(Enum):
    IN_BASIC = "In basic"
    IN_GROUP = "In group"
    IN_GLOBAL = "In global"


EatingEnough_List: List[str] = [
    "你今天已经吃得够多了！",
    "吃这么多的吗？",
    "害搁这吃呢？不工作的吗？",
    "再吃肚子就要爆炸咯~",
    "你是米虫吗？今天碳水要爆炸啦！",
    "去码头整点薯条吧🍟"
]

DrinkingEnough_List: List[str] = [
    "你今天已经喝得够多了！",
    "喝这么多的吗？",
    "害搁这喝呢？不工作的吗？",
    "再喝肚子就要爆炸咯~",
    "你是水桶吗？今天糖分要超标啦！"
]


def save_json(_file: Path, _data: Any) -> None:
    with open(_file, 'w', encoding='utf-8') as f:
        json.dump(_data, f, ensure_ascii=False, indent=4)


def load_json(_file: Path) -> Any:
    with open(_file, 'r', encoding='utf-8') as f:
        return json.load(f)


async def get_image_from_url(url: str) -> Optional[bytes]:
    async with httpx.AsyncClient() as client:
        for i in range(3):
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    continue

                return resp.content

            except Exception:
                logger.warning(
                    f"Error occurred when downloading {url}, retry: {i+1}/3")

    logger.warning(f"Download image failed: {url}")
    return None


async def save_image(_img: bytes, _path: Path) -> None:
    async with aiofiles.open(_path, "wb") as f:
        await f.write(_img)


async def save_cq_image(msg: Message, img_dir: Path) -> None:
    for msg_seg in msg:
        if msg_seg.type == "image":
            filename = msg_seg.data.get("file", False)
            if filename is False:
                continue

            # Check whether there is a same name image
            images: List[str] = [
                f.name for f in img_dir.iterdir() if f.is_file()]
            filepath: Path = img_dir / filename

            if filename not in images:
                url = msg_seg.data.get("url", False)
                if url is False:
                    continue

                data = await get_image_from_url(url)
                if not data:
                    continue

                await save_image(data, filepath)

            msg_seg.data["file"] = MessageSegment.image(filepath)


def delete_cq_image(str_cq: str) -> bool:
    _start: int = str_cq.find("file://")
    if _start == -1:
        return False

    _end: int = str_cq.find(".image")
    if _end == -1:
        return False

    delete_path: Path = Path(str_cq[_start + 7: _end + 6])
    if not delete_path.is_file():
        return False

    delete_path.unlink()

    return not delete_path.is_file()


def get_cq_image_path(str_cq: str) -> str:
    return str_cq[str_cq.find("file://") + 7: str_cq.find(".image") + 6]
