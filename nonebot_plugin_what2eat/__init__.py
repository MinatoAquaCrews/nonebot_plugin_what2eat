from nonebot import on_command, on_regex
from nonebot.permission import SUPERUSER
from nonebot.adapters.cqhttp.permission import GROUP, GROUP_ADMIN, GROUP_OWNER
from nonebot.adapters.cqhttp import Bot, GroupMessageEvent
from nonebot.typing import T_State
from nonebot.log import logger
from .utils import eating_manager

from nonebot import require
scheduler = require("nonebot_plugin_apscheduler").scheduler

what2eat = on_regex(r"^(今天|[早中午晚][上饭餐午]|早上|夜宵|今晚)吃(什么|啥|点啥)", permission=GROUP, priority=15, block=True)
add_group = on_command("添加", permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER, priority=15, block=True)
remove_food = on_command("移除", permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER, priority=15, block=True)
add_basic = on_command("加菜", permission=SUPERUSER, priority=15, block=True)
show = on_command("查看菜单", aliases={"群菜单"}, permission=GROUP, priority=15, block=True)

@what2eat.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    msg = eating_manager.get2eat(event)
    await what2eat.finish(msg)

@add_group.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    args = str(event.get_plaintext()).strip().split()
    if not args:
        await add_group.finish("还没输入你要添加的菜品呢~")
    elif args and len(args) == 1:
        new_food = args[0]
    else:
        await add_group.finish("添加菜品参数错误~")
    
    user_id = str(event.user_id)
    logger.info(f"User {user_id} 添加了 {new_food} 至菜单")
    msg = eating_manager.add_group_food(new_food, event)

    await add_group.finish(msg)

@add_basic.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    args = str(event.get_plaintext()).strip().split()
    if not args:
        await add_basic.finish("还没输入你要添加的菜品呢~")
    elif args and len(args) == 1:
        new_food = args[0]
    else:
        await add_basic.finish("添加菜品参数错误~")
    
    user_id = str(event.user_id)
    logger.info(f"Superuser {user_id} 添加了 {new_food} 至基础菜单")
    msg = eating_manager.add_basic_food(new_food)

    await add_basic.finish(msg)

@remove_food.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    args = str(event.get_plaintext()).strip().split()
    if not args:
        await remove_food.finish("还没输入你要移除的菜品呢~")
    elif args and len(args) == 1:
        food_to_remove = args[0]
    else:
        await remove_food.finish("移除菜品参数错误~")
    
    user_id = str(event.user_id)
    logger.info(f"User {user_id} 从菜单移除了 {food_to_remove}")
    msg = eating_manager.remove_food(food_to_remove, event)

    await remove_food.finish(msg)

@show.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    '''
        show_basic: 显示基础菜单，避免菜单过长导致刷屏
    '''
    msg = eating_manager.show_menu(event, show_basic=False)
    await show.finish(msg)


# 重置吃什么次数，包括夜宵
@scheduler.scheduled_job(
    "cron",
    hour="6,11,17,22",
    minute=0,
)

async def _():
    eating_manager.reset_eating()
    logger.info("今天吃什么次数已刷新")