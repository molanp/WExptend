from WExptend.manager.router import on_command, on_regex


@on_command("create_order")
async def create_order(data: dict):
    """创建订单"""
    return {
        "order_id": data["product_id"],
        "price": data["quantity"] * data["unit_price"],
    }


@on_regex(r"^get_order_\d+$")
async def get_order(data: dict):
    """正则匹配订单查询"""
    action = data["_original_action"]  # 通过插件获取原始action
    order_id = action.split("_")[-1]
    return {"status": "found", "order_id": order_id}
