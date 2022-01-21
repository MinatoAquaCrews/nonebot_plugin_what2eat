from nonebot import on_command, on_regex
from nonebot.adapters.cqhttp.permission import GROUP
from nonebot.adapters.cqhttp import Bot, GroupMessageEvent, MessageEvent
import nonebot
from nonebot.typing import T_State
from nonebot.log import logger
from .utils import eating_manager

from nonebot import require
scheduler = require("nonebot_plugin_apscheduler").scheduler

what2eat = on_regex(r"^(今天|[早中午晚][上饭餐午]|夜宵|今晚)吃(什么|啥|点啥)", priority=15, block=True)
add_food = on_command("添加", permission=GROUP, priority=15, block=True)
remove_food = on_command("移除", permission=GROUP, priority=15, block=True)

@what2eat.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    user_id = str(event.user_id)
    result = eating_manager.get2eat(user_id, event)
    
    await what2eat.finish(result)

@add_food.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    args = str(event.get_plaintext()).strip().split()
    if not args:
        await add_food.finish("还没输入你要添加的菜品呢~")
    elif args and len(args) == 1:
        new_food = args[0]
    else:
        await add_food.finish("添加菜品参数错误~")
    
    user_id = str(event.user_id)
    logger.info(f"User {user_id} 添加了 {new_food} 至菜单")
    await add_food.finish(eating_manager.add_food(new_food))

@remove_food.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    args = str(event.get_plaintext()).strip().split()
    if not args:
        await add_food.finish("还没输入你要移除的菜品呢~")
    elif args and len(args) == 1:
        food_to_remove = args[0]
    else:
        await add_food.finish("移除菜品参数错误~")
    
    user_id = str(event.user_id)
    logger.info(f"User {user_id} 从菜单移除了 {food_to_remove}")
    await add_food.finish(eating_manager.remove_food(food_to_remove))


# 重置三餐吃什么次数
@scheduler.scheduled_job(
    "cron",
    hour="6,11,17", # 每日6、11、17时执行
    minute=0,
)

async def _():
    eating_manager.reset_eating_times()
    logger.info("今天吃什么次数已刷新")