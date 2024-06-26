import time
import asyncio
from typing import Dict
from dataclasses import dataclass

from nonebot.log import logger
from bilireq.live import get_rooms_info_by_uids
from nonebot.adapters.onebot.v11.message import MessageSegment

from ... import config
from ...database import DB as db
from ...utils import PROXIES, safe_send, scheduler, format_time_span


@dataclass
class LiveStatusData:
    """直播间状态数据"""

    status_code: int
    online_time: float = 0
    offline_time: float = 0


all_status: Dict[str, LiveStatusData] = {}  # [uid, LiveStatusData]


@scheduler.scheduled_job(
    "interval", seconds=config.haruka_live_interval, id="live_sched"
)
async def live_sched():  # noqa: C901
    """直播推送"""

    # if not bili_auth.is_logined:
    #     await asyncio.sleep(1)
    #     return

    uids = await db.get_uid_list("live")

    if not uids:  # 订阅为空
        return
    logger.debug(
        f"爬取直播列表，目前开播{sum(o.status_code for o in all_status.values())}人，总共{len(uids)}人"
    )
    try:
        res = await get_rooms_info_by_uids(uids, reqtype="web", proxies=PROXIES)
    except Exception as e:
        logger.error(f"获取开播列表失败: {e}")
        return

    if not res:
        return
    for uid, info in res.items():
        new_status = 0 if info["live_status"] == 2 else info["live_status"]
        if uid not in all_status:
            all_status[uid] = LiveStatusData(new_status)
            continue
        status_data: LiveStatusData = all_status[uid]
        old_status = status_data.status_code
        if new_status == old_status:  # 直播间状态无变化
            continue
        status_data.status_code = new_status

        name = info["uname"]
        title = ""
        area_name = ""
        cover = ""
        url = ""
        if new_status:  # 开播
            status_data.online_time = time.time()
            room_id = info["short_id"] if info["short_id"] else info["room_id"]
            url = "https://live.bilibili.com/" + str(room_id)
            title = info["title"]
            area_name = f"{info['area_v2_parent_name']} - {info['area_v2_name']}"
            cover = (
                info["cover_from_user"] if info["cover_from_user"] else info["keyframe"]
            )
            logger.info(f"检测到开播：{name}（{uid}）")

            live_msg = (
                f"{name} 正在直播\n--------------------\n标题：{title}\n分区：{area_name}\n"
                + MessageSegment.image(cover)
                + f"\n{url}"
            )
        else:  # 下播
            status_data.offline_time = time.time()
            logger.info(f"检测到下播：{name}（{uid}）")
            if not config.haruka_live_off_notify:  # 没开下播推送
                continue
            if status_data.online_time > 0:
                live_msg = f"{name} 下播了\n本次直播时长 {format_time_span(status_data.offline_time - status_data.online_time)}"
            else:
                live_msg = f"{name} 下播了"

        # 推送
        push_list = await db.get_push_list(uid, "live")
        for sets in push_list:
            logger.debug(sets.__dict__)
            real_live_msg = live_msg
            if new_status and sets.live_tips:
                # 自定义开播提示词
                real_live_msg = (
                    f"{sets.live_tips}\n--------------------\n标题：{title}\n分区：{area_name}\n"
                    + MessageSegment.image(cover)
                    + f"\n{url}"
                )
            await safe_send(
                bot_id=sets.bot_id,
                send_type=sets.type,
                type_id=sets.type_id,
                message=real_live_msg,
                at=sets.at,
            )
            await asyncio.sleep(0.7)
        await db.update_user(int(uid), name)
