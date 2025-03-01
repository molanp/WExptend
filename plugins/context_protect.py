from WExptend.manager.plugin import Plugin


@Plugin.on_action(".*", priority=100)  # 最高优先级确保最先执行
async def protect_original_action(data: dict):
    """保护原始action不被篡改"""
    if "_original_action" not in data:
        data["_original_action"] = data.get("_original_action", "")
    return data
