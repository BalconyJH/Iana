from typing import List

from nonebot.matcher import matchers
from nonebot.adapters.onebot.v11.event import MessageEvent
from nonebot.adapters.onebot.v11 import Bot, MessageSegment

from .. import config
from ..version import __version__
from ..utils import to_me, on_command, text_to_img

help = on_command(
    "帮助", aliases={"help"}, rule=to_me(), priority=5, block=True
)  # 数值越小优先级越高


@help.handle()
async def _(event: MessageEvent, bot: Bot):
    bot_id = int(bot.self_id)
    if bot_id in config.bot_names:
        message = f"<font color=green><b>{config.bot_names[bot_id]}目前支持的功能：</b></font>\n（请将UID替换为需要操作的B站UID）\n"
    else:
        message = "<font color=green><b>Bot目前支持的功能：</b></font>\n（请将UID替换为需要操作的B站UID）\n"

    plugin_names: List[str] = []
    for matchers_list in matchers.values():
        for matcher in matchers_list:
            if (
                matcher.plugin_name
                and matcher.plugin_name.startswith("src")
                and matcher.__doc__
            ):
                doc = matcher.__doc__
                plugin_names.append(doc)

                func_name = doc[2:]
                open_func = f"开启{func_name}"
                close_func = f"关闭{func_name}"
                if (open_func in plugin_names) and (close_func in plugin_names):
                    plugin_names.remove(open_func)
                    plugin_names.remove(close_func)
                    plugin_names.append(f"开启|关闭{func_name}")

                open_func2 = f"关注{func_name}"
                close_func2 = f"取关{func_name}"
                if (open_func2 in plugin_names) and (close_func2 in plugin_names):
                    plugin_names.remove(open_func2)
                    plugin_names.remove(close_func2)
                    plugin_names.append(f"关注|取关{func_name}")

    message += "\n".join(plugin_names) + "\n"
    message += "示例：开启动态 123456\n"

    message = MessageSegment.image(await text_to_img(message, width=425))
    message += f"\n当前版本：v{__version__}\n"
    await help.finish(message)
