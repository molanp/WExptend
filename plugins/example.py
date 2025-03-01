# 插件示例（plugins/monitor.py）
from WExptend.log import logger
from WExptend.manager.plugin import Plugin


@Plugin.on_system_event("connect")
async def log_connection(data: dict):
    logger.info(f"新连接来自：{data['client_ip']}")


@Plugin.on_system_event("disconnect")
async def log_disconnection(data: dict):
    logger.info(f"断开连接：{data['client_ip']}")


@Plugin.on_action()
async def preprocess_chat(data: dict):
    logger.info(f"请求数据：{data}")
    return data
