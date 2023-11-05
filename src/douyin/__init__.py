import asyncio

from . import vive_dynamic_dy  # noqa: F401
from .utils_dy.cookie_utils import auto_get_cookie
from .pusher import live_pusher_dy, dynamic_pusher_dy  # noqa: F401
from .sub import add_sub_dy, sub_list_dy, delete_sub_dy  # noqa: F401

asyncio.run(auto_get_cookie())
# 启动时获取下临时cookie
