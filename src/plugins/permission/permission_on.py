from typing import Union

from nonebot.adapters.onebot.v11 import Bot
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from nonebot_plugin_guild_patch import GuildMessageEvent

from ...cli.handle_message_sent import GroupMessageSentEvent
from ...database import DB as db
from ...utils import group_only, on_command, permission_check, to_me

permission_on = on_command(
    "开启权限",
    rule=to_me(),
    # permission=GROUP_OWNER | GROUP_ADMIN | SUPERUSER | GUILD_ADMIN | BOT_SELF,
    priority=5,
    block=True,
)
permission_on.__doc__ = """开启权限"""

permission_on.handle()(permission_check)
permission_on.handle()(group_only)


@permission_on.handle()
async def _(
    event: Union[GroupMessageEvent, GroupMessageSentEvent, GuildMessageEvent], bot: Bot
):
    """开启当前群权限"""
    if isinstance(event, GuildMessageEvent):
        if await db.set_guild_permission(
            event.guild_id, event.channel_id, bot.self_id, True
        ):
            await permission_on.finish("已开启权限，只有管理员和主人可以操作")
    else:
        if await db.set_group_permission(event.group_id, bot.self_id, True):
            await permission_on.finish("已开启权限，只有管理员和主人可以操作")
    await permission_on.finish("权限已经开启了，只有管理员和主人可以操作")
