from WExptend.manager.router import register_router


@register_router("test")
async def _(data):
    data["roure"] = "yes"
    return data