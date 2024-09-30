from nonebot.params import ArgPlainText
from bilireq.exceptions import ResponseCodeError
from nonebot_plugin_guild_patch import GuildMessageEvent
from nonebot.adapters.onebot.v11.event import MessageEvent

from ...database import DB as db
from ...bili_auth import bili_auth
from ...utils import (
    PROXIES,
    to_me,
    uid_check,
    handle_uid,
    on_command,
    get_type_id,
    get_user_card,
    permission_check,
)

add_sub = on_command("关注", aliases={"添加主播"}, rule=to_me(), priority=5, block=True)
add_sub.__doc__ = """关注 UID"""

add_sub.handle()(permission_check)

add_sub.handle()(handle_uid)

add_sub.got("uid", prompt="请输入要关注的UID")(uid_check)


@add_sub.handle()
async def _(event: MessageEvent, uid: str = ArgPlainText("uid")):
    """根据 UID 订阅 UP 主"""
    user = await db.get_user(uid=uid)
    name = user and user.name
    if not name:
        try:
            name = (
                await get_user_card(
                    uid,
                    bili_auth.get_dict_auth_cookies(),
                    proxies=PROXIES,
                    auth=bili_auth.auth,
                )
            )["name"]
        except ResponseCodeError as e:
            if e.code == -400 or e.code == -404:
                await add_sub.finish("UID不存在，注意UID不是房间号")
            elif e.code == -412:
                await add_sub.finish("操作过于频繁IP暂时被风控，请半小时后再尝试")
            else:
                await add_sub.finish(
                    f"未知错误，请联系开发者反馈，错误内容：\n\
                                    {str(e)}"
                )

    if isinstance(event, GuildMessageEvent):
        await db.add_guild(
            guild_id=event.guild_id, channel_id=event.channel_id, admin=True
        )
    result = await db.add_sub(
        uid=uid,
        type=event.message_type,
        type_id=await get_type_id(event),
        bot_id=event.self_id,
        name=name,
        # TODO 自定义默认开关
        live=True,
        dynamic=True,
        at=False,
        live_tips="",
    )
    if result:
        await add_sub.finish(f"已关注 {name}（{uid}）")
    await add_sub.finish(f"{name}（{uid}）已经关注了")
