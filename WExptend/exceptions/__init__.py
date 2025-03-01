import traceback
from WExptend.log import logger


async def handle_exception(e):
    error_message = str(e)
    logger.error(traceback.format_exc())
    return f"[CrashHandle]{error_message}\n>>更多信息详见日志文件<<"
