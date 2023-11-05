from nonebot.adapters.onebot.v11 import Bot
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, MessageEvent

from ... import config
from ...database import DB as db
from ...utils import get_type_id, on_command, to_me

sub_list = on_command("关注列表", aliases={"主播列表"}, rule=to_me(), priority=5, block=True)
print(sub_list)
sub_list.__doc__ = """关注列表"""

# sub_list.handle()(permission_check)


@sub_list.handle()
async def _(event: MessageEvent, bot: Bot):
    """发送当前位置的订阅列表"""
    message = "关注列表（所有群/好友/bot都是分开的）\n\n"
    print(event.message_type, await get_type_id(event), bot.self_id)
    subs = await db.get_sub_list(
        event.message_type, await get_type_id(event), bot.self_id
    )
    print(subs)
    for sub in subs:
        user = await db.get_user(uid=sub.uid)
        print(user)
        assert user is not None
        message += (
            f"{user.name}（{user.uid}）"
            f"直播：{'开' if sub.live else '关'}，"
            f"动态：{'开' if sub.dynamic else '关'}，"
            # TODO 私聊不显示全体
            f"全体：{'开' if sub.at else '关'}"
            f"{('，提示词：' + sub.live_tips) if sub.live_tips else ''}\n"
        )
    message = message.rstrip()
    # 大于8条时使用合并为转发消息
    if len(message.splitlines()) > 8 and isinstance(event, GroupMessageEvent):
        bot_id = int(bot.self_id)
        await bot.send_group_forward_msg(
            group_id=event.group_id,
            messages=[
                {
                    "type": "node",
                    "data": {
                        "name": config.bot_names[bot_id]
                        if bot_id in config.bot_names
                        else "一澄Bot",
                        "uin": bot.self_id,
                        "content": message,
                    },
                }
            ],
        )
    else:
        await sub_list.finish(message)
